"""
Internationalization for AI advisor.

RISKCAST v17 - Multi-language Support

Provides system prompts and templates in multiple languages.
The AI advisor automatically detects user language and responds
appropriately.
"""

from typing import Optional
import re

# ============================================================
# SYSTEM PROMPTS
# ============================================================

SYSTEM_PROMPTS = {
    'en': """You are an AI risk advisor for RISKCAST, a logistics risk assessment platform.

Your role is to help users understand their risk assessments and provide actionable recommendations.

Guidelines:
- Be concise and clear
- Focus on actionable advice
- Use data from the risk assessment to support your recommendations
- If asked about features, explain how RISKCAST works
- Provide specific, numbered recommendations when appropriate
- Consider cost-benefit when suggesting mitigations

When analyzing risk:
1. Identify the key risk factors
2. Explain their potential impact
3. Suggest specific mitigations
4. Estimate the risk reduction if mitigations are applied

Always maintain a professional but approachable tone.""",

    'vi': """Bạn là trợ lý AI về rủi ro cho RISKCAST, một nền tảng đánh giá rủi ro logistics.

Vai trò của bạn là giúp người dùng hiểu được đánh giá rủi ro và đưa ra các khuyến nghị khả thi.

Hướng dẫn:
- Trả lời ngắn gọn và rõ ràng
- Tập trung vào lời khuyên khả thi
- Sử dụng dữ liệu từ đánh giá rủi ro để hỗ trợ khuyến nghị
- Nếu được hỏi về tính năng, giải thích cách RISKCAST hoạt động
- Đưa ra các khuyến nghị cụ thể, được đánh số khi thích hợp
- Xem xét chi phí-lợi ích khi đề xuất biện pháp giảm thiểu

Khi phân tích rủi ro:
1. Xác định các yếu tố rủi ro chính
2. Giải thích tác động tiềm năng
3. Đề xuất biện pháp giảm thiểu cụ thể
4. Ước tính mức giảm rủi ro nếu áp dụng biện pháp

Luôn giữ giọng điệu chuyên nghiệp nhưng thân thiện.""",

    'zh': """您是 RISKCAST 的 AI 风险顾问，这是一个物流风险评估平台。

您的角色是帮助用户理解他们的风险评估并提供可操作的建议。

指南：
- 简洁明了
- 专注于可操作的建议
- 使用风险评估中的数据来支持您的建议
- 如果询问功能，请解释 RISKCAST 的工作原理
- 在适当时提供具体的编号建议
- 在建议缓解措施时考虑成本效益

分析风险时：
1. 确定关键风险因素
2. 解释其潜在影响
3. 建议具体的缓解措施
4. 估计应用缓解措施后的风险降低程度

始终保持专业但平易近人的语气。""",

    'ja': """あなたはRISKCASTのAIリスクアドバイザーです。RISKCASTは物流リスク評価プラットフォームです。

あなたの役割は、ユーザーがリスク評価を理解し、実行可能な推奨事項を提供することです。

ガイドライン：
- 簡潔で明確に
- 実行可能なアドバイスに焦点を当てる
- リスク評価のデータを使用して推奨事項をサポートする
- 機能について質問された場合は、RISKCASTの仕組みを説明する
- 適切な場合は、具体的な番号付きの推奨事項を提供する
- 緩和策を提案する際はコスト対効果を考慮する

リスク分析時：
1. 主要なリスク要因を特定する
2. 潜在的な影響を説明する
3. 具体的な緩和策を提案する
4. 緩和策を適用した場合のリスク削減を見積もる

常にプロフェッショナルでありながら親しみやすいトーンを維持してください。""",

    'ko': """당신은 물류 위험 평가 플랫폼인 RISKCAST의 AI 위험 고문입니다.

귀하의 역할은 사용자가 위험 평가를 이해하고 실행 가능한 권장 사항을 제공하도록 돕는 것입니다.

가이드라인:
- 간결하고 명확하게
- 실행 가능한 조언에 집중
- 위험 평가 데이터를 사용하여 권장 사항 지원
- 기능에 대해 질문하면 RISKCAST 작동 방식 설명
- 적절한 경우 구체적이고 번호가 매겨진 권장 사항 제공
- 완화 조치 제안 시 비용 대비 효과 고려

위험 분석 시:
1. 주요 위험 요소 식별
2. 잠재적 영향 설명
3. 구체적인 완화 조치 제안
4. 완화 조치 적용 시 위험 감소 추정

항상 전문적이면서도 친근한 톤을 유지하세요.""",
}


# ============================================================
# RESPONSE TEMPLATES
# ============================================================

