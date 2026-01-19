"""
AI System Advisor - Core Reasoning Engine
Main orchestrator for AI advisor
"""

import os
from typing import Dict, List, Optional, Any
from anthropic import Anthropic

from app.ai_system_advisor.context_manager import ContextManager
from app.ai_system_advisor.data_access import DataAccess
from app.ai_system_advisor.action_handlers import ActionHandlers
from app.ai_system_advisor.function_registry import FunctionRegistry
from app.ai_system_advisor.prompt_templates import PromptTemplates
from app.ai_system_advisor.types import AdvisorResponse, FunctionCall, FunctionResult


class AdvisorCore:
    """Main AI advisor reasoning engine"""
    
    def __init__(self):
        """Initialize advisor core"""
        # Initialize Claude client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and api_key != "your_anthropic_api_key_here" and len(api_key) > 20:
            try:
                self.anthropic_client = Anthropic(api_key=api_key)
                self.use_llm = True
            except Exception as e:
                print(f"[AdvisorCore] Failed to initialize Claude client: {e}")
                self.anthropic_client = None
                self.use_llm = False
        else:
            self.anthropic_client = None
            self.use_llm = False
        
        # Initialize modules
        self.context_manager = ContextManager()
        self.data_access = DataAccess()
        self.action_handlers = ActionHandlers()
        self.function_registry = FunctionRegistry()
        self.prompt_templates = PromptTemplates()
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> AdvisorResponse:
        """
        Process user message and generate response
        
        Args:
            message: User message
            session_id: Session identifier
            context: Optional page context
            language: Response language
            
        Returns:
            AdvisorResponse object
        """
        try:
            # 1. Load conversation history
            history = await self.context_manager.get_conversation_history(session_id, limit=20)
            
            # 2. Load system context
            system_context_obj = self.data_access.get_system_context(session_id, context)
            system_context_str = self.data_access.format_context_for_prompt(system_context_obj)
            
            # 3. Get available functions
            available_functions = self.function_registry.get_available_functions()
            
            # 4. Build system prompt
            system_prompt = self.prompt_templates.build_system_prompt(
                system_context=system_context_str,
                available_functions=available_functions,
                conversation_history=history,
                language=language
            )
            
            # 5. Call LLM
            print(f"[AdvisorCore] Checking LLM availability: use_llm={self.use_llm}, client={self.anthropic_client is not None}")
            if self.use_llm and self.anthropic_client:
                print(f"[AdvisorCore] Calling Claude API...")
                try:
                    llm_response = await self._call_llm(
                        messages=history + [{"role": "user", "content": message}],
                        system=system_prompt,
                        functions=available_functions
                    )
                    print(f"[AdvisorCore] Claude API response received (model: {llm_response.get('model', 'unknown')})")
                except Exception as e:
                    print(f"[AdvisorCore] Error calling Claude: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to deterministic
                    llm_response = await self._generate_deterministic_response(
                        message, system_context_obj, history, language
                    )
            else:
                print(f"[AdvisorCore] Using deterministic fallback (use_llm={self.use_llm}, client={self.anthropic_client is not None})")
                # Fallback: deterministic response
                llm_response = await self._generate_deterministic_response(
                    message, system_context_obj, history, language
                )
            
            # 6. Parse function calls
            function_results = []
            if llm_response.get("function_calls"):
                for func_call in llm_response["function_calls"]:
                    result = await self.action_handlers.execute_function(
                        function_name=func_call["name"],
                        function_args=func_call.get("arguments", {}),
                        session_id=session_id
                    )
                    function_results.append(FunctionResult(
                        function_name=func_call["name"],
                        success=result.get("success", False),
                        result=result,
                        error=result.get("error")
                    ))
            
            # 7. Save to history
            await self.context_manager.save_message(session_id, "user", message, metadata=context)
            await self.context_manager.save_message(
                session_id,
                "assistant",
                llm_response["content"],
                metadata={"function_calls": len(function_results)}
            )
            
            # 8. Generate action suggestions
            actions = self._generate_action_suggestions(llm_response, function_results, system_context_obj)
            
            return AdvisorResponse(
                reply=llm_response["content"],
                session_id=session_id,
                actions=actions,
                function_calls=function_results,
                metadata={
                    "tokens_used": llm_response.get("tokens_used", 0),
                    "response_time_ms": llm_response.get("response_time_ms", 0),
                    "model": llm_response.get("model", "deterministic"),
                    "confidence": 0.9 if self.use_llm else 0.7
                }
            )
        except Exception as e:
            print(f"[AdvisorCore] Error processing message: {e}")
            import traceback
            traceback.print_exc()
            
            # Return error response
            return AdvisorResponse(
                reply=f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again.",
                session_id=session_id,
                actions=[],
                function_calls=[],
                metadata={"error": str(e)}
            )
    
    async def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        functions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Call Claude API
        
        Args:
            messages: Conversation messages
            system: System prompt
            functions: Available functions
            
        Returns:
            LLM response dictionary
        """
        import time
        start_time = time.time()
        
        try:
            # Convert functions to Claude format
            tools = []
            for func in functions:
                tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                })
            
            # Call Claude with fallback models
            # Try models in order of preference
            models_to_try = [
                "claude-sonnet-4-20250514",  # Current recommended model
                "claude-3-5-sonnet-20241022",  # Fallback if Sonnet 4 not available
                "claude-3-opus-20240229",     # Fallback option
            ]
            
            response = None
            last_error = None
            model_used = None
            
            for model_name in models_to_try:
                try:
                    response = self.anthropic_client.messages.create(
                        model=model_name,
                        max_tokens=4096,
                        system=system,
                        messages=messages,
                        tools=tools if tools else None
                    )
                    model_used = model_name
                    break  # Success, exit loop
                except Exception as model_error:
                    last_error = model_error
                    error_str = str(model_error).lower()
                    # If it's a 404 (model not found), try next model
                    if "404" in error_str or "not_found" in error_str:
                        print(f"[AdvisorCore] Model {model_name} not available, trying next...")
                        continue
                    else:
                        # Other error (auth, etc.) - don't try other models
                        raise
            
            if response is None:
                raise last_error or Exception("All models failed")
            
            # Parse response
            content = ""
            function_calls = []
            
            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    function_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "arguments": block.input
                    })
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "content": content,
                "function_calls": function_calls,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "response_time_ms": response_time,
                "model": model_used or "claude-sonnet-4-20250514"
            }
        except Exception as e:
            print(f"[AdvisorCore] Claude API error: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if it's a model error (404, 401, 500, etc.)
            error_str = str(e).lower()
            is_model_error = any(keyword in error_str for keyword in [
                "not_found", "404", "unauthorized", "401", 
                "forbidden", "403", "model", "not available"
            ])
            
            # If model error, disable LLM for future calls
            if is_model_error:
                print(f"[AdvisorCore] Model error detected - disabling LLM")
                self.use_llm = False
            
            # Fallback to deterministic - need to get language from context if available
            # Try to extract from system prompt or use default
            language = "vi"  # Default to Vietnamese for this system
            return await self._generate_deterministic_response(
                messages[-1].get("content", ""),
                None,
                messages[:-1],
                language
            )
    
    async def _generate_deterministic_response(
        self,
        message: str,
        system_context: Optional[Any],
        history: List[Dict[str, Any]],
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Generate deterministic response (fallback when LLM unavailable)
        
        Args:
            message: User message
            system_context: System context
            history: Conversation history
            language: Response language (default: Vietnamese)
            
        Returns:
            Response dictionary
        """
        message_lower = message.lower()
        is_vietnamese = language.lower() in ["vi", "vietnamese", "vn"] or any(
            char in message for char in "ăâêôơưđ"
        )
        
        # Vietnamese keywords
        if is_vietnamese:
            # Pattern: "Nhận đề xuất giảm thiểu rủi ro?" / "đề xuất" / "giảm thiểu"
            if any(keyword in message_lower for keyword in [
                "đề xuất", "giảm thiểu", "nhận đề xuất", "biện pháp", 
                "khuyến nghị", "đề nghị", "recommend"
            ]):
                return {
                    "content": "Tôi có thể cung cấp các đề xuất giảm thiểu rủi ro. Hãy để tôi phân tích đánh giá hiện tại và tạo các khuyến nghị cho bạn.",
                    "function_calls": [{
                        "name": "get_recommendations",
                        "arguments": {}
                    }]
                }
            
            # Pattern: "rủi ro đơn hàng này như thế nào" / "rủi ro" / "đánh giá rủi ro"
            if any(keyword in message_lower for keyword in [
                "rủi ro", "đánh giá", "như thế nào", "như nào", "thế nào",
                "risk", "assessment", "đơn hàng"
            ]):
                if system_context and system_context.current_assessment:
                    assessment = system_context.current_assessment
                    risk_score = assessment.get('risk_score', 0)
                    drivers = assessment.get('drivers', [])
                    
                    response = f"**Đánh giá Rủi ro cho Đơn hàng:**\n\n"
                    response += f"Điểm rủi ro tổng thể: {risk_score:.1f}/100\n\n"
                    
                    if drivers:
                        response += "**Các yếu tố rủi ro chính:**\n"
                        for i, driver in enumerate(drivers[:5], 1):
                            name = driver.get('name', 'Không xác định')
                            impact = driver.get('impact', 0)
                            response += f"{i}. {name}: {impact:.1f}% ảnh hưởng\n"
                    else:
                        response += "Hiện tại chưa có dữ liệu về các yếu tố rủi ro cụ thể.\n"
                    
                    return {"content": response, "function_calls": []}
                else:
                    return {
                        "content": "Để phân tích rủi ro chi tiết, vui lòng cung cấp thông tin về đơn hàng hoặc đảm bảo có dữ liệu đánh giá trong hệ thống.",
                        "function_calls": []
                    }
            
            # Pattern: "xuất báo cáo" / "export" / "pdf"
            if any(keyword in message_lower for keyword in [
                "xuất", "export", "pdf", "báo cáo", "file"
            ]):
                return {
                    "content": "Tôi có thể giúp bạn xuất báo cáo PDF. Bạn có muốn tôi tạo một báo cáo không?",
                    "function_calls": [{
                        "name": "export_pdf",
                        "arguments": {"format": "standard"}
                    }]
                }
            
            # Pattern: "tóm tắt" / "summary"
            if any(keyword in message_lower for keyword in [
                "tóm tắt", "summary", "tổng quan"
            ]):
                return {
                    "content": "Tôi có thể tạo tóm tắt điều hành. Bạn muốn tóm tắt ngắn, vừa hay dài?",
                    "function_calls": []
                }
            
            # Default Vietnamese response
            return {
                "content": "Tôi hiểu câu hỏi của bạn. Tuy nhiên, hiện tại tôi đang hoạt động ở chế độ hạn chế. Để có đầy đủ khả năng AI, vui lòng đảm bảo API key Claude đã được cấu hình đúng. Tôi vẫn có thể giúp trả lời các câu hỏi cơ bản về đánh giá rủi ro.",
                "function_calls": []
            }
        
        # English patterns (fallback)
        if "risk" in message_lower and ("driver" in message_lower or "factor" in message_lower):
            if system_context and system_context.current_assessment:
                drivers = system_context.current_assessment.get('drivers', [])
                if drivers:
                    response = "The top risk drivers are:\n\n"
                    for i, driver in enumerate(drivers[:3], 1):
                        response += f"{i}. {driver.get('name', 'Unknown')}: {driver.get('impact', 0):.1f}% impact\n"
                    return {"content": response, "function_calls": []}
        
        if "export" in message_lower or "pdf" in message_lower:
            return {
                "content": "I can help you export a PDF report. Would you like me to generate one?",
                "function_calls": []
            }
        
        if "recommend" in message_lower or "suggestion" in message_lower:
            return {
                "content": "I can provide risk mitigation recommendations. Let me analyze the current assessment and generate recommendations for you.",
                "function_calls": [{
                    "name": "get_recommendations",
                    "arguments": {}
                }]
            }
        
        # Default English response
        return {
            "content": "I understand your question. However, I'm currently operating in a limited mode. For full AI capabilities, please ensure the Claude API key is configured. I can still help with basic questions about the risk assessment.",
            "function_calls": []
        }
    
    def _generate_action_suggestions(
        self,
        llm_response: Dict[str, Any],
        function_results: List[FunctionResult],
        system_context: Any
    ) -> List[Dict[str, Any]]:
        """
        Generate action suggestions based on response
        
        Args:
            llm_response: LLM response
            function_results: Function execution results
            system_context: System context
            
        Returns:
            List of action suggestions
        """
        actions = []
        
        # If export was mentioned but not executed
        content_lower = llm_response.get("content", "").lower()
        if ("export" in content_lower or "pdf" in content_lower) and not any(
            f.function_name == "export_pdf" for f in function_results
        ):
            actions.append({
                "type": "suggestion",
                "action": "export_pdf",
                "label": "Export PDF Report",
                "description": "Generate PDF report with full risk analysis"
            })
        
        # If recommendations were mentioned
        if "recommend" in content_lower and not any(
            f.function_name == "get_recommendations" for f in function_results
        ):
            actions.append({
                "type": "suggestion",
                "action": "get_recommendations",
                "label": "View Recommendations",
                "description": "See mitigation strategies"
            })
        
        # If comparison was mentioned
        if "compare" in content_lower:
            actions.append({
                "type": "suggestion",
                "action": "compare_shipments",
                "label": "Compare Shipments",
                "description": "Compare multiple shipments"
            })
        
        return actions
