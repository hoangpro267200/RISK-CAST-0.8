"""
Load Test Runner with Different Scenarios

Run load tests with predefined scenarios and configurations.
"""

import subprocess
import sys
import argparse
import os
from datetime import datetime
from pathlib import Path


def ensure_reports_dir():
    """Ensure reports directory exists."""
    reports_dir = Path("reports/load_tests")
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def run_scenario(
    scenario: str,
    users: int,
    spawn_rate: int,
    duration: str,
    host: str,
    tags: str = None
):
    """Run a specific load test scenario."""
    
    # Map scenarios to user classes
    user_classes = {
        "quotes": "QuoteLoadUser",
        "risk": "RiskAssessmentUser",
        "mixed": "MixedWorkloadUser",
        "spike": "SpikeTestUser",
        "endurance": "EnduranceTestUser"
    }
    
    user_class = user_classes.get(scenario, "MixedWorkloadUser")
    
    # Ensure reports directory
    reports_dir = ensure_reports_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"load_test_{scenario}_{timestamp}"
    
    cmd = [
        "locust",
        "-f", "tests/load/locustfile.py",
        user_class,
        "--host", host,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", duration,
        "--headless",
        "--html", str(reports_dir / f"{report_name}.html"),
        "--csv", str(reports_dir / report_name)
    ]
    
    # Add tags if specified
    if tags:
        cmd.extend(["--tags", tags])
    
    print("=" * 80)
    print(f"Running {scenario.upper()} scenario")
    print(f"Users: {users} | Spawn Rate: {spawn_rate}/s | Duration: {duration}")
    print(f"Host: {host}")
    if tags:
        print(f"Tags: {tags}")
    print(f"Report: {report_name}")
    print("=" * 80)
    print(f"\nCommand: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ Test completed successfully")
        print(f"Report saved to: {reports_dir / report_name}.html")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False


def run_quick_test(host: str):
    """Run a quick smoke test."""
    print("\n🔥 Running QUICK SMOKE TEST")
    return run_scenario(
        scenario="mixed",
        users=10,
        spawn_rate=5,
        duration="1m",
        host=host
    )


def run_baseline_test(host: str):
    """Run baseline performance test."""
    print("\n📊 Running BASELINE PERFORMANCE TEST")
    return run_scenario(
        scenario="mixed",
        users=50,
        spawn_rate=10,
        duration="5m",
        host=host
    )


def run_stress_test(host: str):
    """Run stress test with high load."""
    print("\n💪 Running STRESS TEST")
    return run_scenario(
        scenario="mixed",
        users=200,
        spawn_rate=20,
        duration="10m",
        host=host
    )


def run_spike_test(host: str):
    """Run spike test."""
    print("\n⚡ Running SPIKE TEST")
    return run_scenario(
        scenario="spike",
        users=500,
        spawn_rate=100,
        duration="2m",
        host=host
    )


def run_endurance_test(host: str):
    """Run endurance/soak test."""
    print("\n⏰ Running ENDURANCE TEST (Long Duration)")
    return run_scenario(
        scenario="endurance",
        users=100,
        spawn_rate=10,
        duration="1h",
        host=host
    )


def run_all_scenarios(host: str):
    """Run all test scenarios."""
    print("\n🚀 Running ALL TEST SCENARIOS\n")
    
    scenarios = [
        ("Quick Smoke Test", lambda: run_quick_test(host)),
        ("Baseline Performance", lambda: run_baseline_test(host)),
        ("Quote Load Test", lambda: run_scenario("quotes", 50, 10, "5m", host)),
        ("Risk Assessment Load", lambda: run_scenario("risk", 100, 20, "5m", host)),
        ("Stress Test", lambda: run_stress_test(host)),
        ("Spike Test", lambda: run_spike_test(host))
    ]
    
    results = {}
    for name, test_func in scenarios:
        print(f"\n{'=' * 80}")
        print(f"Starting: {name}")
        print('=' * 80)
        
        success = test_func()
        results[name] = "✅ PASSED" if success else "❌ FAILED"
        
        if not success:
            print(f"\n⚠️  {name} failed, continuing with next test...")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUITE SUMMARY")
    print("=" * 80)
    for name, result in results.items():
        print(f"{result} - {name}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Run load tests for RiskCast",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run quick smoke test
  python tests/load/run_load_tests.py --quick
  
  # Run baseline test
  python tests/load/run_load_tests.py --baseline
  
  # Run specific scenario
  python tests/load/run_load_tests.py --scenario quotes --users 100 --duration 10m
  
  # Run stress test
  python tests/load/run_load_tests.py --stress
  
  # Run spike test
  python tests/load/run_load_tests.py --spike
  
  # Run endurance test
  python tests/load/run_load_tests.py --endurance
  
  # Run all scenarios
  python tests/load/run_load_tests.py --all
  
  # Run with specific tags
  python tests/load/run_load_tests.py --scenario mixed --tags "quotes,risk"
        """
    )
    
    # Predefined test types
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--quick",
        action="store_true",
        help="Run quick smoke test (10 users, 1 minute)"
    )
    test_group.add_argument(
        "--baseline",
        action="store_true",
        help="Run baseline performance test (50 users, 5 minutes)"
    )
    test_group.add_argument(
        "--stress",
        action="store_true",
        help="Run stress test (200 users, 10 minutes)"
    )
    test_group.add_argument(
        "--spike",
        action="store_true",
        help="Run spike test (500 users, 2 minutes)"
    )
    test_group.add_argument(
        "--endurance",
        action="store_true",
        help="Run endurance test (100 users, 1 hour)"
    )
    test_group.add_argument(
        "--all",
        action="store_true",
        help="Run all test scenarios sequentially"
    )
    
    # Custom scenario
    parser.add_argument(
        "--scenario",
        choices=["quotes", "risk", "mixed", "spike", "endurance"],
        help="Test scenario to run"
    )
    
    parser.add_argument(
        "--users",
        type=int,
        default=50,
        help="Number of concurrent users (default: 50)"
    )
    
    parser.add_argument(
        "--spawn-rate",
        type=int,
        default=10,
        help="Users spawned per second (default: 10)"
    )
    
    parser.add_argument(
        "--duration",
        default="5m",
        help="Test duration (e.g., 30s, 5m, 1h) (default: 5m)"
    )
    
    parser.add_argument(
        "--host",
        default="http://localhost:8000",
        help="Target host URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--tags",
        help="Filter by tags (comma-separated, e.g., quotes,create)"
    )
    
    args = parser.parse_args()
    
    # Check if locust is installed
    try:
        subprocess.run(["locust", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Locust is not installed")
        print("Install with: pip install locust")
        sys.exit(1)
    
    # Run appropriate test
    if args.quick:
        success = run_quick_test(args.host)
    elif args.baseline:
        success = run_baseline_test(args.host)
    elif args.stress:
        success = run_stress_test(args.host)
    elif args.spike:
        success = run_spike_test(args.host)
    elif args.endurance:
        success = run_endurance_test(args.host)
    elif args.all:
        run_all_scenarios(args.host)
        success = True
    elif args.scenario:
        success = run_scenario(
            args.scenario,
            args.users,
            args.spawn_rate,
            args.duration,
            args.host,
            args.tags
        )
    else:
        print("❌ Error: No test type specified")
        parser.print_help()
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
