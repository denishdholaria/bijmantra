# Security Policy

## Overview

Bijmantra implements the **ASHTA-STAMBHA** (अष्ट-स्तम्भ) security framework — Eight Pillars of Protection designed for mission-critical agricultural research environments.

🌐 **Website:** [bijmantra.org](https://bijmantra.org)

## Security Features

- Multi-layer threat detection and response
- Self-healing infrastructure
- Adaptive security posture management
- Comprehensive audit logging
- OWASP-compliant security headers
- JWT-based authentication with RBAC

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Active |

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability:

1. **Do NOT** open a public issue
2. Email details to the maintainers privately to denishdholaria@gmail.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

We will acknowledge receipt within 48 hours and provide a detailed response within 7 days.

## Security Best Practices for Deployment

1. **Environment Variables**: Never commit secrets to version control
2. **HTTPS**: Always use TLS in production (Caddy provides auto-TLS)
3. **Database**: Enable Row-Level Security in PostgreSQL
4. **Redis**: Use authentication and TLS for Redis connections
5. **Updates**: Keep all dependencies updated

## Compliance

- OWASP Security Headers
- JWT Best Practices (RS256, short-lived tokens)
- Role-Based Access Control (RBAC)
- Audit Logging for compliance requirements

---

*"अष्ट-स्तम्भ" — Built to protect agricultural research for generations to come.*
