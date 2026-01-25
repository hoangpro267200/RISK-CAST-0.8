"""
Integration Tests for Quotes API

Tests:
1. Quote request flow
2. Quote lifecycle (accept, decline, bind, modify)
3. Quote retrieval and listing
4. Error handling
5. Authorization
6. Quote expiration
7. Audit trail
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from fastapi import status
from typing import Dict, Any


# ============================================================================
# Quote Request Tests
# ============================================================================

class TestQuoteRequest:
    """Test quote request endpoint."""
    
    @pytest.mark.asyncio
    async def test_request_quote_success(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        quote_request_payload: Dict[str, Any]
    ):
        """Test successful quote request."""
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=quote_request_payload,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "quote_id" in data
        assert "quote_number" in data
        assert "total_premium_usd" in data
        assert data["total_premium_usd"] > 0
        assert "status" in data
        assert data["status"] in ["PENDING", "DRAFT"]
        
        # Verify key fields
        assert data["cargo_value_usd"] == 500000
        assert data["origin_port"] == "CNSHA"
        assert data["destination_port"] == "USLAX"
    
    @pytest.mark.asyncio
    async def test_request_quote_missing_required_field(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test quote request with missing required field."""
        payload = {
            "origin_port": "CNSHA",
            # Missing destination_port
            "cargo_type": "ELECTRONICS",
            "cargo_value_usd": 500000
        }
        
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        error_data = response.json()
        assert "detail" in error_data
    
    @pytest.mark.asyncio
    async def test_request_quote_invalid_cargo_value(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        quote_request_payload: Dict[str, Any]
    ):
        """Test quote request with invalid cargo value."""
        quote_request_payload["cargo_value_usd"] = -1000
        
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=quote_request_payload,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_request_quote_zero_cargo_value(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        quote_request_payload: Dict[str, Any]
    ):
        """Test quote request with zero cargo value."""
        quote_request_payload["cargo_value_usd"] = 0
        
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=quote_request_payload,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_request_quote_unauthorized(
        self, 
        async_client: AsyncClient, 
        quote_request_payload: Dict[str, Any]
    ):
        """Test quote request without authentication."""
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=quote_request_payload
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_request_quote_invalid_dates(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        quote_request_payload: Dict[str, Any]
    ):
        """Test quote request with arrival before departure."""
        quote_request_payload["departure_date"] = (date.today() + timedelta(days=30)).isoformat()
        quote_request_payload["arrival_date"] = (date.today() + timedelta(days=7)).isoformat()
        
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=quote_request_payload,
            headers=auth_headers
        )
        
        # Should either reject or auto-correct
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
    
    @pytest.mark.asyncio
    async def test_request_quote_with_optional_fields(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        quote_request_payload: Dict[str, Any]
    ):
        """Test quote request with all optional fields."""
        quote_request_payload["include_war_risk"] = True
        quote_request_payload["include_strikes"] = True
        quote_request_payload["coverage_limit_usd"] = 450000
        
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=quote_request_payload,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["coverage_limit_usd"] == 450000


# ============================================================================
# Quote Retrieval Tests
# ============================================================================

