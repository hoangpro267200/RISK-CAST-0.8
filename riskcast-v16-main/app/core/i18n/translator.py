"""
RISKCAST i18n - Translator
Multi-language translation engine with fallback support
Supports: Vietnamese (vi), English (en), Chinese (zh)
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any, List, Union


class Translator:
    """Multi-language translator with fallback support"""
    
    SUPPORTED_LANGUAGES = ['vi', 'en', 'zh']
    DEFAULT_LANGUAGE = 'en'
    
    # Language display names
    LANGUAGE_NAMES = {
        'vi': 'Tiếng Việt',
        'en': 'English',
        'zh': '中文'
    }
    
    def __init__(self, language: str = 'en'):
        """
        Initialize translator
        
        Args:
            language: Language code (vi, en, zh)
        """
        self.language = language if language in self.SUPPORTED_LANGUAGES else self.DEFAULT_LANGUAGE
        self.translations: Dict[str, Dict[str, Any]] = {}
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
    
    def reload_translations(self):
        """Reload all translation files (useful for hot-reload in development)"""
        self.translations = {}
        self._load_translations()
    
    def translate(self, key: str, lang: Optional[str] = None, **variables: Any) -> str:
        """
        Translate a key to the specified language
        
        Args:
            key: Translation key (supports dot notation: "risk.level.high")
            lang: Language code (defaults to current language)
            **variables: Variables to interpolate in template
            
        Returns:
            Translated string or key if not found
            
        Examples:
            >>> t = Translator('vi')
            >>> t.translate('common.risk')
            'Rủi ro'
            >>> t.translate('risk.level.high')
            'Cao'
        """
        target_lang = lang or self.language
        
        # Validate language
        if target_lang not in self.SUPPORTED_LANGUAGES:
            target_lang = self.DEFAULT_LANGUAGE
        
        # Try to get translation
        translation = self._get_translation(key, target_lang)
        
        # If not found, try fallback to English
        if translation is None and target_lang != self.DEFAULT_LANGUAGE:
            translation = self._get_translation(key, self.DEFAULT_LANGUAGE)
        
        # If still not found, return key
        if translation is None:
            return key
        
        # Format message with variables
        if variables:
            return self.format_message(translation, **variables)
        
        return translation
    
    def t(self, key: str, lang: Optional[str] = None, **variables: Any) -> str:
        """Shorthand for translate()"""
        return self.translate(key, lang, **variables)
    
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
            
            # Return string value only
            if isinstance(value, str):
                return value
            elif isinstance(value, (int, float)):
                return str(value)
            else:
                return None
        except (KeyError, TypeError, AttributeError):
            return None
    
    def get_nested(self, key: str, lang: Optional[str] = None) -> Optional[Union[str, Dict, List]]:
        """
        Get a nested translation object (dict or list)
        
        Args:
            key: Translation key (supports dot notation)
            lang: Language code
            
        Returns:
            Translation value (can be string, dict, or list)
        """
        target_lang = lang or self.language
        
        if target_lang not in self.translations:
            return None
        
        translations = self.translations[target_lang]
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
            return value
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
    
    def get_language_name(self, lang: Optional[str] = None) -> str:
        """Get display name of language"""
        target_lang = lang or self.language
        return self.LANGUAGE_NAMES.get(target_lang, target_lang)
    
    def set_language(self, language: str) -> bool:
        """
        Set current language
        
        Args:
            language: Language code (vi, en, zh)
            
        Returns:
            True if language was set successfully, False otherwise
        """
        if language in self.SUPPORTED_LANGUAGES:
            self.language = language
            return True
        else:
            print(f"[Translator] Unsupported language: {language}, keeping {self.language}")
            return False
    
    def get_all_keys(self, lang: Optional[str] = None, prefix: str = '') -> List[str]:
        """
        Get all translation keys for a language
        
        Args:
            lang: Language code
            prefix: Key prefix to filter
            
        Returns:
            List of translation keys
        """
        target_lang = lang or self.language
        if target_lang not in self.translations:
            return []
        
        keys = []
        
        def _extract_keys(data: Any, current_prefix: str):
            if isinstance(data, dict):
                for k, v in data.items():
                    new_prefix = f"{current_prefix}.{k}" if current_prefix else k
                    if isinstance(v, dict):
                        _extract_keys(v, new_prefix)
                    else:
                        keys.append(new_prefix)
        
        _extract_keys(self.translations[target_lang], '')
        
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        
        return sorted(keys)
    
    def translate_dict(self, data: Dict[str, Any], keys_to_translate: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Translate multiple keys in a dictionary
        
        Args:
            data: Dictionary to translate
            keys_to_translate: List of keys to translate (None = translate all string values that look like keys)
            
        Returns:
            Dictionary with translated values
        """
        result = {}
        
        for key, value in data.items():
            if keys_to_translate and key not in keys_to_translate:
                result[key] = value
                continue
            
            if isinstance(value, str):
                # Try to translate if it looks like a translation key (contains dots)
                if '.' in value and not value.startswith('http') and not value.startswith('/'):
                    translated = self.translate(value)
                    result[key] = translated if translated != value else value
                else:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self.translate_dict(value, keys_to_translate)
            elif isinstance(value, list):
                result[key] = [
                    self.translate(item) if isinstance(item, str) and '.' in item
                    else item for item in value
                ]
            else:
                result[key] = value
        
        return result
    
    def translate_list(self, keys: List[str], lang: Optional[str] = None) -> Dict[str, str]:
        """
        Translate a list of keys and return a dictionary
        
        Args:
            keys: List of translation keys
            lang: Language code
            
        Returns:
            Dictionary mapping keys to translations
        """
        return {key: self.translate(key, lang) for key in keys}
    
    def has_key(self, key: str, lang: Optional[str] = None) -> bool:
        """
        Check if a translation key exists
        
        Args:
            key: Translation key
            lang: Language code
            
        Returns:
            True if key exists
        """
        target_lang = lang or self.language
        return self._get_translation(key, target_lang) is not None
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages with display names
        
        Returns:
            List of dicts with 'code' and 'name' keys
        """
        return [
            {'code': lang, 'name': self.LANGUAGE_NAMES.get(lang, lang)}
            for lang in self.SUPPORTED_LANGUAGES
        ]


# Global translator instance
_default_translator: Optional[Translator] = None


def get_translator(language: Optional[str] = None) -> Translator:
    """
    Get or create a translator instance
    
    Args:
        language: Language code (optional, defaults to 'en')
        
    Returns:
        Translator instance
    """
    global _default_translator
    
    if language:
        return Translator(language)
    
    if _default_translator is None:
        _default_translator = Translator()
    
    return _default_translator


def translate(key: str, lang: Optional[str] = None, **variables: Any) -> str:
    """
    Global translate function
    
    Args:
        key: Translation key
        lang: Language code (optional)
        **variables: Variables for template
        
    Returns:
        Translated string
        
    Examples:
        >>> translate('common.risk', 'vi')
        'Rủi ro'
        >>> translate('risk.level.high', 'en')
        'High'
    """
    if lang:
        translator = Translator(lang)
        return translator.translate(key, **variables)
    return get_translator().translate(key, **variables)


def t(key: str, lang: Optional[str] = None, **variables: Any) -> str:
    """Shorthand for translate()"""
    return translate(key, lang, **variables)


def set_default_language(language: str) -> bool:
    """
    Set the default language for global translator
    
    Args:
        language: Language code
        
    Returns:
        True if successful
    """
    global _default_translator
    if _default_translator is None:
        _default_translator = Translator(language)
        return True
    return _default_translator.set_language(language)


def get_all_translations(lang: str = 'en') -> Dict[str, Any]:
    """
    Get all translations for a language
    
    Args:
        lang: Language code
        
    Returns:
        Full translation dictionary
    """
    translator = get_translator(lang)
    return translator.translations.get(lang, {})
