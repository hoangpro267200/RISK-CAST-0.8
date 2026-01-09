# AI SYSTEM ADVISOR - API DESIGN SPECIFICATION
## Detailed API Contract & Integration Guide

**Version:** 1.0  
**Status:** Design Phase

---

## [1] API OVERVIEW

### Base URL
- **Development:** `http://localhost:8000/api/v1/ai/advisor`
- **Production:** `https://api.riskcast.com/api/v1/ai/advisor`

### Authentication
- **Current:** None (session-based)
- **Future:** API key or JWT token

### Response Format
- **Content-Type:** `application/json`
- **Encoding:** UTF-8
- **Error Format:** Standard FastAPI error response

---

## [2] ENDPOINT SPECIFICATIONS

### 2.1 POST /api/v1/ai/advisor/chat

**Purpose:** Main chat endpoint with conversation history and system awareness

**Request:**
```json
{
  "message": "What are the top 3 risk drivers for this shipment?",
  "session_id": "session-abc123",
  "context": {
    "page": "results",
    "shipment_id": "SH-001",
    "user_id": "user-123"
  },
  "options": {
    "stream": false,
    "include_actions": true,
    "language": "en"
  }
}
```

**Request Schema:**
```python
class ChatRequest(BaseModel):
    message: str  # Required: User message
    session_id: str  # Required: Session identifier
    context: Optional[ChatContext] = None  # Optional: Page context
    options: Optional[ChatOptions] = None  # Optional: Request options

class ChatContext(BaseModel):
    page: Literal["results", "summary", "input"]  # Current page
    shipment_id: Optional[str] = None  # Current shipment ID
    user_id: Optional[str] = None  # User identifier

class ChatOptions(BaseModel):
    stream: bool = False  # Enable streaming
    include_actions: bool = True  # Include action suggestions
    language: Literal["en", "vi", "zh"] = "en"  # Response language
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "reply": "The top 3 risk drivers for this shipment are:\n\n1. **Port Congestion (35% impact)** - High congestion at origin port (Singapore) is causing significant delays...\n\n2. **Weather Exposure (28% impact)** - Current weather patterns in the South China Sea indicate elevated storm risk...\n\n3. **Carrier Reliability (22% impact)** - The selected carrier has a reliability score of 72%, which is below the recommended threshold...",
    "session_id": "session-abc123",
    "actions": [
      {
        "type": "suggestion",
        "action": "export_pdf",
        "label": "Export detailed report",
        "description": "Generate PDF report with full risk analysis"
      },
      {
        "type": "suggestion",
        "action": "get_recommendations",
        "label": "View recommendations",
        "description": "See mitigation strategies for these risks"
      }
    ],
    "function_calls": [],
    "metadata": {
      "tokens_used": 1250,
      "response_time_ms": 1850,
      "model": "claude-3-5-sonnet-20241022",
      "confidence": 0.92
    }
  }
}
```

**Response Schema:**
```python
class ChatResponse(BaseModel):
    status: Literal["success", "error"]
    data: Optional[ChatResponseData] = None
    error: Optional[ErrorDetail] = None

class ChatResponseData(BaseModel):
    reply: str  # AI response text
    session_id: str
    actions: List[ActionSuggestion]  # Suggested actions
    function_calls: List[FunctionCallResult]  # Executed functions
    metadata: ResponseMetadata

class ActionSuggestion(BaseModel):
    type: Literal["suggestion", "required"]
    action: str  # Action identifier
    label: str  # Human-readable label
    description: str  # Action description
    parameters: Optional[Dict] = None  # Action parameters
```

**Error Responses:**
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_SESSION",
    "message": "Session not found",
    "details": {
      "session_id": "session-abc123"
    }
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (if auth required)
- `404` - Session not found
- `429` - Rate limit exceeded
- `500` - Internal server error
- `503` - Service unavailable (Claude API down)

---

### 2.2 POST /api/v1/ai/advisor/stream

**Purpose:** Streaming chat responses (Server-Sent Events)

**Request:** Same as `/chat` but with `options.stream = true`

**Response:** Server-Sent Events (SSE) stream

**Event Types:**
- `message` - Text chunk
- `action` - Action suggestion
- `function_call` - Function execution
- `done` - Stream complete
- `error` - Error occurred

**Example Stream:**
```
event: message
data: {"chunk": "The top 3 risk drivers"}

event: message
data: {"chunk": " for this shipment are:"}

event: action
data: {"type": "suggestion", "action": "export_pdf", "label": "Export PDF"}

event: done
data: {"session_id": "session-abc123", "tokens_used": 1250}
```

---