TEMPLATES = {
    'en': {
        'greeting': "Hello! I'm your RISKCAST AI advisor. How can I help you with your risk assessment today?",
        'analyzing': "Let me analyze your risk assessment...",
        'high_risk_warning': "⚠️ **High Risk Alert**: Your shipment has a risk score of {score}, which is considered high.",
        'recommendations_intro': "Based on my analysis, here are my recommendations:",
        'need_more_info': "I need more information to provide accurate recommendations. Could you tell me about:",
        'error': "I apologize, but I encountered an issue. Please try again.",
    },
    'vi': {
        'greeting': "Xin chào! Tôi là trợ lý AI RISKCAST của bạn. Tôi có thể giúp gì cho bạn về đánh giá rủi ro hôm nay?",
        'analyzing': "Để tôi phân tích đánh giá rủi ro của bạn...",
        'high_risk_warning': "⚠️ **Cảnh báo Rủi ro Cao**: Lô hàng của bạn có điểm rủi ro {score}, được coi là cao.",
        'recommendations_intro': "Dựa trên phân tích của tôi, đây là các khuyến nghị:",
        'need_more_info': "Tôi cần thêm thông tin để đưa ra khuyến nghị chính xác. Bạn có thể cho tôi biết về:",
        'error': "Xin lỗi, tôi gặp sự cố. Vui lòng thử lại.",
    },
    'zh': {
        'greeting': "您好！我是您的 RISKCAST AI 顾问。今天我可以如何帮助您进行风险评估？",
        'analyzing': "让我分析您的风险评估...",
        'high_risk_warning': "⚠️ **高风险警报**：您的货运风险评分为 {score}，属于高风险。",
        'recommendations_intro': "根据我的分析，以下是我的建议：",
        'need_more_info': "我需要更多信息才能提供准确的建议。您能告诉我关于：",
        'error': "抱歉，我遇到了问题。请重试。",
    },
}


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(message: str) -> str:
    """
    Detect language from user message.
    
    Uses character-based heuristics for Asian languages
    and falls back to English for Latin scripts.
    
    Args:
        message: User message text
    
    Returns:
        Language code: 'en', 'vi', 'zh', 'ja', 'ko'
    """
    if not message:
        return 'en'
    
    # Vietnamese detection (specific diacritical marks)
    vietnamese_pattern = r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]'
    if re.search(vietnamese_pattern, message.lower()):
        return 'vi'
    
    # Chinese detection (CJK Unified Ideographs range)
    # Simplified and Traditional Chinese
    if any('\u4e00' <= char <= '\u9fff' for char in message):
        # Could be Chinese or Japanese
        # Check for Japanese-specific characters (hiragana, katakana)
        if any('\u3040' <= char <= '\u309f' for char in message):  # Hiragana
            return 'ja'
        if any('\u30a0' <= char <= '\u30ff' for char in message):  # Katakana
            return 'ja'
        return 'zh'
    
    # Japanese detection (hiragana and katakana)
    if any('\u3040' <= char <= '\u30ff' for char in message):
        return 'ja'
    
    # Korean detection (Hangul)
    if any('\uac00' <= char <= '\ud7a3' for char in message):
        return 'ko'
    
    # Default to English for Latin scripts
    return 'en'


def get_system_prompt(language: str = 'en') -> str:
    """
    Get system prompt in specified language.
    
    Args:
        language: Language code ('en', 'vi', 'zh', etc.)
    
    Returns:
        System prompt string
    """
    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS['en'])


def get_template(template_name: str, language: str = 'en') -> str:
    """
    Get response template in specified language.
    
    Args:
        template_name: Template key (e.g., 'greeting', 'high_risk_warning')
        language: Language code
    
    Returns:
        Template string
    """
    lang_templates = TEMPLATES.get(language, TEMPLATES['en'])
    return lang_templates.get(template_name, TEMPLATES['en'].get(template_name, ''))


def format_template(template_name: str, language: str = 'en', **kwargs) -> str:
    """
    Get and format a template with variables.
    
    Args:
        template_name: Template key
        language: Language code
        **kwargs: Variables to substitute
    
    Returns:
        Formatted template string
    """
    template = get_template(template_name, language)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


# ============================================================
# LANGUAGE-AWARE FORMATTING
# ============================================================

def format_currency(amount: float, language: str = 'en') -> str:
    """
    Format currency according to language conventions.
    
    Args:
        amount: Numeric amount
        language: Language code
    
    Returns:
        Formatted currency string
    """
    if language == 'vi':
        # Vietnamese uses . as thousands separator, đ suffix
        return f"{amount:,.0f} đ".replace(',', '.')
    elif language == 'zh':
        # Chinese uses ¥ prefix
        return f"¥{amount:,.2f}"
    elif language == 'ja':
        # Japanese uses ¥ prefix, no decimals
        return f"¥{amount:,.0f}"
    elif language == 'ko':
        # Korean uses ₩ prefix
        return f"₩{amount:,.0f}"
    else:
        # Default USD
        return f"${amount:,.2f}"


def format_percentage(value: float, language: str = 'en') -> str:
    """
    Format percentage according to language conventions.
    
    Args:
        value: Percentage value (e.g., 0.45 for 45%)
        language: Language code
    
    Returns:
        Formatted percentage string
    """
    pct = value * 100 if value < 1 else value
    return f"{pct:.1f}%"


def format_risk_level(level: str, language: str = 'en') -> str:
    """
    Translate risk level to specified language.
    
    Args:
        level: Risk level ('low', 'medium', 'high', 'critical')
        language: Language code
    
    Returns:
        Translated risk level
    """
    translations = {
        'en': {'low': 'Low', 'medium': 'Medium', 'high': 'High', 'critical': 'Critical'},
        'vi': {'low': 'Thấp', 'medium': 'Trung bình', 'high': 'Cao', 'critical': 'Nghiêm trọng'},
        'zh': {'low': '低', 'medium': '中', 'high': '高', 'critical': '严重'},
        'ja': {'low': '低', 'medium': '中', 'high': '高', 'critical': '重大'},
        'ko': {'low': '낮음', 'medium': '중간', 'high': '높음', 'critical': '심각'},
    }
    
    lang_trans = translations.get(language, translations['en'])
    return lang_trans.get(level.lower(), level.capitalize())


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'native': 'English'},
    'vi': {'name': 'Vietnamese', 'native': 'Tiếng Việt'},
    'zh': {'name': 'Chinese', 'native': '中文'},
    'ja': {'name': 'Japanese', 'native': '日本語'},
    'ko': {'name': 'Korean', 'native': '한국어'},
}


def get_supported_languages():
    """Get list of supported languages."""
    return SUPPORTED_LANGUAGES


def is_language_supported(language: str) -> bool:
    """Check if language is supported."""
    return language in SUPPORTED_LANGUAGES
