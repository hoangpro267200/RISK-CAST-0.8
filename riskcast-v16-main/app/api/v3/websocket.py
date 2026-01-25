"""
WebSocket API Endpoints

Provides WebSocket connection for real-time updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from typing import Optional

from app.realtime.websocket_manager import ws_manager

import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time updates.
    
    ## Connection
    
    Connect to: `ws://api.riskcast.io/api/v3/ws?token=<jwt_token>`
    
    Or without authentication: `ws://api.riskcast.io/api/v3/ws`
    
    ## Client Messages
    
    ### Subscribe to a room
    ```json
    {
        "type": "subscribe",
        "room": "tenant:ABC123:risks"
    }
    ```
    
    ### Unsubscribe from a room
    ```json
    {
        "type": "unsubscribe",
        "room": "tenant:ABC123:risks"
    }
    ```
    
    ### Ping (keep-alive)
    ```json
    {
        "type": "ping"
    }
    ```
    
    ## Server Messages
    
    ### Subscribed confirmation
    ```json
    {
        "type": "subscribed",
        "room": "tenant:ABC123:risks",
        "timestamp": "2026-01-24T22:30:00Z"
    }
    ```
    
    ### Risk update
    ```json
    {
        "type": "risk_update",
        "data": {
            "policy_id": "POL-123",
            "risk_score": 0.65,
            "risk_grade": "B",
            "expected_loss_pct": 0.015,
            "var_95": 0.045,
            "var_99": 0.078,
            "layer_scores": {...},
            "timestamp": "2026-01-24T22:30:00Z"
        }
    }
    ```
    
    ### Alert
    ```json
    {
        "type": "alert",
        "data": {
            "alert_id": "policy:POL-123:high",
            "alert_type": "threshold_breach",
            "severity": "high",
            "entity_type": "policy",
            "entity_id": "POL-123",
            "message": "Policy risk is HIGH: 75%",
            "current_value": 0.75,
            "threshold_value": 0.70,
            "timestamp": "2026-01-24T22:30:00Z",
            "metadata": {...}
        }
    }
    ```
    
    ### Market data
    ```json
    {
        "type": "market_data",
        "data": {
            "weather_alerts": [...],
            "port_congestion": {...},
            "timestamp": "2026-01-24T22:30:00Z"
        }
    }
    ```
    
    ### Error
    ```json
    {
        "type": "error",
        "error": "Access denied to room: tenant:XYZ:risks",
        "timestamp": "2026-01-24T22:30:00Z"
    }
    ```
    
    ## Available Rooms
    
    ### Public rooms (no authentication required)
    - `public:market` - Market conditions and updates
    
    ### Tenant rooms (authentication required, tenant-isolated)
    - `tenant:{tenant_id}:risks` - Real-time risk updates for all policies
    - `tenant:{tenant_id}:alerts` - Risk alerts and threshold breaches
    - `tenant:{tenant_id}:portfolio` - Portfolio-level risk metrics
    - `tenant:{tenant_id}:quotes` - Quote updates
    
    ### Entity-specific rooms (authentication required, ownership validated)
    - `policy:{policy_id}` - Updates for a specific policy
    - `quote:{quote_id}` - Updates for a specific quote
    - `user:{user_id}` - User-specific notifications
    
    ## Authentication
    
    Pass JWT token as query parameter: `?token=<jwt_token>`
    
    Without authentication, only public rooms are accessible.
    
    ## Heartbeat
    
    Server sends periodic pings. Client should respond with pong or send its own pings.
    Connections without activity for 90 seconds will be disconnected.
    
    ## Error Codes
    
    - `4001` - Authentication failed
    - `4003` - Access denied to room
    - `1000` - Normal closure
    
    ## Example Client (JavaScript)
    
    ```javascript
    const ws = new WebSocket('ws://api.riskcast.io/api/v3/ws?token=' + token);
    
    ws.onopen = () => {
        console.log('Connected');
        
        // Subscribe to tenant risks
        ws.send(JSON.stringify({
            type: 'subscribe',
            room: 'tenant:ABC123:risks'
        }));
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('Received:', message);
        
        if (message.type === 'risk_update') {
            // Update UI with new risk data
            updateRiskDisplay(message.data);
        } else if (message.type === 'alert') {
            // Show alert notification
            showAlert(message.data);
        } else if (message.type === 'ping') {
            // Respond to ping
            ws.send(JSON.stringify({type: 'pong'}));
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('Disconnected');
    };
    
    // Send periodic pings
    setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({type: 'ping'}));
        }
    }, 30000);
    ```
    
    ## Example Client (Python)
    
    ```python
    import asyncio
    import websockets
    import json
    
    async def connect():
        uri = f"ws://api.riskcast.io/api/v3/ws?token={token}"
        
        async with websockets.connect(uri) as websocket:
            # Subscribe
            await websocket.send(json.dumps({
                "type": "subscribe",
                "room": "tenant:ABC123:risks"
            }))
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                print(f"Received: {data}")
                
                if data["type"] == "risk_update":
                    handle_risk_update(data["data"])
                elif data["type"] == "alert":
                    handle_alert(data["data"])
                elif data["type"] == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))
    
    asyncio.run(connect())
    ```
    """
    client = None
    
    try:
        # Connect and authenticate
        client = await ws_manager.connect(websocket, token)
        
        logger.info(
            "WebSocket connection established",
            client_id=client.client_id,
            user_id=client.user_id,
            tenant_id=client.tenant_id
        )
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Handle message
                await ws_manager.handle_message(client.client_id, data)
                
            except WebSocketDisconnect:
                logger.info(
                    "WebSocket disconnected by client",
                    client_id=client.client_id
                )
                break
                
            except Exception as e:
                logger.error(
                    "WebSocket message handling error",
                    client_id=client.client_id,
                    error=str(e)
                )
                await ws_manager.send_error(client.client_id, str(e))
                
    except Exception as e:
        logger.error("WebSocket connection failed", error=str(e))
        if client:
            await ws_manager.send_error(client.client_id, str(e))
        raise
        
    finally:
        # Always disconnect on exit
        if client:
            await ws_manager.disconnect(client.client_id)


