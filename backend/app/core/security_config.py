"""
Security Configuration

Centralized security settings loaded from environment variables.
For mission-critical deployments including space research applications.
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseModel
from functools import lru_cache


class SecurityThresholds(BaseModel):
    """Posture escalation thresholds."""
    elevated_threats: int = 1
    elevated_anomalies: int = 3
    elevated_security_score: int = 70
    high_threats: int = 3
    high_anomalies: int = 5
    high_security_score: int = 50
    severe_threats: int = 5
    severe_anomalies: int = 10
    severe_security_score: int = 30
    lockdown_threats: int = 10
    lockdown_anomalies: int = 20
    lockdown_security_score: int = 10


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    default_limit: int = 100  # requests per window
    default_window: int = 60  # seconds
    auth_limit: int = 10  # login attempts
    auth_window: int = 300  # 5 minutes
    api_limit: int = 1000  # API calls
    api_window: int = 3600  # 1 hour


class SecurityConfig(BaseModel):
    """Main security configuration."""
    # Feature flags
    enabled: bool = True
    auto_response_enabled: bool = True
    audit_logging_enabled: bool = True
    middleware_enabled: bool = True

    # Thresholds
    thresholds: SecurityThresholds = SecurityThresholds()
    rate_limits: RateLimitConfig = RateLimitConfig()

    # Blocking
    default_block_duration: int = 3600  # 1 hour
    max_block_duration: int = 604800  # 7 days

    # Anomaly detection
    anomaly_baseline_window: int = 100
    api_latency_warn: int = 500
    api_latency_crit: int = 1000
    error_rate_warn: float = 1.0
    error_rate_crit: float = 5.0

    # Audit
    audit_retention_days: int = 90
    audit_max_memory_entries: int = 10000

    # Whitelist/Blacklist
    ip_whitelist: List[str] = ["127.0.0.1", "::1"]
    ip_blacklist: List[str] = []

    # Headers
    enable_security_headers: bool = True
    csp_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"

    # Redis (for distributed deployments)
    redis_url: Optional[str] = None
    redis_prefix: str = "bijmantra:security:"


@lru_cache()
def get_security_config() -> SecurityConfig:
    """Load security configuration from environment."""
    return SecurityConfig(
        enabled=os.getenv("SECURITY_ENABLED", "true").lower() == "true",
        auto_response_enabled=os.getenv("SECURITY_AUTO_RESPONSE", "true").lower() == "true",
        audit_logging_enabled=os.getenv("SECURITY_AUDIT_ENABLED", "true").lower() == "true",
        middleware_enabled=os.getenv("SECURITY_MIDDLEWARE_ENABLED", "true").lower() == "true",

        thresholds=SecurityThresholds(
            elevated_threats=int(os.getenv("SECURITY_ELEVATED_THREATS", "1")),
            elevated_anomalies=int(os.getenv("SECURITY_ELEVATED_ANOMALIES", "3")),
            high_threats=int(os.getenv("SECURITY_HIGH_THREATS", "3")),
            high_anomalies=int(os.getenv("SECURITY_HIGH_ANOMALIES", "5")),
            severe_threats=int(os.getenv("SECURITY_SEVERE_THREATS", "5")),
            severe_anomalies=int(os.getenv("SECURITY_SEVERE_ANOMALIES", "10")),
            lockdown_threats=int(os.getenv("SECURITY_LOCKDOWN_THREATS", "10")),
        ),

        rate_limits=RateLimitConfig(
            default_limit=int(os.getenv("RATE_LIMIT_DEFAULT", "100")),
            default_window=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            auth_limit=int(os.getenv("RATE_LIMIT_AUTH", "10")),
            api_limit=int(os.getenv("RATE_LIMIT_API", "1000")),
        ),

        default_block_duration=int(os.getenv("SECURITY_BLOCK_DURATION", "3600")),
        anomaly_baseline_window=int(os.getenv("ANOMALY_BASELINE_WINDOW", "100")),
        api_latency_warn=int(os.getenv("API_LATENCY_WARN", "500")),
        api_latency_crit=int(os.getenv("API_LATENCY_CRIT", "1000")),

        audit_retention_days=int(os.getenv("AUDIT_RETENTION_DAYS", "90")),
        audit_max_memory_entries=int(os.getenv("AUDIT_MAX_ENTRIES", "10000")),

        redis_url=os.getenv("REDIS_URL"),
        redis_prefix=os.getenv("REDIS_PREFIX", "bijmantra:security:"),

        enable_security_headers=os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true",
    )


# Convenience function
security_config = get_security_config()
