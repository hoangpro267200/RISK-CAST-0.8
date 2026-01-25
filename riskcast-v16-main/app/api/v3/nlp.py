"""
NLP API Endpoints

Provides document processing and chatbot capabilities.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from app.ml.nlp import (
    document_processor,
    chatbot,
    DocumentType,
    Intent
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["NLP"])


# ============================================================================
# Document Processing Models
# ============================================================================

class EntityResponse(BaseModel):
    """Extracted entity."""
    entity_type: str
    value: str
    confidence: float
    start_pos: int
    end_pos: int
    context: str = ""


class DocumentAnalysisRequest(BaseModel):
    """Request for document analysis."""
    text: str = Field(..., description="Document text to analyze")


class DocumentAnalysisResponse(BaseModel):
    """Response from document analysis."""
    document_type: str
    type_confidence: float
    entities: List[EntityResponse]
    key_values: Dict[str, str]
    summary: Optional[str] = None
    sentiment: Optional[Dict[str, Any]] = None
    flags: List[str]
    metadata: Dict[str, Any]


# ============================================================================
# Chatbot Models
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    user_id: Optional[str] = Field(None, description="User ID")


class ChatResponse(BaseModel):
    """Chat response."""
    response: str
    intent: str
    confidence: float
    session_id: str
    collected_info: Dict[str, Any]
    timestamp: datetime


class ConversationHistoryResponse(BaseModel):
    """Conversation history."""
    session_id: str
    user_id: Optional[str]
    messages: List[Dict[str, Any]]
    current_intent: Optional[str]
    collected_info: Dict[str, Any]
    created_at: datetime
    last_activity: datetime


# ============================================================================
# Document Processing Endpoints
# ============================================================================

@router.post("/nlp/document/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(request: DocumentAnalysisRequest):
    """
    Analyze a document using NLP.
    
    Performs:
    - Document type classification
    - Named entity extraction
    - Key-value extraction
    - Sentiment analysis (for claims)
    - Summarization
    - Issue detection
    
    ## Request Body
    
    ```json
    {
        "text": "BILL OF LADING\\n\\nB/L No: BL123456\\nVessel: MV OCEAN STAR\\n..."
    }
    ```
    
    ## Response
    
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
                "end_pos": 33
            }
        ],
        "key_values": {
            "bl_number": "BL123456",
            "vessel_name": "MV OCEAN STAR"
        },
        "summary": "Bill of Lading for shipment on vessel MV OCEAN STAR...",
        "flags": []
    }
    ```
    """
    try:
        # Analyze document
        analysis = document_processor.analyze(request.text)
        
        # Convert to response model
        entities = [
            EntityResponse(
                entity_type=e.entity_type,
                value=e.value,
                confidence=e.confidence,
                start_pos=e.start_pos,
                end_pos=e.end_pos,
                context=e.context
            )
            for e in analysis.entities
        ]
        
        logger.info(
            "Document analyzed",
            doc_type=analysis.document_type,
            num_entities=len(entities),
            num_flags=len(analysis.flags)
        )
        
        return DocumentAnalysisResponse(
            document_type=analysis.document_type.value,
            type_confidence=analysis.type_confidence,
            entities=entities,
            key_values=analysis.key_values,
            summary=analysis.summary,
            sentiment=analysis.sentiment,
            flags=analysis.flags,
            metadata=analysis.metadata
        )
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Document analysis failed: {str(e)}"
        )


@router.post("/nlp/document/classify")
async def classify_document(request: DocumentAnalysisRequest):
    """
    Classify document type only (faster than full analysis).
    
    ## Request Body
    
    ```json
    {
        "text": "COMMERCIAL INVOICE\\n\\nInvoice No: INV-2026-001..."
    }
    ```
    
    ## Response
    
    ```json
    {
        "document_type": "commercial_invoice",
        "confidence": 0.92
    }
    ```
    """
    try:
        doc_type, confidence = document_processor.classify_document(request.text)
        
        return {
            "document_type": doc_type.value,
            "confidence": confidence
        }
        
    except Exception as e:
        logger.error(f"Document classification failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )


@router.post("/nlp/document/extract-entities")
async def extract_entities(request: DocumentAnalysisRequest):
    """
    Extract named entities from document.
    
    ## Request Body
    
    ```json
    {
        "text": "Policy No: POL-2026-12345\\nClaim filed on 2026-01-15..."
    }
    ```
    
    ## Response
    
    ```json
    {
        "entities": [
            {
                "entity_type": "POLICY_NUMBER",
                "value": "POL-2026-12345",
                "confidence": 0.85,
                "start_pos": 11,
                "end_pos": 25
            }
        ]
    }
    ```
    """
    try:
        entities = document_processor.extract_entities(request.text)
        
        return {
            "entities": [
                {
                    "entity_type": e.entity_type,
                    "value": e.value,
                    "confidence": e.confidence,
                    "start_pos": e.start_pos,
                    "end_pos": e.end_pos,
                    "context": e.context
                }
                for e in entities
            ]
        }
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Entity extraction failed: {str(e)}"
        )


@router.post("/nlp/document/summarize")
async def summarize_document(
    text: str = Form(...),
    max_length: int = Form(150)
):
    """
    Generate document summary.
    
    ## Form Data
    
    - `text`: Document text
    - `max_length`: Maximum summary length (default: 150)
    
    ## Response
    
    ```json
    {
        "summary": "Bill of Lading for container ABCD1234567 on vessel MV OCEAN STAR...",
        "original_length": 1543,
        "summary_length": 148
    }
    ```
    """
    try:
        summary = document_processor.generate_summary(text, max_length)
        
        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary)
        }
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )


# ============================================================================
# Chatbot Endpoints
# ============================================================================

@router.post("/nlp/chat", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """
    Send a message to the AI chatbot.
    
    The chatbot can help with:
    - Getting quotes
    - Checking policy status
    - Filing claims
    - Claim status inquiries
    - Coverage questions
    - Pricing information
    
    ## Request Body
    
    ```json
    {
        "message": "I need a quote for shipping electronics from China to USA",
        "session_id": "user-123-session",
        "user_id": "user-123"
    }
    ```
    
    ## Response
    
    ```json
    {
        "response": "I'd be happy to help you get a quote! I'll need some information:\\n\\n1. What's the approximate value?\\n2. When will you be shipping?",
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
    """
    try:
        # Generate session ID if not provided
        if not request.session_id:
            import uuid
            session_id = str(uuid.uuid4())
        else:
            session_id = request.session_id
        
        # Get response from chatbot
        response, context = chatbot.chat(
            user_message=request.message,
            session_id=session_id,
            user_id=request.user_id
        )
        
        # Get the last user message for intent/confidence
        last_user_msg = [m for m in context.messages if m.role == "user"][-1]
        
        logger.info(
            "Chat response generated",
            session_id=session_id,
            intent=last_user_msg.intent,
            response_length=len(response)
        )
        
        return ChatResponse(
            response=response,
            intent=last_user_msg.intent.value if last_user_msg.intent else "unknown",
            confidence=last_user_msg.confidence,
            session_id=session_id,
            collected_info=context.collected_info,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/nlp/chat/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(session_id: str):
    """
    Get conversation history for a session.
    
    ## Path Parameters
    
    - `session_id`: Session identifier
    
    ## Response
    
    ```json
    {
        "session_id": "user-123-session",
        "user_id": "user-123",
        "messages": [
            {
                "role": "user",
                "content": "I need a quote",
                "timestamp": "2026-01-24T10:29:00Z",
                "intent": "get_quote"
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
    """
    try:
        context = chatbot.get_context(session_id)
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        # Convert messages to dict
        messages = [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "intent": m.intent.value if m.intent else None,
                "entities": m.entities,
                "confidence": m.confidence
            }
            for m in context.messages
        ]
        
        return ConversationHistoryResponse(
            session_id=context.session_id,
            user_id=context.user_id,
            messages=messages,
            current_intent=context.current_intent.value if context.current_intent else None,
            collected_info=context.collected_info,
            created_at=context.created_at,
            last_activity=context.last_activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )


@router.delete("/nlp/chat/session/{session_id}")
async def reset_chat_session(session_id: str):
    """
    Reset a chat session (clear history and context).
    
    ## Path Parameters
    
    - `session_id`: Session identifier
    
    ## Response
    
    ```json
    {
        "session_id": "user-123-session",
        "reset": true,
        "message": "Session reset successfully"
    }
    ```
    """
    try:
        success = chatbot.reset_context(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        return {
            "session_id": session_id,
            "reset": True,
            "message": "Session reset successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset session: {str(e)}"
        )


@router.post("/nlp/chat/cleanup")
async def cleanup_old_sessions(max_age_hours: int = 24):
    """
    Clean up old chat sessions.
    
    ## Query Parameters
    
    - `max_age_hours`: Maximum age in hours (default: 24)
    
    ## Response
    
    ```json
    {
        "cleaned": true,
        "message": "Old sessions cleaned up"
    }
    ```
    """
    try:
        chatbot.cleanup_old_contexts(max_age_hours)
        
        return {
            "cleaned": True,
            "message": f"Sessions older than {max_age_hours} hours cleaned up"
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/nlp/status")
async def get_nlp_status():
    """
    Get NLP system status.
    
    ## Response
    
    ```json
    {
        "document_processing": {
            "available": true,
            "spacy_loaded": true,
            "sentiment_available": true,
            "capabilities": ["classification", "ner", "summarization", "sentiment"]
        },
        "chatbot": {
            "available": true,
            "active_sessions": 5,
            "supported_intents": ["get_quote", "file_claim", ...]
        }
    }
    ```
    """
    # Check document processor status
    doc_status = {
        "available": True,
        "spacy_loaded": document_processor.nlp is not None,
        "sentiment_available": document_processor.sentiment_analyzer is not None,
        "capabilities": ["classification", "entity_extraction"]
    }
    
    if document_processor.nlp:
        doc_status["capabilities"].extend(["ner", "summarization"])
    
    if document_processor.sentiment_analyzer:
        doc_status["capabilities"].append("sentiment_analysis")
    
    # Check chatbot status
    chat_status = {
        "available": True,
        "active_sessions": len(chatbot.contexts),
        "supported_intents": [intent.value for intent in Intent]
    }
    
    return {
        "document_processing": doc_status,
        "chatbot": chat_status,
        "timestamp": datetime.utcnow().isoformat()
    }
