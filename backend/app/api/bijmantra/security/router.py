"""
Security domain router aggregator
Combines all security-related routers: RBAC, RLS, security audit, RAKSHAKA, PRAHARI, and compliance
"""

from fastapi import APIRouter

from app.api.bijmantra.security import (
    audit,
    rbac,
    rls,
    security_audit,
    rakshaka,
    prahari,
    compliance,
    sso,
)

security_router = APIRouter()

# Audit Trail
security_router.include_router(audit.router, tags=["Audit"])

# RBAC (Role-Based Access Control)
security_router.include_router(rbac.router, tags=["RBAC"])

# RLS (Row-Level Security)
security_router.include_router(rls.router, tags=["Row-Level Security"])

# Security Audit
security_router.include_router(security_audit.router, tags=["Security Audit"])

# RAKSHAKA Self-Healing Security
security_router.include_router(rakshaka.router, tags=["RAKSHAKA Self-Healing"])

# PRAHARI Defense System
security_router.include_router(prahari.router, tags=["PRAHARI Defense"])

# Compliance
security_router.include_router(compliance.router, tags=["Compliance"])

# Single Sign-On
security_router.include_router(sso.router, tags=["Single Sign-On"])
