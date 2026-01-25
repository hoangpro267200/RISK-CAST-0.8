#!/usr/bin/env python3
"""
Production Readiness Checklist

Validates all requirements for production deployment.
"""

import argparse
import asyncio
import os
import sys
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Warning: httpx not installed. HTTP checks will be skipped.")
    httpx = None

try:
    import asyncpg
except ImportError:
    print("Warning: asyncpg not installed. Database checks will be skipped.")
    asyncpg = None

try:
    import redis
except ImportError:
    print("Warning: redis not installed. Redis checks will be skipped.")
    redis = None

try:
    import boto3
except ImportError:
    print("Warning: boto3 not installed. AWS checks will be skipped.")
    boto3 = None


class CheckStatus(Enum):
    """Check result status."""
    PASS = "✅"
    FAIL = "❌"
    WARN = "⚠️ "
    SKIP = "⏭️ "


@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    category: str
    status: CheckStatus
    message: str
    details: Optional[str] = None


class ProductionChecklist:
    """Production readiness checker."""
    
    def __init__(self):
        self.results: List[CheckResult] = []
        self.checks: List[tuple] = []
        self._register_checks()
    
    def _register_checks(self):
        """Register all production checks."""
        # Infrastructure
        self.add_check("Database Connection", "Infrastructure", self.check_database)
        self.add_check("Redis Connection", "Infrastructure", self.check_redis)
        self.add_check("API Health", "Infrastructure", self.check_api_health)
        self.add_check("DNS Resolution", "Infrastructure", self.check_dns)
        self.add_check("SSL Certificate", "Infrastructure", self.check_ssl)
        
        # Configuration
        self.add_check("Environment Variables", "Configuration", self.check_env_vars)
        self.add_check("Secrets Configured", "Configuration", self.check_secrets)
        self.add_check("Feature Flags", "Configuration", self.check_feature_flags)
        
        # Security
        self.add_check("Rate Limiting", "Security", self.check_rate_limiting)
        self.add_check("CORS Policy", "Security", self.check_cors)
        self.add_check("Security Headers", "Security", self.check_security_headers)
        self.add_check("API Authentication", "Security", self.check_authentication)
        
        # Monitoring
        self.add_check("Metrics Endpoint", "Monitoring", self.check_metrics)
        self.add_check("Health Endpoints", "Monitoring", self.check_health_endpoints)
        self.add_check("Log Aggregation", "Monitoring", self.check_logging)
        
        # Reliability
        self.add_check("Replica Count", "Reliability", self.check_replicas)
        self.add_check("Resource Limits", "Reliability", self.check_resources)
        self.add_check("Horizontal Pod Autoscaler", "Reliability", self.check_hpa)
        
        # Data
        self.add_check("Database Migrations", "Data", self.check_migrations)
        self.add_check("Backup Configuration", "Data", self.check_backups)
        self.add_check("Data Retention Policy", "Data", self.check_retention)
        
        # Documentation
        self.add_check("Runbooks", "Documentation", self.check_runbooks)
        self.add_check("Architecture Docs", "Documentation", self.check_architecture_docs)
    
    def add_check(self, name: str, category: str, func: Callable):
        """Add a check to the list."""
        self.checks.append((name, category, func))
    
    async def run_all(self) -> List[CheckResult]:
        """Run all checks."""
        print(f"\nRunning {len(self.checks)} production readiness checks...\n")
        
        for name, category, func in self.checks:
            try:
                result = await func()
                result.name = name
                result.category = category
                self.results.append(result)
                
                # Print result immediately
                print(f"{result.status.value} [{result.category}] {result.name}: {result.message}")
                
            except Exception as e:
                result = CheckResult(
                    name=name,
                    category=category,
                    status=CheckStatus.FAIL,
                    message=f"Check failed: {str(e)[:100]}"
                )
                self.results.append(result)
                print(f"{result.status.value} [{result.category}] {result.name}: {result.message}")
        
        return self.results
    
    # =========================================================================
    # Infrastructure Checks
    # =========================================================================
    
    async def check_database(self) -> CheckResult:
        """Check database connectivity."""
        if not asyncpg:
            return CheckResult("", "", CheckStatus.SKIP, "asyncpg not installed")
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return CheckResult("", "", CheckStatus.FAIL, "DATABASE_URL not set")
        
        try:
            conn = await asyncpg.connect(db_url)
            await conn.fetchval("SELECT 1")
            count = await conn.fetchval("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            await conn.close()
            
            if count > 80:
                return CheckResult("", "", CheckStatus.WARN, f"High connection count: {count}")
            return CheckResult("", "", CheckStatus.PASS, f"Connected, {count} connections")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    async def check_redis(self) -> CheckResult:
        """Check Redis connectivity."""
        if not redis:
            return CheckResult("", "", CheckStatus.SKIP, "redis not installed")
        
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return CheckResult("", "", CheckStatus.FAIL, "REDIS_URL not set")
        
        try:
            r = redis.from_url(redis_url)
            if not r.ping():
                return CheckResult("", "", CheckStatus.FAIL, "Ping failed")
            
            info = r.info("memory")
            used_mb = info["used_memory"] / 1024 / 1024
            max_mb = info.get("maxmemory", 0) / 1024 / 1024
            
            if max_mb > 0 and used_mb / max_mb > 0.9:
                return CheckResult("", "", CheckStatus.WARN, f"High memory: {used_mb:.0f}/{max_mb:.0f}MB")
            return CheckResult("", "", CheckStatus.PASS, f"Connected, {used_mb:.0f}MB used")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    async def check_api_health(self) -> CheckResult:
        """Check API health."""
        if not httpx:
            return CheckResult("", "", CheckStatus.SKIP, "httpx not installed")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_url}/health/ready", timeout=10)
                if response.status_code == 200:
                    return CheckResult("", "", CheckStatus.PASS, "API healthy")
                return CheckResult("", "", CheckStatus.FAIL, f"Status: {response.status_code}")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    async def check_dns(self) -> CheckResult:
        """Check DNS resolution."""
        import socket
        domain = os.getenv("API_DOMAIN", "api.riskcast.io")
        
        try:
            ip = socket.gethostbyname(domain)
            return CheckResult("", "", CheckStatus.PASS, f"{domain} → {ip}")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    async def check_ssl(self) -> CheckResult:
        """Check SSL certificate."""
        import ssl
        import socket
        
        domain = os.getenv("API_DOMAIN", "api.riskcast.io")
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days = (not_after - datetime.utcnow()).days
                    
                    if days < 7:
                        return CheckResult("", "", CheckStatus.FAIL, f"Expires in {days} days!")
                    elif days < 30:
                        return CheckResult("", "", CheckStatus.WARN, f"Expires in {days} days")
                    return CheckResult("", "", CheckStatus.PASS, f"Valid, {days} days left")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    # =========================================================================
    # Configuration Checks
    # =========================================================================
    
    async def check_env_vars(self) -> CheckResult:
        """Check environment variables."""
        required = ["DATABASE_URL", "REDIS_URL", "SECRET_KEY", "ENVIRONMENT"]
        missing = [var for var in required if not os.getenv(var)]
        
        if missing:
            return CheckResult("", "", CheckStatus.FAIL, f"Missing: {', '.join(missing)}")
        
        env = os.getenv("ENVIRONMENT")
        if env != "production":
            return CheckResult("", "", CheckStatus.WARN, f"Environment: '{env}'")
        
        return CheckResult("", "", CheckStatus.PASS, "All required vars set")
    
    async def check_secrets(self) -> CheckResult:
        """Check secrets are configured."""
        secrets = ["SECRET_KEY", "TOMORROW_IO_API_KEY", "MARINE_TRAFFIC_API_KEY"]
        configured = [s for s in secrets if os.getenv(s) and len(os.getenv(s)) > 10]
        missing = [s for s in secrets if s not in configured]
        
        if missing:
            return CheckResult("", "", CheckStatus.WARN, f"Missing: {', '.join(missing)}")
        return CheckResult("", "", CheckStatus.PASS, f"{len(configured)} secrets configured")
    
    async def check_feature_flags(self) -> CheckResult:
        """Check feature flags."""
        flags = {
            "ENABLE_SWAGGER": ("false", "Should be disabled"),
            "DEBUG": ("false", "Should be disabled")
        }
        
        issues = []
        for flag, (expected, reason) in flags.items():
            actual = os.getenv(flag, "").lower()
            if actual and actual != expected:
                issues.append(f"{flag}={actual}")
        
        if issues:
            return CheckResult("", "", CheckStatus.WARN, f"Issues: {', '.join(issues)}")
        return CheckResult("", "", CheckStatus.PASS, "Flags configured")
    
    # =========================================================================
    # Security Checks
    # =========================================================================
    
    async def check_rate_limiting(self) -> CheckResult:
        """Check rate limiting."""
        if not httpx:
            return CheckResult("", "", CheckStatus.SKIP, "httpx not installed")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_url}/health/live")
                if "X-RateLimit-Limit" in response.headers:
                    return CheckResult("", "", CheckStatus.PASS, 
                        f"Enabled: {response.headers['X-RateLimit-Limit']}")
                return CheckResult("", "", CheckStatus.WARN, "Headers not found")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    async def check_cors(self) -> CheckResult:
        """Check CORS policy."""
        if not httpx:
            return CheckResult("", "", CheckStatus.SKIP, "httpx not installed")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.options(
                    f"{api_url}/api/v3/quotes/",
                    headers={"Origin": "https://evil.com"}
                )
                allowed = response.headers.get("Access-Control-Allow-Origin", "")
                
                if allowed == "*":
                    return CheckResult("", "", CheckStatus.FAIL, "Allows all origins (*)")
                return CheckResult("", "", CheckStatus.PASS, f"Configured: {allowed[:30]}")
        except Exception as e:
            return CheckResult("", "", CheckStatus.WARN, f"Check failed: {str(e)[:50]}")
    
    async def check_security_headers(self) -> CheckResult:
        """Check security headers."""
        if not httpx:
            return CheckResult("", "", CheckStatus.SKIP, "httpx not installed")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        required = ["X-Content-Type-Options", "X-Frame-Options"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_url}/health/live")
                missing = [h for h in required if h not in response.headers]
                
                if missing:
                    return CheckResult("", "", CheckStatus.WARN, f"Missing: {', '.join(missing)}")
                return CheckResult("", "", CheckStatus.PASS, "All headers present")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    async def check_authentication(self) -> CheckResult:
        """Check authentication is required."""
        if not httpx:
            return CheckResult("", "", CheckStatus.SKIP, "httpx not installed")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_url}/api/v3/quotes/")
                
                if response.status_code in [401, 403]:
                    return CheckResult("", "", CheckStatus.PASS, "Authentication required")
                return CheckResult("", "", CheckStatus.FAIL, f"Status: {response.status_code}")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    # =========================================================================
    # Monitoring Checks
    # =========================================================================
    
    async def check_metrics(self) -> CheckResult:
        """Check metrics endpoint."""
        if not httpx:
            return CheckResult("", "", CheckStatus.SKIP, "httpx not installed")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_url}/metrics")
                if response.status_code == 200 and "riskcast_" in response.text:
                    return CheckResult("", "", CheckStatus.PASS, "Active with metrics")
                return CheckResult("", "", CheckStatus.WARN, f"Status: {response.status_code}")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    async def check_health_endpoints(self) -> CheckResult:
        """Check health endpoints."""
        if not httpx:
            return CheckResult("", "", CheckStatus.SKIP, "httpx not installed")
        
        api_url = os.getenv("API_URL", "http://localhost:8000")
        endpoints = ["/health/live", "/health/ready"]
        
        try:
            async with httpx.AsyncClient() as client:
                results = []
                for endpoint in endpoints:
                    response = await client.get(f"{api_url}{endpoint}")
                    results.append((endpoint, response.status_code))
                
                failed = [e for e, s in results if s != 200]
                if failed:
                    return CheckResult("", "", CheckStatus.FAIL, f"Failed: {', '.join(failed)}")
                return CheckResult("", "", CheckStatus.PASS, f"All {len(endpoints)} healthy")
        except Exception as e:
            return CheckResult("", "", CheckStatus.FAIL, f"Failed: {str(e)[:50]}")
    
    async def check_logging(self) -> CheckResult:
        """Check logging configuration."""
        log_format = os.getenv("LOG_FORMAT", "")
        
        if log_format.lower() != "json":
            return CheckResult("", "", CheckStatus.WARN, "LOG_FORMAT should be 'json'")
        return CheckResult("", "", CheckStatus.PASS, "JSON logging configured")
    
    # =========================================================================
    # Reliability Checks
    # =========================================================================
    
    async def check_replicas(self) -> CheckResult:
        """Check replica count."""
        try:
            result = subprocess.run(
                ["kubectl", "get", "deployment", "riskcast-api", "-n", "riskcast-prod", 
                 "-o", "jsonpath={.spec.replicas}"],
                capture_output=True, text=True, timeout=10
            )
            replicas = int(result.stdout)
            
            if replicas < 2:
                return CheckResult("", "", CheckStatus.FAIL, f"Only {replicas} replica(s)")
            elif replicas < 3:
                return CheckResult("", "", CheckStatus.WARN, f"{replicas} replicas, recommend 3+")
            return CheckResult("", "", CheckStatus.PASS, f"{replicas} replicas")
        except Exception as e:
            return CheckResult("", "", CheckStatus.SKIP, f"kubectl not available")
    
    async def check_resources(self) -> CheckResult:
        """Check resource limits."""
        try:
            result = subprocess.run(
                ["kubectl", "get", "deployment", "riskcast-api", "-n", "riskcast-prod", 
                 "-o", "jsonpath={.spec.template.spec.containers[0].resources}"],
                capture_output=True, text=True, timeout=10
            )
            resources = json.loads(result.stdout) if result.stdout else {}
            
            if not resources.get("limits"):
                return CheckResult("", "", CheckStatus.FAIL, "No limits set")
            if not resources.get("requests"):
                return CheckResult("", "", CheckStatus.WARN, "No requests set")
            return CheckResult("", "", CheckStatus.PASS, "Limits configured")
        except Exception as e:
            return CheckResult("", "", CheckStatus.SKIP, "kubectl not available")
    
    async def check_hpa(self) -> CheckResult:
        """Check Horizontal Pod Autoscaler."""
        try:
            result = subprocess.run(
                ["kubectl", "get", "hpa", "-n", "riskcast-prod", "-o", "name"],
                capture_output=True, text=True, timeout=10
            )
            if "riskcast" in result.stdout:
                return CheckResult("", "", CheckStatus.PASS, "HPA configured")
            return CheckResult("", "", CheckStatus.WARN, "No HPA found")
        except Exception as e:
            return CheckResult("", "", CheckStatus.SKIP, "kubectl not available")
    
    # =========================================================================
    # Data Checks
    # =========================================================================
    
    async def check_migrations(self) -> CheckResult:
        """Check database migrations."""
        try:
            result = subprocess.run(
                ["alembic", "current"],
                capture_output=True, text=True, timeout=10
            )
            if "head" in result.stdout.lower():
                return CheckResult("", "", CheckStatus.PASS, "Up to date")
            return CheckResult("", "", CheckStatus.WARN, f"Status: {result.stdout[:50]}")
        except Exception as e:
            return CheckResult("", "", CheckStatus.SKIP, "alembic not available")
    
    async def check_backups(self) -> CheckResult:
        """Check backup configuration."""
        bucket = os.getenv("BACKUP_S3_BUCKET")
        
        if not bucket:
            return CheckResult("", "", CheckStatus.FAIL, "BACKUP_S3_BUCKET not set")
        
        if not boto3:
            return CheckResult("", "", CheckStatus.SKIP, "boto3 not installed")
        
        try:
            s3 = boto3.client('s3')
            response = s3.list_objects_v2(Bucket=bucket, Prefix="database/", MaxKeys=1)
            
            if response.get("Contents"):
                latest = response["Contents"][0]
                age_hours = (datetime.utcnow() - latest["LastModified"].replace(tzinfo=None)).total_seconds() / 3600
                
                if age_hours > 24:
                    return CheckResult("", "", CheckStatus.WARN, f"Latest backup: {age_hours:.0f}h ago")
                return CheckResult("", "", CheckStatus.PASS, f"Latest: {age_hours:.1f}h ago")
            return CheckResult("", "", CheckStatus.WARN, "No backups found")
        except Exception as e:
            return CheckResult("", "", CheckStatus.WARN, f"Could not verify: {str(e)[:50]}")
    
    async def check_retention(self) -> CheckResult:
        """Check retention policy."""
        retention_days = os.getenv("BACKUP_RETENTION_DAYS")
        
        if not retention_days:
            return CheckResult("", "", CheckStatus.WARN, "BACKUP_RETENTION_DAYS not set")
        return CheckResult("", "", CheckStatus.PASS, f"Retention: {retention_days} days")
    
    # =========================================================================
    # Documentation Checks
    # =========================================================================
    
    async def check_runbooks(self) -> CheckResult:
        """Check runbooks exist."""
        from pathlib import Path
        
        runbooks_path = Path("docs/runbooks")
        required = ["incident-response.md", "scaling.md", "debugging.md", "disaster-recovery.md"]
        
        if not runbooks_path.exists():
            return CheckResult("", "", CheckStatus.FAIL, "Runbooks directory not found")
        
        missing = [r for r in required if not (runbooks_path / r).exists()]
        
        if missing:
            return CheckResult("", "", CheckStatus.WARN, f"Missing: {', '.join(missing)}")
        return CheckResult("", "", CheckStatus.PASS, f"All {len(required)} runbooks present")
    
    async def check_architecture_docs(self) -> CheckResult:
        """Check documentation."""
        from pathlib import Path
        
        docs = ["README.md", "docs/api-guide.md"]
        existing = [d for d in docs if Path(d).exists()]
        
        if len(existing) < 1:
            return CheckResult("", "", CheckStatus.WARN, "Minimal documentation")
        return CheckResult("", "", CheckStatus.PASS, f"{len(existing)} doc files present")
    
    # =========================================================================
    # Report Generation
    # =========================================================================
    
    def generate_report(self) -> str:
        """Generate checklist report."""
        lines = [
            "",
            "=" * 70,
            "PRODUCTION READINESS CHECKLIST",
            "=" * 70,
            ""
        ]
        
        # Summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        warned = sum(1 for r in self.results if r.status == CheckStatus.WARN)
        skipped = sum(1 for r in self.results if r.status == CheckStatus.SKIP)
        
        lines.append(f"Summary: {passed} passed, {failed} failed, {warned} warnings, {skipped} skipped (total: {total})")
        lines.append("")
        
        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # By category
        for category, checks in categories.items():
            lines.append(f"\n{category}")
            lines.append("-" * len(category))
            
            for check in checks:
                lines.append(f"  {check.status.value} {check.name}: {check.message}")
                if check.details:
                    lines.append(f"      {check.details}")
        
        # Overall status
        lines.append("")
        lines.append("=" * 70)
        
        if failed > 0:
            lines.append("❌ NOT READY FOR PRODUCTION")
            lines.append(f"   {failed} critical issues must be fixed")
        elif warned > 3:
            lines.append("⚠️  REVIEW WARNINGS BEFORE PRODUCTION")
            lines.append(f"   {warned} warnings should be addressed")
        else:
            lines.append("✅ READY FOR PRODUCTION")
            if warned > 0:
                lines.append(f"   {warned} warnings noted but acceptable")
        
        lines.append("=" * 70)
        lines.append("")
        
        return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(
        description="Production readiness checklist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all checks
  python checklist.py
  
  # Output as JSON
  python checklist.py --json
  
  # Save report
  python checklist.py > checklist-report.txt
        """
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    
    args = parser.parse_args()
    
    checker = ProductionChecklist()
    results = await checker.run_all()
    
    if args.json:
        output = [
            {
                "name": r.name,
                "category": r.category,
                "status": r.status.name,
                "message": r.message,
                "details": r.details
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        print(checker.generate_report())
    
    # Exit with error if any failures
    failed = any(r.status == CheckStatus.FAIL for r in results)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