### 2.3 GET /api/v1/ai/advisor/history

**Purpose:** Retrieve conversation history

**Query Parameters:**
- `session_id` (required) - Session identifier
- `limit` (optional, default: 20) - Number of messages to return
- `before` (optional) - Get messages before this timestamp

**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "session-abc123",
    "messages": [
      {
        "role": "user",
        "content": "What are the top 3 risk drivers?",
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {
          "page": "results",
          "shipment_id": "SH-001"
        }
      },
      {
        "role": "assistant",
        "content": "The top 3 risk drivers are...",
        "timestamp": "2024-01-15T10:30:02Z",
        "metadata": {
          "tokens_used": 1250,
          "model": "claude-3-5-sonnet"
        }
      }
    ],
    "total_messages": 15,
    "has_more": false
  }
}
```

---

### 2.4 POST /api/v1/ai/advisor/actions/{action}

**Purpose:** Execute system actions

**Actions:**
- `export_pdf` - Export to PDF
- `export_excel` - Export to Excel
- `compare` - Compare shipments
- `scenario` - Run scenario
- `recommendations` - Get recommendations
- `summary` - Get executive summary

**Path Parameters:**
- `action` (required) - Action identifier

**Request Body:**
```json
{
  "session_id": "session-abc123",
  "parameters": {
    "template": "standard",
    "include_charts": true
  }
}
```

**Response (Export Actions):**
```json
{
  "status": "success",
  "data": {
    "action": "export_pdf",
    "file_id": "file-xyz789",
    "file_url": "/api/v1/ai/advisor/downloads/file-xyz789.pdf",
    "file_size": 1024000,
    "expires_at": "2024-01-15T11:30:00Z"
  }
}
```

**Response (Data Actions):**
```json
{
  "status": "success",
  "data": {
    "action": "recommendations",
    "result": [
      {
        "title": "Enhanced Monitoring",
        "risk_reduction": 5.2,
        "cost_impact": 500,
        "feasibility": 0.95,
        "description": "Add real-time tracking..."
      }
    ]
  }
}
```

---

### 2.5 GET /api/v1/ai/advisor/context

**Purpose:** Get current system context for session

**Query Parameters:**
- `session_id` (required) - Session identifier

**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "session-abc123",
    "current_shipment": {
      "shipment_id": "SH-001",
      "route": "SGN-LAX",
      "risk_score": 65.5,
      "risk_level": "MODERATE"
    },
    "risk_assessment": {
      "overall_score": 65.5,
      "confidence": 0.85,
      "drivers": [...],
      "layers": [...]
    },
    "financial_metrics": {
      "expected_loss": 12500,
      "var95": 25000,
      "cvar99": 45000
    },
    "available_actions": [
      "export_pdf",
      "export_excel",
      "compare",
      "scenario"
    ]
  }
}
```

---

### 2.6 DELETE /api/v1/ai/advisor/history

**Purpose:** Clear conversation history

**Query Parameters:**
- `session_id` (required) - Session identifier

**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "session-abc123",
    "messages_deleted": 15
  }
}
```

---

## [3] FUNCTION CALLING SPECIFICATION

### 3.1 Available Functions

#### export_pdf
**Purpose:** Export current risk assessment to PDF

**Parameters:**
```json
{
  "template": "standard" | "executive" | "detailed",
  "include_charts": true,
  "language": "en" | "vi" | "zh"
}
```

**Returns:**
```json
{
  "file_id": "file-xyz789",
  "file_url": "/api/v1/ai/advisor/downloads/file-xyz789.pdf",
  "file_size": 1024000
}
```

#### export_excel
**Purpose:** Export to Excel format

**Parameters:**
```json
{
  "include_raw_data": true,
  "include_charts": false
}
```

#### compare_shipments
**Purpose:** Compare multiple shipments

**Parameters:**
```json
{
  "shipment_ids": ["SH-001", "SH-002", "SH-003"],
  "metrics": ["risk_score", "expected_loss", "delay_probability"]
}
```

**Returns:**
```json
{
  "comparison": {
    "shipments": [...],
    "differences": [...],
    "recommendations": [...]
  }
}
```

#### run_scenario
**Purpose:** Run what-if scenario

**Parameters:**
```json
{
  "scenario_type": "weather_shock" | "port_congestion" | "carrier_change",
  "parameters": {
    "weather_severity": 0.8,
    "port_congestion_level": 0.9
  }
}
```

#### get_recommendations
**Purpose:** Get mitigation recommendations

**Parameters:**
```json
{
  "limit": 5,
  "sort_by": "risk_reduction" | "cost_benefit" | "feasibility"
}
```

#### get_summary
**Purpose:** Get executive summary

**Parameters:**
```json
{
  "length": "short" | "medium" | "long",
  "language": "en" | "vi" | "zh",
  "include_recommendations": true
}
```

#### get_financial_metrics
**Purpose:** Get detailed financial metrics

**Parameters:**
```json
{
  "include_distributions": true,
  "confidence_levels": [0.95, 0.99]
}
```

#### get_historical_trend
**Purpose:** Get historical risk trend

**Parameters:**
```json
{
  "shipment_ids": ["SH-001", "SH-002"],
  "time_range": "30d" | "90d" | "1y",
  "metric": "risk_score" | "expected_loss"
}
```

### 3.2 Function Calling Flow

```
User: "Export a PDF report"
    ↓
