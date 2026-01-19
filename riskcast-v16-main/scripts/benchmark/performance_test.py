#!/usr/bin/env python3
"""
Performance benchmarking for RISKCAST v17.

This script measures:
- API response times (latency)
- Throughput under load
- Concurrent request handling
- Memory usage (optional)

Usage:
    python scripts/benchmark/performance_test.py
    python scripts/benchmark/performance_test.py --url http://localhost:8000
    python scripts/benchmark/performance_test.py --concurrent 20 --requests 200
"""

import time
import statistics
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' library not installed. Install with: pip install requests")


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class BenchmarkConfig:
    """Configuration for benchmark run."""
    base_url: str = "http://localhost:8000"
    sequential_requests: int = 100
    concurrent_requests: int = 50
    concurrent_workers: int = 10
    timeout: int = 30
    warmup_requests: int = 5


DEFAULT_CONFIG = BenchmarkConfig()


# ============================================================
# TEST PAYLOADS
# ============================================================

def get_risk_analysis_payload() -> dict:
    """Get sample payload for risk analysis."""
    return {
        "origin_port": "CNSHA",
        "destination_port": "USLAX",
        "cargo_value": 100000,
        "cargo_type": "electronics_high_value",
        "transport_mode": "ocean_fcl",
        "departure_date": "2026-02-15",
        "priority": "high",
        "packaging": "good",
        "container": "40hc"
    }


def get_health_check_payload() -> None:
    """Health check doesn't need payload."""
    return None


# ============================================================
# BENCHMARK FUNCTIONS
# ============================================================

def make_request(
    url: str,
    method: str = "GET",
    payload: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = 30
) -> Tuple[int, float, Optional[str]]:
    """
    Make HTTP request and measure latency.
    
    Returns:
        (status_code, latency_ms, error_message)
    """
    if not REQUESTS_AVAILABLE:
        return (0, 0, "requests library not available")
    
    start = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        else:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
        
        latency = (time.time() - start) * 1000  # Convert to ms
        return (response.status_code, latency, None)
        
    except requests.Timeout:
        latency = (time.time() - start) * 1000
        return (0, latency, "timeout")
    except requests.ConnectionError:
        latency = (time.time() - start) * 1000
        return (0, latency, "connection_error")
    except Exception as e:
        latency = (time.time() - start) * 1000
        return (0, latency, str(e))


def benchmark_sequential(
    url: str,
    method: str = "GET",
    payload: Optional[dict] = None,
    n_requests: int = 100,
    warmup: int = 5
) -> Dict:
    """
    Run sequential requests and measure latency.
    
    Returns:
        Statistics dictionary
    """
    print(f"\n🏃 Running {n_requests} sequential requests to {url}")
    print(f"   (warmup: {warmup} requests)")
    
    # Warmup
    for _ in range(warmup):
        make_request(url, method, payload)
    
    latencies = []
    errors = []
    status_codes = []
    
    for i in range(n_requests):
        status, latency, error = make_request(url, method, payload)
        
        latencies.append(latency)
        status_codes.append(status)
        
        if error:
            errors.append(error)
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"   Progress: {i + 1}/{n_requests}")
    
    return calculate_stats(latencies, status_codes, errors)


def benchmark_concurrent(
    url: str,
    method: str = "GET",
    payload: Optional[dict] = None,
    n_requests: int = 50,
    n_workers: int = 10
) -> Dict:
    """
    Run concurrent requests and measure throughput.
    
    Returns:
        Statistics dictionary with throughput
    """
    print(f"\n🔀 Running {n_requests} requests with {n_workers} concurrent workers")
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [
            executor.submit(make_request, url, method, payload)
            for _ in range(n_requests)
        ]
        
        for future in as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_time
    
    latencies = [r[1] for r in results]
    status_codes = [r[0] for r in results]
    errors = [r[2] for r in results if r[2]]
    
    stats = calculate_stats(latencies, status_codes, errors)
    stats['total_time_s'] = round(total_time, 3)
    stats['throughput_rps'] = round(n_requests / total_time, 2)
    stats['concurrent_workers'] = n_workers
    
    return stats


