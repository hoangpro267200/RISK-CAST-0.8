"""
RISKCAST Enterprise AI - AI API Endpoints
6 Core AI endpoints with Claude 3.5 Sonnet integration
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json
from typing import Dict, Optional, AsyncGenerator, Any

from app.risk_engine import (
    compute_overall_risk,
    compute_route_risk,
    compute_esg_score,
    compute_delay_probability,
    map_risk_to_insurance,
    generate_summary
)
from app.memory import memory_system
from app.core.utils.validators import sanitize_input, validate_shipment_data, build_ai_prompt
from pathlib import Path

# ===============================
# ENV LOADER - Load .env file
# ===============================
# Note: main.py loads .env first, but we load here too as fallback in case api_ai is imported standalone
root_dir = Path(__file__).resolve().parent.parent
env_file = root_dir / ".env"

# Try multiple paths to find .env file
env_loaded = False
api_key_before_load = os.getenv("ANTHROPIC_API_KEY")

if env_file.exists():
    # Force reload to ensure we get the latest values
    load_dotenv(env_file, override=True)
    env_loaded = True
    print(f"[API_AI] Checking .env at: {env_file}")
    
    # Validate .env file content and manually load if needed
    try:
        # Try different encodings to handle BOM and encoding issues
        encodings = ['utf-8-sig', 'utf-8', 'latin-1']
        env_content = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(env_file, 'r', encoding=encoding) as f:
                    env_content = f.read()
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if not env_content:
            print(f"[API_AI] [ERROR] Could not read .env file with any encoding!")
            raise Exception("Failed to read .env file")
        
        if used_encoding != 'utf-8':
            print(f"[API_AI] [INFO] Read .env file with encoding: {used_encoding}")
        
        has_key_line = 'ANTHROPIC_API_KEY' in env_content
        if not has_key_line:
            print(f"[API_AI] [ERROR] File .env exists but does not contain 'ANTHROPIC_API_KEY' line!")
            print(f"[API_AI] [ERROR] Please add this line to .env file: ANTHROPIC_API_KEY=your_key_here")
        else:
            # Check if key has a value (not just the variable name)
            lines = env_content.split('\n')
            key_line = None
            for line in lines:
                stripped = line.strip()
                # Skip comments and empty lines
                if stripped.startswith('#') or not stripped:
                    continue
                if stripped.startswith('ANTHROPIC_API_KEY'):
                    key_line = stripped
                    break
            
            if key_line:
                if '=' not in key_line:
                    print(f"[API_AI] [ERROR] ANTHROPIC_API_KEY line exists but has no '=' sign!")
                    print(f"[API_AI] [ERROR] Current line: {key_line[:50]}...")
                    print(f"[API_AI] [ERROR] Format should be: ANTHROPIC_API_KEY=your_actual_key")
                else:
                    parts = key_line.split('=', 1)
                    key_value = parts[1].strip() if len(parts) > 1 else ''
                    if not key_value:
                        print(f"[API_AI] [ERROR] ANTHROPIC_API_KEY line exists but has no value!")
                        print(f"[API_AI] [ERROR] Current line: {key_line[:50]}...")
                        print(f"[API_AI] [ERROR] Format should be: ANTHROPIC_API_KEY=your_actual_key")
                    else:
                        # Always manually set to ensure it's loaded (fallback if dotenv fails)
                        os.environ["ANTHROPIC_API_KEY"] = key_value
                        print(f"[API_AI] [INFO] Loaded ANTHROPIC_API_KEY from .env file (length: {len(key_value)})")
    except Exception as e:
        print(f"[API_AI] [WARNING] Could not validate/load .env file content: {str(e)}")
        import traceback
        traceback.print_exc()
else:
    # Try loading from current directory
    current_env = Path(".env")
    if current_env.exists():
        load_dotenv(".env", override=True)
        env_loaded = True
        print(f"[API_AI] Checking .env at current directory: {current_env.absolute()}")
    else:
        # Fallback: try to load from any location
        load_dotenv(override=False)
        print(f"[API_AI] .env file not found at expected locations. Using existing environment variables.")

router = APIRouter()

# Get API key from environment (SECURE: No logging of key)
# Fallback to "dummy" if not set to prevent warnings
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
api_key_after_load = ANTHROPIC_API_KEY

if not ANTHROPIC_API_KEY:
    ANTHROPIC_API_KEY = "dummy"
    print(f"[API_AI] [WARNING] ANTHROPIC_API_KEY not found in environment variables")
    print(f"[API_AI] [DEBUG] Key before load: {bool(api_key_before_load)}, after load: {bool(api_key_after_load)}")
    print(f"[API_AI] [DEBUG] env_file.exists(): {env_file.exists() if env_file else False}")
    print(f"[API_AI] [DEBUG] Current working directory: {os.getcwd()}")
    if env_file.exists():
        print(f"[API_AI] [ACTION REQUIRED] Please check your .env file and ensure it contains:")
        print(f"[API_AI] [ACTION REQUIRED] ANTHROPIC_API_KEY=sk-ant-api03-your_actual_key_here")
        print(f"[API_AI] [ACTION REQUIRED] Get key from: https://console.anthropic.com/")
else:
    print(f"[API_AI] [INFO] ANTHROPIC_API_KEY found (length: {len(ANTHROPIC_API_KEY)})")

# Validate and initialize client
if (ANTHROPIC_API_KEY and 
    ANTHROPIC_API_KEY != "your_anthropic_api_key_here" and 
    ANTHROPIC_API_KEY != "dummy" and 
    len(ANTHROPIC_API_KEY) > 20):
    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        print(f"[INFO] Anthropic client initialized (API key configured, length: {len(ANTHROPIC_API_KEY)})")
    except Exception as e:
        client = None
        print(f"[ERROR] Failed to initialize Anthropic client: {str(e)}")
        print("[WARNING] AI features will not work.")
else:
    client = None
    if ANTHROPIC_API_KEY != "dummy":
        print(f"[WARNING] ANTHROPIC_API_KEY not configured properly. Current value: '{ANTHROPIC_API_KEY[:20] if len(ANTHROPIC_API_KEY) > 20 else ANTHROPIC_API_KEY}...'")
        print("[WARNING] Please set ANTHROPIC_API_KEY in .env file with a valid key (length > 20)")
    else:
        print("[WARNING] ANTHROPIC_API_KEY not set. AI features will not work.")
        print("[WARNING] Please set ANTHROPIC_API_KEY in .env file")


# ==================== PROMPT TEMPLATES ====================

BASE_PROMPT = """You are RISKCAST Enterprise AI — a Logistics Risk Intelligence System specializing in supply chain risk analysis.

