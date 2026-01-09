"""
AI System Advisor API Routes
"""

import uuid
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from app.ai_system_advisor.advisor_core import AdvisorCore
from app.ai_system_advisor.context_manager import ContextManager
from app.ai_system_advisor.data_access import DataAccess
from app.ai_system_advisor.action_handlers import ActionHandlers

router = APIRouter()

# Initialize advisor (lazy initialization to ensure .env is loaded)
advisor_core = None
context_manager = None
data_access = None
action_handlers = None

def get_advisor_core():
    """Get or create advisor core instance"""
    global advisor_core
    if advisor_core is None:
        advisor_core = AdvisorCore()
        print(f"[AI Advisor Routes] AdvisorCore initialized - use_llm: {advisor_core.use_llm}")
    return advisor_core

def get_context_manager():
    """Get or create context manager instance"""
    global context_manager
    if context_manager is None:
        context_manager = ContextManager()
    return context_manager

def get_data_access():
    """Get or create data access instance"""
    global data_access
    if data_access is None:
        data_access = DataAccess()
    return data_access

def get_action_handlers():
    """Get or create action handlers instance"""
    global action_handlers
    if action_handlers is None:
        action_handlers = ActionHandlers()
    return action_handlers


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class ActionRequest(BaseModel):
    session_id: str
    parameters: Optional[Dict[str, Any]] = None


@router.get("/advisor/status")
async def get_status():
    """
    Check if Claude API is configured and available
    Returns status of AI Advisor configuration with model test
    """
    try:
        advisor = get_advisor_core()
        
        # Check if client is initialized
        client_initialized = advisor.anthropic_client is not None
        use_llm = advisor.use_llm
        
        # Test Claude API with a simple call if client is available
        model = None
        llm_available = False
        
        if client_initialized and use_llm:
            # Try models in order of preference
            models_to_try = [
                "claude-sonnet-4-20250514",  # Current recommended model
                "claude-3-5-sonnet-20241022",  # Fallback if Sonnet 4 not available
                "claude-3-opus-20240229",     # Fallback option
            ]
            
            llm_available = False
            model = None
            
            for model_name in models_to_try:
                try:
                    # Test call to verify model is accessible
                    test_response = advisor.anthropic_client.messages.create(
                        model=model_name,
                        max_tokens=10,
                        messages=[{"role": "user", "content": "test"}]
                    )
                    llm_available = True
                    model = model_name
                    break  # Success, exit loop
                except Exception as test_error:
                    error_str = str(test_error).lower()
                    # If it's a 404 (model not found), try next model
                    if "404" in error_str or "not_found" in error_str:
                        print(f"[AI Advisor Status] Model {model_name} not available, trying next...")
                        continue
                    else:
                        # Other error (auth, etc.) - don't try other models
                        print(f"[AI Advisor Status] Claude test failed: {test_error}")
                        llm_available = False
                        model = None
                        advisor.use_llm = False
                        break
            
            if not llm_available:
                print(f"[AI Advisor Status] All models failed - Claude API unavailable")
                advisor.use_llm = False
        
        return {
            "status": "success",
            "data": {
                "llm": llm_available,
                "model": model
            }
        }
    except Exception as e:
        print(f"[AI Advisor Status] Error checking status: {e}")
        return {
            "status": "error",
            "error": {
                "code": "STATUS_CHECK_ERROR",
                "message": str(e)
            },
            "data": {
                "llm": False,
                "model": None
            }
        }


