# 🛠️ Platform Admin Guide

> **Purpose:** Operations guide for platform administrators  
> **Last Updated:** December 26, 2025

---

## Platform Admin vs Organization Admin

| Role | Scope | Access |
|------|-------|--------|
| **Platform Admin** | All organizations | Superuser (`is_superuser=true`) |
| **Organization Admin** | Single organization | Admin role within org |

**You are the Platform Admin.** This guide covers platform-level operations.

---

## Current Admin Capabilities

### What You Can Do Now (Public Repo)

| Feature | Location | Status |
|---------|----------|--------|
| User Management | `/settings/users` | ✅ Working |
| Team Management | `/settings/teams` | ✅ Working |
| System Settings | `/system-settings` | ✅ Working |
| Audit Log | `/auditlog` | ✅ Working |
| Security Dashboard | `/security-dashboard` | ✅ Working |

### What You Need (Private Repo)

| Feature | Priority | Status |
|---------|----------|--------|
| Organization CRUD | P0 | 🔴 Not built |
| License Management | P1 | 🔴 Not built |
| Platform Metrics | P1 | 🔴 Not built |
| User Impersonation | P1 | 🔴 Not built |
| Billing Integration | P2 | 🔴 Not built |

---

## Daily Operations

### Monitoring Health

```bash
# Check application health
curl https://your-domain.com/health

# Check database connection
curl https://your-domain.com/api/v2/health/db

# Check Redis connection
curl https://your-domain.com/api/v2/health/redis
```

### Viewing Logs

```bash
# Application logs
docker-compose -f compose.prod.yaml logs -f backend

# Access logs (Caddy)
docker-compose -f compose.prod.yaml logs -f caddy

# Database logs
docker-compose -f compose.prod.yaml logs -f postgres
```

### Database Operations

```bash
# Connect to database
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production

# List organizations
SELECT id, name, slug, is_active, created_at FROM organizations;

# List users by organization
SELECT u.email, u.full_name, o.name as org_name 
FROM users u 
JOIN organizations o ON u.organization_id = o.id;

# Check RLS policies
SELECT * FROM pg_policies WHERE schemaname = 'public';
```

---

## User Support Operations

### Creating a New Organization

Until the platform admin UI is built, use SQL:

```sql
-- Create organization
INSERT INTO organizations (name, slug, is_active, created_at, updated_at)
VALUES ('New Organization', 'new-org', true, NOW(), NOW())
RETURNING id;

-- Note the returned ID for creating admin user
```

### Creating an Admin User for Organization

```sql
-- First, hash the password (do this in Python)
-- python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('temp_password'))"

INSERT INTO users (
    organization_id, 
    email, 
    hashed_password, 
    full_name, 
    is_active, 
    is_superuser,
    created_at,
    updated_at
)
VALUES (
    <org_id>,
    'admin@neworg.com',
    '<hashed_password>',
    'Org Admin',
    true,
    false,
    NOW(),
    NOW()
);
```

### Resetting User Password

```python
# Run in Python shell
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_hash = pwd_context.hash("new_password")
print(new_hash)
```

```sql
-- Update password
UPDATE users 
SET hashed_password = '<new_hash>', updated_at = NOW()
WHERE email = 'user@example.com';
```

### Deactivating a User

```sql
UPDATE users 
SET is_active = false, updated_at = NOW()
WHERE email = 'user@example.com';
```

### Deactivating an Organization

```sql
-- Soft delete - keeps data but prevents access
UPDATE organizations 
SET is_active = false, updated_at = NOW()
WHERE slug = 'org-slug';

-- Also deactivate all users
UPDATE users 
SET is_active = false, updated_at = NOW()
WHERE organization_id = (SELECT id FROM organizations WHERE slug = 'org-slug');
```

---

## Troubleshooting

### User Can't Login

1. **Check user exists and is active:**
   ```sql
   SELECT email, is_active, organization_id FROM users WHERE email = 'user@example.com';
   ```

2. **Check organization is active:**
   ```sql
   SELECT name, is_active FROM organizations WHERE id = <org_id>;
   ```

3. **Reset password if needed** (see above)

### User Sees Wrong Data

1. **Check organization_id:**
   ```sql
   SELECT organization_id FROM users WHERE email = 'user@example.com';
   ```

