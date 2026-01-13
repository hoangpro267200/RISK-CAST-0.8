"""
AI System Advisor - Prompt Templates
System prompts and context formatting
"""

from typing import Dict, List, Any, Optional


class PromptTemplates:
    """System prompt templates for AI advisor"""
    
    BASE_SYSTEM_PROMPT = """You are RISKCAST AI System Advisor, an intelligent risk intelligence assistant for logistics and supply chain risk management.

SYSTEM CAPABILITIES:
- Analyze risk assessments and provide insights
- Generate executive summaries
- Provide mitigation recommendations
- Compare shipments
- Export reports (PDF/Excel)
- Run what-if scenarios
- Explain risk drivers and metrics
- Answer questions about risk analysis

RESPONSE GUIDELINES:
1. Be concise and actionable
2. Use specific numbers and metrics when available
3. Provide data-driven insights
4. Explain technical concepts clearly
5. Suggest relevant actions when appropriate
6. Use structured format when helpful (lists, tables)
7. LANGUAGE: {language_instruction}

FUNCTION CALLING:
- Use function calling when user requests actions (export, compare, scenario, etc.)
- Always confirm action execution to user
- Provide download links or results after function execution

CURRENT CONTEXT:
{system_context}

AVAILABLE FUNCTIONS:
{available_functions}

CONVERSATION HISTORY:
{conversation_history}

Remember: You are a professional risk intelligence advisor. Provide expert-level insights that help users make informed decisions."""

    CONTEXT_TEMPLATE = """CURRENT SYSTEM CONTEXT:

{context_details}

Available Actions: {available_actions}
"""

    FUNCTION_DESCRIPTION_TEMPLATE = """Available Functions:
{functions_list}

Use these functions when user requests:
- Export: Use export_pdf or export_excel
- Comparison: Use compare_shipments
- Scenarios: Use run_scenario
- Recommendations: Use get_recommendations
- Summaries: Use get_summary
- Financial Analysis: Use get_financial_metrics
- Historical Trends: Use get_historical_trend"""

    @staticmethod
    def build_system_prompt(
        system_context: str,
        available_functions: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]],
        language: str = "en"
    ) -> str:
        """
        Build complete system prompt
        
        Args:
            system_context: Formatted system context
            available_functions: List of available functions
            conversation_history: Conversation history
            language: Response language
            
        Returns:
            Complete system prompt
        """
        # Format functions list
        functions_list = "\n".join([
            f"- {func['name']}: {func['description']}"
            for func in available_functions
        ])
        
        # Format conversation history
        history_text = ""
        if conversation_history:
            history_text = "Recent conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')[:200]  # Truncate long messages
                history_text += f"{role.capitalize()}: {content}\n"
        
        # Language instruction
        if language.lower() in ["vi", "vietnamese", "vn"]:
            language_instruction = "CRITICAL: Always respond in Vietnamese (Tiếng Việt). All your responses must be in Vietnamese language. Use Vietnamese terminology and formatting."
        else:
            language_instruction = f"Always respond in {language} language."
        
        return PromptTemplates.BASE_SYSTEM_PROMPT.format(
            language_instruction=language_instruction,
            system_context=system_context,
            available_functions=functions_list,
            conversation_history=history_text
        )
    
    @staticmethod
    def format_context_for_prompt(context_details: str, available_actions: List[str]) -> str:
        """
        Format context for prompt
        
        Args:
            context_details: Context details string
            available_actions: List of available actions
            
        Returns:
            Formatted context string
        """
        return PromptTemplates.CONTEXT_TEMPLATE.format(
            context_details=context_details,
            available_actions=", ".join(available_actions)
        )
