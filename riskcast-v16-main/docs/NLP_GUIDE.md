# NLP Capabilities Guide

## 📋 Overview

Complete guide to Natural Language Processing (NLP) capabilities for document processing and AI chatbot support.

**Features:**
- Document type classification
- Named entity extraction (NER)
- Key-value extraction
- Sentiment analysis
- Document summarization
- Issue detection
- AI chatbot with intent classification
- Multi-turn conversations
- Context management

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NLP System Architecture                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐  ┌──────────────────────────┐
│  Document Processing         │  │  AI Chatbot              │
│                              │  │                          │
│  ┌────────────────────────┐  │  │  ┌───────────────────┐  │
│  │ Classification         │  │  │  │ Intent            │  │
│  │ - 7 document types     │  │  │  │ - 11 intents      │  │
│  │ - Pattern matching     │  │  │  │ - Pattern match   │  │
│  └────────────────────────┘  │  │  └───────────────────┘  │
│                              │  │                          │
│  ┌────────────────────────┐  │  │  ┌───────────────────┐  │
│  │ Entity Extraction      │  │  │  │ Entity Extract    │  │
│  │ - spaCy NER            │  │  │  │ - Regex patterns  │  │
│  │ - Custom patterns      │  │  │  │ - Context aware   │  │
│  └────────────────────────┘  │  │  └───────────────────┘  │
│                              │  │                          │
│  ┌────────────────────────┐  │  │  ┌───────────────────┐  │
│  │ Key-Value Extract      │  │  │  │ Multi-turn Conv   │  │
│  │ - Domain-specific      │  │  │  │ - State tracking  │  │
│  │ - Document type aware  │  │  │  │ - Info collection │  │
│  └────────────────────────┘  │  │  └───────────────────┘  │
│                              │  │                          │
│  ┌────────────────────────┐  │  │  ┌───────────────────┐  │
│  │ Sentiment Analysis     │  │  │  │ Response Gen      │  │
│  │ - Transformers         │  │  │  │ - Templates       │  │
│  │ - DistilBERT           │  │  │  │ - Context-aware   │  │
│  └────────────────────────┘  │  │  └───────────────────┘  │
│                              │  │                          │
│  ┌────────────────────────┐  │  └──────────────────────────┘
│  │ Summarization          │  │
│  │ - Extractive           │  │
│  │ - Sentence scoring     │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │ Issue Detection        │  │
│  │ - Missing fields       │  │
│  │ - Suspicious patterns  │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

---

## 📄 Document Processing

### Document Types Supported (7)

1. **Bill of Lading** - Shipping documents
2. **Commercial Invoice** - Payment documents
3. **Packing List** - Cargo manifests
4. **Insurance Certificate** - Coverage proof
5. **Claim Report** - Loss/damage reports
6. **Survey Report** - Inspection results
7. **Customs Declaration** - Import/export docs

### Features

#### 1. Document Classification

```python
from app.ml.nlp import document_processor

text = """
BILL OF LADING

B/L No: BL-2026-001234
Vessel: MV OCEAN STAR
Port of Loading: CNSHA (Shanghai)
Port of Discharge: USNYC (New York)

Shipper: ABC Trading Co.
Consignee: XYZ Imports LLC
"""

# Classify document
doc_type, confidence = document_processor.classify_document(text)
# Returns: (DocumentType.BILL_OF_LADING, 0.85)
```

**Algorithm:**
- Pattern matching against 40+ keywords per type
- Confidence = (matched_patterns / total_patterns) × 1.5
- Best match selected

#### 2. Named Entity Extraction

```python
# Extract entities using spaCy + custom patterns
entities = document_processor.extract_entities(text)

# Example entities:
[
    ExtractedEntity(
        entity_type="BL_NUMBER",
        value="BL-2026-001234",
        confidence=0.85,
        start_pos=25,
        end_pos=39,
        context="...BILL OF LADING\n\nB/L No: BL-2026-001234\nVessel..."
    ),
    ExtractedEntity(
        entity_type="VESSEL_NAME",
        value="MV OCEAN STAR",
        confidence=0.85,
        start_pos=48,
        end_pos=61
    ),
    ExtractedEntity(
        entity_type="PORT_CODE",
        value="CNSHA",
        confidence=0.9,
        start_pos=87,
        end_pos=92
    )
]
```

**Entity Types Extracted:**

| Category | Entity Types |
|----------|--------------|
| **Identifiers** | policy_number, claim_number, invoice_number, bl_number |
| **Shipping** | container_number, vessel_name, port_code |
| **Financial** | amount, currency |
| **Temporal** | date, time |
| **Physical** | weight, dimensions |
| **Contact** | email, phone |
| **spaCy NER** | PERSON, ORG, GPE, MONEY, DATE, etc. |

