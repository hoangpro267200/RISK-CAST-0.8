"""
RISKCAST Security - Input Sanitization
Prevents XSS, SQL injection, and other injection attacks
"""

import re
import html
from typing import Any, Dict, List, Union
from html.parser import HTMLParser


class HTMLTagStripper(HTMLParser):
    """Strip HTML tags and dangerous attributes"""
    
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
        self.dangerous_attrs = {
            'onclick', 'onload', 'onerror', 'onmouseover', 'onfocus',
            'onblur', 'onchange', 'onsubmit', 'onkeydown', 'onkeyup'
        }
    
    def handle_starttag(self, tag, attrs):
        # Block script tags completely
        if tag.lower() in ['script', 'iframe', 'object', 'embed', 'form']:
            return
        
        # Check for dangerous attributes
        for attr, value in attrs:
            if attr.lower() in self.dangerous_attrs:
                return  # Skip this tag if it has dangerous attributes
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ''.join(self.text)


def sanitize_html(text: str, allow_tags: List[str] = None) -> str:
    """
    Sanitize HTML content
    
    Args:
        text: Input text containing HTML
        allow_tags: List of allowed HTML tags (None = strip all)
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    if allow_tags is None:
        # Strip all HTML tags
        stripper = HTMLTagStripper()
        stripper.feed(text)
        sanitized = stripper.get_text()
        # Escape remaining HTML entities
        sanitized = html.escape(sanitized)
        return sanitized
    else:
        # Allow specific tags (basic implementation)
        # Remove dangerous tags
        text = re.sub(r'<(script|iframe|object|embed|form)[^>]*>.*?</\1>', '', text, flags=re.IGNORECASE | re.DOTALL)
        # Remove dangerous attributes
        for attr in ['onclick', 'onload', 'onerror', 'onmouseover']:
            text = re.sub(rf'\s+{attr}\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
        return text


def sanitize_sql(text: str) -> str:
    """
    Remove SQL injection patterns
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove common SQL injection patterns
    sql_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION)\b)',
        r'(\s*--\s*)',  # SQL comments
        r'(\s*/\*.*?\*/\s*)',  # SQL block comments
        r'(\bOR\s+1\s*=\s*1\b)',  # OR 1=1
        r'(\bAND\s+1\s*=\s*1\b)',  # AND 1=1
    ]
    
    sanitized = text
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def sanitize_js(text: str) -> str:
    """
    Remove JavaScript injection patterns
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove JavaScript patterns
    js_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # javascript: protocol
        r'on\w+\s*=',  # Event handlers
        r'eval\s*\(',  # eval()
        r'expression\s*\(',  # expression()
    ]
    
    sanitized = text
    for pattern in js_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized


def remove_unicode_control(text: str) -> str:
    """
    Remove Unicode control characters (potential for attacks)
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove control characters except common whitespace
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    return sanitized


def sanitize_string(text: str, max_length: int = 10000) -> str:
    """
    Comprehensive string sanitization
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Fully sanitized text
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Limit length first
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove Unicode control characters
    text = remove_unicode_control(text)
    
    # Remove SQL injection patterns
    text = sanitize_sql(text)
    
    # Remove JavaScript injection patterns
    text = sanitize_js(text)
    
    # Sanitize HTML
    text = sanitize_html(text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def sanitize_dict(data: Dict[str, Any], max_length: int = 10000) -> Dict[str, Any]:
    """
    Recursively sanitize dictionary values
    
    Args:
        data: Dictionary to sanitize
        max_length: Maximum length for string values
        
    Returns:
        Sanitized dictionary
    """
    sanitized = {}
    
    for key, value in data.items():
        # Sanitize key
        safe_key = sanitize_string(str(key), max_length=256)
        
        # Sanitize value based on type
        if isinstance(value, str):
            sanitized[safe_key] = sanitize_string(value, max_length)
        elif isinstance(value, dict):
            sanitized[safe_key] = sanitize_dict(value, max_length)
        elif isinstance(value, list):
            sanitized[safe_key] = sanitize_list(value, max_length)
        elif isinstance(value, (int, float, bool)) or value is None:
            sanitized[safe_key] = value
        else:
            # Convert to string and sanitize
            sanitized[safe_key] = sanitize_string(str(value), max_length)
    
    return sanitized


def sanitize_list(data: List[Any], max_length: int = 10000) -> List[Any]:
    """
    Recursively sanitize list items
    
    Args:
        data: List to sanitize
        max_length: Maximum length for string values
        
    Returns:
        Sanitized list
    """
    sanitized = []
    
    for item in data:
        if isinstance(item, str):
            sanitized.append(sanitize_string(item, max_length))
        elif isinstance(item, dict):
            sanitized.append(sanitize_dict(item, max_length))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item, max_length))
        elif isinstance(item, (int, float, bool)) or item is None:
            sanitized.append(item)
        else:
            sanitized.append(sanitize_string(str(item), max_length))
    
    return sanitized


def sanitize_input(data: Union[str, Dict, List], max_length: int = 10000) -> Union[str, Dict, List]:
    """
    Main sanitization function - handles all input types
    
    Args:
        data: Input data (string, dict, or list)
        max_length: Maximum length for string values
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return sanitize_string(data, max_length)
    elif isinstance(data, dict):
        return sanitize_dict(data, max_length)
    elif isinstance(data, list):
        return sanitize_list(data, max_length)
    else:
        return sanitize_string(str(data), max_length)





















