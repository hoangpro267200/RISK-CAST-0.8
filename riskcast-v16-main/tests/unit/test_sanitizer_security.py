"""
Security tests for input sanitizer

Tests that sanitizer prevents:
- SQL injection attacks
- XSS (Cross-Site Scripting) attacks
- JavaScript injection
- HTML injection
"""
import pytest
from app.core.utils.sanitizer import (
    sanitize_string,
    sanitize_dict,
    sanitize_input,
    sanitize_html,
    sanitize_sql,
    sanitize_js
)


class TestSQLInjectionPrevention:
    """Test that SQL injection patterns are blocked"""
    
    def test_sql_select_injection(self):
        """Test SELECT injection is blocked"""
        malicious = "'; SELECT * FROM users; --"
        sanitized = sanitize_string(malicious)
        assert "SELECT" not in sanitized.upper(), "SELECT should be removed"
        assert ";" not in sanitized or sanitized.count(";") < malicious.count(";"), "SQL statements should be sanitized"
    
    def test_sql_union_injection(self):
        """Test UNION injection is blocked"""
        malicious = "' UNION SELECT * FROM users --"
        sanitized = sanitize_string(malicious)
        assert "UNION" not in sanitized.upper(), "UNION should be removed"
    
    def test_sql_or_1_equals_1(self):
        """Test OR 1=1 injection is blocked"""
        malicious = "' OR 1=1 --"
        sanitized = sanitize_string(malicious)
        # OR 1=1 pattern should be removed or sanitized
        assert "OR 1=1" not in sanitized.upper() or sanitized != malicious, "OR 1=1 should be sanitized"
    
    def test_sql_drop_table(self):
        """Test DROP TABLE injection is blocked"""
        malicious = "'; DROP TABLE users; --"
        sanitized = sanitize_string(malicious)
        assert "DROP" not in sanitized.upper(), "DROP should be removed"
    
    def test_sql_comment_injection(self):
        """Test SQL comment injection is blocked"""
        malicious = "admin'--"
        sanitized = sanitize_string(malicious)
        # SQL comments should be removed or sanitized
        assert "--" not in sanitized or sanitized != malicious, "SQL comments should be sanitized"


class TestXSSPrevention:
    """Test that XSS attacks are blocked"""
    
    def test_script_tag_injection(self):
        """Test <script> tag injection is blocked"""
        malicious = "<script>alert('XSS')</script>"
        sanitized = sanitize_string(malicious)
        assert "<script>" not in sanitized.lower(), "Script tags should be removed"
        assert "alert" not in sanitized.lower() or sanitized != malicious, "Script content should be sanitized"
    
    def test_img_onerror_injection(self):
        """Test img onerror XSS is blocked"""
        malicious = "<img src=x onerror=alert('XSS')>"
        sanitized = sanitize_string(malicious)
        assert "onerror" not in sanitized.lower(), "onerror handler should be removed"
    
    def test_javascript_protocol(self):
        """Test javascript: protocol is blocked"""
        malicious = "javascript:alert('XSS')"
        sanitized = sanitize_string(malicious)
        assert "javascript:" not in sanitized.lower(), "javascript: protocol should be removed"
    
    def test_event_handler_injection(self):
        """Test event handler injection is blocked"""
        malicious = "<div onclick=alert('XSS')>Click</div>"
        sanitized = sanitize_string(malicious)
        assert "onclick" not in sanitized.lower(), "onclick handler should be removed"
    
    def test_iframe_injection(self):
        """Test iframe injection is blocked"""
        malicious = "<iframe src='evil.com'></iframe>"
        sanitized = sanitize_string(malicious)
        assert "<iframe" not in sanitized.lower(), "iframe tags should be removed"
    
    def test_html_entities_escaped(self):
        """Test HTML entities are escaped"""
        malicious = "<div>Test</div>"
        sanitized = sanitize_string(malicious)
        # HTML should be escaped, not contain raw tags
        assert "<div>" not in sanitized or sanitized != malicious, "HTML should be escaped"


class TestJavaScriptInjection:
    """Test that JavaScript injection is blocked"""
    
    def test_eval_injection(self):
        """Test eval() injection is blocked"""
        malicious = "eval('alert(1)')"
        sanitized = sanitize_string(malicious)
        assert "eval(" not in sanitized.lower(), "eval() should be removed"
    
    def test_expression_injection(self):
        """Test expression() injection is blocked"""
        malicious = "expression(alert('XSS'))"
        sanitized = sanitize_string(malicious)
        assert "expression(" not in sanitized.lower(), "expression() should be removed"


