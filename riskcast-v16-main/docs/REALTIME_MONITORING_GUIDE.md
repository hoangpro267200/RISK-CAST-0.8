# Real-Time Risk Monitoring Guide

## 📋 Overview

Complete guide to the real-time risk monitoring system with WebSocket event streaming.

**Features:**
- Real-time risk score updates
- Threshold-based alerts
- Market condition monitoring
- Portfolio risk aggregation
- Room-based subscriptions
- Tenant isolation
- Heartbeat/keepalive

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│  (Web Dashboard, Mobile App, Trading Systems)                │
└──────────────────────┬──────────────────────────────────────┘
                       │ WebSocket
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              WebSocket Manager                               │
│  - Connection management                                     │
│  - Room-based pub/sub                                        │
│  - Tenant isolation                                          │
│  - Heartbeat monitoring                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│           Real-Time Risk Monitor                             │
│  - Continuous risk assessment (60s intervals)                │
│  - Threshold monitoring                                      │
│  - Trend detection                                           │
│  - Portfolio aggregation                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│          Risk Engine + Data Services                         │
│  - Risk calculation                                          │
│  - Market data                                               │
│  - Historical data                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 WebSocket Connection

### Connection URL

```
ws://api.riskcast.io/api/v3/ws?token=<jwt_token>
```

**With authentication:**
```javascript
const ws = new WebSocket('ws://api.riskcast.io/api/v3/ws?token=' + jwtToken);
```

**Without authentication (public rooms only):**
```javascript
const ws = new WebSocket('ws://api.riskcast.io/api/v3/ws');
```

---

## 📨 Message Protocol

### Client → Server Messages

#### Subscribe to Room

```json
{
    "type": "subscribe",
    "room": "tenant:ABC123:risks"
}
```

**Available Rooms:**

| Room Pattern | Description | Authentication |
|--------------|-------------|----------------|
| `public:market` | Market conditions | No |
| `tenant:{tenant_id}:risks` | Risk updates | Yes (tenant member) |
| `tenant:{tenant_id}:alerts` | Alerts | Yes (tenant member) |
| `tenant:{tenant_id}:portfolio` | Portfolio metrics | Yes (tenant member) |
| `tenant:{tenant_id}:quotes` | Quote updates | Yes (tenant member) |
| `policy:{policy_id}` | Single policy updates | Yes (owner) |
| `quote:{quote_id}` | Single quote updates | Yes (owner) |
| `user:{user_id}` | User notifications | Yes (self) |

#### Unsubscribe from Room

```json
{
    "type": "unsubscribe",
    "room": "tenant:ABC123:risks"
}
```

#### Ping (Heartbeat)

```json
{
    "type": "ping"
}
```

---

### Server → Client Messages

#### Subscribed Confirmation

```json
{
    "type": "subscribed",
    "room": "tenant:ABC123:risks",
    "timestamp": "2026-01-24T22:30:00Z"
}
```

#### Risk Update

```json
{
    "type": "risk_update",
    "data": {
        "policy_id": "POL-123",
        "tenant_id": "ABC123",
        "risk_score": 0.65,
        "risk_grade": "B",
        "expected_loss_pct": 0.015,
        "var_95": 0.045,
        "var_99": 0.078,
        "layer_scores": {
            "route": 0.55,
            "cargo": 0.45,
            "carrier": 0.35,
            "weather": 0.70,
            "geopolitical": 0.40
        },
        "timestamp": "2026-01-24T22:30:00Z"
    }
}
```

#### Alert

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
        "metadata": {
            "layer_scores": {...},
            "var_95": 0.082,
            "var_99": 0.145
        }
    }
}
```

**Alert Types:**
- `threshold_breach` - Risk exceeded threshold
- `trend_change` - Significant risk increase
- `anomaly` - Unusual pattern detected

**Severity Levels:**
- `low` - Informational
- `medium` - Monitor closely
- `high` - Action recommended
- `critical` - Immediate action required

#### Market Data

```json
{
    "type": "market_data",
    "data": {
        "weather_alerts": [
            {
                "region": "North Atlantic",
                "severity": "high",
                "event_type": "hurricane",
                "affected_routes": ["EU-US", "EU-CA"]
            }
        ],
        "port_congestion": {
            "USNYC": {"level": "high", "delay_days": 3},
            "NLROT": {"level": "medium", "delay_days": 1}
        },
        "timestamp": "2026-01-24T22:30:00Z"
    }
}
```

#### Portfolio Update

```json
{
    "type": "portfolio_update",
    "data": {
        "tenant_id": "ABC123",
        "policy_count": 42,
        "avg_risk_score": 0.58,
        "max_risk_score": 0.85,
        "min_risk_score": 0.23,
        "total_exposure": 50000000,
        "timestamp": "2026-01-24T22:30:00Z"
    }
}
```

#### Error

```json
{
    "type": "error",
    "error": "Access denied to room: tenant:XYZ:risks",
    "timestamp": "2026-01-24T22:30:00Z"
}
```

#### Pong (Heartbeat Response)

```json
{
    "type": "pong",
    "timestamp": "2026-01-24T22:30:00Z"
}
```

---

## 🔒 Security & Access Control

### Tenant Isolation

All tenant-specific rooms enforce isolation:
- Can only subscribe to your own tenant's rooms
- Cannot access other tenants' data
- Enforced at WebSocket manager level

### Room Access Rules

```python
# Public rooms - anyone
if room.startswith("public:"):
    return True

