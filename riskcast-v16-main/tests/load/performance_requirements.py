"""
Performance Requirements and Validation

Define and validate performance SLAs for RiskCast API.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class PerformanceRequirement:
    """Performance requirement definition."""
    endpoint: str
    p50_ms: int  # 50th percentile
    p95_ms: int  # 95th percentile
    p99_ms: int  # 99th percentile
    max_error_rate: float  # Maximum acceptable error rate (0.0-1.0)
    min_rps: float  # Minimum requests per second


# ============================================================================
# Performance SLAs
# ============================================================================

PERFORMANCE_REQUIREMENTS = {
    "quote_request": PerformanceRequirement(
        endpoint="/api/v3/quotes/request",
        p50_ms=500,
        p95_ms=1500,
        p99_ms=3000,
        max_error_rate=0.01,  # 1%
        min_rps=50
    ),
    "risk_assessment": PerformanceRequirement(
        endpoint="/api/v3/risk/assess",
        p50_ms=300,
        p95_ms=800,
        p99_ms=1500,
        max_error_rate=0.01,  # 1%
        min_rps=100
    ),
    "quote_list": PerformanceRequirement(
        endpoint="/api/v3/quotes/",
        p50_ms=100,
        p95_ms=300,
        p99_ms=500,
        max_error_rate=0.005,  # 0.5%
        min_rps=200
    ),
    "quote_get": PerformanceRequirement(
        endpoint="/api/v3/quotes/[id]",
        p50_ms=50,
        p95_ms=150,
        p99_ms=300,
        max_error_rate=0.005,  # 0.5%
        min_rps=300
    ),
    "quote_accept": PerformanceRequirement(
        endpoint="/api/v3/quotes/[id]/accept",
        p50_ms=200,
        p95_ms=500,
        p99_ms=1000,
        max_error_rate=0.01,  # 1%
        min_rps=50
    ),
    "dashboard": PerformanceRequirement(
        endpoint="/api/v3/portal/dashboard",
        p50_ms=200,
        p95_ms=500,
        p99_ms=1000,
        max_error_rate=0.005,  # 0.5%
        min_rps=100
    ),
    "policies_list": PerformanceRequirement(
        endpoint="/api/v3/portal/policies",
        p50_ms=150,
        p95_ms=400,
        p99_ms=800,
        max_error_rate=0.005,  # 0.5%
        min_rps=150
    ),
    "analytics": PerformanceRequirement(
        endpoint="/api/v3/analytics/",
        p50_ms=300,
        p95_ms=800,
        p99_ms=1500,
        max_error_rate=0.01,  # 1%
        min_rps=50
    ),
    "usage": PerformanceRequirement(
        endpoint="/api/v3/usage/current",
        p50_ms=100,
        p95_ms=250,
        p99_ms=500,
        max_error_rate=0.005,  # 0.5%
        min_rps=200
    ),
    "health_check": PerformanceRequirement(
        endpoint="/health/live",
        p50_ms=10,
        p95_ms=50,
        p99_ms=100,
        max_error_rate=0.001,  # 0.1%
        min_rps=1000
    )
}


# ============================================================================
# Validation Functions
# ============================================================================

def validate_results(results: Dict) -> List[str]:
    """
    Validate load test results against performance requirements.
    
    Args:
        results: Dictionary with endpoint stats
            {
                "endpoint_name": {
                    "p50": 250,
                    "p95": 600,
                    "p99": 1200,
                    "error_rate": 0.005,
                    "rps": 120
                }
            }
    
    Returns:
        List of violation messages (empty if all pass)
    """
    violations = []
    
    for name, req in PERFORMANCE_REQUIREMENTS.items():
        if name not in results:
            continue
        
        result = results[name]
        
        # Check p50
        if result.get("p50", 0) > req.p50_ms:
            violations.append(
                f"❌ {name}: p50 {result['p50']:.0f}ms exceeds limit {req.p50_ms}ms"
            )
        
        # Check p95
        if result.get("p95", 0) > req.p95_ms:
            violations.append(
                f"❌ {name}: p95 {result['p95']:.0f}ms exceeds limit {req.p95_ms}ms"
            )
        
        # Check p99
        if result.get("p99", 0) > req.p99_ms:
            violations.append(
                f"❌ {name}: p99 {result['p99']:.0f}ms exceeds limit {req.p99_ms}ms"
            )
        
        # Check error rate
        if result.get("error_rate", 0) > req.max_error_rate:
            violations.append(
                f"❌ {name}: error rate {result['error_rate']:.2%} exceeds limit {req.max_error_rate:.2%}"
            )
        
        # Check RPS
        if result.get("rps", 0) < req.min_rps:
            violations.append(
                f"❌ {name}: RPS {result['rps']:.1f} below minimum {req.min_rps}"
            )
    
    return violations


def parse_locust_stats(stats_file: Path) -> Dict:
    """
    Parse Locust stats CSV file into results dictionary.
    
    Args:
        stats_file: Path to _stats.csv file from Locust
    
    Returns:
        Dictionary with parsed results
    """
    results = {}
    
    try:
        with open(stats_file, 'r') as f:
            lines = f.readlines()
            
            # Skip header
            for line in lines[1:]:
                parts = line.strip().split(',')
                if len(parts) < 10 or parts[0] == "Aggregated":
                    continue
                
                endpoint = parts[1].strip('"')
                num_requests = int(parts[2])
                num_failures = int(parts[3])
                median = float(parts[4])
                p95 = float(parts[7])
                p99 = float(parts[8])
                avg = float(parts[5])
                rps = float(parts[10]) if len(parts) > 10 else 0
                
                error_rate = num_failures / num_requests if num_requests > 0 else 0
                
                # Map endpoint to requirement key
                req_key = _map_endpoint_to_key(endpoint)
                
                results[req_key] = {
                    "endpoint": endpoint,
                    "p50": median,
                    "p95": p95,
                    "p99": p99,
                    "avg": avg,
                    "error_rate": error_rate,
                    "rps": rps,
                    "num_requests": num_requests,
                    "num_failures": num_failures
                }
    
    except Exception as e:
        print(f"Error parsing stats file: {e}")
    
    return results


def _map_endpoint_to_key(endpoint: str) -> str:
    """Map endpoint path to requirement key."""
    mapping = {
        "/api/v3/quotes/request": "quote_request",
        "/api/v3/risk/assess": "risk_assessment",
        "/api/v3/quotes/": "quote_list",
        "/api/v3/quotes/ [LIST]": "quote_list",
        "/api/v3/quotes/[id]": "quote_get",
        "/api/v3/quotes/[id] [GET]": "quote_get",
        "/api/v3/quotes/[id]/accept": "quote_accept",
        "/api/v3/portal/dashboard": "dashboard",
        "/api/v3/portal/policies": "policies_list",
        "/api/v3/analytics/": "analytics",
        "/api/v3/usage/current": "usage",
        "/health/live": "health_check"
    }
    
    for pattern, key in mapping.items():
        if pattern in endpoint:
            return key
    
    return endpoint


def generate_report(results: Dict, violations: List[str]) -> str:
    """
    Generate a performance validation report.
    
    Args:
        results: Parsed test results
        violations: List of SLA violations
    
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 80)
    report.append("PERFORMANCE VALIDATION REPORT")
    report.append("=" * 80)
    report.append("")
    
    if not violations:
        report.append("✅ ALL PERFORMANCE REQUIREMENTS MET")
    else:
        report.append(f"❌ {len(violations)} PERFORMANCE VIOLATIONS DETECTED")
    
    report.append("")
    report.append("=" * 80)
    report.append("DETAILED RESULTS")
    report.append("=" * 80)
    report.append("")
    
    for name, req in PERFORMANCE_REQUIREMENTS.items():
        if name not in results:
            continue
        
        result = results[name]
        report.append(f"Endpoint: {req.endpoint}")
        report.append(f"  Requirements:")
        report.append(f"    p50 ≤ {req.p50_ms}ms | p95 ≤ {req.p95_ms}ms | p99 ≤ {req.p99_ms}ms")
        report.append(f"    Error Rate ≤ {req.max_error_rate:.2%} | RPS ≥ {req.min_rps}")
        report.append(f"  Actual:")
        report.append(f"    p50: {result['p50']:.0f}ms {_status(result['p50'], req.p50_ms)}")
        report.append(f"    p95: {result['p95']:.0f}ms {_status(result['p95'], req.p95_ms)}")
        report.append(f"    p99: {result['p99']:.0f}ms {_status(result['p99'], req.p99_ms)}")
        report.append(f"    Error Rate: {result['error_rate']:.2%} {_status(result['error_rate'], req.max_error_rate, reverse=True)}")
        report.append(f"    RPS: {result['rps']:.1f} {_status(result['rps'], req.min_rps, is_min=True)}")
        report.append(f"    Requests: {result['num_requests']} | Failures: {result['num_failures']}")
        report.append("")
    
    if violations:
        report.append("=" * 80)
        report.append("VIOLATIONS")
        report.append("=" * 80)
        report.append("")
        for violation in violations:
            report.append(violation)
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def _status(actual: float, requirement: float, reverse: bool = False, is_min: bool = False) -> str:
    """Get status indicator for metric."""
    if is_min:
        return "✅" if actual >= requirement else "❌"
    elif reverse:
        return "✅" if actual <= requirement else "❌"
    else:
        return "✅" if actual <= requirement else "❌"


def validate_load_test(stats_csv_path: str, output_path: Optional[str] = None):
    """
    Validate load test results from Locust CSV output.
    
    Args:
        stats_csv_path: Path to Locust _stats.csv file
        output_path: Optional path to save report
    """
    print(f"Parsing results from: {stats_csv_path}")
    
    # Parse results
    results = parse_locust_stats(Path(stats_csv_path))
    
    if not results:
        print("❌ No results found in stats file")
        return
    
    print(f"Found {len(results)} endpoints in results")
    
    # Validate
    violations = validate_results(results)
    
    # Generate report
    report = generate_report(results, violations)
    
    # Print report
    print("\n" + report)
    
    # Save report if output path specified
    if output_path:
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {output_path}")
    
    # Exit with appropriate code
    if violations:
        print(f"\n❌ Performance validation failed with {len(violations)} violations")
        return False
    else:
        print("\n✅ Performance validation passed")
        return True


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python performance_requirements.py <stats_csv_path> [output_report_path]")
        print("\nExample:")
        print("  python tests/load/performance_requirements.py reports/load_tests/test_stats.csv")
        sys.exit(1)
    
    stats_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = validate_load_test(stats_path, output_path)
    sys.exit(0 if success else 1)
