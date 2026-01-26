"""
Contract tests for Quote API endpoints.

These tests define the contract between consumers and the Quote API.
"""

import pytest
import requests
from typing import Dict


class TestQuoteContracts:
    """Quote API contract tests."""
    
    def test_create_quote_request(self, pact_quote_consumer, mock_auth_header):
        """
        Contract: Consumer can request a quote.
        """
        try:
            from pact import Like, EachLike, Term, Format
        except ImportError:
            pytest.skip("pact-python not installed")
        
        expected_response = {
            "quote_id": Like("qt_abc123"),
            "quote_number": Like("QT-2026-0001"),
            "status": "PENDING",
            "cargo": {
                "type": Like("ELECTRONICS"),
                "description": Like("Consumer electronics"),
                "value_usd": Like(500000.00)
            },
            "route": {
                "origin_port": Like("CNSHA"),
                "destination_port": Like("USLAX"),
                "departure_date": Term(r"\d{4}-\d{2}-\d{2}", "2026-02-15")
            },
            "risk_assessment": {
                "risk_score": Like(0.35),
                "risk_grade": Term(r"[A-F]", "B"),
                "factors": EachLike({
                    "name": Like("weather_risk"),
                    "score": Like(0.2),
                    "weight": Like(0.15)
                })
            },
            "premium": {
                "total_premium_usd": Like(12500.00),
                "base_premium_usd": Like(10000.00),
                "rate_per_mille": Like(25.0)
            },
            "valid_until": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-02-01T23:59:59"),
            "created_at": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-01-25T10:00:00")
        }
        
        (pact_quote_consumer
            .given("a valid user is authenticated")
            .upon_receiving("a request to create a quote")
            .with_request(
                method="POST",
                path="/api/v3/quotes",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token-12345"
                },
                body={
                    "cargo_type": "ELECTRONICS",
                    "cargo_description": "Consumer electronics",
                    "cargo_value_usd": 500000.00,
                    "origin_port": "CNSHA",
                    "destination_port": "USLAX",
                    "departure_date": "2026-02-15",
                    "coverage_type": "ALL_RISKS"
                }
            )
            .will_respond_with(
                status=201,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_quote_consumer:
            response = requests.post(
                f"{pact_quote_consumer.uri}/api/v3/quotes",
                json={
                    "cargo_type": "ELECTRONICS",
                    "cargo_description": "Consumer electronics",
                    "cargo_value_usd": 500000.00,
                    "origin_port": "CNSHA",
                    "destination_port": "USLAX",
                    "departure_date": "2026-02-15",
                    "coverage_type": "ALL_RISKS"
                },
                headers=mock_auth_header
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "quote_id" in data
            assert data["status"] == "PENDING"
    
    def test_get_quote_by_id(self, pact_quote_consumer, mock_auth_header):
        """
        Contract: Consumer can retrieve a quote by ID.
        """
        try:
            from pact import Like, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        quote_id = "qt_abc123"
        
        expected_response = {
            "quote_id": quote_id,
            "quote_number": Like("QT-2026-0001"),
            "status": Like("PENDING"),
            "cargo": {
                "type": Like("ELECTRONICS"),
                "value_usd": Like(500000.00)
            },
            "premium": {
                "total_premium_usd": Like(12500.00)
            }
        }
        
        (pact_quote_consumer
            .given(f"quote {quote_id} exists")
            .upon_receiving("a request to get quote by ID")
            .with_request(
                method="GET",
                path=f"/api/v3/quotes/{quote_id}",
                headers={"Authorization": "Bearer test-token-12345"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_quote_consumer:
            response = requests.get(
                f"{pact_quote_consumer.uri}/api/v3/quotes/{quote_id}",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            assert response.json()["quote_id"] == quote_id
    
    def test_get_quote_not_found(self, pact_quote_consumer, mock_auth_header):
        """
        Contract: 404 response when quote not found.
        """
        try:
            from pact import Like
        except ImportError:
            pytest.skip("pact-python not installed")
        
        quote_id = "qt_nonexistent"
        
        (pact_quote_consumer
            .given(f"quote {quote_id} does not exist")
            .upon_receiving("a request for non-existent quote")
            .with_request(
                method="GET",
                path=f"/api/v3/quotes/{quote_id}",
                headers={"Authorization": "Bearer test-token-12345"}
            )
            .will_respond_with(
                status=404,
                headers={"Content-Type": "application/json"},
                body={
                    "error": "not_found",
                    "message": Like("Quote not found"),
                    "detail": {
                        "resource_type": "Quote",
                        "resource_id": quote_id
                    }
                }
            ))
        
        with pact_quote_consumer:
            response = requests.get(
                f"{pact_quote_consumer.uri}/api/v3/quotes/{quote_id}",
                headers=mock_auth_header
            )
            
            assert response.status_code == 404
    
    def test_accept_quote(self, pact_quote_consumer, mock_auth_header):
        """
        Contract: Consumer can accept a quote to create a policy.
        """
        try:
            from pact import Like, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        quote_id = "qt_abc123"
        
        expected_response = {
            "quote_id": quote_id,
            "status": "ACCEPTED",
            "policy": {
                "policy_id": Like("pol_xyz789"),
                "policy_number": Like("POL-2026-0001"),
                "status": "ACTIVE",
                "effective_from": Term(r"\d{4}-\d{2}-\d{2}", "2026-02-15"),
                "effective_to": Term(r"\d{4}-\d{2}-\d{2}", "2026-03-15")
            }
        }
        
        (pact_quote_consumer
            .given(f"quote {quote_id} is pending and valid")
            .upon_receiving("a request to accept a quote")
            .with_request(
                method="POST",
                path=f"/api/v3/quotes/{quote_id}/accept",
                headers={"Authorization": "Bearer test-token-12345"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_quote_consumer:
            response = requests.post(
                f"{pact_quote_consumer.uri}/api/v3/quotes/{quote_id}/accept",
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "ACCEPTED"
            assert "policy" in response.json()
    
    def test_list_quotes(self, pact_quote_consumer, mock_auth_header):
        """
        Contract: Consumer can list quotes with pagination.
        """
        try:
            from pact import Like, EachLike, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        expected_response = {
            "items": EachLike({
                "quote_id": Like("qt_abc123"),
                "quote_number": Like("QT-2026-0001"),
                "status": Like("PENDING"),
                "cargo_type": Like("ELECTRONICS"),
                "cargo_value_usd": Like(500000.00),
                "total_premium_usd": Like(12500.00),
                "created_at": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-01-25T10:00:00")
            }),
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": Like(50),
                "total_pages": Like(3),
                "has_next": Like(True),
                "has_previous": Like(False)
            }
        }
        
        (pact_quote_consumer
            .given("user has quotes")
            .upon_receiving("a request to list quotes")
            .with_request(
                method="GET",
                path="/api/v3/quotes",
                query={"page": "1", "page_size": "20"},
                headers={"Authorization": "Bearer test-token-12345"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_quote_consumer:
            response = requests.get(
                f"{pact_quote_consumer.uri}/api/v3/quotes",
                params={"page": 1, "page_size": 20},
                headers=mock_auth_header
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "pagination" in data