class TestQuoteRetrieval:
    """Test quote retrieval endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_quote_success(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test getting quote by ID."""
        response = await async_client.get(
            f"/api/v3/quotes/{created_quote['quote_id']}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["quote_id"] == created_quote["quote_id"]
        assert data["quote_number"] == created_quote["quote_number"]
        assert "pricing_breakdown" in data
        assert "risk_score" in data
    
    @pytest.mark.asyncio
    async def test_get_quote_not_found(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test getting non-existent quote."""
        response = await async_client.get(
            "/api/v3/quotes/nonexistent-quote-id-12345",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_get_quote_unauthorized(
        self, 
        async_client: AsyncClient, 
        created_quote: Dict[str, Any]
    ):
        """Test getting quote without authentication."""
        response = await async_client.get(
            f"/api/v3/quotes/{created_quote['quote_id']}"
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_list_quotes(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test listing quotes."""
        response = await async_client.get(
            "/api/v3/quotes/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Find our created quote
        our_quote = next((q for q in data if q["quote_id"] == created_quote["quote_id"]), None)
        assert our_quote is not None
    
    @pytest.mark.asyncio
    async def test_list_quotes_with_pagination(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test listing quotes with pagination."""
        response = await async_client.get(
            "/api/v3/quotes/?limit=10&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    @pytest.mark.asyncio
    async def test_list_quotes_filter_by_status(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test listing quotes with status filter."""
        response = await async_client.get(
            "/api/v3/quotes/?status=PENDING",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        for quote in data:
            assert quote["status"] == "PENDING"


# ============================================================================
# Quote Lifecycle Tests
# ============================================================================

class TestQuoteLifecycle:
    """Test quote lifecycle operations."""
    
    @pytest.mark.asyncio
    async def test_accept_quote(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test accepting a quote."""
        response = await async_client.post(
            f"/api/v3/quotes/{created_quote['quote_id']}/accept",
            json={"acceptance_notes": "Accepted for testing"},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "ACCEPTED"
        assert data["quote_id"] == created_quote["quote_id"]
    
    @pytest.mark.asyncio
    async def test_accept_already_accepted_quote(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        accepted_quote: Dict[str, Any]
    ):
        """Test accepting an already accepted quote."""
        response = await async_client.post(
            f"/api/v3/quotes/{accepted_quote['quote_id']}/accept",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error = response.json()
        assert "already" in error.get("detail", "").lower()
    
    @pytest.mark.asyncio
    async def test_decline_quote(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test declining a quote."""
        response = await async_client.post(
            f"/api/v3/quotes/{created_quote['quote_id']}/decline",
            json={
                "reason": "PRICE_TOO_HIGH",
                "reason_details": "Found cheaper alternative"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "DECLINED"
    
    @pytest.mark.asyncio
    async def test_decline_without_reason(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test declining quote without reason fails."""
        response = await async_client.post(
            f"/api/v3/quotes/{created_quote['quote_id']}/decline",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_bind_quote_to_policy(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        accepted_quote: Dict[str, Any]
    ):
        """Test binding accepted quote to create policy."""
        response = await async_client.post(
            f"/api/v3/quotes/{accepted_quote['quote_id']}/bind",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "policy_id" in data
        assert data["status"] == "BOUND"
    
    @pytest.mark.asyncio
    async def test_bind_pending_quote_fails(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test binding pending quote fails."""
        response = await async_client.post(
            f"/api/v3/quotes/{created_quote['quote_id']}/bind",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error = response.json()
        assert "accepted" in error.get("detail", "").lower()
    
    @pytest.mark.asyncio
    async def test_modify_quote(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test modifying a quote."""
        response = await async_client.put(
            f"/api/v3/quotes/{created_quote['quote_id']}",
            json={
                "cargo_value_usd": 600000,
                "deductible_value": 0.02
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["cargo_value_usd"] == 600000
        # Premium should be recalculated
        assert data["total_premium_usd"] != created_quote["total_premium_usd"]
    
    @pytest.mark.asyncio
    async def test_modify_accepted_quote_fails(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        accepted_quote: Dict[str, Any]
    ):
        """Test modifying accepted quote fails."""
        response = await async_client.put(
            f"/api/v3/quotes/{accepted_quote['quote_id']}",
            json={"cargo_value_usd": 600000},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_cancel_quote(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test canceling a quote."""
        response = await async_client.post(
            f"/api/v3/quotes/{created_quote['quote_id']}/cancel",
            json={"cancellation_reason": "Customer request"},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "CANCELLED"


# ============================================================================
# Quote Expiration Tests
# ============================================================================

class TestQuoteExpiration:
    """Test quote expiration handling."""
    
    @pytest.mark.asyncio
    async def test_expired_quote_cannot_be_accepted(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        expired_quote: Dict[str, Any]
    ):
        """Test accepting expired quote fails."""
        response = await async_client.post(
            f"/api/v3/quotes/{expired_quote['quote_id']}/accept",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error = response.json()
        assert "expired" in error.get("detail", "").lower()
    
    @pytest.mark.asyncio
    async def test_get_expired_quote_shows_status(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        expired_quote: Dict[str, Any]
    ):
        """Test getting expired quote shows expired status."""
        response = await async_client.get(
            f"/api/v3/quotes/{expired_quote['quote_id']}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Status should be EXPIRED or indicate expiration
        assert data["status"] == "EXPIRED" or "expired" in str(data).lower()
    
    @pytest.mark.asyncio
    async def test_expired_quote_cannot_be_bound(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        expired_quote: Dict[str, Any]
    ):
        """Test binding expired quote fails."""
        response = await async_client.post(
            f"/api/v3/quotes/{expired_quote['quote_id']}/bind",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Quote Comparison Tests
# ============================================================================

class TestQuoteComparison:
    """Test quote comparison endpoint."""
    
    @pytest.mark.asyncio
    async def test_compare_coverage_options(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test getting quote comparison with different coverage options."""
        response = await async_client.get(
            f"/api/v3/quotes/{created_quote['quote_id']}/comparison",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "current" in data
        assert "alternatives" in data
        assert len(data["alternatives"]) > 0
        
        # Should have different coverage options
        coverage_types = set(alt["coverage_type"] for alt in data["alternatives"])
        assert len(coverage_types) >= 2
    
    @pytest.mark.asyncio
    async def test_comparison_shows_savings(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test comparison shows potential savings."""
        response = await async_client.get(
            f"/api/v3/quotes/{created_quote['quote_id']}/comparison",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # At least one alternative should show savings
        for alt in data["alternatives"]:
            if alt["total_premium_usd"] < data["current"]["total_premium_usd"]:
                assert "savings_usd" in alt or "savings_pct" in alt
                break


# ============================================================================
# Quote Analytics Tests
# ============================================================================

class TestQuoteAnalytics:
    """Test quote analytics endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_quote_summary(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test getting quote summary statistics."""
        response = await async_client.get(
            "/api/v3/quotes/analytics/summary",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_quotes" in data
        assert "by_status" in data
        assert "average_premium" in data
    
    @pytest.mark.asyncio
    async def test_get_conversion_rate(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test getting quote conversion rate."""
        response = await async_client.get(
            "/api/v3/quotes/analytics/conversion-rate",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "conversion_rate" in data
        assert 0 <= data["conversion_rate"] <= 1


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestQuoteErrorHandling:
    """Test error handling in quote operations."""
    
    @pytest.mark.asyncio
    async def test_invalid_quote_id_format(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test handling of invalid quote ID format."""
        response = await async_client.get(
            "/api/v3/quotes/invalid-id-format!@#",
            headers=auth_headers
        )
        
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
    
    @pytest.mark.asyncio
    async def test_malformed_json_payload(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test handling of malformed JSON."""
        response = await async_client.post(
            "/api/v3/quotes/request",
            content="not-valid-json{]",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_concurrent_modification(
        self, 
        async_client: AsyncClient, 
        auth_headers: Dict[str, str], 
        created_quote: Dict[str, Any]
    ):
        """Test handling of concurrent modifications."""
        # This is a placeholder - actual implementation depends on versioning strategy
        response1 = await async_client.put(
            f"/api/v3/quotes/{created_quote['quote_id']}",
            json={"cargo_value_usd": 550000},
            headers=auth_headers
        )
        
        response2 = await async_client.put(
            f"/api/v3/quotes/{created_quote['quote_id']}",
            json={"cargo_value_usd": 600000},
            headers=auth_headers
        )
        
        # At least one should succeed
        assert response1.status_code == status.HTTP_200_OK or response2.status_code == status.HTTP_200_OK