CRITICAL INSTRUCTIONS:
1. **FOCUS ON THE USER'S QUESTION**: Read the user's question carefully and answer it directly and specifically. Do not provide generic information that doesn't address the question.
2. **BE CONCISE**: Provide clear, actionable answers without unnecessary background unless directly relevant to the question.
3. **STRUCTURE YOUR RESPONSE**: Use structured format (JSON when appropriate, or clear sections) to make information easy to scan.
4. **PRIORITIZE RELEVANCE**: Only include information that directly relates to the user's question. Skip general knowledge unless it's essential context.

Your expertise areas:
- Logistics risk analysis and quantification
- Route optimization and recommendations
- Insurance guidance and risk mitigation
- ESG advisory and carbon footprint analysis
- Delay prediction and supply chain disruptions
- Risk driver identification and impact assessment

Response style: Expert consulting tone (KPMG / Deloitte / BCG style) - professional, data-driven, actionable."""

ANALYZE_PROMPT = """Analyze this shipment and provide:

1. Top 3 risk drivers (with why they matter)
2. What-if analysis (2 scenarios: best case, worst case)
3. Priority actions ranked by impact
4. Executive summary (120 words)

Shipment Data:
{shipment_data}

Risk Analysis:
{risk_analysis}

Provide expert-level insights in KPMG consulting style."""

ROUTE_PROMPT = """Recommend the best route for this shipment:

Shipment Data:
{shipment_data}

Current Route Risk:
{route_risk}

Provide:
1. Best route recommendation (SEA / AIR / RAIL / MULTIMODAL)
2. Estimated risk score for recommended route
3. Supporting evidence: weather, port congestion, political stability
4. Why this route is safer
5. Alternative routes if applicable

Format as structured analysis."""

INSURANCE_PROMPT = """Provide risk-based insurance guidance:

Shipment Data:
{shipment_data}

Risk Analysis:
{risk_analysis}

Insurance Mapping:
{insurance_mapping}

Answer:
1. Should the client buy insurance? (Yes/No/Recommended)
2. Optimal coverage level (Basic/Standard/Comprehensive)
3. Expected Loss (USD)
4. Quantitative reasoning
5. Cost-benefit analysis

Provide expert insurance advisory."""

DELAY_PROMPT = """Predict delivery delay probability:

Shipment Data:
{shipment_data}

Delay Analysis:
{delay_analysis}

Provide:
1. Delay probability (%)
2. Main factors causing delay
3. Prevention measures (actionable)
4. Expected delay duration (days)
5. Risk mitigation strategies

