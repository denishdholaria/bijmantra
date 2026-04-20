# BijMantra Public Sync - Simple Manual Workflow

This is a **simple, manual-control** approach to publishing your private repo to the public repo without accidentally leaking sensitive files.

## Why This Approach?

- **Manual review**: You see exactly what gets published
- **No automation surprises**: No GitHub Actions that might leak secrets
- **Simple to understand**: Three clear steps
- **Safe by default**: Creates a local snapshot you can inspect

## The 3-Step Process

### Step 1: Create Snapshot

```bash
./scripts/create_public_snapshot.sh
```

This creates a clean copy at `~/bijmantra-public-snapshot/` with:
- All files from your repo
- Excluding patterns from `.public-exclude`
- A detailed report of what was excluded

**Output location**: `~/bijmantra-public-snapshot/`

### Step 2: Security Scan

```bash
./scripts/scan_public_snapshot.sh
```

This scans the snapshot for:
- `.env` files
- Private keys (`.key`, `.pem`, etc.)
- Sensitive folder names (`.kiro`, `.agent`, `.ai`, etc.)
- Secret patterns in code (API keys, tokens, passwords)
- Hardcoded IPs and domains
- Sensitive TODOs

**Output**: `~/bijmantra-public-snapshot/SECURITY_SCAN.txt`

### Step 3: Review & Publish

```bash
# First, manually review the snapshot
open ~/bijmantra-public-snapshot/

# Check the reports
cat ~/bijmantra-public-snapshot/SNAPSHOT_REPORT.txt
cat ~/bijmantra-public-snapshot/SECURITY_SCAN.txt

# If everything looks good, publish
./scripts/publish_to_public.sh
```

The publish script will:
- Ask for confirmation (type `PUBLISH`)
- Create a fresh git repo with no history
- Force push to `github.com/denishdholaria/bijmantra`

## What Gets Excluded?

Everything in `.public-exclude`:

- `.agent/`, `.ai/` - Agent coordination files
- `.github/copilot-instructions.md` - AI instructions
- `.env*` - Environment files
- `*.key`, `*.pem` - Private keys
- `.bijmantra/`, `.openclaw/` - Runtime state
- `ops-private/` - Private operations docs
- And more...

## Safety Features

1. **Local snapshot**: Everything happens locally first
2. **Security scanner**: Catches common secret patterns
3. **Manual review**: You see everything before publishing
4. **Confirmation required**: Must type `PUBLISH` to proceed
5. **No git history**: Public repo gets a clean snapshot, not your full history

## Quick Reference

```bash
# Full workflow
./scripts/create_public_snapshot.sh
./scripts/scan_public_snapshot.sh
open ~/bijmantra-public-snapshot/  # Review manually
./scripts/publish_to_public.sh

# Just create snapshot (no publish)
./scripts/create_public_snapshot.sh

# Re-scan existing snapshot
./scripts/scan_public_snapshot.sh
```

## Troubleshooting

**Q: Snapshot location?**  
A: `~/bijmantra-public-snapshot/`

**Q: How to add more exclusions?**  
A: Edit `.public-exclude` in your repo root

**Q: Can I review before publishing?**  
A: Yes! That's the whole point. Review the snapshot folder before running `publish_to_public.sh`

**Q: What if scan finds issues?**  
A: Fix them in your private repo, then re-run `create_public_snapshot.sh`

**Q: How to update public repo?**  
A: Run all 3 steps again. The publish script force-pushes a fresh snapshot.

## Comparison with Old Workflow

| Feature | Old (Automated) | New (Manual) |
|---------|----------------|--------------|
| Control | GitHub Actions | You |
| Review | Automated | Manual |
| Safety | Trust automation | Verify yourself |
| Complexity | High | Low |
| Leak risk | Medium | Very Low |

## Emergency: Found a Leak?

If you accidentally published sensitive data:

1. **Immediately** rotate all secrets/keys
2. Delete the public repo (or make it private)
3. Review what was leaked
4. Create a fresh public repo
5. Re-run the 3-step process

## Notes

- The public repo has **no git history** - just clean snapshots
- Each publish is a force push with a single commit
- Your private repo history stays private
- The snapshot is created fresh each time (old one is deleted)
