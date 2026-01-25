"""
Load Testing with Locust

Scenarios:
1. Quote request load
2. Risk assessment load
3. Mixed workload
4. Spike testing
5. Endurance testing
"""

import json
import random
from datetime import date, timedelta
from locust import HttpUser, task, between, events, tag
from locust.runners import MasterRunner


# ============================================================================
# Test Data
# ============================================================================

PORTS = [
    "CNSHA", "CNNBO", "CNQIN", "HKHKG",  # Asia
    "USLAX", "USNYC", "USOAK", "USSEA",  # US
    "NLRTM", "DEHAM", "GBFXT", "FRLEH",  # Europe
    "SGSIN", "MYPKG", "KRPUS", "JPYOK",  # Asia Pacific
]

CARGO_TYPES = [
    "ELECTRONICS", "MACHINERY", "TEXTILES", "FOOD_PERISHABLE",
    "FOOD_DRY", "CHEMICALS", "PHARMACEUTICALS", "AUTOMOTIVE",
    "RAW_MATERIALS", "GENERAL"
]

CARRIERS = ["MAEU", "MSCU", "CMDU", "COSU", "EGLV", "HLCU", "ONEY", "YMLU"]


def generate_quote_request():
    """Generate random quote request payload."""
    origin = random.choice(PORTS)
    destination = random.choice([p for p in PORTS if p != origin])
    
    return {
        "origin_port": origin,
        "destination_port": destination,
        "cargo_type": random.choice(CARGO_TYPES),
        "cargo_value_usd": random.randint(50000, 2000000),
        "container_count": random.randint(1, 10),
        "departure_date": (date.today() + timedelta(days=random.randint(7, 30))).isoformat(),
        "arrival_date": (date.today() + timedelta(days=random.randint(35, 60))).isoformat(),
        "coverage_type": random.choice(["ALL_RISKS", "NAMED_PERILS", "TOTAL_LOSS_ONLY"]),
        "carrier_code": random.choice(CARRIERS) if random.random() > 0.3 else None
    }


def generate_risk_assessment_request():
    """Generate random risk assessment payload."""
    origin = random.choice(PORTS)
    destination = random.choice([p for p in PORTS if p != origin])
    
    return {
        "origin_port": origin,
        "destination_port": destination,
        "cargo_type": random.choice(CARGO_TYPES),
        "cargo_value_usd": random.randint(50000, 2000000),
        "departure_date": (date.today() + timedelta(days=random.randint(7, 30))).isoformat(),
        "carrier_code": random.choice(CARRIERS) if random.random() > 0.5 else None
    }


# ============================================================================
# Base User Class
# ============================================================================

class RiskcastUser(HttpUser):
    """Base user class with authentication."""
    
    abstract = True
    
    def on_start(self):
        """Authenticate on start."""
        # Try to login to get token
        try:
            response = self.client.post("/api/v3/auth/login", json={
                "email": f"loadtest_{random.randint(1, 1000)}@test.com",
                "password": "testpassword"
            })
            
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                self.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "X-Tenant-ID": "test-tenant-001"
                }
            else:
                # Use API key fallback
                self.headers = {
                    "X-API-Key": "load-test-api-key",
                    "X-Tenant-ID": "test-tenant-001"
                }
        except Exception as e:
            print(f"Auth failed: {e}, using API key fallback")
            self.headers = {
                "X-API-Key": "load-test-api-key",
                "X-Tenant-ID": "test-tenant-001"
            }


# ============================================================================
# Quote Load Test
# ============================================================================

