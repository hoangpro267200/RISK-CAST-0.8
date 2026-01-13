# 🚀 QUICK START - AI SYSTEM ADVISOR

## ✅ Current Status

- ✅ Server is running
- ✅ API endpoints working
- ✅ API key configured
- ✅ All imports fixed
- ✅ Frontend integrated

## 🔄 To Enable Full Claude API

**Simply restart the server:**

1. Stop current server (Ctrl+C in terminal)
2. Restart:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

3. Check logs for:
   ```
   [AI Advisor Routes] AdvisorCore initialized - use_llm: True
   ```

## 🧪 Test AI Advisor

### Option 1: Use Test Script
```bash
python test_ai_with_claude.py
```

### Option 2: Use Frontend
1. Navigate to: `http://localhost:8000/results`
2. Look for AI Chat Panel (bottom right)
3. Ask: "What are the top 3 risk drivers?"

## 📡 API Endpoint

```bash
POST http://localhost:8000/api/v1/advisor/chat
Content-Type: application/json

{
  "message": "Hello, what can you help me with?",
  "session_id": "test-001",
  "context": {"page": "results"}
}
```

## ✅ Everything is Ready!

Just restart the server and Claude API will be fully active.