@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns connection counts, room information, and uptime.
    
    ## Response
    
    ```json
    {
        "total_connections": 42,
        "total_rooms": 15,
        "users_connected": 28,
        "tenants_connected": 5,
        "rooms": {
            "public:market": 12,
            "tenant:ABC:risks": 8,
            "tenant:ABC:alerts": 8,
            "policy:POL-123": 2
        },
        "uptime_seconds": 3600
    }
    ```
    """
    stats = ws_manager.get_stats()
    
    logger.debug("WebSocket stats requested", stats=stats)
    
    return stats


@router.post("/ws/broadcast")
async def broadcast_message(
    message: dict,
    # In production, add authentication and admin check
):
    """
    Broadcast a message to all connected clients.
    
    **Admin only endpoint.**
    
    ## Request Body
    
    ```json
    {
        "type": "announcement",
        "message": "System maintenance in 30 minutes",
        "severity": "info"
    }
    ```
    """
    # In production, verify admin permissions here
    # For now, this is a placeholder
    
    await ws_manager.broadcast(message)
    
    logger.info("Broadcast message sent", message_type=message.get("type"))
    
    return {
        "status": "sent",
        "recipients": ws_manager.connection_count
    }


@router.post("/ws/rooms/{room}/send")
async def send_to_room(
    room: str,
    message: dict,
    # In production, add authentication and authorization
):
    """
    Send a message to all clients in a specific room.
    
    **Authorized users only.**
    
    ## Parameters
    
    - `room`: Room name (e.g., "tenant:ABC:risks")
    - `message`: Message to send
    
    ## Request Body
    
    ```json
    {
        "type": "custom",
        "data": {
            "key": "value"
        }
    }
    ```
    """
    # In production, verify user can send to this room
    
    await ws_manager.send_to_room(room, message)
    
    # Get room stats
    stats = ws_manager.get_stats()
    recipient_count = stats.get("rooms", {}).get(room, 0)
    
    logger.info(
        "Message sent to room",
        room=room,
        recipients=recipient_count,
        message_type=message.get("type")
    )
    
    return {
        "status": "sent",
        "room": room,
        "recipients": recipient_count
    }