#### 3. Key-Value Extraction

```python
# Extract structured key-value pairs
key_values = document_processor.extract_key_values(text, doc_type)

# Example output:
{
    "bl_number": "BL-2026-001234",
    "vessel_name": "MV OCEAN STAR",
    "port_code": "CNSHA",
    "shipper": "ABC Trading Co.",
    "consignee": "XYZ Imports LLC"
}
```

**Document-Specific Extraction:**

- **Bill of Lading:** shipper, consignee, vessel, ports, commodity
- **Claim Report:** loss_date, loss_description, cause, policy_number
- **Commercial Invoice:** seller, buyer, payment_terms, amounts

#### 4. Sentiment Analysis

```python
# For claim descriptions
sentiment = document_processor.analyze_sentiment(claim_text)

# Example output:
{
    "label": "NEGATIVE",
    "score": 0.89,
    "positive": 0.11,
    "negative": 0.89
}
```

**Uses:** DistilBERT sentiment model (fine-tuned on SST-2)

#### 5. Summarization

```python
# Generate extractive summary
summary = document_processor.generate_summary(text, max_length=150)

# Example:
"Bill of Lading for container ABCD1234567 on vessel MV OCEAN STAR 
from Shanghai to New York. Cargo valued at $100,000. Shipper: ABC 
Trading Co., Consignee: XYZ Imports LLC."
```

**Algorithm:**
- Sentence scoring based on:
  - Position (first sentences prioritized)
  - Entity density
  - Keyword presence
- Top 3 sentences selected
- Original order preserved

#### 6. Issue Detection

```python
# Detect problems in documents
flags = document_processor.detect_issues(text, doc_type, key_values)

# Example flags:
[
    "⚠️ Missing critical fields: claim_number, amount",
    "🚨 Total loss claim - requires special handling",
    "⚠️ Contains vague language - request clarification"
]
```

**Checks:**
- Missing required fields
- Suspicious keywords (theft, total loss, fire)
- Vague language
- PII that needs redaction
- Multiple currencies
- Document length issues

#### 7. Complete Analysis

```python
# All-in-one analysis
analysis = document_processor.analyze(text)

# Returns DocumentAnalysis with:
# - document_type
# - type_confidence
# - entities (list)
# - key_values (dict)
# - summary (str)
# - sentiment (dict, if claim)
# - flags (list)
# - metadata (dict)
```

---

## 🤖 AI Chatbot

### Intents Supported (11)

1. **get_quote** - Request insurance quote
2. **check_policy** - View policy details
3. **file_claim** - Report loss/damage
4. **claim_status** - Check claim progress
5. **coverage_question** - Ask about coverage
6. **pricing_question** - Ask about rates
7. **general_question** - General inquiries
8. **greeting** - Hi, hello
9. **goodbye** - Bye, thanks
10. **help** - What can you do?
11. **unknown** - Fallback

### Features

#### 1. Intent Classification

```python
from app.ml.nlp import chatbot

message = "I need a quote for shipping electronics from China to USA"
intent, confidence = chatbot.classify_intent(message)
# Returns: (Intent.GET_QUOTE, 0.95)
```

**Algorithm:**
- Pattern matching with 40+ patterns across 11 intents
- Scoring based on pattern specificity
- Boost for patterns matching at message start

#### 2. Entity Extraction

```python
# Extract structured info from messages
entities = chatbot.extract_entities(message)

# Example output:
{
    "cargo_type": "electronics",
    "origin_port": "China",
    "destination_port": "USA"
}
```

**Entities Extracted:**
- cargo_value
- origin_port / destination_port
- cargo_type
- policy_number / claim_number
- date
- weight
- container_count

#### 3. Multi-Turn Conversations

```python
# Session-based context management
session_id = "user-123-session"

# Turn 1
response1, context = chatbot.chat(
    "I need a quote",
    session_id
)
# Response: "I'd be happy to help! What type of cargo..."

# Turn 2
response2, context = chatbot.chat(
    "Electronics worth $50,000",
    session_id
)
# Response: "Great! I have cargo type and value. Where is it shipping from and to?"

# Turn 3
response3, context = chatbot.chat(
    "From Shanghai to New York",
    session_id
)
# Response: "Perfect! Generating quote for $50,000 electronics from Shanghai to NY..."

# Context maintains:
# - Message history
# - Collected information
# - Current intent
# - Pending actions
```

#### 4. Context Management

