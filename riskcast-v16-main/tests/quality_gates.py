"""
Quality Gate Checks

Validates test results against quality thresholds.

Usage:
    python tests/quality_gates.py \
        --unit-results junit-unit.xml \
        --integration-results junit-integration.xml \
        --security-results junit-security.xml \
        --e2e-results junit-e2e.xml \
        --coverage-report htmlcov/ \
        --bandit-report bandit-report.json
"""

import argparse
import xml.etree.ElementTree as ET
import json
import sys
from dataclasses import dataclass
from typing import List, Optional, Union
from pathlib import Path


@dataclass
class QualityThreshold:
    """Quality threshold configuration."""
    name: str
    threshold: Union[float, str]
    actual: Union[float, str]
    passed: bool
    message: str


class QualityGateChecker:
    """Checks quality gates against thresholds."""
    
    # Quality thresholds
    THRESHOLDS = {
        "unit_test_pass_rate": 1.0,        # 100% pass rate
        "integration_test_pass_rate": 1.0,  # 100% pass rate
        "security_test_pass_rate": 1.0,     # 100% pass rate
        "e2e_test_pass_rate": 1.0,          # 100% pass rate
        "code_coverage": 0.80,              # 80% coverage
        "critical_security_issues": 0,      # No critical issues
        "high_security_issues": 5,          # Max 5 high issues
    }
    
    def __init__(self):
        self.results: List[QualityThreshold] = []
        self.passed = True
    
    def check_junit_results(
        self,
        file_path: str,
        test_type: str
    ) -> QualityThreshold:
        """Check JUnit test results."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Get test counts
            if root.tag == "testsuites":
                total = sum(int(ts.get("tests", 0)) for ts in root.findall("testsuite"))
                failures = sum(int(ts.get("failures", 0)) for ts in root.findall("testsuite"))
                errors = sum(int(ts.get("errors", 0)) for ts in root.findall("testsuite"))
            else:
                total = int(root.get("tests", 0))
                failures = int(root.get("failures", 0))
                errors = int(root.get("errors", 0))
            
            passed = total - failures - errors
            pass_rate = passed / total if total > 0 else 0
            
            threshold_key = f"{test_type}_test_pass_rate"
            threshold = self.THRESHOLDS.get(threshold_key, 1.0)
            
            result = QualityThreshold(
                name=f"{test_type.title()} Test Pass Rate",
                threshold=f"{threshold:.0%}",
                actual=f"{pass_rate:.1%}",
                passed=pass_rate >= threshold,
                message=f"{passed}/{total} tests passed ({pass_rate:.1%})"
            )
            
            if not result.passed:
                self.passed = False
            
            self.results.append(result)
            return result
            
        except FileNotFoundError:
            result = QualityThreshold(
                name=f"{test_type.title()} Test Pass Rate",
                threshold="100%",
                actual="N/A",
                passed=False,
                message=f"Test results file not found: {file_path}"
            )
            self.passed = False
            self.results.append(result)
            return result
        except Exception as e:
            result = QualityThreshold(
                name=f"{test_type.title()} Test Pass Rate",
                threshold="100%",
                actual="Error",
                passed=False,
                message=f"Failed to parse results: {e}"
            )
            self.passed = False
            self.results.append(result)
            return result
    
    def check_coverage(self, coverage_dir: str) -> QualityThreshold:
        """Check code coverage."""
        try:
            coverage_dir_path = Path(coverage_dir)
            
            # Try to read coverage from various sources
            coverage_file = coverage_dir_path / "coverage.json"
            
            if coverage_file.exists():
                with open(coverage_file) as f:
                    data = json.load(f)
                    coverage = data.get("totals", {}).get("percent_covered", 0) / 100
            else:
                # Try to extract from HTML report
                index_file = coverage_dir_path / "index.html"
                if index_file.exists():
                    content = index_file.read_text()
                    # Extract coverage percentage
                    import re
                    match = re.search(r'<span class="pc_cov">(\d+)%</span>', content)
                    if not match:
                        match = re.search(r'(\d+)%', content)
                    coverage = int(match.group(1)) / 100 if match else 0
                else:
                    # Try XML
                    xml_file = coverage_dir_path.parent / "coverage.xml"
                    if xml_file.exists():
                        tree = ET.parse(xml_file)
                        root = tree.getroot()
                        line_rate = float(root.get("line-rate", 0))
                        coverage = line_rate
                    else:
                        coverage = 0
            
            threshold = self.THRESHOLDS["code_coverage"]
            
            result = QualityThreshold(
                name="Code Coverage",
                threshold=f"{threshold:.0%}",
                actual=f"{coverage:.1%}",
                passed=coverage >= threshold,
                message=f"{coverage:.1%} coverage (threshold: {threshold:.0%})"
            )
            
            if not result.passed:
                self.passed = False
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = QualityThreshold(
                name="Code Coverage",
                threshold=f"{self.THRESHOLDS['code_coverage']:.0%}",
                actual="N/A",
                passed=False,
                message=f"Failed to check coverage: {e}"
            )
            self.passed = False
            self.results.append(result)
            return result
    
    def check_security_report(self, bandit_report: str) -> QualityThreshold:
        """Check security scan results."""
        try:
            with open(bandit_report) as f:
                data = json.load(f)
            
            metrics = data.get("metrics", {}).get("_totals", {})
            
            # Count by severity
            high_severity = 0
            critical_severity = 0
            
            # Check results for severity levels
            results = data.get("results", [])
            for issue in results:
                severity = issue.get("issue_severity", "").upper()
                if severity == "HIGH":
                    high_severity += 1
                elif severity == "CRITICAL":
                    critical_severity += 1
            
            # Alternative: check metrics
            if not results:
                for key, value in metrics.items():
                    if "SEVERITY.HIGH" in key.upper():
                        high_severity = value
                    elif "SEVERITY.CRITICAL" in key.upper():
                        critical_severity = value
            
            # Check critical issues
            critical_threshold = self.THRESHOLDS["critical_security_issues"]
            critical_passed = critical_severity <= critical_threshold
            
            # Check high issues
            high_threshold = self.THRESHOLDS["high_security_issues"]
            high_passed = high_severity <= high_threshold
            
            passed = critical_passed and high_passed
            
            result = QualityThreshold(
                name="Security Issues",
                threshold=f"Critical: {critical_threshold}, High: ≤{high_threshold}",
                actual=f"Critical: {critical_severity}, High: {high_severity}",
                passed=passed,
                message=f"{critical_severity} critical, {high_severity} high severity issues found"
            )
            
            if not passed:
                self.passed = False
            
            self.results.append(result)
            return result
            
        except FileNotFoundError:
            # If no security report, consider it passed with warning
            result = QualityThreshold(
                name="Security Issues",
                threshold="0 critical",
                actual="N/A",
                passed=True,
                message="Security report not found - assuming no issues"
            )
            self.results.append(result)
            return result
        except Exception as e:
            result = QualityThreshold(
                name="Security Issues",
                threshold="0 critical",
                actual="Error",
                passed=False,
                message=f"Failed to parse security report: {e}"
            )
            self.passed = False
            self.results.append(result)
            return result
    
    def generate_report(self) -> str:
        """Generate quality gate report."""
        lines = [
            "# 🎯 Quality Gate Results",
            "",
            f"**Overall Status:** {'✅ PASSED' if self.passed else '❌ FAILED'}",
            "",
            "## 📊 Quality Checks",
            "",
            "| Check | Threshold | Actual | Status |",
            "|-------|-----------|--------|--------|"
        ]
        
        for result in self.results:
            status = "✅ Pass" if result.passed else "❌ Fail"
            lines.append(
                f"| {result.name} | {result.threshold} | {result.actual} | {status} |"
            )
        
        lines.extend([
            "",
            "## 📝 Details",
            ""
        ])
        
        for result in self.results:
            emoji = "✅" if result.passed else "❌"
            lines.append(f"{emoji} **{result.name}**: {result.message}")
        
        lines.extend([
            "",
            "---",
            "",
            "### Quality Thresholds",
            "",
            "- **Unit Tests**: 100% pass rate required",
            "- **Integration Tests**: 100% pass rate required",
            "- **Security Tests**: 100% pass rate required",
            "- **E2E Tests**: 100% pass rate required",
            "- **Code Coverage**: ≥80% required",
            "- **Security Issues**: 0 critical, ≤5 high severity",
            ""
        ])
        
        if not self.passed:
            lines.extend([
                "## ⚠️ Action Required",
                "",
                "Quality gate has failed. Please address the issues above before merging.",
                ""
            ])
        else:
            lines.extend([
                "## 🎉 Success",
                "",
                "All quality gates have passed! This PR meets all quality standards.",
                ""
            ])
        
        return "\n".join(lines)
    
    def generate_summary(self) -> str:
        """Generate short summary for console output."""
        lines = [
            "",
            "=" * 80,
            "QUALITY GATE RESULTS",
            "=" * 80,
            ""
        ]
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            lines.append(f"{status} | {result.name}: {result.message}")
        
        lines.extend([
            "",
            "=" * 80,
            f"OVERALL: {'✅ PASSED' if self.passed else '❌ FAILED'}",
            "=" * 80,
            ""
        ])
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check quality gates",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--unit-results", help="Path to unit test JUnit XML")
    parser.add_argument("--integration-results", help="Path to integration test JUnit XML")
    parser.add_argument("--security-results", help="Path to security test JUnit XML")
    parser.add_argument("--e2e-results", help="Path to E2E test JUnit XML")
    parser.add_argument("--coverage-report", help="Path to coverage report directory")
    parser.add_argument("--bandit-report", help="Path to Bandit security report JSON")
    
    args = parser.parse_args()
    
    checker = QualityGateChecker()
    
    print("\n🔍 Running Quality Gate Checks...")
    print("=" * 80)
    
    # Check test results
    if args.unit_results:
        print(f"\n📋 Checking unit tests: {args.unit_results}")
        checker.check_junit_results(args.unit_results, "unit")
    
    if args.integration_results:
        print(f"\n🔗 Checking integration tests: {args.integration_results}")
        checker.check_junit_results(args.integration_results, "integration")
    
    if args.security_results:
        print(f"\n🔒 Checking security tests: {args.security_results}")
        checker.check_junit_results(args.security_results, "security")
    
    if args.e2e_results:
        print(f"\n🎭 Checking E2E tests: {args.e2e_results}")
        checker.check_junit_results(args.e2e_results, "e2e")
    
    # Check coverage
    if args.coverage_report:
        print(f"\n📊 Checking code coverage: {args.coverage_report}")
        checker.check_coverage(args.coverage_report)
    
    # Check security
    if args.bandit_report:
        print(f"\n🛡️ Checking security issues: {args.bandit_report}")
        checker.check_security_report(args.bandit_report)
    
    # Print summary
    print(checker.generate_summary())
    
    # Generate report for PR comment
    report = checker.generate_report()
    
    # Save report
    output_file = Path("quality-gate-summary.md")
    output_file.write_text(report)
    print(f"✅ Quality gate report saved to: {output_file}")
    
    # Exit with appropriate code
    if checker.passed:
        print("\n🎉 SUCCESS: All quality gates passed!")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Quality gates failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
