# ✅ Deployment Checklist

> **Purpose:** Pre-launch verification checklist  
> **Last Updated:** December 26, 2025

---

## Pre-Deployment Checklist

### 🔴 Critical (Must Complete Before Launch)

#### Code & Data

- [ ] **Migrate remaining mock data files to database**
  - [ ] `scales.py` — Remove DEMO_SCALES array
  - [ ] `methods.py` — Remove DEMO_METHODS array
  - [ ] `observationlevels.py` — Remove DEMO_OBSERVATION_LEVELS
  - [ ] `attributevalues.py` — Remove init_demo_data()
  - [ ] `attributes.py` — Remove init_demo_data()
  - [ ] `extensions/iot.py` — Remove generate_demo_*() functions

- [ ] **Verify all tests pass**
  ```bash
  cd backend && pytest
  cd frontend && npm run test
  ```

- [ ] **Build production assets**
  ```bash
  cd frontend && npm run build
  ```

#### Environment Configuration

- [ ] **Create production .env file**
  ```bash
  # Required settings
  ENVIRONMENT=production
  SEED_DEMO_DATA=false
  DEMO_MODE=false
  ```

- [ ] **Generate strong secrets**
  ```bash
  # Generate SECRET_KEY (64 chars)
  openssl rand -hex 32
  
  # Generate POSTGRES_PASSWORD
  openssl rand -base64 24
  
  # Generate REDIS_PASSWORD
  openssl rand -base64 24
  ```

- [ ] **Configure database connection**
  ```bash
  POSTGRES_SERVER=<production-host>
  POSTGRES_PORT=5432
  POSTGRES_USER=bijmantra_prod
  POSTGRES_PASSWORD=<generated-password>
  POSTGRES_DB=bijmantra_production
  ```

#### Database

- [ ] **Run all migrations**
  ```bash
  cd backend
  alembic upgrade head
  ```

- [ ] **Verify RLS policies are active**
  ```sql
  SELECT tablename, policyname 
  FROM pg_policies 
  WHERE schemaname = 'public';
  ```

- [ ] **Create initial organization**
  ```sql
  INSERT INTO organizations (name, slug, is_active)
  VALUES ('Your Organization', 'your-org', true);
  ```

- [ ] **Create admin user**
  ```bash
  cd backend
  python -m app.db_seed --create-admin
  ```

#### Security

- [ ] **SSL/TLS certificates configured**
  - Caddy handles this automatically with Let's Encrypt
  - Verify domain is pointed to server

- [ ] **Firewall rules configured**
  - Port 80 (HTTP → redirects to HTTPS)
  - Port 443 (HTTPS)
  - Port 22 (SSH — restrict to your IP)

- [ ] **Secrets not in code**
  - No hardcoded passwords
  - No API keys in repository
  - All secrets in environment variables

---

### 🟡 Important (Complete Within First Week)

#### Monitoring & Logging

- [ ] **Health check endpoint working**
  ```bash
  curl https://your-domain.com/health
  # Should return: {"status": "healthy"}
  ```

- [ ] **Error alerting configured**
  - Email alerts for 5xx errors
  - Slack/Discord webhook for critical issues

- [ ] **Log aggregation set up**
  - Application logs → centralized logging
  - Access logs → security monitoring

#### Backups

- [ ] **Database backup configured**
  ```bash
  # Daily backup script
  pg_dump -h localhost -U bijmantra_prod bijmantra_production | gzip > backup_$(date +%Y%m%d).sql.gz
  ```

- [ ] **Backup storage configured**
  - S3/MinIO bucket for backups
  - Retention policy (30 days minimum)

- [ ] **Backup restoration tested**
  ```bash
  # Test restore to staging
  gunzip -c backup_20251226.sql.gz | psql -h staging -U bijmantra staging_db
  ```

#### Performance

- [ ] **Database indexes verified**
  ```sql
  SELECT indexname, tablename 
  FROM pg_indexes 
  WHERE schemaname = 'public' 
  AND indexname LIKE '%organization_id%';
  ```

- [ ] **Redis caching working**
  ```bash
  redis-cli ping
  # Should return: PONG
  ```

- [ ] **Static assets cached**
  - Verify Cache-Control headers
  - CDN configured (optional)

---

### 🟢 Nice to Have (Complete Within First Month)

#### Platform Admin

- [ ] **Private repo set up** (bijmantraorg)
- [ ] **Platform admin dashboard deployed**
- [ ] **Organization management working**

#### Security Enhancements

- [ ] **2FA enabled for admin accounts**
- [ ] **Rate limiting configured**
- [ ] **API key management implemented**

#### Documentation

- [ ] **Runbooks created**
  - Incident response
  - Backup/restore
  - User support

- [ ] **API documentation updated**
- [ ] **User guide published**

---

## Deployment Commands

### Start Production Stack

```bash
# Using Docker Compose
docker-compose -f compose.prod.yaml up -d

# Or using Podman
podman-compose -f compose.prod.yaml up -d
```

### Verify Deployment

```bash
# Check all containers running
docker-compose -f compose.prod.yaml ps

# Check logs
docker-compose -f compose.prod.yaml logs -f

# Test health endpoint
curl -I https://your-domain.com/health
```

### Rollback Procedure

```bash
# Stop current deployment
docker-compose -f compose.prod.yaml down

# Restore previous version
git checkout <previous-tag>
docker-compose -f compose.prod.yaml up -d

# Restore database if needed
gunzip -c backup_previous.sql.gz | psql -h localhost -U bijmantra_prod bijmantra_production
```

---

## Post-Deployment Verification

### Functional Tests

- [ ] Login works
- [ ] User registration works
- [ ] Data isolation verified (org A can't see org B data)
- [ ] Demo user sees only demo data
- [ ] Admin functions work
- [ ] API endpoints respond correctly

### Security Tests

- [ ] HTTPS enforced (HTTP redirects)
- [ ] Security headers present
- [ ] JWT tokens expire correctly
- [ ] RLS policies filtering correctly

### Performance Tests

- [ ] Page load < 3 seconds
- [ ] API response < 500ms
- [ ] No memory leaks after 24h

---

## Emergency Contacts

| Role | Contact | When to Contact |
|------|---------|-----------------|
| Platform Admin | (you) | All issues |
| Database Admin | TBD | Database issues |
| Infrastructure | TBD | Server/network issues |

---

*Complete all 🔴 Critical items before launch. Update this checklist as you progress.*
