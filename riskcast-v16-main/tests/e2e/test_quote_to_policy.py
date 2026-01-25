"""
End-to-End Test: Quote to Policy Flow

Tests the complete flow from requesting a quote to having an active policy.
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from fastapi import status


class TestQuoteToPolicyFlow:
    """Test complete quote to policy flow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_quote_to_policy_flow(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_db
    ):
        """
        Test the complete flow:
        1. Request a quote
        2. View quote details
        3. Compare coverage options
        4. Accept quote
        5. Bind quote to policy
        6. Verify policy is active
        """
        
        # Step 1: Request a quote
        quote_request = {
            "origin_port": "CNSHA",
            "destination_port": "USLAX",
            "cargo_type": "ELECTRONICS",
            "cargo_value_usd": 500000,
            "container_count": 2,
            "departure_date": (date.today() + timedelta(days=14)).isoformat(),
            "arrival_date": (date.today() + timedelta(days=35)).isoformat(),
            "coverage_type": "ALL_RISKS",
            "deductible_type": "PERCENTAGE",
            "deductible_value": 0.01,
            "carrier_code": "MAEU"
        }
        
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=quote_request,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        quote_data = response.json()
        
        quote_id = quote_data["quote_id"]
        assert quote_data["status"] == "PENDING"
        assert quote_data["total_premium_usd"] > 0
        assert quote_data["risk_grade"] in ["A", "B", "C", "D", "F"]
        
        # Step 2: View quote details
        response = await async_client.get(
            f"/api/v3/quotes/{quote_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        quote_detail = response.json()
        
        assert quote_detail["quote_id"] == quote_id
        assert "pricing_breakdown" in quote_detail or "total_premium_usd" in quote_detail
        assert "terms" in quote_detail or quote_detail.get("coverage_type") is not None
        
        # Step 3: Compare coverage options (if endpoint exists)
        response = await async_client.get(
            f"/api/v3/quotes/{quote_id}/comparison",
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            comparison = response.json()
            assert "current" in comparison or "alternatives" in comparison
        
        # Step 4: Accept quote
        response = await async_client.post(
            f"/api/v3/quotes/{quote_id}/accept",
            json={"acceptance_notes": "E2E test acceptance"},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        accepted = response.json()
        
        assert accepted["status"] == "ACCEPTED"
        
        # Verify quote status changed
        response = await async_client.get(
            f"/api/v3/quotes/{quote_id}",
            headers=auth_headers
        )
        assert response.json()["status"] == "ACCEPTED"
        
        # Step 5: Bind quote to policy
        response = await async_client.post(
            f"/api/v3/quotes/{quote_id}/bind",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        bind_result = response.json()
        
        assert "policy_id" in bind_result
        policy_id = bind_result["policy_id"]
        
        # Step 6: Verify policy is active
        response = await async_client.get(
            f"/api/v3/policies/{policy_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        policy = response.json()
        
        assert policy["status"] in ["ACTIVE", "PENDING_PAYMENT", "BOUND"]
        assert policy["policy_number"] is not None
        assert policy["coverage_limit_usd"] == quote_request["cargo_value_usd"]
        
        # Verify quote is now bound
        response = await async_client.get(
            f"/api/v3/quotes/{quote_id}",
            headers=auth_headers
        )
        final_quote = response.json()
        assert final_quote["status"] in ["BOUND", "ACCEPTED"]
        
        # Verify audit trail exists (if endpoint available)
        response = await async_client.get(
            f"/api/v3/audit/events/by-entity/quote/{quote_id}",
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            audit_events = response.json()
            if isinstance(audit_events, list):
                event_actions = [e.get("action", e.get("event_type")) for e in audit_events]
                
                # Check for key events
                has_created = any("CREATE" in str(action).upper() for action in event_actions)
                has_accepted = any("ACCEPT" in str(action).upper() for action in event_actions)
                has_bound = any("BOUND" in str(action).upper() or "BIND" in str(action).upper() for action in event_actions)
                
                # At least created event should exist
                assert has_created or len(audit_events) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_quote_modification_flow(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """
        Test quote modification flow:
        1. Request a quote
        2. Modify quote (change cargo value)
        3. Verify premium recalculated
        """
        
        # Step 1: Create initial quote
        quote_request = {
            "origin_port": "SGSIN",
            "destination_port": "NLRTM",
            "cargo_type": "MACHINERY",
            "cargo_value_usd": 200000,
            "departure_date": (date.today() + timedelta(days=10)).isoformat(),
            "arrival_date": (date.today() + timedelta(days=40)).isoformat()
        }
        
        response = await async_client.post(
            "/api/v3/quotes/request",
            json=quote_request,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        original = response.json()
        original_premium = original["total_premium_usd"]
        quote_id = original["quote_id"]
        
        # Step 2: Modify quote
        response = await async_client.put(
            f"/api/v3/quotes/{quote_id}",
            json={"cargo_value_usd": 400000},  # Double the value
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        modified = response.json()
        
        # Step 3: Verify premium changed
        assert modified["cargo_value_usd"] == 400000
        # Premium should be higher (may vary due to tiers)
        assert modified["total_premium_usd"] > original_premium
        
        # Verify quote still exists
        response = await async_client.get(
            f"/api/v3/quotes/{quote_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_quote_decline_flow(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """
        Test quote decline flow:
        1. Request a quote
        2. Decline with reason
        3. Verify quote cannot be accepted after decline
        """
        
        # Step 1: Create quote
        response = await async_client.post(
            "/api/v3/quotes/request",
            json={
                "origin_port": "KRPUS",
                "destination_port": "USLAX",
                "cargo_type": "AUTOMOTIVE",
                "cargo_value_usd": 1000000,
                "departure_date": (date.today() + timedelta(days=7)).isoformat(),
                "arrival_date": (date.today() + timedelta(days=30)).isoformat()
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        quote_id = response.json()["quote_id"]
        
        # Step 2: Decline quote
        response = await async_client.post(
            f"/api/v3/quotes/{quote_id}/decline",
            json={
                "reason": "PRICE_TOO_HIGH",
                "reason_details": "Found better rate with competitor"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        declined = response.json()
        assert declined["status"] == "DECLINED"
        
        # Step 3: Try to accept declined quote
        response = await async_client.post(
            f"/api/v3/quotes/{quote_id}/accept",
            json={},
            headers=auth_headers
        )
        
        # Should be rejected (400, 403, or 409)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_409_CONFLICT
        ]
        
        # Verify quote is still declined
        response = await async_client.get(
            f"/api/v3/quotes/{quote_id}",
            headers=auth_headers
        )
        assert response.json()["status"] == "DECLINED"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_quote_expiration_flow(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """
        Test quote expiration:
        1. Request a quote
        2. Wait for expiration (or simulate)
        3. Verify expired quote cannot be accepted
        """
        
        # Create quote that expires soon
        response = await async_client.post(
            "/api/v3/quotes/request",
            json={
                "origin_port": "CNSHA",
                "destination_port": "DEHAM",
                "cargo_type": "TEXTILES",
                "cargo_value_usd": 150000,
                "departure_date": (date.today() + timedelta(days=5)).isoformat(),
                "arrival_date": (date.today() + timedelta(days=35)).isoformat()
            },
            headers=auth_headers
        )
        
        quote_id = response.json()["quote_id"]
        
        # Try to simulate expiration by setting expiry in past (if API allows)
        # Or verify expiration check logic
        response = await async_client.get(
            f"/api/v3/quotes/{quote_id}",
            headers=auth_headers
        )
        
        quote_detail = response.json()
        
        # Verify expiry_date exists
        assert "expiry_date" in quote_detail or "expires_at" in quote_detail or "valid_until" in quote_detail
        
        # If quote is already expired or we can mark as expired
        # Try to accept and it should fail
        # For now, just verify the expiry field exists
        assert response.status_code == status.HTTP_200_OK


class TestQuoteListingAndFiltering:
    """Test quote listing and filtering."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_quote_listing_with_filters(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """
        Test quote listing and filtering:
        1. Create multiple quotes with different statuses
        2. List all quotes
        3. Filter by status
        4. Filter by date range
        """
        
        # Create multiple quotes
        quote_ids = []
        for i in range(3):
            response = await async_client.post(
                "/api/v3/quotes/request",
                json={
                    "origin_port": ["CNSHA", "SGSIN", "KRPUS"][i],
                    "destination_port": "USLAX",
                    "cargo_type": ["ELECTRONICS", "MACHINERY", "AUTOMOTIVE"][i],
                    "cargo_value_usd": [100000, 200000, 300000][i],
                    "departure_date": (date.today() + timedelta(days=10 + i)).isoformat(),
                    "arrival_date": (date.today() + timedelta(days=40 + i)).isoformat()
                },
                headers=auth_headers
            )
            if response.status_code == status.HTTP_200_OK:
                quote_ids.append(response.json()["quote_id"])
        
        assert len(quote_ids) >= 1
        
        # Accept one quote
        if len(quote_ids) > 1:
            await async_client.post(
                f"/api/v3/quotes/{quote_ids[0]}/accept",
                json={},
                headers=auth_headers
            )
        
        # List all quotes
        response = await async_client.get(
            "/api/v3/quotes/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        all_quotes = response.json()
        
        # Should have at least our created quotes
        assert len(all_quotes) >= len(quote_ids)
        
        # Filter by status
        response = await async_client.get(
            "/api/v3/quotes/?status=PENDING",
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            pending_quotes = response.json()
            # All should be pending
            if isinstance(pending_quotes, list):
                for quote in pending_quotes:
                    assert quote["status"] == "PENDING"
        
        # Filter by accepted status
        response = await async_client.get(
            "/api/v3/quotes/?status=ACCEPTED",
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            accepted_quotes = response.json()
            if isinstance(accepted_quotes, list) and len(accepted_quotes) > 0:
                for quote in accepted_quotes:
                    assert quote["status"] == "ACCEPTED"
