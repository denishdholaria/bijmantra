# 🔒 Security Protocols

> **Purpose:** Security procedures and incident response  
> **Last Updated:** December 26, 2025  
> **Classification:** CONFIDENTIAL

---

## Security Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  SECURITY LAYERS                                        │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Layer 1: Network                                       │
│  ├── HTTPS only (TLS 1.3)                              │
│  ├── Firewall (ports 80, 443, 22)                      │
│  └── DDoS protection (Cloudflare optional)             │
│                                                         │
│  Layer 2: Application                                   │
│  ├── JWT authentication (24h access, 7d refresh)       │
│  ├── RBAC (6 roles)                                    │
│  ├── Rate limiting                                     │
│  └── Input validation (Pydantic)                       │
│                                                         │
│  Layer 3: Database                                      │
│  ├── Row-Level Security (RLS)                          │
│  ├── Encrypted connections                             │
│  ├── Parameterized queries (SQLAlchemy)                │
│  └── Audit logging                                     │
│                                                         │
│  Layer 4: Infrastructure                                │
│  ├── Container isolation                               │
│  ├── Secrets in environment variables                  │
│  └── Regular security updates                          │
└─────────────────────────────────────────────────────────┘
```

---

## Authentication

### JWT Token Structure

```json
{
  "sub": "user_id",
  "org": "organization_id",
  "roles": ["breeder", "admin"],
  "exp": 1735257600,
  "iat": 1735171200
}
```

### Token Lifetimes

| Token Type | Lifetime | Storage |
|------------|----------|---------|
| Access Token | 24 hours | Memory/localStorage |
| Refresh Token | 7 days | httpOnly cookie |

### Password Policy

- Minimum 8 characters
- Hashed with bcrypt (cost factor 12)
- No plaintext storage ever

---

## Authorization (RBAC)

### Role Hierarchy

```
superuser
    └── admin
        └── data_manager
            └── researcher
                └── breeder
                    └── viewer
```

### Permission Matrix

| Permission | Viewer | Breeder | Researcher | Data Manager | Admin | Superuser |
|------------|--------|---------|------------|--------------|-------|-----------|
| Read Plant Sciences | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Write Plant Sciences | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Admin Plant Sciences | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Read Seed Bank | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Write Seed Bank | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Manage Users | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Admin System | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| View Audit Log | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Bypass RLS | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Row-Level Security (RLS)

### How It Works

```sql
-- RLS policy on programs table
CREATE POLICY tenant_isolation ON programs
    USING (
        current_setting('app.current_organization_id')::int = 0  -- Superuser
        OR organization_id = current_setting('app.current_organization_id')::int
    );
```

### Tenant Context Flow

```
1. Request arrives with JWT
2. Middleware extracts organization_id from JWT
3. Middleware sets: SET LOCAL app.current_organization_id = X
4. All queries automatically filtered by RLS
5. User only sees their organization's data
```

### RLS-Protected Tables

- organizations, users, programs, trials, studies, locations, people
- seed_bank_vaults, seed_bank_accessions, seed_bank_viability_tests
- seed_bank_regeneration_tasks, seed_bank_exchanges
- (All tables with organization_id)

---

## Audit Logging

### What's Logged

| Event | Logged Data |
|-------|-------------|
| Login success | user_id, IP, timestamp |
| Login failure | email, IP, timestamp, reason |
| Data access | user_id, resource, action |
| Data modification | user_id, resource, before/after |
| Admin actions | user_id, action, target |
| Security events | type, severity, details |

### Audit Log Schema

```sql
CREATE TABLE security_audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    actor_id INTEGER,
    actor_email VARCHAR(255),
    action VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    organization_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    severity VARCHAR(20),  -- info, warning, error, critical
    details JSONB,
    success BOOLEAN
);
```

### Retention Policy

- Keep audit logs for minimum 1 year
- Archive to cold storage after 90 days
- Never delete security-related logs

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P1 - Critical | Service down, data breach | 15 minutes | Database compromised, all users affected |
| P2 - High | Major feature broken, security vulnerability | 1 hour | Auth broken, data leak |
| P3 - Medium | Minor feature broken, performance issue | 4 hours | Slow queries, minor bug |
| P4 - Low | Cosmetic, documentation | 24 hours | UI glitch, typo |

### Incident Response Procedure

#### 1. Detection
- Monitoring alerts
- User reports
- Security scans

#### 2. Containment
```bash
# Disable affected accounts
UPDATE users SET is_active = false WHERE ...;

# Block suspicious IPs (if using Cloudflare)
# Or add to firewall

# Enable maintenance mode (if implemented)
```

#### 3. Assessment
- Review audit logs
- Identify scope of impact
- Determine root cause

#### 4. Remediation
- Fix vulnerability
- Patch systems
- Restore from backup if needed

#### 5. Recovery
- Re-enable services
- Notify affected users
- Monitor for recurrence

#### 6. Post-Incident
- Document incident
- Update procedures
- Implement preventive measures

---

## Security Checklist

### Daily

- [ ] Review error logs for anomalies
- [ ] Check failed login attempts
- [ ] Verify backups completed

### Weekly

- [ ] Review audit logs for suspicious activity
- [ ] Check for security updates
- [ ] Verify SSL certificates valid

### Monthly

- [ ] Rotate secrets (if policy requires)
- [ ] Review user access (remove inactive)
- [ ] Security scan (OWASP ZAP, etc.)

### Quarterly

- [ ] Penetration testing
- [ ] Access review (all users)
- [ ] Update security documentation
- [ ] Disaster recovery drill

---

## Secrets Management

### Current Approach

Secrets stored in environment variables:

```bash
# .env.production (NEVER commit!)
SECRET_KEY=<64-char-random>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
```

### Best Practices

1. **Never commit secrets** to git
2. **Rotate regularly** (quarterly minimum)
3. **Use strong passwords** (24+ chars, random)
4. **Limit access** to production secrets
5. **Audit access** to secrets

### Future: Secrets Manager

Consider using:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

---

## Security Headers

### Implemented Headers

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; ...
Referrer-Policy: strict-origin-when-cross-origin
```

### Caddy Configuration

```caddyfile
(security_headers) {
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
}
```

---

## Vulnerability Disclosure

### If You Find a Vulnerability

1. **Do NOT** disclose publicly
2. Email: security@bijmantra.org (set this up)
3. Include: Description, steps to reproduce, impact
4. We will respond within 48 hours

### Bug Bounty (Future)

Consider implementing a bug bounty program for:
- Critical vulnerabilities: $500-2000
- High vulnerabilities: $200-500
- Medium vulnerabilities: $50-200

---

## Compliance Considerations

### GDPR (if serving EU users)

- [ ] Data processing agreement
- [ ] Right to erasure (delete user data)
- [ ] Data portability (export user data)
- [ ] Privacy policy
- [ ] Cookie consent

### Data Sovereignty

- Data stored in user's preferred region
- Federation enables local data storage
- Clear data residency documentation

---

## Emergency Contacts

| Role | Contact | When |
|------|---------|------|
| Platform Admin | (you) | All security issues |
| Hosting Provider | Support portal | Infrastructure issues |
| Domain Registrar | Support portal | DNS issues |

---

*Security is everyone's responsibility. When in doubt, escalate.*