Format as predictive analysis."""

ESG_PROMPT = """Provide ESG and carbon advisory:

Shipment Data:
{shipment_data}

ESG Analysis:
{esg_analysis}

Provide:
1. Carbon footprint (kg CO2e)
2. ESG score breakdown (0–100)
3. How to reduce emissions (specific actions)
4. Environmental impact assessment
5. Social and governance considerations

Format as sustainability advisory."""

HISTORY_PROMPT = """Compare these shipments and provide insights:

Shipment 1:
{shipment_1}

Shipment 2:
{shipment_2}

Comparison Data:
{comparison}

Provide:
1. Risk trend analysis
2. Key differences
3. Historical movement
4. Recommendations based on trends
5. Pattern recognition

Format as comparative analysis."""


# ==================== HELPER FUNCTIONS ====================

def _check_api_key_configured():
    """Check if API key is properly configured and return error message if not"""
    if not client:
        error_msg = "ANTHROPIC_API_KEY not configured. Please set ANTHROPIC_API_KEY in your .env file at the project root."
        if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "dummy":
            error_msg += " The API key was not found in environment variables."
        elif ANTHROPIC_API_KEY == "your_anthropic_api_key_here":
            error_msg += " The API key is still set to placeholder value."
        elif len(ANTHROPIC_API_KEY) <= 20:
            error_msg += f" The API key appears to be invalid (length: {len(ANTHROPIC_API_KEY)})."
        return False, error_msg
    return True, None


async def _call_claude(
    prompt: str,
    stream: bool = False,
    user_question: Optional[str] = None
) -> Any:
    """Call Claude API with question-focused system prompt"""
    if not client:
        raise HTTPException(
            status_code=500,
            detail="AI service is not available. Please contact support."
        )
    
    # Founder Context
    founder_context = """
Bạn đang chạy trong hệ thống RISKCAST v12.5.

Người tạo ra hệ thống này là Bùi Xuân Hoàng – Founder & AI-first Developer.

Triết lý của Bùi Xuân Hoàng: tốc độ, tối ưu, tạo giá trị thật, AI-first development.

Tầm nhìn RISKCAST: tạo ra nền tảng dự báo rủi ro logistics & ESG thông minh, 
ứng dụng mô hình FAHP, TOPSIS, VaR/CVaR, climate risk, và network resilience.

Sứ mệnh: đưa ra đánh giá rủi ro minh bạch, chính xác, giúp doanh nghiệp ra quyết định tốt hơn.

Nếu người dùng hỏi:
- "Ai tạo ra hệ thống này?" → trả lời rằng người tạo ra là Bùi Xuân Hoàng.
- "Founder là ai?" → mô tả đúng vai trò Founder AI-first developer (Bùi Xuân Hoàng).
- "Tầm nhìn dự án?" → trả lời theo tầm nhìn ở trên.
- "Sứ mệnh dự án?" → trả lời theo nội dung đã mô tả.
- "Bạn có biết owner của dự án không?" → trả lời Bùi Xuân Hoàng.

Không bao giờ bịa thêm thông tin.
"""
    
    # Build system instruction to focus on the question
    system_instruction = founder_context + """
You are RISKCAST Enterprise AI. Answer the user's question directly and specifically. Focus on providing relevant, actionable information that directly addresses what was asked. Use structured formats for clarity. Be concise - avoid unnecessary background unless directly relevant.

