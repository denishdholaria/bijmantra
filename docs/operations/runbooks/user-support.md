# 👥 User Support Runbook

> **Purpose:** Common user support tasks and procedures  
> **Last Updated:** December 26, 2025  
> **Priority:** 🟡 Important

---

## Common Support Tasks

### 1. Password Reset

**User reports:** "I forgot my password"

```bash
# Generate password hash
python3 -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('TempPassword123!'))
"

# Update password in database
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
UPDATE users 
SET hashed_password = '<hash_from_above>', updated_at = NOW()
WHERE email = 'user@example.com';
"

# Notify user of temporary password
# Instruct them to change it immediately
```

**Better approach (if self-service reset exists):**
- Direct user to "Forgot Password" link
- Verify email is correct in system

---

### 2. Account Locked/Disabled

**User reports:** "I can't log in"

```bash
# Check account status
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT email, is_active, organization_id, created_at, updated_at
FROM users 
WHERE email = 'user@example.com';
"

# If is_active = false, re-enable
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
UPDATE users 
SET is_active = true, updated_at = NOW()
WHERE email = 'user@example.com';
"

# Check organization is active
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT o.name, o.is_active 
FROM organizations o
JOIN users u ON u.organization_id = o.id
WHERE u.email = 'user@example.com';
"
```

---

### 3. User Can't See Data

**User reports:** "My data is missing" or "I can't see my trials"

```bash
# Check user's organization
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT u.email, u.organization_id, o.name as org_name
FROM users u
JOIN organizations o ON u.organization_id = o.id
WHERE u.email = 'user@example.com';
"

# Check if data exists for that organization
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT count(*) as trial_count
FROM trials
WHERE organization_id = <org_id>;
"

# Check RLS is working (as superuser)
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
-- Set context to user's org
SET LOCAL app.current_organization_id = '<org_id>';

-- Check what they should see
SELECT id, trial_name FROM trials LIMIT 10;
"
```

**Common causes:**
- User in wrong organization
- Data was created in different organization
- RLS policy issue (rare)

---

### 4. Create New User

**Request:** "Add a new user to our organization"

```bash
# 1. Get organization ID
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT id, name FROM organizations WHERE name ILIKE '%org_name%';
"

# 2. Generate password hash
python3 -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('TempPassword123!'))
"

# 3. Create user
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
INSERT INTO users (
    organization_id,
    email,
    hashed_password,
    full_name,
    is_active,
    is_superuser,
    created_at,
    updated_at
) VALUES (
    <org_id>,
    'newuser@example.com',
    '<password_hash>',
    'New User Name',
    true,
    false,
    NOW(),
    NOW()
);
"

# 4. Send credentials to user securely
```

---

### 5. Change User Role

**Request:** "Make this user an admin"

```bash
# Check current roles
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT u.email, r.role_id
FROM users u
LEFT JOIN roles r ON r.user_id = u.id
WHERE u.email = 'user@example.com';
"

# Add admin role (if roles table exists)
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
INSERT INTO roles (organization_id, user_id, role_id, created_at, updated_at)
SELECT organization_id, id, 'admin', NOW(), NOW()
FROM users WHERE email = 'user@example.com';
"

# Or update existing role
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
UPDATE roles 
SET role_id = 'admin', updated_at = NOW()
WHERE user_id = (SELECT id FROM users WHERE email = 'user@example.com');
"
```

---

### 6. Delete User

**Request:** "Remove this user from our organization"

```bash
# Soft delete (recommended)
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
UPDATE users 
SET is_active = false, updated_at = NOW()
WHERE email = 'user@example.com';
"

# Hard delete (if required - be careful!)
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
-- Delete related records first
DELETE FROM user_sessions WHERE user_id = (SELECT id FROM users WHERE email = 'user@example.com');
DELETE FROM roles WHERE user_id = (SELECT id FROM users WHERE email = 'user@example.com');
-- Then delete user
DELETE FROM users WHERE email = 'user@example.com';
"
```

---

### 7. Create New Organization

**Request:** "Set up a new organization for us"

```bash
# 1. Create organization
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
INSERT INTO organizations (name, slug, is_active, created_at, updated_at)
VALUES ('New Organization Name', 'new-org-slug', true, NOW(), NOW())
RETURNING id;
"
# Note the returned ID

# 2. Create admin user for the organization
# (See "Create New User" above, use the new org_id)

# 3. Verify setup
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
SELECT o.name, o.slug, u.email, u.full_name
FROM organizations o
JOIN users u ON u.organization_id = o.id
WHERE o.slug = 'new-org-slug';
"
```

---

### 8. Export User Data (GDPR)

**Request:** "I need a copy of all my data"

```bash
# Export user's data
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
-- Set context to user's org
SET LOCAL app.current_organization_id = '<org_id>';

-- Export to CSV (example for trials)
\copy (SELECT * FROM trials WHERE created_by = '<user_id>') TO '/tmp/user_trials.csv' CSV HEADER;
"

# Copy file out of container
docker cp $(docker-compose -f compose.prod.yaml ps -q postgres):/tmp/user_trials.csv .

# Repeat for other tables as needed
```

---

### 9. Delete User Data (GDPR Right to Erasure)

**Request:** "Delete all my data"

```bash
# This is complex - need to delete from all tables
# Consider anonymization instead of deletion

# Anonymize user
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production -c "
UPDATE users 
SET 
    email = 'deleted_' || id || '@deleted.local',
    full_name = 'Deleted User',
    hashed_password = 'DELETED',
    is_active = false,
    updated_at = NOW()
WHERE email = 'user@example.com';
"

# For full deletion, consult legal requirements first
```

---

## Troubleshooting Guide

### User Can't Login

| Check | Command | Solution |
|-------|---------|----------|
| User exists | `SELECT * FROM users WHERE email = '...'` | Create user |
| User active | Check `is_active` column | Set to true |
| Org active | Check organization `is_active` | Activate org |
| Password correct | User tries reset | Reset password |
| JWT expired | Check token | User re-login |

### User Sees Wrong Data

| Check | Command | Solution |
|-------|---------|----------|
| Correct org | Check `organization_id` | Move user to correct org |
| RLS working | Test with `SET LOCAL app.current_organization_id` | Check RLS policies |
| Data exists | Count records for org | Data may not exist |

### Performance Issues

| Check | Command | Solution |
|-------|---------|----------|
| Slow queries | Check `pg_stat_statements` | Add indexes |
| High connections | `SELECT count(*) FROM pg_stat_activity` | Connection pooling |
| Memory | `docker stats` | Increase resources |

---

## Communication Templates

### Password Reset Email

```
Subject: Your Bijmantra Password Has Been Reset

Hi [Name],

Your password has been reset as requested. Your temporary password is:

[Temporary Password]

Please log in and change your password immediately.

If you did not request this reset, please contact us immediately.

Best regards,
Bijmantra Support
```

### New Account Email

```
Subject: Welcome to Bijmantra

Hi [Name],

Your Bijmantra account has been created. Here are your login details:

Email: [email]
Temporary Password: [password]
Organization: [org_name]

Please log in at https://bijmantra.org and change your password.

Getting Started:
1. Log in with your temporary password
2. Change your password
3. Explore the dashboard
4. Check out our documentation at [link]

If you have any questions, please don't hesitate to reach out.

Welcome aboard!
Bijmantra Team
```

---

*Document all support interactions for future reference.*
