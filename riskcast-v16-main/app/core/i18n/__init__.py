"""
RISKCAST i18n Module
Multi-language support for global-ready platform
Supports: Vietnamese (vi), English (en), Chinese (zh)
"""

from .translator import (
    Translator,
    translate,
    t,
    get_translator,
    set_default_language,
    get_all_translations
)

__all__ = [
    "Translator",
    "translate",
    "t",
    "get_translator",
    "set_default_language",
    "get_all_translations"
]
