# AI SYSTEM ADVISOR - ARCHITECTURE DIAGRAM UPDATE
## Visual Architecture Documentation

**Version:** 1.0  
**Status:** Design Phase

---

## [1] CURRENT ARCHITECTURE (BEFORE)

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND                                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ResultsPage  │  │ SummaryPage  │  │  InputPage   │     │
│  │  (React)     │  │  (React)     │  │  (Vanilla)   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │              │
│         └─────────────────┴──────────────────┘             │
│                            │                                │
│                    ┌───────▼────────┐                       │
│                    │  AI Chat JS    │                       │
│                    │  (Vanilla)     │                       │
│                    └───────┬────────┘                       │
└────────────────────────────┼────────────────────────────────┘
                              │ HTTP
┌─────────────────────────────▼────────────────────────────────┐
│                    API LAYER                                 │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ /api/ai/chat │  │/api/ai/analyze│ │/api/ai/explain│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         └─────────────────┴──────────────────┘              │
│                            │                                │
│                    ┌───────▼────────┐                       │
│                    │   api_ai.py    │                       │
│                    │  (Scattered)   │                       │
│                    └───────┬────────┘                       │
└────────────────────────────┼────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│              SCATTERED AI MODULES                             │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ llm_reasoner.py  │  │ai_explanation.py │               │
│  │ (Engine v2)      │  │ (Rule-based)     │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ai_explanation_   │  │  api_ai.py       │               │
│  │ultra_v22.py      │  │  (6 endpoints)   │               │
│  └──────────────────┘  └──────────────────┘               │
└────────────────────────────┬─────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Claude API     │
                    │  (Direct calls)│
                    └─────────────────┘

ISSUES:
❌ No conversation history
❌ No system awareness
❌ No function calling
❌ Fragmented logic
❌ Manual context extraction
```

---

## [2] NEW ARCHITECTURE (AFTER)

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                            │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ResultsPage  │  │ SummaryPage  │  │  InputPage  │     │
│  │  (React)     │  │  (React)     │  │  (Vanilla)   │     │
│  │              │  │              │  │              │     │
│  │  ┌─────────┐ │  │  ┌─────────┐ │  │  ┌─────────┐ │     │
│  │  │System   │ │  │  │System   │ │  │  │System   │ │     │
│  │  │ChatPanel│ │  │  │ChatPanel│ │  │  │ChatPanel│ │     │
│  │  │(React)  │ │  │  │(React)  │ │  │  │(React)  │ │     │
│  │  └────┬────┘ │  │  └────┬────┘ │  │  └────┬────┘ │     │
│  └───────┼───────┘  └───────┼───────┘  └───────┼───────┘     │
│          │                  │                  │              │
│          └──────────────────┴──────────────────┘             │
│                            │                                  │
│                    ┌───────▼────────┐                        │
│                    │  Unified Chat  │                        │
│                    │  Interface      │                        │
│                    └───────┬────────┘                        │
└────────────────────────────┼──────────────────────────────────┘
                              │ HTTP/WebSocket
┌─────────────────────────────▼─────────────────────────────────┐
│                    API LAYER                                   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  /api/v1/ai/advisor/*                                │    │
│  │                                                       │    │
│  │  POST /chat      - Main chat endpoint                │    │
│  │  POST /stream    - Streaming responses               │    │
│  │  GET  /history   - Conversation history              │    │
│  │  POST /actions/* - System actions                    │    │
│  │  GET  /context   - System context                    │    │
│  └───────────────────┬──────────────────────────────────┘    │
└──────────────────────┼────────────────────────────────────────┘
                       │
┌───────────────────────▼───────────────────────────────────────┐
│         AI SYSTEM ADVISOR LAYER                                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  advisor_core.py                                      │    │
│  │  - Main reasoning engine                              │    │
│  │  - LLM client (Claude)                                │    │
│  │  - Function calling                                   │    │
│  │  - Response orchestration                             │    │
│  └───────────────┬──────────────────────────────────────┘    │
│                  │                                            │
│  ┌───────────────▼──────────────────────────────────────┐    │
│  │  context_manager.py                                  │    │
│  │  - Conversation history (persistent)                  │    │
│  │  - Context window management                          │    │
│  │  - Session management                                 │    │
│  │  - Context summarization                              │    │
│  └───────────────┬──────────────────────────────────────┘    │
│                  │                                            │
│  ┌───────────────▼──────────────────────────────────────┐    │
│  │  data_access.py                                      │    │
│  │  - Read engine outputs (LAST_RESULT_V2)              │    │
│  │  - Read historical data                              │    │
│  │  - Read financial metrics                            │    │
│  │  - Read ESG metrics                                  │    │
│  │  - Read scenario results                             │    │
│  └───────────────┬──────────────────────────────────────┘    │
│                  │                                            │
│  ┌───────────────▼──────────────────────────────────────┐    │
│  │  function_registry.py                               │    │
│  │  - Available functions                               │    │
│  │  - Function schemas                                  │    │
│  │  - Function validation                               │    │
│  └───────────────┬──────────────────────────────────────┘    │
│                  │                                            │
│  ┌───────────────▼──────────────────────────────────────┐    │
│  │  action_handlers.py                                 │    │
│  │  - export_pdf()                                      │    │
│  │  - export_excel()                                    │    │
│  │  - compare_shipments()                               │    │
│  │  - run_scenario()                                    │    │
│  │  - get_recommendations()                             │    │
│  └───────────────┬──────────────────────────────────────┘    │
│                  │                                            │
│  ┌───────────────▼──────────────────────────────────────┐    │
│  │  recommendation.py                                  │    │
│  │  - Generate mitigation suggestions                   │    │
│  │  - Cost-benefit analysis                            │    │
│  │  - Priority ranking                                 │    │
│  └───────────────┬──────────────────────────────────────┘    │
│                  │                                            │
│  ┌───────────────▼──────────────────────────────────────┐    │
│  │  summarizer.py                                      │    │
│  │  - Executive summaries                              │    │
│  │  - Multi-shipment summaries                         │    │
│  │  - Historical trend summaries                       │    │
│  └───────────────┬──────────────────────────────────────┘    │
│                  │                                            │
│  ┌───────────────▼──────────────────────────────────────┐    │
│  │  exporter.py                                         │    │
│  │  - PDF export                                        │    │
│  │  - Excel export                                      │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼───────────────────────────────────────┐
│                    SYSTEM LAYER                                │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Risk Engine  │  │   Scenario   │  │   Export     │      │
│  │  (v2, v16)   │  │   Engine     │  │   Services   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │State Storage │  │   Financial   │  │   Historical │      │
│  │              │  │   Metrics     │  │   Data       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────────────────────────────────────────┘
                        │
                ┌───────▼────────┐
                │  Claude API    │
                │  (with function│
                │   calling)     │
                └────────────────┘

BENEFITS:
✅ Unified AI layer
✅ Conversation history
✅ System awareness
✅ Function calling
✅ Centralized logic
✅ Automatic context
```