[Advisor] → Detects intent → Calls export_pdf()
    ↓
[Action Handler] → Executes export
    ↓
[Response] → "I've generated a PDF report. Download it here: [link]"
```

---

## [4] SYSTEM PROMPT TEMPLATE

### Base System Prompt

```
You are RISKCAST AI System Advisor, an intelligent risk intelligence assistant for logistics and supply chain risk management.

SYSTEM CAPABILITIES:
- Analyze risk assessments and provide insights
- Generate executive summaries
- Provide mitigation recommendations
- Compare shipments
- Export reports (PDF/Excel)
- Run what-if scenarios
- Explain risk drivers and metrics

CURRENT CONTEXT:
{system_context}

AVAILABLE FUNCTIONS:
{available_functions}

CONVERSATION HISTORY:
{conversation_history}

INSTRUCTIONS:
1. Be concise and actionable
2. Use function calling when appropriate
3. Provide data-driven insights
4. Explain technical concepts clearly
5. Suggest relevant actions
6. Respond in {language}

RESPONSE FORMAT:
- Use structured format when appropriate
- Include specific numbers and metrics
- Provide actionable recommendations
- Link to relevant system actions
```

---

## [5] INTEGRATION EXAMPLES

### 5.1 Frontend Integration (React)

```typescript
// SystemChatPanel.tsx
import { useState, useEffect } from 'react';

export function SystemChatPanel({ sessionId, context }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  
  const sendMessage = async () => {
    const response = await fetch('/api/v1/ai/advisor/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: input,
        session_id: sessionId,
        context: context
      })
    });
    
    const data = await response.json();
    setMessages([...messages, 
      { role: 'user', content: input },
      { role: 'assistant', content: data.data.reply }
    ]);
    setInput('');
  };
  
  return (
    <div className="system-chat-panel">
      {/* Chat UI */}
    </div>
  );
}
```

### 5.2 Backend Integration

```python
# app/api/v1/ai_routes.py
from app.ai_system_advisor.advisor_core import AdvisorCore

router = APIRouter()
advisor = AdvisorCore()

@router.post("/advisor/chat")
async def chat_endpoint(request: ChatRequest):
    result = await advisor.process_message(
        message=request.message,
        session_id=request.session_id,
        context=request.context
    )
    return ChatResponse(status="success", data=result)
```

---

## [6] ERROR HANDLING

### Error Codes

- `INVALID_SESSION` - Session not found
- `INVALID_MESSAGE` - Message format invalid
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `CLAUDE_API_ERROR` - Claude API error
- `FUNCTION_EXECUTION_ERROR` - Function call failed
- `CONTEXT_TOO_LARGE` - Context window exceeded
- `PERMISSION_DENIED` - Action not allowed

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "CLAUDE_API_ERROR",
    "message": "Claude API request failed",
    "details": {
      "api_error": "Rate limit exceeded",
      "retry_after": 60
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## [7] RATE LIMITING

### Limits

- **Chat:** 30 requests/minute per session
- **Stream:** 10 requests/minute per session
- **Actions:** 20 requests/minute per session
- **History:** 60 requests/minute per session

### Headers

```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1642234800
```

---

## [8] BACKWARD COMPATIBILITY

### Legacy Endpoint Mapping

```
POST /api/ai/chat → POST /api/v1/ai/advisor/chat
POST /api/ai/analyze → POST /api/v1/ai/advisor/chat (with analyze intent)
POST /api/ai/explain → POST /api/v1/ai/advisor/chat (with explain intent)
POST /api/ai/recommend → POST /api/v1/ai/advisor/actions/recommendations
```

### Migration Strategy

1. **Phase 1:** New endpoints alongside old ones
2. **Phase 2:** Old endpoints proxy to new advisor
3. **Phase 3:** Deprecation notice (optional)

---

**END OF API DESIGN SPECIFICATION**
