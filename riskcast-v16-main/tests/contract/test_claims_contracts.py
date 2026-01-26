"""
Contract tests for Claims API endpoints.
"""

import pytest
import requests


class TestClaimsContracts:
    """Claims API contract tests."""
    
    def test_file_claim(self, pact_claims_consumer, mock_auth_header):
        """
        Contract: Consumer can file a new claim.
        """
        try:
            from pact import Like, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        policy_id = "pol_xyz789"
        
        expected_response = {
            "claim_id": Like("clm_abc123"),
            "claim_number": Like("CLM-2026-0001"),
            "policy_id": policy_id,
            "status": "FILED",
            "loss_details": {
                "loss_date": Term(r"\d{4}-\d{2}-\d{2}", "2026-02-20"),
                "loss_type": Like("DAMAGE"),
                "loss_location": Like("Port of Long Beach"),
                "description": Like("Water damage to cargo")
            },
            "claimed_amount_usd": Like(50000.00),
            "filed_at": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-02-21T10:00:00")
        }
        
        (pact_claims_consumer
            .given(f"policy {policy_id} exists and covers the loss date")
            .upon_receiving("a request to file a claim")
            .with_request(
                method="POST",
                path="/api/v3/claims",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token-12345"
                },
                body={
                    "policy_id": policy_id,
                    "loss_date": "2026-02-20",
                    "loss_type": "DAMAGE",
                    "loss_location": "Port of Long Beach",
                    "description": "Water damage to cargo",
                    "claimed_amount_usd": 50000.00
                }
            )
            .will_respond_with(
                status=201,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_claims_consumer:
            response = requests.post(
                f"{pact_claims_consumer.uri}/api/v3/claims",
                json={
                    "policy_id": policy_id,
                    "loss_date": "2026-02-20",
                    "loss_type": "DAMAGE",
                    "loss_location": "Port of Long Beach",
                    "description": "Water damage to cargo",
                    "claimed_amount_usd": 50000.00
                },
                headers=mock_auth_header
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "FILED"
            assert "claim_id" in data
    
    def test_get_claim_status(self, pact_claims_consumer, mock_auth_header):
        """
        Contract: Consumer can check claim status.
        """
        try:
            from pact import Like, EachLike, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        claim_id = "clm_abc123"
        
        expected_response = {
            "claim_id": claim_id,
            "claim_number": Like("CLM-2026-0001"),
            "status": Like("IN_REVIEW"),
            "status_history": EachLike({
                "status": Like("FILED"),
                "changed_at": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-02-21T10:00:00"),
                "notes": Like("Claim received")
            }),
            "claimed_amount_usd": Like(50000.00),
            "assessed_amount_usd": Like(45000.00),
            "next_steps": Like("Awaiting adjuster report")
        }
        
        (pact_claims_consumer
            .given(f"claim {claim_id} exists")
            .upon_receiving("a request to get claim status")
            .with_request(
                method="GET",
                path=f"/api/v3/claims/{claim_id}",
                headers={"Authorization": "Bearer test-token-12345"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_claims_consumer:
            response = requests.get(
                f"{pact_claims_consumer.uri}/api/v3/claims/{claim_id}",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