def calculate_stats(
    latencies: List[float],
    status_codes: List[int],
    errors: List[str]
) -> Dict:
    """Calculate statistics from benchmark results."""
    if not latencies:
        return {'error': 'No data collected'}
    
    sorted_latencies = sorted(latencies)
    
    # Calculate percentiles
    def percentile(data: List[float], p: int) -> float:
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (k - f) * (data[c] - data[f]) if f != c else data[f]
    
    success_count = sum(1 for s in status_codes if 200 <= s < 300)
    error_count = len(errors)
    
    return {
        'total_requests': len(latencies),
        'successful': success_count,
        'failed': len(latencies) - success_count,
        'error_count': error_count,
        'success_rate': round(success_count / len(latencies) * 100, 2),
        
        'latency_ms': {
            'mean': round(statistics.mean(latencies), 2),
            'median': round(statistics.median(latencies), 2),
            'std_dev': round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0,
            'min': round(min(latencies), 2),
            'max': round(max(latencies), 2),
            'p50': round(percentile(sorted_latencies, 50), 2),
            'p75': round(percentile(sorted_latencies, 75), 2),
            'p90': round(percentile(sorted_latencies, 90), 2),
            'p95': round(percentile(sorted_latencies, 95), 2),
            'p99': round(percentile(sorted_latencies, 99), 2),
        },
        
        'status_codes': dict(sorted(
            {str(k): v for k, v in 
             {s: status_codes.count(s) for s in set(status_codes)}.items()
            }.items()
        ))
    }


# ============================================================
# BENCHMARK SUITE
# ============================================================