---

## [3] DETAILED DATA FLOW

### 3.1 Chat Request Flow

```
User types: "What are the top 3 risk drivers?"
    │
    ▼
[SystemChatPanel] 
    │ Extract page context (shipment_id, risk_score, etc.)
    ▼
POST /api/v1/ai/advisor/chat
    │ { message, session_id, context }
    ▼
[API Router]
    │
    ▼
[advisor_core.py]
    │
    ├─→ [context_manager.py]
    │   │ Load conversation history (last 20 messages)
    │   └─→ Return: List[Message]
    │
    ├─→ [data_access.py]
    │   │ Load system context:
    │   │ - Current risk assessment (from LAST_RESULT_V2)
    │   │ - Financial metrics
    │   │ - Shipment details
    │   │ - Available scenarios
    │   └─→ Return: SystemContext
    │
    ├─→ [function_registry.py]
    │   │ Get available functions
    │   └─→ Return: List[FunctionSchema]
    │
    └─→ Build system prompt
        │ - Conversation history
        │ - System context
        │ - Available functions
        │ - Instructions
        ▼
[Claude API] (with function calling)
    │
    ├─→ Response: "The top 3 risk drivers are..."
    │
    └─→ Function calls: [] (none in this case)
        ▼
[context_manager.py]
    │ Save conversation:
    │ - User message
    │ - AI response
    │ - Metadata
    ▼
[API Response]
    │ {
    │   reply: "...",
    │   actions: [...],
    │   session_id: "..."
    │ }
    ▼
[SystemChatPanel]
    │ Display response
    │ Show action buttons
    ▼
User sees response
```

### 3.2 Function Calling Flow

