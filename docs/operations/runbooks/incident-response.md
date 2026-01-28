# 🚨 Incident Response Runbook

> **Purpose:** Security incident handling procedures  
> **Last Updated:** December 26, 2025  
> **Priority:** 🔴 Critical

---

## Incident Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **P1 - Critical** | Service down, data breach | 15 minutes | Database compromised, all users affected |
| **P2 - High** | Major feature broken, security vulnerability | 1 hour | Auth broken, data leak |
| **P3 - Medium** | Minor feature broken, performance issue | 4 hours | Slow queries, minor bug |
| **P4 - Low** | Cosmetic, documentation | 24 hours | UI glitch, typo |

---

## Incident Response Flow

```
┌─────────────────────────────────────────────────────────┐
│  INCIDENT RESPONSE FLOW                                 │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  1. DETECT ──► 2. CONTAIN ──► 3. ASSESS                │
│                                    │                    │
│                                    ▼                    │
│  6. REVIEW ◄── 5. RECOVER ◄── 4. REMEDIATE            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: Detection

### How Incidents Are Detected

- Monitoring alerts (Prometheus, Grafana)
- User reports
- Security scans
- Log analysis
- Error tracking (Sentry)

### Initial Assessment

```bash
# Check service status
docker-compose -f compose.prod.yaml ps

# Check recent logs
docker-compose -f compose.prod.yaml logs --tail=100

# Check error rate
# (via monitoring dashboard)

# Check database connectivity
docker-compose -f compose.prod.yaml exec postgres pg_isready
```

---

## Phase 2: Containment

### For Security Breaches

```bash
# 1. Disable affected user accounts
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
UPDATE users SET is_active = false WHERE id IN (SELECT id FROM users WHERE ...);
"

# 2. Invalidate sessions
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
DELETE FROM user_sessions WHERE user_id IN (...);
"

# 3. Block suspicious IPs (if using firewall)
sudo ufw deny from <suspicious_ip>

# 4. Enable maintenance mode (if implemented)
# Or take application offline temporarily
docker-compose -f compose.prod.yaml stop backend
```

### For Service Outages

```bash
# 1. Check which component is failing
docker-compose -f compose.prod.yaml ps

# 2. Restart failed component
docker-compose -f compose.prod.yaml restart <service>

# 3. If database is down, check logs
docker-compose -f compose.prod.yaml logs postgres

# 4. If out of disk space
df -h
# Clean up if needed
docker system prune -f
```

### For Data Corruption

```bash
# 1. Stop writes immediately
docker-compose -f compose.prod.yaml stop backend

# 2. Take database snapshot
docker-compose -f compose.prod.yaml exec postgres pg_dump -U bijmantra_prod bijmantra_production > emergency_backup.sql

# 3. Assess damage before proceeding
```

---

## Phase 3: Assessment

### Gather Information

```bash
# 1. Review audit logs
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT * FROM security_audit_log 
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC
LIMIT 100;
"

# 2. Check for unauthorized access
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT * FROM security_audit_log 
WHERE action = 'unauthorized_access'
AND created_at > NOW() - INTERVAL '24 hours';
"

# 3. Check failed login attempts
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT actor_email, ip_address, count(*) 
FROM security_audit_log 
WHERE action = 'login_failed'
AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY actor_email, ip_address
ORDER BY count DESC;
"

# 4. Check application logs
docker-compose -f compose.prod.yaml logs --since="1h" backend | grep -i error
```

### Document Findings

Create incident report with:
- Timeline of events
- Affected systems/users
- Root cause (if known)
- Actions taken
- Evidence collected

---

## Phase 4: Remediation

### For Security Vulnerabilities

```bash
# 1. Apply security patch
git pull origin main
docker-compose -f compose.prod.yaml build backend
docker-compose -f compose.prod.yaml up -d backend

# 2. Force password reset for affected users
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
UPDATE users SET must_change_password = true WHERE ...;
"

# 3. Rotate compromised secrets
# Generate new secrets and update .env
openssl rand -hex 32 > new_secret_key.txt
# Update .env and restart
```

### For Data Issues

```bash
# 1. Restore from backup if needed
# See backup-restore.md

# 2. Fix corrupted data
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
-- Fix specific data issues
UPDATE table SET column = correct_value WHERE ...;
"

# 3. Verify data integrity
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
-- Run integrity checks
SELECT count(*) FROM users WHERE organization_id IS NULL;
"
```

---

## Phase 5: Recovery

### Restore Service

```bash
# 1. Start services
docker-compose -f compose.prod.yaml up -d

# 2. Verify health
curl https://bijmantra.org/health

# 3. Run smoke tests
# - Login works
# - Data is accessible
# - Key features work

# 4. Monitor for issues
docker-compose -f compose.prod.yaml logs -f
```

### Notify Users

If users were affected:

1. **Email notification** with:
   - What happened (high level)
   - What we did to fix it
   - What users should do (change password, etc.)
   - Apology and commitment to improvement

2. **In-app notification** (if applicable)

---

## Phase 6: Post-Incident Review

### Within 48 Hours

1. **Document the incident**
   - Timeline
   - Root cause
   - Impact
   - Actions taken
   - Lessons learned

2. **Identify improvements**
   - What could have prevented this?
   - What could have detected it faster?
   - What could have reduced impact?

3. **Create action items**
   - Security improvements
   - Monitoring improvements
   - Process improvements

### Incident Report Template

```markdown
# Incident Report: [Title]

**Date:** YYYY-MM-DD
**Severity:** P1/P2/P3/P4
**Duration:** X hours
**Affected Users:** X

## Summary
Brief description of what happened.

## Timeline
- HH:MM - Event 1
- HH:MM - Event 2
- HH:MM - Resolution

## Root Cause
What caused the incident.

## Impact
- X users affected
- X hours of downtime
- Data impact (if any)

## Resolution
What was done to fix it.

## Action Items
- [ ] Action 1
- [ ] Action 2

## Lessons Learned
What we learned and how we'll prevent this in the future.
```

---

## Emergency Contacts

| Role | Contact | When |
|------|---------|------|
| Platform Admin | (you) | All incidents |
| Hosting Provider | Support portal | Infrastructure issues |
| Domain Registrar | Support portal | DNS issues |

---

## Quick Reference

### Stop Everything

```bash
docker-compose -f compose.prod.yaml down
```

### Start Everything

```bash
docker-compose -f compose.prod.yaml up -d
```

### Check Status

```bash
docker-compose -f compose.prod.yaml ps
docker-compose -f compose.prod.yaml logs --tail=50
curl https://bijmantra.org/health
```

---

*Stay calm. Follow the procedure. Document everything.*