def run_full_benchmark(config: BenchmarkConfig = DEFAULT_CONFIG) -> Dict:
    """
    Run complete benchmark suite.
    
    Tests:
    1. Health check endpoint
    2. Risk analysis endpoint (sequential)
    3. Risk analysis endpoint (concurrent)
    """
    print("=" * 70)
    print("🚀 RISKCAST v17 Performance Benchmark")
    print("=" * 70)
    print(f"Target: {config.base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {}
    
    # 1. Health Check
    print("\n📊 Benchmark 1: Health Check Endpoint")
    print("-" * 40)
    
    health_url = f"{config.base_url}/health"
    health_results = benchmark_sequential(
        health_url,
        method="GET",
        n_requests=50,
        warmup=3
    )
    results['health_check'] = health_results
    print_stats(health_results, "Health Check")
    
    # 2. Risk Analysis - Sequential
    print("\n📊 Benchmark 2: Risk Analysis (Sequential)")
    print("-" * 40)
    
    analyze_url = f"{config.base_url}/api/v1/risk/v2/analyze"
    payload = get_risk_analysis_payload()
    
    sequential_results = benchmark_sequential(
        analyze_url,
        method="POST",
        payload=payload,
        n_requests=config.sequential_requests,
        warmup=config.warmup_requests
    )
    results['risk_analysis_sequential'] = sequential_results
    print_stats(sequential_results, "Risk Analysis (Sequential)")
    
    # 3. Risk Analysis - Concurrent
    print("\n📊 Benchmark 3: Risk Analysis (Concurrent)")
    print("-" * 40)
    
    concurrent_results = benchmark_concurrent(
        analyze_url,
        method="POST",
        payload=payload,
        n_requests=config.concurrent_requests,
        n_workers=config.concurrent_workers
    )
    results['risk_analysis_concurrent'] = concurrent_results
    print_stats(concurrent_results, "Risk Analysis (Concurrent)")
    
    # Summary
    print_summary(results, config)
    
    return results


def print_stats(stats: Dict, name: str):
    """Print statistics in formatted way."""
    print(f"\n   📈 {name} Results:")
    print(f"   {'─' * 35}")
    
    if 'error' in stats:
        print(f"   ❌ Error: {stats['error']}")
        return
    
    latency = stats.get('latency_ms', {})
    
    print(f"   Requests:  {stats.get('total_requests', 0)}")
    print(f"   Success:   {stats.get('success_rate', 0):.1f}%")
    print(f"   Mean:      {latency.get('mean', 0):.2f} ms")
    print(f"   Median:    {latency.get('median', 0):.2f} ms")
    print(f"   P95:       {latency.get('p95', 0):.2f} ms")
    print(f"   P99:       {latency.get('p99', 0):.2f} ms")
    print(f"   Min:       {latency.get('min', 0):.2f} ms")
    print(f"   Max:       {latency.get('max', 0):.2f} ms")
    
    if 'throughput_rps' in stats:
        print(f"   Throughput: {stats['throughput_rps']} req/s")


def print_summary(results: Dict, config: BenchmarkConfig):
    """Print benchmark summary with pass/fail status."""
    print("\n" + "=" * 70)
    print("📋 BENCHMARK SUMMARY")
    print("=" * 70)
    
    # Define targets
    targets = {
        'health_check': {'p95': 100, 'p99': 200},
        'risk_analysis_sequential': {'p95': 500, 'p99': 1000},
        'risk_analysis_concurrent': {'p95': 1000, 'p99': 2000},
    }
    
    all_passed = True
    
    for test_name, stats in results.items():
        if 'error' in stats:
            print(f"\n❌ {test_name}: ERROR")
            all_passed = False
            continue
        
        target = targets.get(test_name, {})
        latency = stats.get('latency_ms', {})
        
        p95_pass = latency.get('p95', 0) <= target.get('p95', float('inf'))
        p99_pass = latency.get('p99', 0) <= target.get('p99', float('inf'))
        success_pass = stats.get('success_rate', 0) >= 95
        
        status = "✅ PASS" if (p95_pass and p99_pass and success_pass) else "❌ FAIL"
        
        if status == "❌ FAIL":
            all_passed = False
        
        print(f"\n{status} {test_name}")
        print(f"   P95: {latency.get('p95', 0):.0f}ms (target: {target.get('p95', 'N/A')}ms)")
        print(f"   P99: {latency.get('p99', 0):.0f}ms (target: {target.get('p99', 'N/A')}ms)")
        print(f"   Success Rate: {stats.get('success_rate', 0):.1f}%")
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("🎉 ALL BENCHMARKS PASSED!")
    else:
        print("⚠️ SOME BENCHMARKS FAILED - Review results above")
    
    print("=" * 70)


# ============================================================
# CLI
# ============================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RISKCAST v17 Performance Benchmark"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the server (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--sequential", "-s",
        type=int,
        default=100,
        help="Number of sequential requests (default: 100)"
    )
    
    parser.add_argument(
        "--concurrent", "-c",
        type=int,
        default=50,
        help="Number of concurrent requests (default: 50)"
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=10,
        help="Number of concurrent workers (default: 10)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file for JSON results"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (fewer requests)"
    )
    
    args = parser.parse_args()
    
    if not REQUESTS_AVAILABLE:
        print("Error: 'requests' library is required")
        print("Install with: pip install requests")
        sys.exit(1)
    
    # Configure
    config = BenchmarkConfig(
        base_url=args.url,
        sequential_requests=args.sequential if not args.quick else 20,
        concurrent_requests=args.concurrent if not args.quick else 20,
        concurrent_workers=args.workers
    )
    
    # Run benchmark
    try:
        results = run_full_benchmark(config)
        
        # Save results if output specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to: {args.output}")
        
    except requests.ConnectionError:
        print(f"\n❌ Error: Cannot connect to {config.base_url}")
        print("   Make sure the server is running")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Benchmark interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