class QuoteLoadUser(RiskcastUser):
    """User for quote load testing."""
    
    wait_time = between(1, 3)
    
    @task(10)
    @tag("quotes", "create")
    def request_quote(self):
        """Request a new quote."""
        payload = generate_quote_request()
        
        with self.client.post(
            "/api/v3/quotes/request",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/v3/quotes/request"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "quote_id" in data and data.get("total_premium_usd", 0) > 0:
                    response.success()
                    # Store quote ID for other operations
                    self.quote_ids = getattr(self, 'quote_ids', [])
                    self.quote_ids.append(data["quote_id"])
                    if len(self.quote_ids) > 100:
                        self.quote_ids = self.quote_ids[-100:]
                else:
                    response.failure("Invalid quote response")
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Failed with {response.status_code}")
    
    @task(5)
    @tag("quotes", "list")
    def list_quotes(self):
        """List quotes."""
        with self.client.get(
            "/api/v3/quotes/?limit=20",
            headers=self.headers,
            catch_response=True,
            name="/api/v3/quotes/ [LIST]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) or isinstance(data, dict):
                    response.success()
                else:
                    response.failure("Invalid list response")
            else:
                response.failure(f"Failed with {response.status_code}")
    
    @task(3)
    @tag("quotes", "get")
    def get_quote(self):
        """Get quote details."""
        quote_ids = getattr(self, 'quote_ids', [])
        if not quote_ids:
            return
        
        quote_id = random.choice(quote_ids)
        
        with self.client.get(
            f"/api/v3/quotes/{quote_id}",
            headers=self.headers,
            catch_response=True,
            name="/api/v3/quotes/[id] [GET]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Quote may have been cleaned up
            else:
                response.failure(f"Failed with {response.status_code}")
    
    @task(2)
    @tag("quotes", "accept")
    def accept_quote(self):
        """Accept a quote."""
        quote_ids = getattr(self, 'quote_ids', [])
        if not quote_ids:
            return
        
        quote_id = quote_ids.pop(0) if quote_ids else None
        if not quote_id:
            return
        
        with self.client.post(
            f"/api/v3/quotes/{quote_id}/accept",
            json={},
            headers=self.headers,
            catch_response=True,
            name="/api/v3/quotes/[id]/accept"
        ) as response:
            if response.status_code in [200, 400]:  # 400 if already accepted
                response.success()
            else:
                response.failure(f"Failed with {response.status_code}")
    
    @task(1)
    @tag("quotes", "analytics")
    def quote_analytics(self):
        """Get quote analytics."""
        with self.client.get(
            "/api/v3/quotes/analytics/summary",
            headers=self.headers,
            catch_response=True,
            name="/api/v3/quotes/analytics/summary"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with {response.status_code}")


# ============================================================================
# Risk Assessment Load Test
# ============================================================================

class RiskAssessmentUser(RiskcastUser):
    """User for risk assessment load testing."""
    
    wait_time = between(0.5, 2)
    
    @task(10)
    @tag("risk", "assess")
    def assess_risk(self):
        """Run risk assessment."""
        payload = generate_risk_assessment_request()
        
        with self.client.post(
            "/api/v3/risk/assess",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/v3/risk/assess"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "overall_risk_score" in data or "risk_score" in data:
                    score = data.get("overall_risk_score", data.get("risk_score", 0))
                    if 0 <= score <= 1:
                        response.success()
                    else:
                        response.failure(f"Invalid risk score: {score}")
                else:
                    response.failure("Missing risk score")
            else:
                response.failure(f"Failed with {response.status_code}")
    
    @task(3)
    @tag("risk", "history")
    def get_risk_history(self):
        """Get risk assessment history."""
        with self.client.get(
            "/api/v3/risk/history?limit=10",
            headers=self.headers,
            catch_response=True,
            name="/api/v3/risk/history"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with {response.status_code}")
    
    @task(2)
    @tag("risk", "factors")
    def get_risk_factors(self):
        """Get risk factor breakdown."""
        # Use stored assessment ID if available
        assessment_ids = getattr(self, 'assessment_ids', [])
        if assessment_ids:
            assessment_id = random.choice(assessment_ids)
            endpoint = f"/api/v3/risk/{assessment_id}/factors"
        else:
            return
        
        with self.client.get(
            endpoint,
            headers=self.headers,
            catch_response=True,
            name="/api/v3/risk/[id]/factors"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with {response.status_code}")


# ============================================================================
# Mixed Workload Test
# ============================================================================

class MixedWorkloadUser(RiskcastUser):
    """User simulating realistic mixed workload."""
    
    wait_time = between(1, 5)
    
    @task(5)
    @tag("mixed", "quote")
    def request_quote(self):
        """Request a quote."""
        payload = generate_quote_request()
        
        with self.client.post(
            "/api/v3/quotes/request",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/v3/quotes/request"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(3)
    @tag("mixed", "risk")
    def assess_risk(self):
        """Run risk assessment."""
        payload = generate_risk_assessment_request()
        
        with self.client.post(
            "/api/v3/risk/assess",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/v3/risk/assess"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(4)
    @tag("mixed", "dashboard")
    def view_dashboard(self):
        """View customer dashboard."""
        with self.client.get(
            "/api/v3/portal/dashboard",
            headers=self.headers,
            catch_response=True,
            name="/api/v3/portal/dashboard"
        ) as response:
            if response.status_code in [200, 404, 401]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    @tag("mixed", "policies")
    def list_policies(self):
        """List policies."""
        with self.client.get(
            "/api/v3/portal/policies",
            headers=self.headers,
            catch_response=True,
            name="/api/v3/portal/policies"
        ) as response:
            if response.status_code in [200, 404, 401]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(1)
    @tag("mixed", "analytics")
    def view_analytics(self):
        """View analytics."""
        with self.client.get(
            "/api/v3/analytics/competitive/market-position",
            headers=self.headers,
            catch_response=True,
            name="/api/v3/analytics/competitive/market-position"
        ) as response:
            if response.status_code in [200, 404, 401]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    @tag("mixed", "health")
    def health_check(self):
        """Health check."""
        with self.client.get(
            "/health/live",
            catch_response=True,
            name="/health/live"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(1)
    @tag("mixed", "usage")
    def check_usage(self):
        """Check API usage."""
        with self.client.get(
            "/api/v3/usage/current",
            headers=self.headers,
            catch_response=True,
            name="/api/v3/usage/current"
        ) as response:
            if response.status_code in [200, 404, 401]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


# ============================================================================
# Spike Test User
# ============================================================================

class SpikeTestUser(RiskcastUser):
    """User for spike testing - rapid burst of requests."""
    
    wait_time = between(0.1, 0.5)  # Very fast
    
    @task(5)
    @tag("spike", "quote")
    def rapid_quote_request(self):
        """Rapid quote requests."""
        payload = generate_quote_request()
        
        with self.client.post(
            "/api/v3/quotes/request",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/v3/quotes/request [SPIKE]"
        ) as response:
            if response.status_code in [200, 429]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(5)
    @tag("spike", "risk")
    def rapid_risk_assessment(self):
        """Rapid risk assessments."""
        payload = generate_risk_assessment_request()
        
        with self.client.post(
            "/api/v3/risk/assess",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/v3/risk/assess [SPIKE]"
        ) as response:
            if response.status_code in [200, 429]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    @tag("spike", "health")
    def rapid_health_check(self):
        """Rapid health checks."""
        with self.client.get(
            "/health/live",
            catch_response=True,
            name="/health/live [SPIKE]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


# ============================================================================
# Endurance Test User
# ============================================================================

class EnduranceTestUser(RiskcastUser):
    """User for endurance/soak testing - sustained load over time."""
    
    wait_time = between(2, 5)
    
    @task(3)
    @tag("endurance", "quote")
    def sustained_quote_requests(self):
        """Sustained quote requests."""
        payload = generate_quote_request()
        
        with self.client.post(
            "/api/v3/quotes/request",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/v3/quotes/request [ENDURANCE]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(3)
    @tag("endurance", "risk")
    def sustained_risk_assessments(self):
        """Sustained risk assessments."""
        payload = generate_risk_assessment_request()
        
        with self.client.post(
            "/api/v3/risk/assess",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/v3/risk/assess [ENDURANCE]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    @tag("endurance", "list")
    def sustained_list_operations(self):
        """Sustained list operations."""
        with self.client.get(
            "/api/v3/quotes/?limit=20",
            headers=self.headers,
            catch_response=True,
            name="/api/v3/quotes/ [LIST-ENDURANCE]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(1)
    @tag("endurance", "health")
    def sustained_health_checks(self):
        """Sustained health checks."""
        with self.client.get(
            "/health/live",
            catch_response=True,
            name="/health/live [ENDURANCE]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


# ============================================================================
# Event Hooks for Custom Metrics
# ============================================================================

# Track custom metrics
request_counts = {}
error_counts = {}


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track custom metrics."""
    # Track request counts
    request_counts[name] = request_counts.get(name, 0) + 1
    
    # Track errors
    if exception:
        error_counts[name] = error_counts.get(name, 0) + 1
        print(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Setup before test starts."""
    print("=" * 80)
    print("Load test starting...")
    print(f"Host: {environment.host}")
    
    if isinstance(environment.runner, MasterRunner):
        print(f"Running distributed test with {environment.runner.worker_count} workers")
    
    print("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Cleanup after test stops."""
    print("\n" + "=" * 80)
    print("Load test completed")
    
    # Print summary
    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Failures: {stats.total.num_failures}")
    print(f"Failure rate: {stats.total.fail_ratio:.2%}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Median response time: {stats.total.median_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests/s: {stats.total.current_rps:.2f}")
    
    # Top endpoints by request count
    print("\nTop endpoints by request count:")
    sorted_requests = sorted(request_counts.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_requests[:10]:
        print(f"  {name}: {count} requests")
    
    # Endpoints with errors
    if error_counts:
        print("\nEndpoints with errors:")
        for name, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {name}: {count} errors")
    
    print("=" * 80)
