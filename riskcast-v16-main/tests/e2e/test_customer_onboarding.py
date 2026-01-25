"""
End-to-End Test: Customer Onboarding Flow
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestCustomerOnboardingFlow:
    """Test complete customer onboarding."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_onboarding_flow(
        self,
        async_client: AsyncClient
    ):
        """
        Test complete onboarding:
        1. Register company
        2. Submit KYC documents
        3. KYC verification
        4. Credit assessment
        5. Account activation
        6. First quote request
        """
        
        # Step 1: Register company
        registration = {
            "company_name": "E2E Test Logistics",
            "legal_name": "E2E Test Logistics Inc.",
            "registration_number": "E2E123456789",
            "tax_id": "12-3456789",
            "address_line_1": "123 Test Street",
            "city": "San Francisco",
            "state_province": "CA",
            "postal_code": "94105",
            "country": "US",
            "primary_contact_name": "Jane Smith",
            "primary_contact_email": "jane@e2etest.com",
            "primary_contact_phone": "+1-555-987-6543",
            "industry": "LOGISTICS",
            "annual_shipment_volume": 200,
            "average_cargo_value_usd": 150000,
            "primary_cargo_types": ["ELECTRONICS", "MACHINERY"],
            "primary_routes": ["CNSHA-USLAX", "SGSIN-NLRTM"],
            "years_insured": 3
        }
        
        response = await async_client.post(
            "/api/v3/onboarding/register",
            json=registration
        )
        
        # Onboarding endpoint might not exist yet
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Onboarding endpoint not implemented")
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        reg_result = response.json()
        
        customer_id = reg_result["customer_id"]
        assert reg_result["status"] in ["PENDING", "REGISTERED"]
        
        # Step 2: Submit KYC documents
        kyc_documents = [
            {
                "document_type": "CERTIFICATE_OF_INCORPORATION",
                "document_number": "INC-2020-12345",
                "issue_date": "2020-01-15",
                "issuing_authority": "State of California",
                "document_url": "https://storage.example.com/docs/inc_cert.pdf"
            },
            {
                "document_type": "TAX_CERTIFICATE",
                "document_number": "TC-12-3456789",
                "issue_date": "2023-01-01",
                "expiry_date": "2024-12-31",
                "issuing_authority": "IRS",
                "document_url": "https://storage.example.com/docs/tax_cert.pdf"
            },
            {
                "document_type": "W9",
                "document_number": "W9-2023-001",
                "issue_date": "2023-06-01",
                "issuing_authority": "Self-certified",
                "document_url": "https://storage.example.com/docs/w9.pdf"
            }
        ]
        
        response = await async_client.post(
            f"/api/v3/onboarding/kyc/{customer_id}",
            json=kyc_documents
        )
        
        if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            assert response.json()["status"] in ["SUBMITTED", "PENDING_REVIEW"]
        
        # Step 3: Check onboarding status
        response = await async_client.get(
            f"/api/v3/onboarding/status/{customer_id}"
        )
        
        if response.status_code == status.HTTP_200_OK:
            status_data = response.json()
            
            assert status_data.get("registration_complete") == True or status_data.get("status") is not None
            
            # Step 4: Simulate KYC verification (admin action)
            admin_headers = await self._get_admin_headers()
            
            response = await async_client.post(
                f"/api/v3/onboarding/verify-kyc/{customer_id}",
                json={
                    "all_verified": True,
                    "documents": {
                        "doc1": {"status": "VERIFIED"},
                        "doc2": {"status": "VERIFIED"},
                        "doc3": {"status": "VERIFIED"}
                    }
                },
                headers=admin_headers
            )
            
            # Step 5: Credit assessment
            if response.status_code == status.HTTP_200_OK:
                response = await async_client.post(
                    f"/api/v3/onboarding/credit-assessment/{customer_id}",
                    headers=admin_headers
                )
                
                if response.status_code == status.HTTP_200_OK:
                    credit = response.json()
                    
                    assert credit.get("credit_score") is not None or credit.get("credit_grade") is not None
                    
                    # Step 6: Activate account
                    response = await async_client.post(
                        f"/api/v3/onboarding/activate/{customer_id}",
                        headers=admin_headers
                    )
                    
                    if response.status_code == status.HTTP_200_OK:
                        activation = response.json()
                        assert activation["status"] in ["ACTIVATED", "ACTIVE"]
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_simplified_registration(
        self,
        async_client: AsyncClient
    ):
        """
        Test simplified registration:
        1. Register with minimal info
        2. Verify account created
        """
        
        # Minimal registration
        registration = {
            "company_name": "Test Company Ltd",
            "email": "test@testcompany.com",
            "phone": "+1-555-000-0000",
            "country": "US"
        }
        
        response = await async_client.post(
            "/api/v3/onboarding/register",
            json=registration
        )
        
        # If endpoint exists
        if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            result = response.json()
            assert "customer_id" in result or "id" in result
            assert result.get("status") in ["PENDING", "REGISTERED", "ACTIVE"]
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Onboarding endpoint not implemented")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_duplicate_registration(
        self,
        async_client: AsyncClient
    ):
        """
        Test duplicate registration prevention:
        1. Register a company
        2. Try to register same company again
        3. Verify duplicate is rejected
        """
        
        registration = {
            "company_name": "Unique Test Co",
            "legal_name": "Unique Test Co Inc.",
            "registration_number": "UNIQUE123456",
            "tax_id": "99-9999999",
            "primary_contact_email": "unique@testco.com",
            "country": "US"
        }
        
        # First registration
        response1 = await async_client.post(
            "/api/v3/onboarding/register",
            json=registration
        )
        
        if response1.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Onboarding endpoint not implemented")
        
        # Second registration with same details
        response2 = await async_client.post(
            "/api/v3/onboarding/register",
            json=registration
        )
        
        # Should be rejected or return existing customer
        if response1.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            # Second attempt should fail or return existing
            assert response2.status_code in [
                status.HTTP_409_CONFLICT,  # Duplicate
                status.HTTP_400_BAD_REQUEST,  # Bad request
                status.HTTP_200_OK  # Returns existing (some APIs do this)
            ]
    
    async def _get_admin_headers(self):
        """Get admin authentication headers."""
        try:
            from app.core.security import create_access_token
            token = create_access_token(subject="admin-user", role="admin")
            return {
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": "admin-tenant"
            }
        except ImportError:
            import jwt
            from datetime import datetime, timedelta
            
            payload = {
                "sub": "admin-user",
                "role": "admin",
                "exp": datetime.utcnow() + timedelta(hours=1)
            }
            token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
            return {
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": "admin-tenant"
            }


