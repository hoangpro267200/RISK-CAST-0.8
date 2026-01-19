"""
Unit tests for input sanitization
"""
import pytest
from app.core.utils.sanitizer import (
    sanitize_string,
    sanitize_html,
    sanitize_sql,
    sanitize_js,
    sanitize_dict
)


class TestSanitizeString:
    """Test string sanitization"""
    
    def test_sanitize_normal_string(self):
        """Test sanitizing normal string"""
        input_text = "Hello World"
        result = sanitize_string(input_text)
        assert result == "Hello World"
    
    def test_sanitize_html_tags(self):
        """Test removing HTML tags"""
        input_text = "<script>alert('xss')</script>Hello"
        result = sanitize_string(input_text)
        assert "<script>" not in result
        assert "Hello" in result
    
    def test_sanitize_sql_injection(self):
        """Test removing SQL injection patterns"""
        input_text = "test'; DROP TABLE users; --"
        result = sanitize_string(input_text)
        assert "DROP TABLE" not in result
        assert "test" in result
    
    def test_sanitize_js_injection(self):
        """Test removing JavaScript injection"""
        input_text = "<script>alert('xss')</script>"
        result = sanitize_string(input_text)
        assert "<script>" not in result
    
    def test_sanitize_max_length(self):
        """Test max length enforcement"""
        input_text = "a" * 20000
        result = sanitize_string(input_text, max_length=10000)
        assert len(result) <= 10000


class TestSanitizeHTML:
    """Test HTML sanitization"""
    
    def test_sanitize_script_tags(self):
        """Test removing script tags"""
        input_text = "<script>alert('xss')</script><p>Hello</p>"
        result = sanitize_html(input_text)
        assert "<script>" not in result
        assert "Hello" in result
    
    def test_sanitize_dangerous_attributes(self):
        """Test removing dangerous attributes"""
        input_text = '<div onclick="alert(\'xss\')">Click</div>'
        result = sanitize_html(input_text)
        assert "onclick" not in result


class TestSanitizeSQL:
    """Test SQL sanitization"""
    
    def test_sanitize_sql_commands(self):
        """Test removing SQL commands"""
        input_text = "SELECT * FROM users; DROP TABLE users;"
        result = sanitize_sql(input_text)
        assert "SELECT" not in result
        assert "DROP TABLE" not in result
    
    def test_sanitize_sql_comments(self):
        """Test removing SQL comments"""
        input_text = "test -- comment"
        result = sanitize_sql(input_text)
        assert "--" not in result


class TestSanitizeDict:
    """Test dictionary sanitization"""
    
    def test_sanitize_dict(self):
        """Test sanitizing dictionary values"""
        input_dict = {
            "name": "<script>alert('xss')</script>",
            "value": "normal text",
            "number": 123
        }
        result = sanitize_dict(input_dict)
        assert "<script>" not in result["name"]
        assert result["value"] == "normal text"
        assert result["number"] == 123

