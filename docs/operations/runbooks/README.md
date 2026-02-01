# 📚 Operational Runbooks

> **Purpose:** Step-by-step procedures for common operations  
> **Last Updated:** December 26, 2025

---

## Available Runbooks

| Runbook | Purpose | Priority |
|---------|---------|----------|
| [Backup & Restore](./backup-restore.md) | Database backup and recovery | 🔴 Critical |
| [Incident Response](./incident-response.md) | Security incident handling | 🔴 Critical |
| [User Support](./user-support.md) | Common support tasks | 🟡 Important |

---

## Runbook Standards

Each runbook follows this format:

1. **Purpose** — What this runbook is for
2. **Prerequisites** — What you need before starting
3. **Procedure** — Step-by-step instructions
4. **Verification** — How to confirm success
5. **Rollback** — How to undo if something goes wrong
6. **Troubleshooting** — Common issues and solutions

---

## Quick Reference

### Emergency Commands

```bash
# Stop all services
docker-compose -f compose.prod.yaml down

# Start all services
docker-compose -f compose.prod.yaml up -d

# View logs
docker-compose -f compose.prod.yaml logs -f

# Restart specific service
docker-compose -f compose.prod.yaml restart backend
```

### Database Quick Commands

```bash
# Connect to database
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod bijmantra_production

# Quick backup
docker-compose -f compose.prod.yaml exec postgres pg_dump -U bijmantra_prod bijmantra_production > backup.sql

# Check connections
docker-compose -f compose.prod.yaml exec postgres psql -U bijmantra_prod -c "SELECT count(*) FROM pg_stat_activity;"
```

---

*Keep these runbooks updated as procedures change.*