2. **Verify RLS is working:**
   ```sql
   -- As superuser, check if RLS policies exist
   SELECT * FROM pg_policies WHERE tablename = 'programs';
   ```

3. **Check JWT token claims** (decode at jwt.io)

### Performance Issues

1. **Check slow queries:**
   ```sql
   SELECT query, calls, mean_time 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

2. **Check missing indexes:**
   ```sql
   SELECT relname, seq_scan, idx_scan 
   FROM pg_stat_user_tables 
   WHERE seq_scan > idx_scan 
   ORDER BY seq_scan DESC;
   ```

3. **Check connection pool:**
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

---

## Backup & Recovery

### Manual Backup

```bash
# Full database backup
docker-compose -f compose.prod.yaml exec postgres \
  pg_dump -U bijmantra_prod bijmantra_production | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Upload to S3/MinIO
aws s3 cp backup_*.sql.gz s3://bijmantra-backups/
```

### Restore from Backup

```bash
# Download backup
aws s3 cp s3://bijmantra-backups/backup_20251226.sql.gz .

# Restore (WARNING: This overwrites existing data!)
gunzip -c backup_20251226.sql.gz | docker-compose -f compose.prod.yaml exec -T postgres \
  psql -U bijmantra_prod bijmantra_production
```

### Point-in-Time Recovery

If using PostgreSQL WAL archiving:

```bash
# Restore to specific timestamp
pg_restore --target-time="2025-12-26 14:30:00" ...
```

---

## Security Operations

### Viewing Audit Logs

```sql
-- Recent security events
SELECT * FROM security_audit_log 
ORDER BY created_at DESC 
LIMIT 100;

-- Failed login attempts
SELECT * FROM security_audit_log 
WHERE action = 'login_failed' 
AND created_at > NOW() - INTERVAL '24 hours';

-- Actions by specific user
SELECT * FROM security_audit_log 
WHERE actor_id = '<user_id>'
ORDER BY created_at DESC;
```

### Revoking Access

```sql
-- Immediate: Deactivate user
UPDATE users SET is_active = false WHERE email = 'user@example.com';

-- Also invalidate sessions (if using session table)
DELETE FROM user_sessions WHERE user_id = (SELECT id FROM users WHERE email = 'user@example.com');
```

### Investigating Security Incidents

1. **Identify affected users/data:**
   ```sql
   SELECT * FROM security_audit_log 
   WHERE created_at BETWEEN '<start>' AND '<end>'
   AND severity IN ('warning', 'error', 'critical');
   ```

2. **Check for unauthorized access:**
   ```sql
   SELECT * FROM security_audit_log 
   WHERE action = 'unauthorized_access'
   ORDER BY created_at DESC;
   ```

3. **Document and report** (see incident response runbook)

---

## Scaling Operations

### Adding Read Replicas

When you need to scale reads:

1. Set up PostgreSQL streaming replication
2. Point read queries to replica
3. Update connection string in config

### Horizontal Scaling

When you need more app servers:

1. Deploy additional backend containers
2. Put behind load balancer
3. Ensure session storage is shared (Redis)

---

## Maintenance Windows

### Planned Maintenance

1. **Announce maintenance** (email users, banner in app)
2. **Enable maintenance mode** (if implemented)
3. **Perform maintenance**
4. **Verify functionality**
5. **Disable maintenance mode**
6. **Announce completion**

### Database Migrations

```bash
# Always backup first!
./deployment/scripts/backup.sh

# Run migrations
docker-compose -f compose.prod.yaml exec backend alembic upgrade head

# Verify
docker-compose -f compose.prod.yaml exec backend alembic current
```

---

## Emergency Procedures

### Application Down

1. Check container status: `docker-compose ps`
2. Check logs: `docker-compose logs -f`
3. Restart if needed: `docker-compose restart`
4. If persistent, check resources (disk, memory)

### Database Down

1. Check PostgreSQL logs
2. Check disk space
3. Check connections: `SELECT count(*) FROM pg_stat_activity;`
4. Restart if needed (last resort)

### Security Breach

1. **Contain:** Disable affected accounts
2. **Assess:** Review audit logs
3. **Notify:** Inform affected users
4. **Remediate:** Fix vulnerability
5. **Document:** Post-incident report

---

*This guide will expand as the platform grows. Keep it updated.*
