"""
Alerting Configuration (Phase 3 - Day 9)

CRITICAL: Defines alert thresholds and conditions for production monitoring.

Alerts are configured for Prometheus Alertmanager or similar systems.
These thresholds ensure we're notified of issues before they impact users.
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


# Alert Definitions
ALERT_DEFINITIONS = {
    "high_error_rate": {
        "name": "HighErrorRate",
        "description": "Error rate exceeds 5% for 5 minutes",
        "severity": "critical",
        "condition": "rate(riskcast_http_errors_total[5m]) / rate(riskcast_http_requests_total[5m]) > 0.05",
        "threshold": 0.05,  # 5%
        "duration": "5m",
        "action": "Investigate error logs and check system health"
    },
    "high_latency_p95": {
        "name": "HighLatencyP95",
        "description": "P95 latency exceeds 2 seconds for 5 minutes",
        "severity": "warning",
        "condition": "histogram_quantile(0.95, rate(riskcast_http_request_duration_seconds_bucket[5m])) > 2.0",
        "threshold": 2.0,  # seconds
        "duration": "5m",
        "action": "Check slow queries, database performance, or external API latency"
    },
    "high_latency_p99": {
        "name": "HighLatencyP99",
        "description": "P99 latency exceeds 5 seconds for 5 minutes",
        "severity": "critical",
        "condition": "histogram_quantile(0.99, rate(riskcast_http_request_duration_seconds_bucket[5m])) > 5.0",
        "threshold": 5.0,  # seconds
        "duration": "5m",
        "action": "Investigate system bottlenecks immediately"
    },
    "high_memory_usage": {
        "name": "HighMemoryUsage",
        "description": "Memory usage exceeds 80%",
        "severity": "warning",
        "condition": "process_resident_memory_bytes / process_memory_limit_bytes > 0.8",
        "threshold": 0.8,  # 80%
        "action": "Check for memory leaks, restart service if needed"
    },
    "ai_advisor_failures": {
        "name": "AIAdvisorFailures",
        "description": "AI advisor failure rate exceeds 10%",
        "severity": "warning",
        "condition": "rate(riskcast_ai_advisor_errors_total[5m]) / rate(riskcast_ai_advisor_requests_total[5m]) > 0.10",
        "threshold": 0.10,  # 10%
        "duration": "5m",
        "action": "Check Anthropic API status, verify API key, check rate limits"
    },
    "monte_carlo_non_deterministic": {
        "name": "MonteCarloNonDeterministic",
        "description": "Monte Carlo simulation producing non-deterministic results",
        "severity": "critical",
        "condition": "increase(riskcast_monte_carlo_non_deterministic_total[1h]) > 0",
        "action": "CRITICAL: Risk engine determinism violated. Investigate seed generation immediately."
    },
    "request_timeout_rate": {
        "name": "RequestTimeoutRate",
        "description": "Request timeout rate exceeds 1%",
        "severity": "warning",
        "condition": "rate(riskcast_http_requests_total{status_code=\"504\"}[5m]) / rate(riskcast_http_requests_total[5m]) > 0.01",
        "threshold": 0.01,  # 1%
        "duration": "5m",
        "action": "Check for slow endpoints, optimize queries, or increase timeout if needed"
    },
    "missing_secrets": {
        "name": "MissingSecrets",
        "description": "Required secrets not configured",
        "severity": "critical",
        "condition": "riskcast_secrets_configured == 0",
        "action": "CRITICAL: System cannot start without required secrets. Check environment variables."
    }
}


def get_prometheus_alerts() -> List[Dict[str, Any]]:
    """
    Get Prometheus alert rules in YAML format.
    
    Returns:
        List of alert rule dictionaries
    """
    alerts = []
    
    for alert_key, alert_def in ALERT_DEFINITIONS.items():
        alert_rule = {
            "alert": alert_def["name"],
            "expr": alert_def["condition"],
            "for": alert_def.get("duration", "5m"),
            "labels": {
                "severity": alert_def["severity"],
                "component": "riskcast"
            },
            "annotations": {
                "summary": alert_def["description"],
                "description": f"{alert_def['description']}. Action: {alert_def['action']}",
                "action": alert_def["action"]
            }
        }
        alerts.append(alert_rule)
    
    return alerts


def get_alert_summary() -> Dict[str, Any]:
    """
    Get summary of all alerts for documentation.
    
    Returns:
        Dictionary with alert summary
    """
    return {
        "total_alerts": len(ALERT_DEFINITIONS),
        "critical_alerts": len([a for a in ALERT_DEFINITIONS.values() if a["severity"] == "critical"]),
        "warning_alerts": len([a for a in ALERT_DEFINITIONS.values() if a["severity"] == "warning"]),
        "alerts": ALERT_DEFINITIONS
    }


# Prometheus Alertmanager Configuration (YAML format)
PROMETHEUS_ALERT_RULES_YAML = """
groups:
  - name: riskcast_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(riskcast_http_errors_total[5m]) / rate(riskcast_http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
          component: riskcast
        annotations:
          summary: "Error rate exceeds 5%"
          description: "Error rate is {{ $value | humanizePercentage }} for 5 minutes. Investigate error logs."
      
      - alert: HighLatencyP95
        expr: histogram_quantile(0.95, rate(riskcast_http_request_duration_seconds_bucket[5m])) > 2.0
        for: 5m
        labels:
          severity: warning
          component: riskcast
        annotations:
          summary: "P95 latency exceeds 2 seconds"
          description: "P95 latency is {{ $value }}s. Check slow queries or external API latency."
      
      - alert: HighLatencyP99
        expr: histogram_quantile(0.99, rate(riskcast_http_request_duration_seconds_bucket[5m])) > 5.0
        for: 5m
        labels:
          severity: critical
          component: riskcast
        annotations:
          summary: "P99 latency exceeds 5 seconds"
          description: "P99 latency is {{ $value }}s. Investigate system bottlenecks immediately."
      
      - alert: AIAdvisorFailures
        expr: rate(riskcast_ai_advisor_errors_total[5m]) / rate(riskcast_ai_advisor_requests_total[5m]) > 0.10
        for: 5m
        labels:
          severity: warning
          component: riskcast
        annotations:
          summary: "AI advisor failure rate exceeds 10%"
          description: "AI advisor failure rate is {{ $value | humanizePercentage }}. Check Anthropic API status."
      
      - alert: RequestTimeoutRate
        expr: rate(riskcast_http_requests_total{status_code="504"}[5m]) / rate(riskcast_http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: warning
          component: riskcast
        annotations:
          summary: "Request timeout rate exceeds 1%"
          description: "Timeout rate is {{ $value | humanizePercentage }}. Check for slow endpoints."
"""


def export_alert_rules_to_file(filepath: str):
    """
    Export Prometheus alert rules to YAML file.
    
    Args:
        filepath: Path to output file
    """
    try:
        with open(filepath, 'w') as f:
            f.write(PROMETHEUS_ALERT_RULES_YAML)
        logger.info(f"Alert rules exported to {filepath}")
    except Exception as e:
        logger.error(f"Failed to export alert rules: {e}")


if __name__ == "__main__":
    # Export alert rules when run directly
    import sys
    from pathlib import Path
    
    output_file = Path(__file__).parent.parent / "prometheus_alerts.yml"
    export_alert_rules_to_file(str(output_file))
    print(f"✅ Alert rules exported to {output_file}")
    print(f"\n📊 Alert Summary:")
    summary = get_alert_summary()
    print(f"  Total alerts: {summary['total_alerts']}")
    print(f"  Critical: {summary['critical_alerts']}")
    print(f"  Warning: {summary['warning_alerts']}")