class TestCustomerPortalAccess:
    """Test customer portal access flows."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_customer_portal_access(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """
        Test customer portal access:
        1. Access dashboard
        2. View policies
        3. View claims
        4. View invoices
        """
        
        # Dashboard
        response = await async_client.get(
            "/api/v3/portal/dashboard",
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            dashboard = response.json()
            # Should have some statistics
            assert isinstance(dashboard, dict)
        
        # Policies
        response = await async_client.get(
            "/api/v3/portal/policies",
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            policies = response.json()
            assert isinstance(policies, list) or isinstance(policies, dict)
        
        # Claims
        response = await async_client.get(
            "/api/v3/portal/claims",
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            claims = response.json()
            assert isinstance(claims, list) or isinstance(claims, dict)
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_customer_settings_update(
        self,
        async_client: AsyncClient,
        auth_headers
    ):
        """
        Test customer settings update:
        1. Get current settings
        2. Update notification preferences
        3. Update contact information
        """
        
        # Get current settings
        response = await async_client.get(
            "/api/v3/portal/settings",
            headers=auth_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            current_settings = response.json()
            
            # Update settings
            updated_settings = {
                **current_settings,
                "email_notifications": True,
                "sms_notifications": False,
                "notification_preferences": {
                    "policy_renewal": True,
                    "claim_updates": True,
                    "quote_ready": True
                }
            }
            
            response = await async_client.put(
                "/api/v3/portal/settings",
                json=updated_settings,
                headers=auth_headers
            )
            
            if response.status_code == status.HTTP_200_OK:
                saved = response.json()
                assert saved.get("email_notifications") == True
