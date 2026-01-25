"""
Performance Validation

Validates performance test results against SLAs.

Usage:
    python tests/load/validate_performance.py
    
Expects Locust CSV output at: performance_stats.csv
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List

try:
    from tests.load.performance_requirements import (
        PERFORMANCE_REQUIREMENTS,
        validate_results
    )
except ImportError:
    # Fallback if performance_requirements not available
    PERFORMANCE_REQUIREMENTS = {
        "quote_request": {"p50": 200, "p95": 500, "p99": 1000, "error_rate": 0.01},
        "risk_assessment": {"p50": 300, "p95": 800, "p99": 1500, "error_rate": 0.01},
        "quote_list": {"p50": 100, "p95": 300, "p99": 600, "error_rate": 0.005},
        "dashboard": {"p50": 150, "p95": 400, "p99": 800, "error_rate": 0.005},
        "health_check": {"p50": 50, "p95": 100, "p99": 200, "error_rate": 0.001}
    }
    
    def validate_results(results: dict) -> List[str]:
        """Validate performance results against SLAs."""
        violations = []
        
        for endpoint, requirements in PERFORMANCE_REQUIREMENTS.items():
            if endpoint not in results:
                violations.append(f"{endpoint}: No results found")
                continue
            
            actual = results[endpoint]
            
            # Check P50
            if actual.get("p50", float('inf')) > requirements["p50"]:
                violations.append(
                    f"{endpoint} P50: {actual['p50']:.0f}ms > {requirements['p50']}ms"
                )
            
            # Check P95
            if actual.get("p95", float('inf')) > requirements["p95"]:
                violations.append(
                    f"{endpoint} P95: {actual['p95']:.0f}ms > {requirements['p95']}ms"
                )
            
            # Check P99
            if actual.get("p99", float('inf')) > requirements["p99"]:
                violations.append(
                    f"{endpoint} P99: {actual['p99']:.0f}ms > {requirements['p99']}ms"
                )
            
            # Check error rate
            if actual.get("error_rate", 1.0) > requirements["error_rate"]:
                violations.append(
                    f"{endpoint} Error Rate: {actual['error_rate']:.2%} > {requirements['error_rate']:.2%}"
                )
        
        return violations


def parse_locust_csv(csv_path: str) -> Dict[str, dict]:
    """Parse Locust CSV results."""
    results = {}
    
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "")
            
            # Skip aggregated rows
            if name.lower() in ["aggregated", "total", ""]:
                continue
            
            # Map endpoint names to our performance requirements keys
            endpoint_key = map_endpoint_name(name, row.get("Type", ""))
            
            if endpoint_key:
                try:
                    results[endpoint_key] = {
                        "p50": float(row.get("50%", row.get("Median Response Time", 0))),
                        "p95": float(row.get("95%", row.get("95%ile Response Time", 0))),
                        "p99": float(row.get("99%", row.get("99%ile Response Time", 0))),
                        "error_rate": calculate_error_rate(row),
                        "rps": float(row.get("Requests/s", row.get("RPS", 0))),
                        "total_requests": int(row.get("Request Count", row.get("# Requests", 0)))
                    }
                except (ValueError, KeyError) as e:
                    print(f"Warning: Could not parse row for {name}: {e}")
    
    return results


def map_endpoint_name(name: str, method: str) -> str:
    """Map Locust endpoint name to performance requirement key."""
    name_lower = name.lower()
    method_upper = method.upper()
    
    # Quote endpoints
    if "quote" in name_lower and ("request" in name_lower or method_upper == "POST"):
        return "quote_request"
    elif "quote" in name_lower and ("list" in name_lower or method_upper == "GET"):
        return "quote_list"
    
    # Risk endpoints
    if "risk" in name_lower and "assess" in name_lower:
        return "risk_assessment"
    
    # Dashboard
    if "dashboard" in name_lower:
        return "dashboard"
    
    # Health check
    if "health" in name_lower:
        return "health_check"
    
    return None


def calculate_error_rate(row: dict) -> float:
    """Calculate error rate from Locust CSV row."""
    try:
        failures = float(row.get("Failure Count", row.get("# Failures", 0)))
        total = float(row.get("Request Count", row.get("# Requests", 1)))
        return failures / total if total > 0 else 0
    except (ValueError, ZeroDivisionError):
        return 0


def print_results_table(results: Dict[str, dict]):
    """Print performance results in a table format."""
    print("\n" + "=" * 100)
    print("PERFORMANCE TEST RESULTS")
    print("=" * 100)
    print(f"\n{'Endpoint':<20} {'P50':<10} {'P95':<10} {'P99':<10} {'Error Rate':<12} {'RPS':<10}")
    print("-" * 100)
    
    for endpoint, metrics in results.items():
        print(
            f"{endpoint:<20} "
            f"{metrics['p50']:>7.0f}ms "
            f"{metrics['p95']:>7.0f}ms "
            f"{metrics['p99']:>7.0f}ms "
            f"{metrics['error_rate']:>10.2%} "
            f"{metrics['rps']:>8.1f}"
        )
    
    print("=" * 100)


def print_sla_comparison(results: Dict[str, dict]):
    """Print SLA comparison."""
    print("\n" + "=" * 100)
    print("SLA COMPARISON")
    print("=" * 100)
    
    for endpoint, requirements in PERFORMANCE_REQUIREMENTS.items():
        if endpoint not in results:
            print(f"\n❌ {endpoint}: NO DATA")
            continue
        
        actual = results[endpoint]
        
        print(f"\n{'='*20} {endpoint.upper()} {'='*20}")
        
        # P50
        p50_status = "✅" if actual["p50"] <= requirements["p50"] else "❌"
        print(f"  P50: {actual['p50']:>7.0f}ms / {requirements['p50']:>7.0f}ms {p50_status}")
        
        # P95
        p95_status = "✅" if actual["p95"] <= requirements["p95"] else "❌"
        print(f"  P95: {actual['p95']:>7.0f}ms / {requirements['p95']:>7.0f}ms {p95_status}")
        
        # P99
        p99_status = "✅" if actual["p99"] <= requirements["p99"] else "❌"
        print(f"  P99: {actual['p99']:>7.0f}ms / {requirements['p99']:>7.0f}ms {p99_status}")
        
        # Error rate
        error_status = "✅" if actual["error_rate"] <= requirements["error_rate"] else "❌"
        print(f"  Error Rate: {actual['error_rate']:>6.2%} / {requirements['error_rate']:>6.2%} {error_status}")
    
    print("\n" + "=" * 100)


def main():
    """Main validation function."""
    print("\n🚀 Starting Performance Validation...")
    
    csv_path = Path("performance_stats.csv")
    
    if not csv_path.exists():
        print(f"❌ ERROR: Performance results not found at {csv_path}")
        print("\nExpected Locust CSV output file.")
        sys.exit(1)
    
    print(f"📊 Reading results from: {csv_path}")
    
    try:
        results = parse_locust_csv(str(csv_path))
    except Exception as e:
        print(f"❌ ERROR: Failed to parse performance results: {e}")
        sys.exit(1)
    
    if not results:
        print("❌ ERROR: No valid performance results found in CSV")
        sys.exit(1)
    
    print(f"✅ Found results for {len(results)} endpoints")
    
    # Print results
    print_results_table(results)
    print_sla_comparison(results)
    
    # Validate against SLAs
    print("\n🔍 Validating against SLAs...")
    violations = validate_results(results)
    
    if violations:
        print("\n❌ PERFORMANCE VALIDATION FAILED")
        print("\n⚠️  SLA Violations:")
        for violation in violations:
            print(f"  - {violation}")
        print("")
        sys.exit(1)
    else:
        print("\n✅ PERFORMANCE VALIDATION PASSED")
        print("\n🎉 All endpoints meet SLA requirements!")
        print("")
        sys.exit(0)


if __name__ == "__main__":
    main()