# Tenant rooms - tenant members only
if room.startswith("tenant:"):
    room_tenant = room.split(":")[1]
    return client.tenant_id == room_tenant

# User rooms - self only
if room.startswith("user:"):
    room_user = room.split(":")[1]
    return client.user_id == room_user

# Entity rooms - owners only (verified in database)
if room.startswith("policy:") or room.startswith("quote:"):
    # Requires database check
    return verify_ownership(client, room)
```

---

## 📊 Risk Thresholds

### Policy Risk Thresholds

```python
POLICY_RISK_HIGH = 0.70       # 70% risk score
POLICY_RISK_CRITICAL = 0.85   # 85% risk score
```

### Expected Loss Thresholds

```python
EXPECTED_LOSS_WARNING = 0.02   # 2% expected loss
EXPECTED_LOSS_CRITICAL = 0.05  # 5% expected loss
```

### Trend Detection

```python
TREND_INCREASE_THRESHOLD = 0.10  # 10% increase triggers alert
```

### Portfolio Thresholds

```python
PORTFOLIO_VAR_WARNING = 0.05    # 5% Value at Risk
PORTFOLIO_VAR_CRITICAL = 0.10   # 10% Value at Risk

CONCENTRATION_WARNING = 0.30    # 30% in single route/cargo
CONCENTRATION_CRITICAL = 0.50   # 50% in single route/cargo
```

---

## 💻 Client Implementation Examples

### JavaScript / TypeScript

```javascript
class RiskCastWebSocket {
    constructor(token) {
        this.token = token;
        this.ws = null;
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
    }
    
    connect() {
        const url = `ws://api.riskcast.io/api/v3/ws?token=${this.token}`;
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
            console.log('Connected to RiskCast WebSocket');
            this.reconnectDelay = 1000;
            
            // Subscribe to tenant risks
            this.subscribe('tenant:ABC123:risks');
            this.subscribe('tenant:ABC123:alerts');
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('Disconnected from RiskCast WebSocket');
            this.reconnect();
        };
        
        // Send periodic pings
        this.pingInterval = setInterval(() => {
            if (this.ws.readyState === WebSocket.OPEN) {
                this.send({type: 'ping'});
            }
        }, 30000);
    }
    
    reconnect() {
        setTimeout(() => {
            console.log('Reconnecting...');
            this.connect();
            this.reconnectDelay = Math.min(
                this.reconnectDelay * 2,
                this.maxReconnectDelay
            );
        }, this.reconnectDelay);
    }
    
    subscribe(room) {
        this.send({
            type: 'subscribe',
            room: room
        });
    }
    
    unsubscribe(room) {
        this.send({
            type: 'unsubscribe',
            room: room
        });
    }
    
    send(message) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'subscribed':
                console.log(`Subscribed to ${message.room}`);
                break;
                
            case 'risk_update':
                this.onRiskUpdate(message.data);
                break;
                
            case 'alert':
                this.onAlert(message.data);
                break;
                
            case 'market_data':
                this.onMarketData(message.data);
                break;
                
            case 'ping':
                this.send({type: 'pong'});
                break;
                
            case 'error':
                console.error('WebSocket error:', message.error);
                break;
        }
    }
    
    onRiskUpdate(data) {
        console.log('Risk update:', data);
        // Update UI with new risk score
        updateRiskDisplay(data.policy_id, data.risk_score);
    }
    
    onAlert(data) {
        console.log('Alert:', data);
        // Show notification
        showNotification(data.severity, data.message);
    }
    
    onMarketData(data) {
        console.log('Market data:', data);
        // Update market conditions display
        updateMarketDisplay(data);
    }
    
    disconnect() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
        }
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage
const wsClient = new RiskCastWebSocket(jwtToken);
wsClient.connect();
```

---

### Python (asyncio)

```python
import asyncio
import websockets
import json
from typing import Callable