IMPORTANT: Always respond in Vietnamese (Tiếng Việt). All your responses must be in Vietnamese language."""
    
    try:
        from anthropic import APIError
        if stream:
            # For streaming, we'll handle it differently
            response = client.messages.stream(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                system=system_instruction,
                messages=[{"role": "user", "content": prompt}]
            )
            return response
        else:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                system=system_instruction,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
    except APIError as e:
        raise HTTPException(
            status_code=e.status_code if hasattr(e, 'status_code') else 500,
            detail=f"Anthropic API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Claude API error: {str(e)}"
        )


async def _stream_response(stream_manager) -> AsyncGenerator[str, None]:
    """Stream Claude response using MessageStreamManager"""
    import traceback
    import asyncio
    from queue import Queue, Empty
    try:
        from anthropic import APIError
        
        if not stream_manager:
            yield f"data: {json.dumps({'error': 'No response stream available'})}\n\n"
            return
        
        # MessageStreamManager uses synchronous context manager (with, not async with)
        # Use a queue to bridge sync iterator to async generator for real-time streaming
        queue = Queue()
        stream_state = {'done': False, 'error': None}
        
        def process_stream_sync():
            """Process stream synchronously and put chunks in queue"""
            try:
                from anthropic import APIError
                with stream_manager as stream:
                    # stream.text_stream is a synchronous iterator
                    for text_chunk in stream.text_stream:
                        if text_chunk:
                            queue.put(('chunk', text_chunk))
                    queue.put(('done', None))
                    stream_state['done'] = True
            except APIError as api_error:
                # Handle Anthropic API errors specifically
                error_detail = str(api_error)
                if hasattr(api_error, 'status_code') and api_error.status_code == 401:
                    error_detail = "Invalid API key. Please check your ANTHROPIC_API_KEY in .env file. Get a new key from https://console.anthropic.com/"
                elif "401" in error_detail or "authentication_error" in error_detail or "invalid x-api-key" in error_detail.lower():
                    error_detail = "Invalid API key. Please check your ANTHROPIC_API_KEY in .env file. Get a new key from https://console.anthropic.com/"
                stream_state['error'] = error_detail
                queue.put(('error', error_detail))
                stream_state['done'] = True
            except Exception as e:
                stream_state['error'] = str(e)
                queue.put(('error', str(e)))
                stream_state['done'] = True
        
        # Start stream processing in executor
        loop = asyncio.get_event_loop()
        executor_task = loop.run_in_executor(None, process_stream_sync)
        
        # Yield chunks as they arrive
        try:
            while not stream_state['done'] or not queue.empty():
                try:
                    # Try to get item from queue (non-blocking)
                    item_type, item_data = queue.get_nowait()
                    
                    if item_type == 'chunk':
                        yield f"data: {json.dumps({'text': item_data})}\n\n"
                    elif item_type == 'done':
                        yield "data: [DONE]\n\n"
                        break
                    elif item_type == 'error':
                        # Parse error to provide better message
                        error_data = item_data
                        if "401" in error_data or "authentication_error" in error_data or "invalid x-api-key" in error_data.lower():
                            error_data = "Invalid API key. Please check your ANTHROPIC_API_KEY in .env file. Get a new key from https://console.anthropic.com/"
                        raise Exception(error_data)
                        
                except Empty:
                    # Queue is empty, wait a bit and check again
                    await asyncio.sleep(0.05)
                    # Check if executor is done and queue is still empty
                    if executor_task.done() and queue.empty():
                        if stream_state['error']:
                            error_msg = stream_state['error']
                            # Improve error message for authentication errors
                            if "401" in error_msg or "authentication_error" in error_msg or "invalid x-api-key" in error_msg.lower():
                                error_msg = "Invalid API key. Please check your ANTHROPIC_API_KEY in .env file. Get a new key from https://console.anthropic.com/"
                            raise Exception(error_msg)
                        yield "data: [DONE]\n\n"
                        break
                    
        except Exception as stream_error:
            error_msg = str(stream_error)
            # Improve error message for authentication errors
            if "401" in error_msg or "authentication_error" in error_msg or "invalid x-api-key" in error_msg.lower() or "Invalid API key" in error_msg:
                error_msg = "Invalid API key. Please check your ANTHROPIC_API_KEY in .env file. Get a new key from https://console.anthropic.com/"
            else:
                error_msg = f'Stream processing error: {error_msg}'
            print(f"[ERROR] Error in stream processing: {error_msg}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
                
    except APIError as e:
        error_msg = f'Anthropic API error: {str(e)}'
        print(f"[ERROR] APIError in stream: {error_msg}")
        yield f"data: {json.dumps({'error': error_msg})}\n\n"
    except Exception as e:
        error_msg = f'Stream error: {str(e)}'
        print(f"[ERROR] Exception in stream: {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        yield f"data: {json.dumps({'error': error_msg})}\n\n"


# ==================== REQUEST MODELS ====================

class StreamRequest(BaseModel):
    prompt: str
    context: Optional[Dict] = None


# ==================== API ENDPOINTS ====================

@router.get("/health")
async def health():
    """Health check endpoint"""
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY in ("dummy", "your_anthropic_api_key_here"):
        return {
            "status": "error",
            "message": "ANTHROPIC_API_KEY not configured"
        }
    return {"status": "ok", "model": "claude-3-5-sonnet"}


@router.post("/stream")
async def stream(request: StreamRequest):
    """
    Streaming AI response endpoint (real-time)
    
    Input:
        prompt: User prompt
        context: Optional context data
    
    Output:
        Streaming text response
    """
    import traceback
    
    try:
        if not request.prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Check API key
        if not client:
            raise HTTPException(
                status_code=500,
                detail="ANTHROPIC_API_KEY not configured. Please set ANTHROPIC_API_KEY in your .env file."
            )
        if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY in ("your_anthropic_api_key_here", "dummy"):
            raise HTTPException(
                status_code=500,
                detail="ANTHROPIC_API_KEY is not set or is still a placeholder. Please set a valid API key in .env file."
            )
        
        # Extract and emphasize the user's question
        user_question = request.prompt.strip()
        
        # Build focused prompt that emphasizes the question
        focused_prompt = f"""USER QUESTION (ANSWER THIS DIRECTLY):
{user_question}

