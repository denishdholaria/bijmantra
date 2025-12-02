# Cloudflare-Compatible PWA Tech Stack (Free Tier)

## Overview

Cloudflare's free tier supports a specific set of technologies. Here's what works fully on Cloudflare without external services.

---

## ✅ Fully Compatible Stack

### Frontend (Cloudflare Pages)
| Technology | Notes |
|------------|-------|
| React / Vue / Svelte / Solid | Any SPA framework |
| Next.js | Static export or Edge runtime |
| Nuxt | Static or Edge |
| Astro | Static or Hybrid |
| Remix | With Cloudflare adapter |
| SvelteKit | With Cloudflare adapter |
| Qwik | Native Cloudflare support |
| Vite / Webpack | Any bundler |

### Backend (Cloudflare Workers)
| Technology | Notes |
|------------|-------|
| JavaScript / TypeScript | Native support |
| Hono | Lightweight, fast framework |
| Itty-router | Minimal router |
| Worktop | Full-featured framework |
| tRPC | Type-safe APIs |
| GraphQL Yoga | GraphQL server |

### Database (Cloudflare D1)
| Technology | Notes |
|------------|-------|
| SQLite | D1 is SQLite-based |
| Drizzle ORM | Best D1 support |
| Prisma | D1 adapter available |
| Kysely | Query builder |

### Storage (Cloudflare R2)
| Technology | Notes |
|------------|-------|
| S3-compatible API | Images, files, blobs |
| 10 GB free | No egress fees |

### Key-Value (Cloudflare KV)
| Technology | Notes |
|------------|-------|
| Key-value store | Sessions, cache, config |
| 100k reads/day free | 1k writes/day free |

### Queues & Cron
| Technology | Notes |
|------------|-------|
| Cloudflare Queues | Message queues |
| Cron Triggers | Scheduled tasks |

---

## 🏗️ Recommended Full-Stack Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Cloudflare Edge                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐    ┌──────────────────────────┐   │
│  │   Pages      │    │      Workers             │   │
│  │              │    │                          │   │
│  │  React/Vue   │───▶│  Hono / Itty-router     │   │
│  │  SvelteKit   │    │  TypeScript API          │   │
│  │  Next.js     │    │                          │   │
│  └──────────────┘    └──────────┬───────────────┘   │
│                                 │                    │
│         ┌───────────────────────┼───────────────┐   │
│         │                       │               │   │
│         ▼                       ▼               ▼   │
│  ┌──────────────┐    ┌──────────────┐  ┌────────┐  │
│  │     D1       │    │     R2       │  │   KV   │  │
│  │   SQLite     │    │   Storage    │  │ Cache  │  │
│  │   Database   │    │   (Images)   │  │        │  │
│  └──────────────┘    └──────────────┘  └────────┘  │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Example Project Structure

```
my-cloudflare-pwa/
├── src/
│   ├── client/           # Frontend (React/Vue/Svelte)
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.tsx
│   └── server/           # Workers API
│       ├── routes/
│       ├── db/
│       └── index.ts
├── public/
│   ├── manifest.json     # PWA manifest
│   └── sw.js             # Service worker
├── drizzle/
│   └── schema.ts         # D1 database schema
├── wrangler.toml         # Cloudflare config
├── package.json
└── vite.config.ts
```

---

## 🛠️ Recommended Frameworks

### Option 1: Hono + React (Simplest)
```bash
npm create hono@latest my-app -- --template cloudflare-pages
```

### Option 2: SvelteKit (Full-featured)
```bash
npm create svelte@latest my-app
# Select: Cloudflare adapter
```

### Option 3: Remix (React + Server)
```bash
npx create-remix@latest --template remix-run/remix/templates/cloudflare-pages
```

### Option 4: Next.js (Edge Runtime)
```bash
npx create-next-app@latest --example with-cloudflare
```

---

## 💰 Free Tier Limits

| Service | Free Limit |
|---------|------------|
| Pages | Unlimited sites, 500 builds/month |
| Workers | 100k requests/day |
| D1 | 5 GB storage, 5M rows read/day |
| R2 | 10 GB storage, 10M reads/month |
| KV | 100k reads/day, 1k writes/day |

---

## ⚠️ What Cloudflare Does NOT Support

| Technology | Alternative |
|------------|-------------|
| Python / FastAPI | Rewrite in TypeScript |
| PostgreSQL | Use D1 (SQLite) or Hyperdrive |
| Redis | Use KV or Durable Objects |
| WebSockets (long) | Use Durable Objects |
| Large file uploads | Use R2 direct upload |
| Background jobs > 30s | Use Queues |

---

## 🔄 Migration Path for Bijmantra

To make Bijmantra fully Cloudflare-compatible:

1. **Keep**: React frontend (works as-is on Pages)
2. **Rewrite**: FastAPI → Hono (TypeScript)
3. **Migrate**: PostgreSQL → D1 (SQLite)
4. **Move**: MinIO → R2
5. **Replace**: Redis → KV

**Estimated effort**: 2-4 weeks for full rewrite

---

## 🚀 Quick Start Template

```bash
# Create a Cloudflare-native full-stack app
npm create cloudflare@latest my-pwa -- --template full-stack

# Or use Hono with D1
npm create hono@latest my-api -- --template cloudflare-pages
```

---

## Summary

For a **100% Cloudflare-compatible PWA**:

```
Frontend: React/Vue/Svelte + Vite
Backend:  Hono or Itty-router (TypeScript)
Database: D1 (SQLite) + Drizzle ORM
Storage:  R2
Cache:    KV
```

This stack runs entirely on Cloudflare's edge network with zero external dependencies.