class RiskCastWebSocket:
    def __init__(self, token: str):
        self.token = token
        self.ws = None
        self.handlers = {}
        
    async def connect(self):
        uri = f"ws://api.riskcast.io/api/v3/ws?token={self.token}"
        
        async with websockets.connect(uri) as websocket:
            self.ws = websocket
            print("Connected to RiskCast WebSocket")
            
            # Subscribe to rooms
            await self.subscribe("tenant:ABC123:risks")
            await self.subscribe("tenant:ABC123:alerts")
            
            # Start ping task
            ping_task = asyncio.create_task(self.send_pings())
            
            # Listen for messages
            try:
                async for message in websocket:
                    data = json.loads(message)
                    await self.handle_message(data)
            finally:
                ping_task.cancel()
    
    async def subscribe(self, room: str):
        await self.send({
            "type": "subscribe",
            "room": room
        })
    
    async def unsubscribe(self, room: str):
        await self.send({
            "type": "unsubscribe",
            "room": room
        })
    
    async def send(self, message: dict):
        if self.ws:
            await self.ws.send(json.dumps(message))
    
    async def handle_message(self, message: dict):
        msg_type = message.get("type")
        
        if msg_type == "subscribed":
            print(f"Subscribed to {message['room']}")
        
        elif msg_type == "risk_update":
            await self.on_risk_update(message["data"])
        
        elif msg_type == "alert":
            await self.on_alert(message["data"])
        
        elif msg_type == "market_data":
            await self.on_market_data(message["data"])
        
        elif msg_type == "ping":
            await self.send({"type": "pong"})
        
        elif msg_type == "error":
            print(f"Error: {message['error']}")
    
    async def on_risk_update(self, data: dict):
        print(f"Risk update: {data}")
        # Process risk update
    
    async def on_alert(self, data: dict):
        print(f"Alert: {data}")
        # Process alert
    
    async def on_market_data(self, data: dict):
        print(f"Market data: {data}")
        # Process market data
    
    async def send_pings(self):
        while True:
            await asyncio.sleep(30)
            await self.send({"type": "ping"})

# Usage
async def main():
    client = RiskCastWebSocket(token)
    await client.connect()

asyncio.run(main())
```

---

## 🔧 Testing WebSocket Connections

### Using wscat (CLI tool)

```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c "ws://localhost:8000/api/v3/ws?token=YOUR_JWT_TOKEN"

# Subscribe to room
> {"type": "subscribe", "room": "public:market"}

# Send ping
> {"type": "ping"}

# Unsubscribe
> {"type": "unsubscribe", "room": "public:market"}
```

### Using curl (REST API for stats)

```bash
# Get WebSocket statistics
curl http://localhost:8000/api/v3/ws/stats

# Response:
{
    "total_connections": 42,
    "total_rooms": 15,
    "users_connected": 28,
    "tenants_connected": 5,
    "rooms": {
        "public:market": 12,
        "tenant:ABC:risks": 8
    }
}
```

---

## 📈 Monitoring & Operations

### Check WebSocket Status

```bash
# Get current statistics
curl http://api.riskcast.io/api/v3/ws/stats | jq .

# Check logs
kubectl logs -f deployment/riskcast-api | grep "WebSocket"
```

### Monitor Metrics

Key metrics to track:
- `websocket_connections_total` - Total active connections
- `websocket_messages_sent_total` - Messages sent counter
- `websocket_messages_received_total` - Messages received counter
- `websocket_subscription_total` - Active subscriptions by room
- `risk_assessments_total` - Risk assessments performed
- `risk_alerts_sent_total` - Alerts sent

---

## 🐛 Troubleshooting

### Connection Drops

**Problem:** WebSocket connections drop frequently

**Solutions:**
1. Check client is responding to pings
2. Increase heartbeat interval if needed
3. Check network stability
4. Review connection timeout settings

```python
# Client should respond to pings or send its own
if message.type == "ping":
    ws.send({"type": "pong"})
```

### Not Receiving Updates

**Problem:** Subscribed to room but not getting updates

**Diagnosis:**
```bash
# Check if subscribed
curl http://api.riskcast.io/api/v3/ws/stats | jq '.rooms'

# Check logs
kubectl logs -f deployment/riskcast-api | grep "room=tenant:ABC"
```

**Solutions:**
1. Verify room name is correct
2. Check authentication token is valid
3. Verify user has access to room
4. Check if policy is being monitored

### Authentication Failures

**Problem:** Connection closes with code 4001

**Solutions:**
1. Verify JWT token is valid
2. Check token hasn't expired
3. Ensure token has required claims (sub, tenant_id)

---

## 🎯 Best Practices

### Connection Management

✅ **DO:**
- Implement automatic reconnection with exponential backoff
- Handle all message types gracefully
- Send periodic pings (every 30s)
- Unsubscribe from rooms before disconnecting
- Close connections cleanly

❌ **DON'T:**
- Create multiple connections per user
- Subscribe to rooms you don't need
- Ignore ping messages
- Leave connections open indefinitely

### Performance

✅ **DO:**
- Subscribe only to needed rooms
- Batch risk assessments when possible
- Use portfolio rooms for aggregate data
- Implement client-side caching

❌ **DON'T:**
- Subscribe to individual policies if portfolio view suffices
- Poll for updates (use WebSocket events)
- Request frequent updates unnecessarily

### Security

✅ **DO:**
- Always use authentication tokens
- Validate room access on client side
- Use WSS (secure WebSocket) in production
- Rotate tokens regularly

❌ **DON'T:**
- Share WebSocket connections between users
- Store tokens in localStorage (use httpOnly cookies)
- Subscribe to unauthorized rooms

---

## 📚 Additional Resources

- [WebSocket API Reference](./API_REFERENCE.md)
- [Risk Threshold Configuration](./RISK_THRESHOLDS.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Monitoring & Alerting](../runbooks/debugging.md)

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0  
**Owner:** Engineering Team
