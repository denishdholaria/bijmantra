# Railway Deployment Guide

Deploy Bijmantra to Railway for a full working demo.

## Prerequisites

1. GitHub account (repo already connected)
2. Railway account: https://railway.app (sign up with GitHub)

## Quick Deploy

### Step 1: Create Railway Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `denishdholaria/bijmantra`
4. Railway will detect the monorepo

### Step 2: Add PostgreSQL

1. In your Railway project, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway auto-provisions the database

### Step 3: Configure Backend Service

1. Click "New Service" → "GitHub Repo" → select `bijmantra`
2. Set root directory: `backend`
3. Add environment variables:

```
POSTGRES_SERVER=${{Postgres.PGHOST}}
POSTGRES_PORT=${{Postgres.PGPORT}}
POSTGRES_USER=${{Postgres.PGUSER}}
POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}
POSTGRES_DB=${{Postgres.PGDATABASE}}
SECRET_KEY=<generate-random-64-char-string>
ENVIRONMENT=production
BACKEND_CORS_ORIGINS=["https://your-frontend.up.railway.app"]
```

### Step 4: Configure Frontend Service

1. Click "New Service" → "GitHub Repo" → select `bijmantra`
2. Set root directory: `frontend`
3. Add environment variables:

```
VITE_API_BASE_URL=https://your-backend.up.railway.app
```

### Step 5: Generate Domain

1. Click on each service → Settings → Generate Domain
2. Update CORS origins in backend with frontend URL
3. Update VITE_API_BASE_URL in frontend with backend URL

## Environment Variables Reference

### Backend
| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_SERVER` | DB host | `${{Postgres.PGHOST}}` |
| `POSTGRES_PORT` | DB port | `${{Postgres.PGPORT}}` |
| `POSTGRES_USER` | DB user | `${{Postgres.PGUSER}}` |
| `POSTGRES_PASSWORD` | DB password | `${{Postgres.PGPASSWORD}}` |
| `POSTGRES_DB` | DB name | `${{Postgres.PGDATABASE}}` |
| `SECRET_KEY` | JWT secret | Random 64-char string |
| `ENVIRONMENT` | Environment | `production` |
| `BACKEND_CORS_ORIGINS` | Allowed origins | `["https://..."]` |

### Frontend
| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend URL | `https://backend.up.railway.app` |

## Database Migrations

After first deploy, run migrations:

```bash
# In Railway CLI or dashboard shell
cd backend
python run_migrations.py
```

Or add to backend start command:
```
python run_migrations.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Costs

Railway free tier includes:
- $5/month credit
- Enough for demo usage
- Sleeps after inactivity (wakes on request)

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify environment variables are set
- Check logs in Railway dashboard

### Frontend can't reach backend
- Verify CORS origins include frontend URL
- Check VITE_API_BASE_URL is correct
- Ensure backend is running

### Database connection fails
- Use Railway's variable references: `${{Postgres.PGHOST}}`
- Don't hardcode credentials

## Alternative: One-Click Deploy

Add this button to README for easy deployment:

```markdown
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/...)
```

(Requires creating a Railway template)