INSTRUCTIONS:
- Answer the question above directly and specifically
- Focus only on information relevant to answering this question
- If the question asks about specific data, use that data in your answer
- If the question is about analysis, provide focused analysis on what was asked
- Be concise but thorough in addressing the question
- Use structured format (JSON, bullets, or clear sections) for readability

"""
        
        # Add context if provided
        if request.context:
            focused_prompt += f"RELEVANT CONTEXT DATA:\n{json.dumps(request.context, indent=2)}\n\n"
        
        # Add base instructions
        focused_prompt += BASE_PROMPT
        
        full_prompt = focused_prompt
        
        try:
            # Verify client is initialized with valid API key
            if not client or not hasattr(client, 'api_key') or not client.api_key or ANTHROPIC_API_KEY in ("dummy", "your_anthropic_api_key_here"):
                raise HTTPException(
                    status_code=500,
                    detail="Anthropic client not properly initialized. Please check ANTHROPIC_API_KEY in .env file."
                )
            
            # Founder Context
            founder_context = """
Bạn đang chạy trong hệ thống RISKCAST v12.5.

Người tạo ra hệ thống này là Bùi Xuân Hoàng – Founder & AI-first Developer.

Triết lý của Bùi Xuân Hoàng: tốc độ, tối ưu, tạo giá trị thật, AI-first development.

Tầm nhìn RISKCAST: tạo ra nền tảng dự báo rủi ro logistics & ESG thông minh, 
ứng dụng mô hình FAHP, TOPSIS, VaR/CVaR, climate risk, và network resilience.

Sứ mệnh: đưa ra đánh giá rủi ro minh bạch, chính xác, giúp doanh nghiệp ra quyết định tốt hơn.

Nếu người dùng hỏi:
- "Ai tạo ra hệ thống này?" → trả lời rằng người tạo ra là Bùi Xuân Hoàng.
- "Founder là ai?" → mô tả đúng vai trò Founder AI-first developer (Bùi Xuân Hoàng).
- "Tầm nhìn dự án?" → trả lời theo tầm nhìn ở trên.
- "Sứ mệnh dự án?" → trả lời theo nội dung đã mô tả.
- "Bạn có biết owner của dự án không?" → trả lời Bùi Xuân Hoàng.

Không bao giờ bịa thêm thông tin.
"""
            
            # Create system instruction to emphasize question-focused behavior
            system_instruction = founder_context + """
You are RISKCAST Enterprise AI - a Logistics Risk Intelligence System.

CRITICAL: Your primary goal is to answer the user's question directly and specifically.

Response Guidelines:
1. **Answer the question first** - Address what was asked before providing additional context
2. **Be specific** - Use concrete data, numbers, and examples when available
3. **Stay relevant** - Only include information that directly relates to the question
4. **Structure clearly** - Use JSON, bullets, or clear sections for easy scanning
5. **Be concise** - Avoid unnecessary background unless essential for understanding

IMPORTANT: Always respond in Vietnamese (Tiếng Việt). All your responses must be in Vietnamese language.

