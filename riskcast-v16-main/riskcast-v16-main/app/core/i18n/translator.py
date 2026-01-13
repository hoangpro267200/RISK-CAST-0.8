"""
RISKCAST i18n - Translator
Multi-language translation engine with fallback support
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any, List
import os


class Translator:
    """Multi-language translator with fallback support"""
    
    SUPPORTED_LANGUAGES = ['vi', 'en', 'zh']
    DEFAULT_LANGUAGE = 'en'
    
    def __init__(self, language: str = 'en'):
        """
        Initialize translator
        
        Args:
            language: Language code (vi, en, zh)
        """
        self.language = language if language in self.SUPPORTED_LANGUAGES else self.DEFAULT_LANGUAGE
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files"""
        base_dir = Path(__file__).parent / 'languages'
        
        # Load all languages for fallback
        for lang in self.SUPPORTED_LANGUAGES:
            lang_file = base_dir / f'{lang}.json'
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
                except Exception as e:
                    print(f"[Translator] Error loading {lang}.json: {e}")
                    self.translations[lang] = {}
            else:
                self.translations[lang] = {}
    
    def translate(self, key: str, lang: Optional[str] = None, **variables: Any) -> str:
        """
        Translate a key to the specified language
        
        Args:
            key: Translation key (supports dot notation: "risk.level.high")
            lang: Language code (defaults to current language)
            **variables: Variables to interpolate in template
            
        Returns:
            Translated string or key if not found
        """
        target_lang = lang or self.language
        
        # Try to get translation
        translation = self._get_translation(key, target_lang)
        
        # If not found, try fallback to English
        if not translation and target_lang != self.DEFAULT_LANGUAGE:
            translation = self._get_translation(key, self.DEFAULT_LANGUAGE)
        
        # If still not found, return key
        if not translation:
            return key
        
        # Format message with variables
        if variables:
            return self.format_message(translation, **variables)
        
        return translation
    
    def _get_translation(self, key: str, lang: str) -> Optional[str]:
        """
        Get translation for a key (supports nested keys)
        
        Args:
            key: Translation key (supports dot notation)
            lang: Language code
            
        Returns:
            Translation string or None
        """
        if lang not in self.translations:
            return None
        
        translations = self.translations[lang]
        
        # Handle nested keys (dot notation)
        keys = key.split('.')
        value = translations
        
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return None
                
                if value is None:
                    return None
            
            return str(value) if value is not None else None
        except (KeyError, TypeError, AttributeError):
            return None
    
    def format_message(self, template: str, **variables: Any) -> str:
        """
        Format message template with variables
        
        Args:
            template: Message template with {variable} placeholders
            **variables: Variables to substitute
            
        Returns:
            Formatted message
        """
        try:
            return template.format(**variables)
        except (KeyError, ValueError):
            # If formatting fails, return template as-is
            return template
    
    def get_language(self) -> str:
        """Get current language"""
        return self.language
    
    def set_language(self, language: str):
        """
        Set current language
        
        Args:
            language: Language code (vi, en, zh)
        """
        if language in self.SUPPORTED_LANGUAGES:
            self.language = language
        else:
            print(f"[Translator] Unsupported language: {language}, defaulting to {self.DEFAULT_LANGUAGE}")
            self.language = self.DEFAULT_LANGUAGE
    
    def translate_dict(self, data: Dict[str, Any], keys_to_translate: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Translate multiple keys in a dictionary
        
        Args:
            data: Dictionary to translate
            keys_to_translate: List of keys to translate (None = translate all string values)
            
        Returns:
            Dictionary with translated values
        """
        result = {}
        
        for key, value in data.items():
            if keys_to_translate and key not in keys_to_translate:
                result[key] = value
                continue
            
            if isinstance(value, str):
                # Try to translate if it looks like a translation key
                if value.startswith('risk.') or value.startswith('common.'):
                    result[key] = self.translate(value)
                else:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self.translate_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.translate(item) if isinstance(item, str) and item.startswith('risk.')
                    else item for item in value
                ]
            else:
                result[key] = value
        
        return result


# Global translator instance
_default_translator = Translator()

def translate(key: str, lang: Optional[str] = None, **variables: Any) -> str:
    """
    Global translate function
    
    Args:
        key: Translation key
        lang: Language code (optional)
        **variables: Variables for template
        
    Returns:
        Translated string
    """
    if lang:
        translator = Translator(lang)
        return translator.translate(key, lang, **variables)
    return _default_translator.translate(key, **variables)