```
User: "Export a PDF report"
    │
    ▼
[advisor_core.py]
    │ Detects intent: export_pdf
    │
    ▼
[Claude API]
    │ Returns function call:
    │ {
    │   name: "export_pdf",
    │   arguments: {
    │     template: "standard",
    │     include_charts: true
    │   }
    │ }
    ▼
[action_handlers.py]
    │ Execute export_pdf()
    │
    ├─→ [pdf_builder.py]
    │   │ Generate PDF
    │   └─→ Return: file_bytes
    │
    └─→ Save to storage
        │ Return: file_id, file_url
        ▼
[advisor_core.py]
    │ Format response:
    │ "I've generated a PDF report. 
    │  Download it here: [link]"
    ▼
[API Response]
    │ {
    │   reply: "...",
    │   actions: [{
    │     type: "function_call",
    │     function: "export_pdf",
    │     result: { file_url: "..." }
    │   }]
    │ }
    ▼
[SystemChatPanel]
    │ Display response
    │ Show download button
```

### 3.3 Context Building Flow

```
[data_access.py]
    │
    ├─→ Read LAST_RESULT_V2 (from engine_state.py)
    │   └─→ Current risk assessment
    │
    ├─→ Read shipment state (from state_storage.py)
    │   └─→ Shipment details, route, cargo
    │
    ├─→ Read financial metrics (from risk assessment)
    │   └─→ Expected loss, VaR, CVaR
    │
    ├─→ Read historical data (from MySQL, if available)
    │   └─→ Previous shipments, trends
    │
    └─→ Build SystemContext object
        │ {
        │   current_assessment: {...},
        │   shipment: {...},
        │   financial: {...},
        │   history: [...],
        │   available_actions: [...]
        │ }
        ▼
[advisor_core.py]
    │ Format context for system prompt
    │
    └─→ Include in prompt:
        "CURRENT CONTEXT:
         Risk Score: 65.5/100 (MODERATE)
         Expected Loss: $12,500
         Top Drivers: Port Congestion (35%), Weather (28%)
         ..."
```

---

## [4] MODULE INTERACTIONS

### 4.1 advisor_core.py Dependencies

```
advisor_core.py
    │
    ├─→ context_manager.py
    │   └─→ Conversation history
    │
    ├─→ data_access.py
    │   └─→ System context
    │
    ├─→ function_registry.py
    │   └─→ Available functions
    │
    ├─→ action_handlers.py
    │   └─→ Execute functions
    │
    └─→ Anthropic Client
        └─→ Claude API
```

### 4.2 action_handlers.py Dependencies

```
action_handlers.py
    │
    ├─→ app/core/report/pdf_builder.py
    │   └─→ PDF generation
    │
    ├─→ app/core/scenario_engine/
    │   └─→ Scenario execution
    │
    ├─→ app/core/services/risk_service.py
    │   └─→ Risk analysis
    │
    └─→ app/core/state_storage.py
        └─→ State management
```

---

## [5] STORAGE ARCHITECTURE

### 5.1 Conversation History Storage

**Development:**
```
data/conversations/
  └── {session_id}.json
      {
        "session_id": "session-abc123",
        "created_at": "2024-01-15T10:00:00Z",
        "messages": [
          {
            "role": "user",
            "content": "...",
            "timestamp": "..."
          },
          {
            "role": "assistant",
            "content": "...",
            "timestamp": "..."
          }
        ]
      }
```

**Production:**
```sql
CREATE TABLE conversation_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(255) NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_created (created_at)
);
```

### 5.2 Context Cache

**In-Memory (Redis, future):**
```
Key: context:{session_id}
Value: {
  "risk_assessment": {...},
  "shipment": {...},
  "financial": {...},
  "last_updated": "..."
}
TTL: 1 hour
```

---

## [6] SECURITY CONSIDERATIONS

### 6.1 Session Management

- **Session ID:** UUID v4 (random, unguessable)
- **Session Expiry:** 24 hours of inactivity
- **Session Isolation:** Each session isolated

### 6.2 Data Access Control

- **Context Access:** Only session owner's data
- **Action Permissions:** Validate before execution
- **Export Files:** Signed URLs with expiry

### 6.3 Rate Limiting

- **Per Session:** 30 requests/minute
- **Per IP:** 100 requests/minute
- **Per User:** 200 requests/minute

---

## [7] PERFORMANCE CONSIDERATIONS

### 7.1 Caching Strategy

- **Conversation History:** Cache last 20 messages in memory
- **System Context:** Cache for 5 minutes
- **LLM Responses:** Cache similar queries (future)

### 7.2 Async Processing

- **LLM Calls:** Fully async
- **Function Execution:** Async where possible
- **File Generation:** Background tasks for large files

### 7.3 Optimization Targets

- **Response Time:** <2s (p95)
- **Streaming Latency:** <500ms (first token)
- **Context Loading:** <100ms

---

**END OF ARCHITECTURE DIAGRAM**