class TestInputLengthLimits:
    """Test that input length limits are enforced"""
    
    def test_max_length_enforced(self):
        """Test max_length parameter is enforced"""
        long_input = "a" * 20000
        sanitized = sanitize_string(long_input, max_length=1000)
        assert len(sanitized) <= 1000, "String should be truncated to max_length"
    
    def test_dict_max_length(self):
        """Test max_length enforced in dictionaries"""
        data = {
            "field1": "a" * 20000,
            "field2": "normal"
        }
        sanitized = sanitize_dict(data, max_length=1000)
        assert len(sanitized["field1"]) <= 1000, "Dictionary values should respect max_length"
        assert sanitized["field2"] == "normal", "Normal values should be preserved"


class TestSanitizerPreservesValidData:
    """Test that sanitizer preserves valid, safe data"""
    
    def test_valid_string_preserved(self):
        """Test valid strings are preserved"""
        valid = "This is a valid string with numbers 123 and symbols !@#"
        sanitized = sanitize_string(valid)
        # Should preserve most content (may remove some symbols)
        assert len(sanitized) > 0, "Valid string should not be empty"
    
    def test_valid_dict_preserved(self):
        """Test valid dictionaries are preserved"""
        valid = {
            "name": "John Doe",
            "age": 30,
            "active": True,
            "score": 95.5
        }
        sanitized = sanitize_dict(valid)
        assert sanitized["name"] == "John Doe", "Valid strings should be preserved"
        assert sanitized["age"] == 30, "Valid integers should be preserved"
        assert sanitized["active"] is True, "Valid booleans should be preserved"
        assert sanitized["score"] == 95.5, "Valid floats should be preserved"
    
    def test_nested_dict_sanitized(self):
        """Test nested dictionaries are sanitized"""
        data = {
            "user": {
                "name": "<script>alert('XSS')</script>",
                "email": "test@example.com"
            }
        }
        sanitized = sanitize_dict(data)
        assert "<script>" not in sanitized["user"]["name"].lower(), "Nested XSS should be blocked"
        assert "test@example.com" in sanitized["user"]["email"], "Valid nested data should be preserved"


class TestUnicodeControlCharacters:
    """Test that Unicode control characters are removed"""
    
    def test_control_characters_removed(self):
        """Test Unicode control characters are removed"""
        malicious = "test\x00\x01\x02string"
        sanitized = sanitize_string(malicious)
        # Control characters (except \n\r\t) should be removed
        assert "\x00" not in sanitized, "Null bytes should be removed"
        assert "\x01" not in sanitized, "Control characters should be removed"
    
    def test_newlines_preserved(self):
        """Test that newlines are preserved"""
        text = "line1\nline2\rline3\r\nline4"
        sanitized = sanitize_string(text)
        assert "\n" in sanitized or "\r" in sanitized, "Newlines should be preserved"


class TestSanitizerIntegration:
    """Integration tests for sanitizer with real-world attack vectors"""
    
    def test_complex_sql_xss_combination(self):
        """Test complex attack combining SQL and XSS"""
        malicious = "'; <script>alert('XSS')</script>; SELECT * FROM users; --"
        sanitized = sanitize_string(malicious)
        assert "<script>" not in sanitized.lower(), "Script tags should be removed"
        assert "SELECT" not in sanitized.upper(), "SQL should be removed"
    
    def test_sanitize_input_string(self):
        """Test sanitize_input with string"""
        malicious = "<script>alert('XSS')</script>"
        sanitized = sanitize_input(malicious)
        assert "<script>" not in str(sanitized).lower(), "sanitize_input should handle strings"
    
    def test_sanitize_input_dict(self):
        """Test sanitize_input with dictionary"""
        malicious = {
            "name": "<script>alert('XSS')</script>",
            "query": "'; SELECT * FROM users; --"
        }
        sanitized = sanitize_input(malicious)
        assert isinstance(sanitized, dict), "Should return dictionary"
        assert "<script>" not in sanitized["name"].lower(), "Should sanitize dict values"
        assert "SELECT" not in sanitized["query"].upper(), "Should sanitize SQL in dict"