```python
# Get conversation context
context = chatbot.get_context(session_id)

# Context contains:
{
    "session_id": "user-123-session",
    "user_id": "user-123",
    "messages": [...],  # Full history
    "current_intent": Intent.GET_QUOTE,
    "collected_info": {
        "cargo_type": "electronics",
        "cargo_value": "50000",
        "origin_port": "Shanghai",
        "destination_port": "New York"
    },
    "pending_action": None,
    "created_at": datetime(...),
    "last_activity": datetime(...)
}
```

#### 5. Response Generation

**Template-Based Responses:**

```python
# Simple responses (greetings, help)
responses = [
    "Hello! I'm the RISKCAST insurance assistant...",
    "Hi there! I can help with quotes, policies..."
]

# Multi-turn responses (quotes, claims)
responses = {
    "initial": "I'd be happy to help...",
    "need_cargo": "What type of cargo?",
    "need_value": "What's the value?",
    "complete": "Perfect! Generating quote..."
}
```

**Progressive Information Collection:**

```python
# Chatbot tracks what's collected vs. needed
GET_QUOTE requires:
- cargo_type
- cargo_value
- origin_port
- destination_port

FILE_CLAIM requires:
- policy_number
- loss_description
- date

# Shows progress:
"Great! I have:
✓ Cargo Type: Electronics
✓ Value: $50,000

I still need:
• Origin port
• Destination port"
```

---

## 💻 API Usage

### Document Processing API

#### Analyze Document (Complete)

```bash
curl -X POST http://localhost:8000/api/v3/nlp/document/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "BILL OF LADING\n\nB/L No: BL123456\nVessel: MV OCEAN STAR..."
}'
```

**Response:**
```json
{
    "document_type": "bill_of_lading",
    "type_confidence": 0.85,
    "entities": [
        {
            "entity_type": "BL_NUMBER",
            "value": "BL123456",
            "confidence": 0.85,
            "start_pos": 25,
            "end_pos": 33,
            "context": "...BILL OF LADING\n\nB/L No: BL123456\nVessel..."
        }
    ],
    "key_values": {
        "bl_number": "BL123456",
        "vessel_name": "MV OCEAN STAR"
    },
    "summary": "Bill of Lading for shipment on vessel MV OCEAN STAR...",
    "flags": [],
    "metadata": {
        "text_length": 543,
        "num_entities": 8,
        "spacy_available": true
    }
}
```

#### Classify Only (Fast)

```bash
curl -X POST http://localhost:8000/api/v3/nlp/document/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "COMMERCIAL INVOICE..."
}'
```

**Response:**
```json
{
    "document_type": "commercial_invoice",
    "confidence": 0.92
}
```

#### Extract Entities

```bash
curl -X POST http://localhost:8000/api/v3/nlp/document/extract-entities \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Policy No: POL-2026-12345\nClaim filed on 2026-01-15..."
}'
```

#### Summarize

```bash
curl -X POST http://localhost:8000/api/v3/nlp/document/summarize \
  -F "text=<long document text>" \
  -F "max_length=150"
```

### Chatbot API

#### Send Message

```bash
curl -X POST http://localhost:8000/api/v3/nlp/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a quote for shipping electronics from China to USA",
    "session_id": "user-123-session",
    "user_id": "user-123"
}'
```

**Response:**
```json
{
    "response": "I'd be happy to help you get a quote! What's the approximate value of the electronics?",
    "intent": "get_quote",
    "confidence": 0.95,
    "session_id": "user-123-session",
    "collected_info": {
        "cargo_type": "electronics",
        "origin_port": "China",
        "destination_port": "USA"
    },
    "timestamp": "2026-01-24T10:30:00Z"
}
```

#### Get Conversation History

```bash
curl http://localhost:8000/api/v3/nlp/chat/history/user-123-session
```

**Response:**
```json
{
    "session_id": "user-123-session",
    "user_id": "user-123",
    "messages": [
        {
            "role": "user",
            "content": "I need a quote",
            "timestamp": "2026-01-24T10:29:00Z",
            "intent": "get_quote",
            "confidence": 0.92
        },
        {
            "role": "assistant",
            "content": "I'd be happy to help...",
            "timestamp": "2026-01-24T10:29:01Z"
        }
    ],
    "current_intent": "get_quote",
    "collected_info": {},
    "created_at": "2026-01-24T10:29:00Z",
    "last_activity": "2026-01-24T10:29:01Z"
}
```

#### Reset Session

```bash
curl -X DELETE http://localhost:8000/api/v3/nlp/chat/session/user-123-session
```

#### Check Status

```bash
curl http://localhost:8000/api/v3/nlp/status
```