If the question asks about specific data points, analysis, or recommendations, focus your entire response on that. Do not provide generic information that doesn't address the specific question."""
            
            # Create stream manager (returns MessageStreamManager, not directly iterable)
            stream_manager = client.messages.stream(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                system=system_instruction,
                messages=[{"role": "user", "content": full_prompt}]
            )
        except Exception as stream_error:
            from anthropic import APIError
            error_msg = str(stream_error)
            status_code = 500
            
            # Handle authentication errors specifically
            if isinstance(stream_error, APIError):
                if hasattr(stream_error, 'status_code'):
                    status_code = stream_error.status_code
                    if status_code == 401:
                        error_msg = "Invalid API key. Please check your ANTHROPIC_API_KEY in .env file. Get a new key from https://console.anthropic.com/"
                    else:
                        error_msg = f"Anthropic API error (status {status_code}): {error_msg}"
                else:
                    error_msg = f"Anthropic API error: {error_msg}"
            elif "401" in error_msg or "authentication_error" in error_msg or "invalid x-api-key" in error_msg.lower():
                status_code = 401
                error_msg = "Invalid API key. Please check your ANTHROPIC_API_KEY in .env file. Get a new key from https://console.anthropic.com/"
            else:
                error_msg = f"Failed to create stream: {error_msg}"
            
            # Log full error for debugging
            print(f"[ERROR] Stream creation failed: {error_msg}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            
            raise HTTPException(
                status_code=status_code,
                detail=error_msg
            )
        
        # Return streaming response
        # Pass stream_manager to _stream_response which will handle it with async context manager
        return StreamingResponse(
            _stream_response(stream_manager),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other unexpected errors
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] Unexpected error in /stream: {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        from anthropic import APIError
        if isinstance(e, APIError):
            raise HTTPException(
                status_code=e.status_code if hasattr(e, 'status_code') else 500,
                detail=f"Anthropic API error: {str(e)}"
            )
        
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@router.post("/analyze")
async def analyze(payload: dict):
    """
    AI Insights Panel - Main risk analysis
    
    Input:
        route, cargo, incoterm, carrier, season, political_risk, etc.
    
    Output:
        Main risks, top drivers, scenario analysis, recommendations
    """
    shipment_data = sanitize_input(payload.get("shipment_data", {}))
    
    # Validate
    is_valid, error = validate_shipment_data(shipment_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Calculate risk
    from app.core.engine.risk_engine_v16 import calculate_enterprise_risk
    risk_result = calculate_enterprise_risk(shipment_data)
    
    # Build prompt
    prompt = ANALYZE_PROMPT.format(
        shipment_data=json.dumps(shipment_data, indent=2),
        risk_analysis=json.dumps({
            "overall_risk": risk_result.get("overall_risk_index", 50),
            "risk_level": risk_result.get("risk_level", "Medium"),
            "expected_loss": risk_result.get("expected_loss", 0)
        }, indent=2)
    )
    
    # Get AI response
    ai_response = await _call_claude(prompt)
    
    # Save to memory
    shipment_id = memory_system.save_shipment(
        shipment_data,
        risk_result,
        generate_summary(shipment_data, risk_result)
    )
    
    return {
        "status": "success",
        "shipment_id": shipment_id,
        "insights": {
            "ai_analysis": ai_response,
            "overall_risk": risk_result.get("overall_risk_index", 50),
            "risk_level": risk_result.get("risk_level", "Medium"),
            "expected_loss": risk_result.get("expected_loss", 0),
            "reliability": risk_result.get("reliability_score", 50)
        },
        "summary": generate_summary(shipment_data, risk_result),
        "drivers": risk_result.get("risk_factors", {}),
        "scenarios": risk_result.get("scenario_analysis", {}),
        "actions": risk_result.get("recommendations", [])
    }


@router.post("/route")
async def route_recommendation(payload: dict):
    """
    AI-Recommended Route
    
    Input:
        shipment_data with route information
    
    Output:
        Best route recommendation with evidence
    """
    shipment_data = sanitize_input(payload.get("shipment_data", {}))
    
    # Calculate route risk
    route_risk = compute_route_risk(shipment_data)
    
    # Build prompt
    prompt = ROUTE_PROMPT.format(
        shipment_data=json.dumps(shipment_data, indent=2),
        route_risk=json.dumps(route_risk, indent=2)
    )
    
    # Get AI response
    ai_response = await _call_claude(prompt)
    
    return {
        "status": "success",
        "recommended_route": route_risk.get("recommended_mode", "sea"),
        "route_analysis": ai_response,
        "route_risk": route_risk,
        "evidence": {
            "weather_risk": route_risk.get("weather_risk", 50),
            "port_risk": route_risk.get("port_risk", 50),
            "reliability": route_risk.get("transport_reliability", 50)
        }
    }


@router.post("/insurance")
async def insurance_optimizer(payload: dict):
    """
    Risk-Based Insurance Optimizer
    
    Input:
        shipment_data, overall_risk
    
    Output:
        Insurance recommendation, coverage level, expected loss
    """
    shipment_data = sanitize_input(payload.get("shipment_data", {}))
    
    # Calculate overall risk
    overall_risk = compute_overall_risk(shipment_data)
    
    # Map to insurance
    insurance_mapping = map_risk_to_insurance(shipment_data, overall_risk)
    
    # Build prompt
    prompt = INSURANCE_PROMPT.format(
        shipment_data=json.dumps(shipment_data, indent=2),
        risk_analysis=json.dumps({"overall_risk": overall_risk}, indent=2),
        insurance_mapping=json.dumps(insurance_mapping, indent=2)
    )
    
    # Get AI response
    ai_response = await _call_claude(prompt)
    
    return {
        "status": "success",
        "recommendation": insurance_mapping.get("recommendation", "Optional"),
        "coverage_level": insurance_mapping.get("coverage_level", "Basic"),
        "expected_loss_usd": insurance_mapping.get("expected_loss_usd", 0),
        "reasoning": insurance_mapping.get("reasoning", ""),
        "ai_advisory": ai_response,
        "insurance_details": insurance_mapping
    }


@router.post("/delay")
async def delay_prediction(payload: dict):
    """
    Predictive Delay Analysis
    
    Input:
        shipment_data
    
    Output:
        Delay probability, main factors, prevention measures
    """
    shipment_data = sanitize_input(payload.get("shipment_data", {}))
    
    # Calculate delay probability
    delay_analysis = compute_delay_probability(shipment_data)
    
    # Build prompt
    prompt = DELAY_PROMPT.format(
        shipment_data=json.dumps(shipment_data, indent=2),
        delay_analysis=json.dumps(delay_analysis, indent=2)
    )
    
    # Get AI response
    ai_response = await _call_claude(prompt)
    
    return {
        "status": "success",
        "delay_probability_percent": delay_analysis.get("delay_probability_percent", 30),
        "expected_delay_days": delay_analysis.get("expected_delay_days", 2),
        "main_factors": delay_analysis.get("main_factors", []),
        "prevention_measures": delay_analysis.get("prevention_measures", []),
        "ai_analysis": ai_response,
        "reliability_score": delay_analysis.get("reliability_score", 50)
    }


@router.post("/esg")
async def esg_advisory(payload: dict):
    """
    Carbon + ESG Advisory
    
    Input:
        shipment_data
    
    Output:
        Carbon footprint, ESG score, reduction strategies
    """
    shipment_data = sanitize_input(payload.get("shipment_data", {}))
    
    # Calculate ESG score
    esg_analysis = compute_esg_score(shipment_data)
    
    # Build prompt
    prompt = ESG_PROMPT.format(
        shipment_data=json.dumps(shipment_data, indent=2),
        esg_analysis=json.dumps(esg_analysis, indent=2)
    )
    
    # Get AI response
    ai_response = await _call_claude(prompt)
    
    return {
        "status": "success",
        "esg_score": esg_analysis.get("esg_score", 50),
        "carbon_footprint_kg": esg_analysis.get("carbon_footprint_kg", 0),
        "green_score": esg_analysis.get("green_score", 50),
        "social_score": esg_analysis.get("social_score", 50),
        "governance_score": esg_analysis.get("governance_score", 50),
        "climate_impact": esg_analysis.get("climate_impact", ""),
        "ai_advisory": ai_response,
        "esg_details": esg_analysis
    }


@router.post("/history")
async def history_comparison(payload: dict):
    """
    Mini AI Memory - Compare shipments
    
    Input:
        shipment_id_1, shipment_id_2 (optional)
    
    Output:
        Comparison analysis, historical trend
    """
    shipment_id_1 = payload.get("shipment_id_1")
    shipment_id_2 = payload.get("shipment_id_2")
    
    if shipment_id_1 and shipment_id_2:
        # Compare two specific shipments
        comparison = memory_system.compare_shipments(shipment_id_1, shipment_id_2)
        
        if comparison.get("status") == "error":
            raise HTTPException(status_code=404, detail=comparison.get("error"))
        
        # Build prompt
        prompt = HISTORY_PROMPT.format(
            shipment_1=json.dumps(comparison.get("shipment_1", {}), indent=2),
            shipment_2=json.dumps(comparison.get("shipment_2", {}), indent=2),
            comparison=json.dumps(comparison.get("comparison", {}), indent=2)
        )
        
        # Get AI response
        ai_response = await _call_claude(prompt)
        
        return {
            "status": "success",
            "comparison": comparison,
            "ai_analysis": ai_response
        }
    else:
        # Get historical trend
        limit = payload.get("limit", 5)
        trend = memory_system.get_historical_trend(limit)
        
        return {
            "status": "success",
            "trend": trend,
            "recent_shipments": memory_system.get_all_shipments(limit)
        }


class PromptData(BaseModel):
    prompt: str


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict] = None


@router.post("/chat")
async def ai_chat(request: ChatRequest):
    """
    AI Chat endpoint - General chat with Founder context
    
    Input:
        message: User message
        context: Optional context data
    
    Output:
        AI response with Founder context awareness
    """
    try:
        from anthropic import APIError
        
        # Check API key configuration
        is_configured, error_msg = _check_api_key_configured()
        if not is_configured:
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Founder Context
        founder_context = """
Bạn đang chạy trong hệ thống RISKCAST v12.5.

Người tạo ra hệ thống này là Bùi Xuân Hoàng – Founder & AI-first Developer.

Triết lý của Bùi Xuân Hoàng: tốc độ, tối ưu, tạo giá trị thật, AI-first development.

Tầm nhìn RISKCAST: tạo ra nền tảng dự báo rủi ro logistics & ESG thông minh, 
ứng dụng mô hình FAHP, TOPSIS, VaR/CVaR, climate risk, và network resilience.

Sứ mệnh: đưa ra đánh giá rủi ro minh bạch, chính xác, giúp doanh nghiệp ra quyết định tốt hơn.

Nếu người dùng hỏi:
- "Ai tạo ra hệ thống này?" → trả lời rằng người tạo ra là Bùi Xuân Hoàng....
- "Founder là ai?" → mô tả đúng vai trò Founder AI-first developer (Bùi Xuân Hoàng).
- "Tầm nhìn dự án?" → trả lời theo tầm nhìn ở trên.
- "Sứ mệnh dự án?" → trả lời theo nội dung đã mô tả.
- "Bạn có biết owner của dự án không?" → trả lời Bùi Xuân Hoàng.

Không bao giờ bịa thêm thông tin.
"""
        
        # Build system prompt with Founder context
        system_prompt = founder_context + """
Bạn là AI Assistant của hệ thống RISKCAST. Hãy trả lời đúng bối cảnh và dữ liệu người dùng cung cấp.

IMPORTANT: Always respond in Vietnamese (Tiếng Việt). All your responses must be in Vietnamese language.
"""
        
        # Build user message
        user_message = request.message.strip()
        
        # Add context if provided
        if request.context:
            context_str = json.dumps(request.context, indent=2, ensure_ascii=False)
            user_message = f"{user_message}\n\nCONTEXT:\n{context_str}"
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        
        reply = response.content[0].text
        return {"reply": reply}
    except APIError as e:
        raise HTTPException(
            status_code=e.status_code if hasattr(e, 'status_code') else 500,
            detail=f"Anthropic API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adviser")
async def ai_adviser(data: PromptData):
    """
    AI Adviser endpoint - Simple prompt/response with question focus
    
    Input:
        prompt: User prompt
    
    Output:
        AI response focused on the question
    """
    try:
        from anthropic import APIError
        
        # Check API key configuration
        is_configured, error_msg = _check_api_key_configured()
        if not is_configured:
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Founder Context
        founder_context = """
Bạn đang chạy trong hệ thống RISKCAST v12.5.

Người tạo ra hệ thống này là Bùi Xuân Hoàng – Founder & AI-first Developer.

Triết lý của Bùi Xuân Hoàng: tốc độ, tối ưu, tạo giá trị thật, AI-first development.

Tầm nhìn RISKCAST: tạo ra nền tảng dự báo rủi ro logistics & ESG thông minh, 
ứng dụng mô hình FAHP, TOPSIS, VaR/CVaR, climate risk, và network resilience.

Sứ mệnh: đưa ra đánh giá rủi ro minh bạch, chính xác, giúp doanh nghiệp ra quyết định tốt hơn.

Nếu người dùng hỏi:
- "Ai tạo ra hệ thống này?" → trả lời rằng người tạo ra là Bùi Xuân Hoàng.
- "Founder là ai?" → mô tả đúng vai trò Founder AI-first developer (Bùi Xuân Hoàng).
- "Tầm nhìn dự án?" → trả lời theo tầm nhìn ở trên.
- "Sứ mệnh dự án?" → trả lời theo nội dung đã mô tả.
- "Bạn có biết owner của dự án không?" → trả lời Bùi Xuân Hoàng.

Không bao giờ bịa thêm thông tin.
"""
        
        # Build focused prompt
        user_question = data.prompt.strip()
        focused_prompt = f"""QUESTION: {user_question}

Please answer this question directly and specifically. Focus on providing relevant information that directly addresses what was asked."""
        
        system_instruction = founder_context + """
You are RISKCAST Enterprise AI. Answer the user's question directly and specifically. Focus on providing relevant, actionable information. Be concise and structured. Do not provide generic information that doesn't address the specific question.

IMPORTANT: Always respond in Vietnamese (Tiếng Việt). All your responses must be in Vietnamese language."""
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            system=system_instruction,
            messages=[{"role": "user", "content": focused_prompt}]
        )
        
        reply = response.content[0].text
        return {"reply": reply}
    except APIError as e:
        raise HTTPException(
            status_code=e.status_code if hasattr(e, 'status_code') else 500,
            detail=f"Anthropic API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
