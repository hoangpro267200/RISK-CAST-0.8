"""
Contract tests for Policy API endpoints.
"""

import pytest
import requests


class TestPolicyContracts:
    """Policy API contract tests."""
    
    def test_get_policy_by_id(self, pact_policy_consumer, mock_auth_header):
        """
        Contract: Consumer can retrieve a policy.
        """
        try:
            from pact import Like, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        policy_id = "pol_xyz789"
        
        expected_response = {
            "policy_id": policy_id,
            "policy_number": Like("POL-2026-0001"),
            "status": Like("ACTIVE"),
            "quote_id": Like("qt_abc123"),
            "customer_id": Like("cust_123"),
            
            "coverage": {
                "type": Like("ALL_RISKS"),
                "limit_usd": Like(500000.00),
                "deductible_usd": Like(5000.00)
            },
            
            "premium": {
                "total_premium_usd": Like(12500.00),
                "paid_premium_usd": Like(12500.00),
                "payment_status": Like("PAID")
            },
            
            "dates": {
                "effective_from": Term(r"\d{4}-\d{2}-\d{2}", "2026-02-15"),
                "effective_to": Term(r"\d{4}-\d{2}-\d{2}", "2026-03-15"),
                "issued_at": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-01-25T12:00:00")
            },
            
            "cargo": {
                "type": Like("ELECTRONICS"),
                "description": Like("Consumer electronics"),
                "value_usd": Like(500000.00)
            },
            
            "route": {
                "origin_port": Like("CNSHA"),
                "destination_port": Like("USLAX")
            }
        }
        
        (pact_policy_consumer
            .given(f"policy {policy_id} exists and is active")
            .upon_receiving("a request to get policy by ID")
            .with_request(
                method="GET",
                path=f"/api/v3/policies/{policy_id}",
                headers={"Authorization": "Bearer test-token-12345"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_policy_consumer:
            response = requests.get(
                f"{pact_policy_consumer.uri}/api/v3/policies/{policy_id}",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["policy_id"] == policy_id
            assert data["status"] == "ACTIVE"
    
    def test_cancel_policy(self, pact_policy_consumer, mock_auth_header):
        """
        Contract: Consumer can cancel a policy.
        """
        try:
            from pact import Like, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        policy_id = "pol_xyz789"
        
        expected_response = {
            "policy_id": policy_id,
            "status": "CANCELLED",
            "cancellation": {
                "cancelled_at": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-01-26T10:00:00"),
                "reason": Like("Customer request"),
                "refund_amount_usd": Like(10000.00)
            }
        }
        
        (pact_policy_consumer
            .given(f"policy {policy_id} is active and cancellable")
            .upon_receiving("a request to cancel policy")
            .with_request(
                method="POST",
                path=f"/api/v3/policies/{policy_id}/cancel",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token-12345"
                },
                body={
                    "reason": "Customer request"
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_policy_consumer:
            response = requests.post(
                f"{pact_policy_consumer.uri}/api/v3/policies/{policy_id}/cancel",
                json={"reason": "Customer request"},
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "CANCELLED"
    
    def test_list_active_policies(self, pact_policy_consumer, mock_auth_header):
        """
        Contract: Consumer can list active policies.
        """
        try:
            from pact import Like, EachLike, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        expected_response = {
            "items": EachLike({
                "policy_id": Like("pol_xyz789"),
                "policy_number": Like("POL-2026-0001"),
                "status": "ACTIVE",
                "cargo_type": Like("ELECTRONICS"),
                "coverage_limit_usd": Like(500000.00),
                "effective_from": Term(r"\d{4}-\d{2}-\d{2}", "2026-02-15"),
                "effective_to": Term(r"\d{4}-\d{2}-\d{2}", "2026-03-15")
            }),
            "total_count": Like(5)
        }
        
        (pact_policy_consumer
            .given("user has active policies")
            .upon_receiving("a request to list active policies")
            .with_request(
                method="GET",
                path="/api/v3/policies",
                query={"status": "ACTIVE"},
                headers={"Authorization": "Bearer test-token-12345"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_policy_consumer:
            response = requests.get(
                f"{pact_policy_consumer.uri}/api/v3/policies",
                params={"status": "ACTIVE"},
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
