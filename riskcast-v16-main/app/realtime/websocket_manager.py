"""
WebSocket Connection Manager

Features:
1. Connection management
2. Room-based subscriptions
3. Authentication
4. Heartbeat/keepalive
5. Message broadcasting
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.logging import get_logger


logger = get_logger(__name__)


class MessageType(str, Enum):
    """WebSocket message types."""
    # Client -> Server
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    
    # Server -> Client
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    PONG = "pong"
    ERROR = "error"
    
    # Data messages
    RISK_UPDATE = "risk_update"
    QUOTE_UPDATE = "quote_update"
    POLICY_UPDATE = "policy_update"
    ALERT = "alert"
    MARKET_DATA = "market_data"


@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client."""
    websocket: WebSocket
    client_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WebSocketManager:
    """
    Manages WebSocket connections and message routing.
    
    Features:
    - Connection lifecycle management
    - Room-based pub/sub
    - Tenant isolation
    - Heartbeat monitoring
    - Targeted messaging (user, tenant, room, broadcast)
    """
    
    def __init__(self, heartbeat_interval: int = 30):
        # Connection tracking
        self._clients: Dict[str, WebSocketClient] = {}
        
        # Room-based subscriptions: room_name -> set of client_ids
        self._rooms: Dict[str, Set[str]] = {}
        
        # User to client mapping for targeted messages
        self._user_clients: Dict[str, Set[str]] = {}
        
        # Tenant to client mapping
        self._tenant_clients: Dict[str, Set[str]] = {}
        
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Start the WebSocket manager."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("WebSocket manager started", heartbeat_interval=self._heartbeat_interval)
    
    async def stop(self):
        """Stop the WebSocket manager."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for client in list(self._clients.values()):
            await self.disconnect(client.client_id)
        
        logger.info("WebSocket manager stopped", final_connection_count=0)
    
    async def connect(
        self,
        websocket: WebSocket,
        token: Optional[str] = None
    ) -> WebSocketClient:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
            token: Optional JWT token for authentication
            
        Returns:
            WebSocketClient instance
            
        Raises:
            Exception if authentication fails
        """
        await websocket.accept()
        
        client_id = str(uuid.uuid4())
        user_id = None
        tenant_id = None
        
        # Authenticate if token provided
        if token:
            try:
                # Import here to avoid circular dependency
                from app.core.security import verify_token
                payload = verify_token(token)
                user_id = payload.get("sub")
                tenant_id = payload.get("tenant_id")
            except Exception as e:
                logger.warning(f"WebSocket auth failed: {e}")
                await websocket.close(code=4001, reason="Authentication failed")
                raise
        
        client = WebSocketClient(
            websocket=websocket,
            client_id=client_id,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        async with self._lock:
            self._clients[client_id] = client
            
            if user_id:
                if user_id not in self._user_clients:
                    self._user_clients[user_id] = set()
                self._user_clients[user_id].add(client_id)
            
            if tenant_id:
                if tenant_id not in self._tenant_clients:
                    self._tenant_clients[tenant_id] = set()
                self._tenant_clients[tenant_id].add(client_id)
        
        logger.info(
            "WebSocket connected",
            client_id=client_id,
            user_id=user_id,
            tenant_id=tenant_id,
            total_connections=len(self._clients)
        )
        
        return client
    
    async def disconnect(self, client_id: str):
        """
        Disconnect a WebSocket client.
        
        Args:
            client_id: Client identifier
        """
        async with self._lock:
            client = self._clients.pop(client_id, None)
            
            if not client:
                return
            
            # Remove from user mapping
            if client.user_id and client.user_id in self._user_clients:
                self._user_clients[client.user_id].discard(client_id)
                if not self._user_clients[client.user_id]:
                    del self._user_clients[client.user_id]
            
            # Remove from tenant mapping
            if client.tenant_id and client.tenant_id in self._tenant_clients:
                self._tenant_clients[client.tenant_id].discard(client_id)
                if not self._tenant_clients[client.tenant_id]:
                    del self._tenant_clients[client.tenant_id]
            
            # Remove from all rooms
            for room_name in list(client.subscriptions):
                await self._leave_room(client_id, room_name)
            
            # Close WebSocket
            try:
                if client.websocket.client_state == WebSocketState.CONNECTED:
                    await client.websocket.close()
            except Exception:
                pass
        
        logger.info(
            "WebSocket disconnected",
            client_id=client_id,
            total_connections=len(self._clients)
        )
    
    async def subscribe(self, client_id: str, room: str):
        """
        Subscribe a client to a room.
        
        Args:
            client_id: Client identifier
            room: Room name (e.g., "tenant:ABC:risks", "policy:123")
            
        Returns:
            bool: True if subscribed successfully
        """
        async with self._lock:
            client = self._clients.get(client_id)
            if not client:
                return False
            
            # Validate room access (e.g., tenant isolation)
            if not self._can_access_room(client, room):
                await self.send_error(client_id, f"Access denied to room: {room}")
                logger.warning(
                    "Room access denied",
                    client_id=client_id,
                    room=room,
                    tenant_id=client.tenant_id
                )
                return False
            
            if room not in self._rooms:
                self._rooms[room] = set()
            
            self._rooms[room].add(client_id)
            client.subscriptions.add(room)
        
        await self.send_to_client(client_id, {
            "type": MessageType.SUBSCRIBED,
            "room": room,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.debug(
            "Client subscribed to room",
            client_id=client_id,
            room=room,
            total_rooms=len(self._rooms)
        )
        return True
    
    async def unsubscribe(self, client_id: str, room: str):
        """
        Unsubscribe a client from a room.
        
        Args:
            client_id: Client identifier
            room: Room name
        """
        await self._leave_room(client_id, room)
        
        await self.send_to_client(client_id, {
            "type": MessageType.UNSUBSCRIBED,
            "room": room,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.debug("Client unsubscribed from room", client_id=client_id, room=room)
    
    async def _leave_room(self, client_id: str, room: str):
        """Internal method to leave a room."""
        async with self._lock:
            if room in self._rooms:
                self._rooms[room].discard(client_id)
                if not self._rooms[room]:
                    del self._rooms[room]
            
            client = self._clients.get(client_id)
            if client:
                client.subscriptions.discard(room)
    
    def _can_access_room(self, client: WebSocketClient, room: str) -> bool:
        """
        Check if client can access a room.
        Implements tenant isolation and access control.
        
        Args:
            client: WebSocket client
            room: Room name
            
        Returns:
            bool: True if access granted
        """
        # Public rooms (market data, etc.)
        if room.startswith("public:"):
            return True
        
        # Tenant-specific rooms
        if room.startswith("tenant:"):
            parts = room.split(":")
            if len(parts) >= 2:
                room_tenant = parts[1]
                return client.tenant_id == room_tenant
            return False
        
        # User-specific rooms
        if room.startswith("user:"):
            parts = room.split(":")
            if len(parts) >= 2:
                room_user = parts[1]
                return client.user_id == room_user
            return False
        
        # Policy/quote specific rooms
        # In production, would verify ownership via database
        if room.startswith("policy:") or room.startswith("quote:"):
            # TODO: Verify entity ownership
            # For now, require authentication
            return client.user_id is not None
        
        # Default deny
        return False
    
    async def send_to_client(self, client_id: str, message: dict):
        """
        Send a message to a specific client.
        
        Args:
            client_id: Client identifier
            message: Message dictionary
        """
        client = self._clients.get(client_id)
        if not client:
            return
        
        try:
            await client.websocket.send_json(message)
        except Exception as e:
            logger.error(
                "Failed to send to client",
                client_id=client_id,
                error=str(e)
            )
            await self.disconnect(client_id)
    
    async def send_to_room(self, room: str, message: dict):
        """
        Broadcast a message to all clients in a room.
        
        Args:
            room: Room name
            message: Message dictionary
        """
        client_ids = self._rooms.get(room, set()).copy()
        
        if not client_ids:
            return
        
        logger.debug(
            "Broadcasting to room",
            room=room,
            client_count=len(client_ids)
        )
        
        for client_id in client_ids:
            await self.send_to_client(client_id, message)
    
    async def send_to_user(self, user_id: str, message: dict):
        """
        Send a message to all connections of a user.
        
        Args:
            user_id: User identifier
            message: Message dictionary
        """
        client_ids = self._user_clients.get(user_id, set()).copy()
        
        for client_id in client_ids:
            await self.send_to_client(client_id, message)
    
    async def send_to_tenant(self, tenant_id: str, message: dict):
        """
        Send a message to all clients of a tenant.
        
        Args:
            tenant_id: Tenant identifier
            message: Message dictionary
        """
        client_ids = self._tenant_clients.get(tenant_id, set()).copy()
        
        for client_id in client_ids:
            await self.send_to_client(client_id, message)
    
    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message dictionary
        """
        logger.debug(
            "Broadcasting to all clients",
            client_count=len(self._clients)
        )
        
        for client_id in list(self._clients.keys()):
            await self.send_to_client(client_id, message)
    
    async def send_error(self, client_id: str, error: str):
        """
        Send an error message to a client.
        
        Args:
            client_id: Client identifier
            error: Error message
        """
        await self.send_to_client(client_id, {
            "type": MessageType.ERROR,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def handle_message(self, client_id: str, message: dict):
        """
        Handle an incoming message from a client.
        
        Args:
            client_id: Client identifier
            message: Message dictionary
        """
        message_type = message.get("type")
        
        if message_type == MessageType.PING:
            client = self._clients.get(client_id)
            if client:
                client.last_ping = datetime.utcnow()
            await self.send_to_client(client_id, {
                "type": MessageType.PONG,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == MessageType.SUBSCRIBE:
            room = message.get("room")
            if room:
                await self.subscribe(client_id, room)
            else:
                await self.send_error(client_id, "Missing 'room' parameter")
        
        elif message_type == MessageType.UNSUBSCRIBE:
            room = message.get("room")
            if room:
                await self.unsubscribe(client_id, room)
            else:
                await self.send_error(client_id, "Missing 'room' parameter")
        
        else:
            await self.send_error(client_id, f"Unknown message type: {message_type}")
    
    async def _heartbeat_loop(self):
        """
        Periodic heartbeat to detect dead connections.
        
        Sends pings to all clients and disconnects those that don't respond.
        """
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                now = datetime.utcnow()
                dead_clients = []
                
                for client_id, client in self._clients.items():
                    # Check if client hasn't responded to pings
                    time_since_ping = (now - client.last_ping).total_seconds()
                    
                    if time_since_ping > self._heartbeat_interval * 3:
                        dead_clients.append(client_id)
                    else:
                        # Send ping
                        try:
                            await client.websocket.send_json({
                                "type": MessageType.PING,
                                "timestamp": now.isoformat()
                            })
                        except Exception:
                            dead_clients.append(client_id)
                
                # Disconnect dead clients
                for client_id in dead_clients:
                    logger.info("Disconnecting dead client", client_id=client_id)
                    await self.disconnect(client_id)
                
                if dead_clients:
                    logger.info(
                        "Heartbeat cleanup completed",
                        disconnected=len(dead_clients),
                        active=len(self._clients)
                    )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat error", error=str(e))
    
    @property
    def connection_count(self) -> int:
        """Get current connection count."""
        return len(self._clients)
    
    def get_stats(self) -> dict:
        """
        Get connection statistics.
        
        Returns:
            dict: Statistics including connection counts and room information
        """
        return {
            "total_connections": len(self._clients),
            "total_rooms": len(self._rooms),
            "users_connected": len(self._user_clients),
            "tenants_connected": len(self._tenant_clients),
            "rooms": {
                room: len(clients) 
                for room, clients in self._rooms.items()
            },
            "uptime_seconds": (
                datetime.utcnow() - min(
                    (c.connected_at for c in self._clients.values()),
                    default=datetime.utcnow()
                )
            ).total_seconds() if self._clients else 0
        }


# Global instance
ws_manager = WebSocketManager()