@router.post("/advisor/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint with conversation history
    """
    try:
        # Get instances (lazy initialization)
        advisor = get_advisor_core()
        
        # Check if LLM is available before processing
        if not advisor.use_llm or advisor.anthropic_client is None:
            return ChatResponse(
                status="error",
                error={
                    "code": "LLM_UNAVAILABLE",
                    "message": "Claude API is not available. Please configure the API key."
                }
            )
        
        # Generate session_id if not provided
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        
        # Get options
        options = request.options or {}
        language = options.get("language", "vi")  # Default to Vietnamese
        
        # Auto-detect Vietnamese if message contains Vietnamese characters
        if not options.get("language"):
            message_text = request.message.lower()
            vietnamese_chars = ["ă", "â", "ê", "ô", "ơ", "ư", "đ", "rủi ro", "đề xuất", "giảm thiểu"]
            if any(char in message_text for char in vietnamese_chars):
                language = "vi"
        
        # Process message
        response = await advisor.process_message(
            message=request.message,
            session_id=session_id,
            context=request.context,
            language=language
        )
        
        # Check if response indicates model error
        metadata = response.metadata or {}
        if metadata.get("error") or metadata.get("model") == "deterministic":
            # If we got a deterministic response due to model error, mark LLM as unavailable
            error_msg = metadata.get("error", "")
            if error_msg and any(keyword in error_msg.lower() for keyword in ["not_found", "404", "model"]):
                advisor.use_llm = False
        
        # Format response
        return ChatResponse(
            status="success",
            data={
                "reply": response.reply,
                "session_id": response.session_id,
                "actions": response.actions,
                "function_calls": [
                    {
                        "function_name": fc.function_name,
                        "success": fc.success,
                        "result": fc.result,
                        "error": fc.error
                    }
                    for fc in response.function_calls
                ],
                "metadata": response.metadata
            }
        )
    except Exception as e:
        # Check if it's a model-related error
        error_str = str(e).lower()
        is_model_error = any(keyword in error_str for keyword in [
            "not_found", "404", "unauthorized", "401", 
            "forbidden", "403", "model"
        ])
        
        if is_model_error:
            # Disable LLM for future calls
            try:
                advisor = get_advisor_core()
                advisor.use_llm = False
            except:
                pass
        
        return ChatResponse(
            status="error",
            error={
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        )


@router.get("/advisor/history")
async def get_history(session_id: str, limit: int = 20):
    """
    Get conversation history
    """
    try:
        cm = get_context_manager()
        history = await cm.get_conversation_history(session_id, limit=limit)
        
        return {
            "status": "success",
            "data": {
                "session_id": session_id,
                "messages": [
                    {
                        "role": msg["role"],
                        "content": msg["content"]
                    }
                    for msg in history
                ],
                "total_messages": len(history),
                "has_more": len(history) >= limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advisor/context")
async def get_context(session_id: str):
    """
    Get current system context
    """
    try:
        da = get_data_access()
        context = da.get_system_context(session_id)
        
        return {
            "status": "success",
            "data": {
                "session_id": session_id,
                "current_assessment": context.current_assessment,
                "shipment": context.shipment,
                "financial_metrics": context.financial_metrics,
                "esg_metrics": context.esg_metrics,
                "scenario_results": context.scenario_results,
                "available_actions": context.available_actions
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advisor/actions/{action}")
async def execute_action(action: str, request: ActionRequest):
    """
    Execute system action
    """
    try:
        ah = get_action_handlers()
        result = await ah.execute_function(
            function_name=action,
            function_args=request.parameters or {},
            session_id=request.session_id
        )
        
        return {
            "status": "success" if result.get("success") else "error",
            "data": {
                "action": action,
                "result": result
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": {
                "code": "ACTION_EXECUTION_ERROR",
                "message": str(e)
            }
        }


@router.delete("/advisor/history")
async def clear_history(session_id: str):
    """
    Clear conversation history
    """
    try:
        cm = get_context_manager()
        await cm.clear_conversation(session_id)
        
        return {
            "status": "success",
            "data": {
                "session_id": session_id,
                "messages_deleted": "all"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advisor/downloads/{file_id}")
async def download_file(file_id: str):
    """
    Download exported file
    """
    try:
        # Get file path
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        file_path = root_dir / "data" / "exports" / f"{file_id}.pdf"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=f"riskcast_report_{file_id}.pdf",
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
