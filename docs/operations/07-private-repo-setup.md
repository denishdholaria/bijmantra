# 🔐 Private Repository Setup Guide

> **Repository:** `https://github.com/denishdholaria/bijmantraorg.git`  
> **Purpose:** Main working repository (everything, zero restrictions)  
> **Last Updated:** December 26, 2025

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   bijmantraorg (PRIVATE)          bijmantra (PUBLIC)            │
│   ═══════════════════════         ══════════════════            │
│                                                                 │
│   Your main working repo    ──►   Open source release           │
│   Everything, no filters          Filtered, safe for public     │
│                                                                 │
│   ┌─────────────────────┐         ┌─────────────────────┐       │
│   │ All source code     │         │ All source code     │       │
│   │ docs/gupt/  │    ✗    │                     │       │
│   │ secrets/            │    ✗    │                     │       │
│   │ platform-admin/     │    ✗    │                     │       │
│   │ configs/            │    ✗    │                     │       │
│   │ .env files          │    ✗    │ .env.example only   │       │
│   └─────────────────────┘         └─────────────────────┘       │
│                                                                 │
│              GitHub Action: sync-to-public.yml                  │
│              Triggers on push to main branch                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why This Architecture?

### Previous Approach (Submodule - Rejected)
- Private repo contains admin tools
- Public repo as git submodule
- **Problem:** Complex, two repos to manage, sync nightmares

### Current Approach (Single Source + Filtered Sync)
- **Private repo = Your ONLY working repo**
- Work freely, commit everything
- GitHub Action automatically syncs filtered content to public
- **Simple:** One repo to work in, one command to push

---

## What Gets Filtered (Stays Private)

Defined in `.github/sync-to-public-exclude.txt`:

| Path | Reason |
|------|--------|
| `docs/gupt/` | Business strategy, security docs, personal notes |
| `secrets/` | Production credentials |
| `platform-admin/` | Private admin tools |
| `configs/` | Per-organization configurations |
| `.env` files | Environment secrets |
| `bijmantraorg-setup/` | Setup files (temporary) |

---

## Setup Instructions

### Step 1: Change Origin to Private Repo

```bash
cd /Volumes/ai/PlantBreedingAPP/bijmantra

# Rename current origin (public) to 'public'
git remote rename origin public

# Add private repo as new origin
git remote add origin git@github.com:denishdholaria/bijmantraorg.git

# Verify remotes
git remote -v
# Should show:
# origin   git@github.com:denishdholaria/bijmantraorg.git (fetch)
# origin   git@github.com:denishdholaria/bijmantraorg.git (push)
# public   https://github.com/denishdholaria/bijmantra.git (fetch)
# public   https://github.com/denishdholaria/bijmantra.git (push)
```

### Step 2: Push Everything to Private Repo

```bash
# Push all branches and tags to private repo
git push -u origin main --force
git push origin --tags
```

### Step 3: Create GitHub Secret for Sync

1. Go to https://github.com/denishdholaria/bijmantraorg/settings/secrets/actions
2. Click "New repository secret"
3. Name: `PUBLIC_REPO_TOKEN`
4. Value: Create a Personal Access Token with `repo` scope
   - Go to https://github.com/settings/tokens
   - Generate new token (classic)
   - Select `repo` scope
   - Copy the token

### Step 4: Test the Sync

```bash
# Make a small change
echo "# Test" >> README.md
git add README.md
git commit -m "test: verify sync workflow"
git push origin main
```

Check GitHub Actions tab in bijmantraorg to see the sync run.

---

## Daily Workflow

### Normal Development

```bash
# Work as usual - everything goes to private repo
git add .
git commit -m "feat: add new feature"
git push origin main

# GitHub Action automatically syncs to public repo
# (filtered, excluding confidential content)
```

### Manual Sync (if needed)

```bash
# Go to GitHub Actions tab
# Click "Sync to Public Repository"
# Click "Run workflow"
```

### Check What's Public

```bash
# Clone public repo to verify
git clone https://github.com/denishdholaria/bijmantra.git /tmp/bijmantra-public
ls /tmp/bijmantra-public/docs/
# Should NOT contain 'confidential/' directory
```

---

## Adding New Private Content

If you create new files/directories that should stay private:

1. Edit `.github/sync-to-public-exclude.txt`
2. Add the path pattern
3. Commit and push

```bash
# Example: Add new private directory
echo "my-private-stuff/" >> .github/sync-to-public-exclude.txt
git add .github/sync-to-public-exclude.txt
git commit -m "chore: exclude my-private-stuff from public sync"
git push origin main
```

---

## Troubleshooting

### Sync Failed with 403 Error

**Error:** `remote: Permission to denishdholaria/bijmantra.git denied to github-actions[bot]`

This means the `PUBLIC_REPO_TOKEN` doesn't have permission to push. Fix:

1. **Test your token locally first:**
   ```bash
   ./scripts/test-public-repo-token.sh YOUR_TOKEN_HERE
   ```

2. **Generate a NEW token:**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - **IMPORTANT:** Select `repo` scope (full control)
   - Set expiration (90 days recommended)
   - Copy the token immediately (you won't see it again)

3. **Update the secret:**
   - Go to https://github.com/denishdholaria/bijmantraorg/settings/secrets/actions
   - **Delete** the existing `PUBLIC_REPO_TOKEN`
   - Click "New repository secret"
   - Name: `PUBLIC_REPO_TOKEN`
   - Value: Paste your new token
   - Click "Add secret"

4. **Re-enable the workflow:**
   ```bash
   mv .github/workflows/sync-to-public.yml.disabled .github/workflows/sync-to-public.yml
   git add .github/workflows/sync-to-public.yml
   git commit -m "chore: re-enable sync workflow"
   git push origin main
   ```

5. **Check the Actions tab** to see if sync succeeds

### Common Token Issues

| Issue | Solution |
|-------|----------|
| Token expired | Generate new token, update secret |
| Wrong scope | Token needs `repo` scope, not just `public_repo` |
| Token not saved | Delete and re-create the secret |
| Typo in secret name | Must be exactly `PUBLIC_REPO_TOKEN` |

### Sync Failed (Other Reasons)

1. Check GitHub Actions logs in bijmantraorg
2. Verify `PUBLIC_REPO_TOKEN` secret is set correctly
3. Ensure token has `repo` scope

### Confidential File Leaked to Public

1. **Immediately** rotate any exposed secrets
2. Remove from public repo history:
   ```bash
   # In public repo
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/file" \
     --prune-empty --tag-name-filter cat -- --all
   git push --force
   ```
3. Add path to exclude list to prevent future leaks

### Want to Push Directly to Public (bypass sync)

```bash
# Only for emergencies - prefer the automated sync
git push public main
```

---

## Security Checklist

- [ ] Private repo is actually private (check GitHub settings)
- [ ] `PUBLIC_REPO_TOKEN` has minimal required permissions
- [ ] `docs/gupt/` is in exclude list
- [ ] `secrets/` is in exclude list
- [ ] `.env` files are in exclude list
- [ ] No hardcoded secrets in code (use environment variables)

---

## Summary

| Repo | URL | Purpose | You Push Here? |
|------|-----|---------|----------------|
| **bijmantraorg** | github.com/denishdholaria/bijmantraorg | Main working repo | ✅ YES |
| **bijmantra** | github.com/denishdholaria/bijmantra | Public release | ❌ NO (auto-synced) |

**Remember:** Work in private repo only. Public repo is automatically updated.

---

*This is your command center. Keep it secure.*
