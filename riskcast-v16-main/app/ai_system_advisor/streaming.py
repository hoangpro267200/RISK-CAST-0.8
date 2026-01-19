"""
Streaming responses for AI advisor.

RISKCAST v17 - Real-time AI Streaming

Uses Server-Sent Events (SSE) for real-time response streaming.
This provides a better UX as users see responses appearing in real-time
rather than waiting for the complete response.
"""

import json
import os
from typing import AsyncGenerator, Optional, List, Dict, Any
from datetime import datetime

# Try to import anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


class StreamingAdvisor:
    """
    AI advisor with streaming responses.
    
    Uses Server-Sent Events (SSE) format for real-time streaming.
    
    Usage:
        advisor = StreamingAdvisor()
        
        async for chunk in advisor.stream_response(messages, system):
            # chunk is SSE formatted: "data: {...}\n\n"
            yield chunk
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize streaming advisor.
        
        Args:
            api_key: Anthropic API key. If not provided, uses
                    ANTHROPIC_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        
        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                print(f"[StreamingAdvisor] Error initializing client: {e}")
    
    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        system_context: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI response as Server-Sent Events.
        
        Args:
            messages: Conversation history
            system_context: System prompt
            model: Claude model to use
            max_tokens: Maximum response tokens
        
        Yields:
            SSE formatted chunks: "data: {json}\n\n"
            
            Chunk types:
            - {"type": "text", "content": "..."}  - Text chunk
            - {"type": "done"}                    - Stream complete
            - {"type": "error", "error": "..."}   - Error occurred
        """
        if not self.client:
            error_chunk = {
                'type': 'error',
                'error': 'AI service not available. Check ANTHROPIC_API_KEY.'
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            return
        
        try:
            # Create streaming request
            with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                system=system_context,
                messages=messages
            ) as stream:
                # Stream text chunks
                for text in stream.text_stream:
                    chunk = {
                        'type': 'text',
                        'content': text
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except anthropic.APIConnectionError:
            error_chunk = {
                'type': 'error',
                'error': 'Connection error. Please try again.'
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            
        except anthropic.RateLimitError:
            error_chunk = {
                'type': 'error',
                'error': 'Rate limit exceeded. Please wait a moment.'
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            
        except anthropic.APIStatusError as e:
            error_chunk = {
                'type': 'error',
                'error': f'API error: {e.message}'
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            
        except Exception as e:
            error_chunk = {
                'type': 'error',
                'error': str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    async def stream_with_context(
        self,
        message: str,
        conversation_id: str,
        risk_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream response with full context management.
        
        Automatically:
        - Retrieves conversation history
        - Injects risk data context
        - Saves messages to database
        
        Args:
            message: User message
            conversation_id: Conversation ID for history
            risk_data: Optional risk assessment to include
        
        Yields:
            SSE formatted chunks
        """
        from app.ai_system_advisor.i18n import get_system_prompt, detect_language
        
        # Detect language
        language = detect_language(message)
        
        # Get system prompt
        system_context = get_system_prompt(language)
        
        # Add risk data context if available
        if risk_data:
            risk_context = f"""

Current Risk Assessment Data:
- Risk Score: {risk_data.get('risk_score', 'N/A')}
- Risk Level: {risk_data.get('risk_level', 'N/A')}
- VaR 95%: ${risk_data.get('var_95', 0):,.2f}
- Expected Loss: ${risk_data.get('expected_loss', 0):,.2f}

Key Risk Factors:
{self._format_risk_factors(risk_data.get('risk_factors', []))}

Use this data to provide specific, actionable recommendations.
"""
            system_context += risk_context
        
        # Get conversation history (mock - implement with DB)
        messages = await self._get_conversation_history(conversation_id)
        messages.append({'role': 'user', 'content': message})
        
        # Collect full response for saving
        full_response = ""
        
        async for chunk in self.stream_response(messages, system_context):
            # Parse chunk to collect response
            try:
                data = json.loads(chunk.replace('data: ', '').strip())
                if data.get('type') == 'text':
                    full_response += data.get('content', '')
            except Exception:
                pass
            
            yield chunk
        
        # Save messages to database (async)
        await self._save_messages(conversation_id, message, full_response)
    
    def _format_risk_factors(self, factors: List[Dict]) -> str:
        """Format risk factors for context."""
        if not factors:
            return "No specific risk factors identified."
        
        lines = []
        for factor in factors[:5]:  # Top 5 factors
            name = factor.get('name', 'Unknown')
            score = factor.get('score', 0)
            lines.append(f"  - {name}: {score}/100")
        
        return '\n'.join(lines)
    
    async def _get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation history from database.
        
        Returns last N messages in conversation.
        """
        try:
            from app.database import get_db
            from app.database.queries import ConversationQueries
            
            db = next(get_db())
            messages = ConversationQueries.get_conversation_history(
                db, conversation_id, limit
            )
            
            return [
                {'role': msg.role, 'content': msg.content}
                for msg in messages
            ]
        except Exception as e:
            print(f"[StreamingAdvisor] Error getting history: {e}")
            return []
    
    async def _save_messages(
        self,
        conversation_id: str,
        user_message: str,
        assistant_response: str
    ):
        """Save messages to database."""
        try:
            from app.database import get_db
            from app.models.conversation import Conversation, ConversationMessage
            
            db = next(get_db())
            
            # Get or create conversation
            conv = db.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            
            if not conv:
                conv = Conversation(
                    conversation_id=conversation_id,
                    title=user_message[:50] + "..." if len(user_message) > 50 else user_message
                )
                db.add(conv)
            
            # Add messages
            db.add(ConversationMessage(
                conversation_id=conversation_id,
                role='user',
                content=user_message
            ))
            
            db.add(ConversationMessage(
                conversation_id=conversation_id,
                role='assistant',
                content=assistant_response
            ))
            
            conv.updated_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            print(f"[StreamingAdvisor] Error saving messages: {e}")


# ============================================================
# NON-STREAMING FALLBACK
# ============================================================

class FallbackAdvisor:
    """
    Fallback advisor when streaming is not available.
    
    Returns complete response instead of streaming.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        
        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception:
                pass
    
    def get_response(
        self,
        messages: List[Dict[str, str]],
        system_context: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Get complete AI response (non-streaming).
        
        Returns:
            {
                'success': True/False,
                'content': 'response text',
                'error': 'error message if failed'
            }
        """
        if not self.client:
            return {
                'success': False,
                'content': '',
                'error': 'AI service not available'
            }
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_context,
                messages=messages
            )
            
            return {
                'success': True,
                'content': response.content[0].text,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'content': '',
                'error': str(e)
            }


# ============================================================
# FASTAPI INTEGRATION
# ============================================================

async def create_streaming_endpoint():
    """
    Example FastAPI endpoint for streaming.
    
    Usage in routes:
        from fastapi import APIRouter
        from fastapi.responses import StreamingResponse
        from app.ai_system_advisor.streaming import StreamingAdvisor
        
        router = APIRouter()
        
        @router.post("/ai/advisor/chat/stream")
        async def stream_chat(request: ChatRequest):
            advisor = StreamingAdvisor()
            
            return StreamingResponse(
                advisor.stream_with_context(
                    request.message,
                    request.conversation_id,
                    request.risk_data
                ),
                media_type="text/event-stream"
            )
    """
    pass  # Implementation example in docstring