**Response:**
```json
{
    "document_processing": {
        "available": true,
        "spacy_loaded": true,
        "sentiment_available": true,
        "capabilities": [
            "classification",
            "entity_extraction",
            "ner",
            "summarization",
            "sentiment_analysis"
        ]
    },
    "chatbot": {
        "available": true,
        "active_sessions": 5,
        "supported_intents": [
            "get_quote",
            "check_policy",
            "file_claim",
            ...
        ]
    }
}
```

---

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements-ml.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Verify installation
python -c "import spacy; import transformers; print('NLP dependencies OK')"
```

### Python Usage

#### Document Processing

```python
from app.ml.nlp import document_processor

# Load document
with open("claim_report.txt", "r") as f:
    text = f.read()

# Analyze
analysis = document_processor.analyze(text)

print(f"Document Type: {analysis.document_type}")
print(f"Confidence: {analysis.type_confidence:.2f}")
print(f"Entities: {len(analysis.entities)}")
print(f"Key Values: {analysis.key_values}")
print(f"Summary: {analysis.summary}")
print(f"Flags: {analysis.flags}")
```

#### Chatbot

```python
from app.ml.nlp import chatbot

# Start conversation
session_id = "demo-session"

messages = [
    "Hi, I need help with insurance",
    "I want a quote for shipping goods",
    "Electronics worth $50,000",
    "From Shanghai to Los Angeles"
]

for msg in messages:
    response, context = chatbot.chat(msg, session_id)
    print(f"\nUser: {msg}")
    print(f"Bot: {response}")
    print(f"Collected: {context.collected_info}")
```

---

## 📊 Performance

### Document Processing

| Operation | Latency | Model Used |
|-----------|---------|------------|
| Classification | <50ms | Pattern matching |
| Entity Extraction (no spaCy) | <100ms | Regex |
| Entity Extraction (with spaCy) | <300ms | spaCy en_core_web_sm |
| Sentiment Analysis | <200ms | DistilBERT |
| Summarization | <500ms | Extractive |
| Complete Analysis | <800ms | All above |

### Chatbot

| Operation | Latency |
|-----------|---------|
| Intent Classification | <10ms |
| Entity Extraction | <20ms |
| Response Generation | <50ms |
| Full Turn | <100ms |

### Resource Usage

| Component | Memory | Disk Space |
|-----------|--------|------------|
| spaCy (en_core_web_sm) | ~150MB | ~15MB |
| DistilBERT (sentiment) | ~250MB | ~260MB |
| Chatbot | ~10MB | <1MB |
| **Total** | **~410MB** | **~276MB** |

---

## 🔧 Configuration

### Document Processor

```python
from app.ml.nlp.document_processor import DocumentProcessor

# Custom processor
processor = DocumentProcessor()

# Add custom patterns
processor.field_patterns["custom_field"] = r"my_pattern"

# Adjust confidence thresholds
# (modify in classify_document method)
```

### Chatbot

```python
from app.ml.nlp.chatbot import InsuranceChatbot

# Custom chatbot
bot = InsuranceChatbot()

# Add custom intent
from app.ml.nlp.chatbot import Intent

# Add patterns
bot.intent_patterns[Intent.CUSTOM] = [
    r"custom pattern 1",
    r"custom pattern 2"
]

# Add responses
bot.responses[Intent.CUSTOM] = [
    "Custom response 1",
    "Custom response 2"
]
```

---

## 🐛 Troubleshooting

### spaCy Model Not Found

**Problem:** `OSError: [E050] Can't find model 'en_core_web_sm'`

**Solution:**
```bash
python -m spacy download en_core_web_sm
```

### Transformers Model Download Slow

**Problem:** Sentiment model download takes long

**Solution:**
```bash
# Pre-download model
python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"
```

### Out of Memory

**Problem:** `RuntimeError: CUDA out of memory`

**Solution:**
- Use CPU-only: `device=-1` in pipeline
- Reduce batch size
- Use lighter models

---

## 📚 Best Practices

### Document Processing

✅ **DO:**
- Pre-process text (remove extra whitespace)
- Use appropriate document type hints
- Validate extracted values
- Handle missing entities gracefully

❌ **DON'T:**
- Process extremely long documents (>10k chars) without chunking
- Trust all extracted values without validation
- Ignore confidence scores
- Skip issue detection

### Chatbot

✅ **DO:**
- Use unique session IDs per user
- Clean up old sessions regularly
- Validate collected information
- Provide fallback responses

❌ **DON'T:**
- Store sensitive data in context
- Keep sessions indefinitely
- Ignore user intent confidence
- Make assumptions about incomplete data

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0  
**Owner:** ML Engineering Team
