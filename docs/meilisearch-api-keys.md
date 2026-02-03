# Meilisearch API Key Configuration

## Overview

BijMantra uses Meilisearch for instant, typo-tolerant search across all breeding data. For security, we use different API keys for backend and frontend operations.

## API Keys

### Master Key (Backend Only)

- **Location**: `.env` → `MEILI_MASTER_KEY` and `MEILISEARCH_API_KEY`
- **Value**: `d079c179c18a6229017f9ed12e63e4a03080dc09e71736f75e15a281d07a33ac`
- **Permissions**: Full access (indexing, admin operations, search)
- **Usage**: Backend Python code only
- **⚠️ NEVER expose this key to the frontend**

### Default Search Key (Frontend)

- **Location**: `frontend/.env` → `VITE_MEILISEARCH_API_KEY`
- **Value**: `d5feddbd46068b7e42de69abd3be92a15bb246d21341d3a00266d9074f702170`
- **Permissions**: Search operations only
- **Usage**: Frontend TypeScript/React code
- **✅ Safe to expose in browser** (limited permissions)

## How It Works

1. **Meilisearch Server** runs with `MEILI_MASTER_KEY` set (via Docker Compose)
2. **Backend** uses the master key to:
   - Create and configure indexes
   - Add/update/delete documents
   - Perform admin operations
3. **Frontend** uses the default search key to:
   - Search across all indexes
   - Display search results
   - Cannot modify data or settings

## Default Keys Created by Meilisearch

When you set a `MEILI_MASTER_KEY`, Meilisearch automatically creates these keys:

1. **Default Search API Key** - For frontend search (what we use)
2. **Default Admin API Key** - Full access (backend alternative)
3. **Default Read-Only Admin API Key** - Read-only admin access
4. **Default Chat API Key** - For chat + search operations

## Viewing All Keys

To see all available API keys:

\`\`\`bash
curl -X GET 'http://localhost:7700/keys' \\
-H 'Authorization: Bearer d079c179c18a6229017f9ed12e63e4a03080dc09e71736f75e15a281d07a33ac'
\`\`\`

## Creating Custom Keys

If you need a custom key with specific permissions:

\`\`\`bash
curl -X POST 'http://localhost:7700/keys' \\
-H 'Authorization: Bearer d079c179c18a6229017f9ed12e63e4a03080dc09e71736f75e15a281d07a33ac' \\
-H 'Content-Type: application/json' \\
--data-binary '{
"description": "Custom key description",
"actions": ["search"],
"indexes": ["germplasm", "traits"],
"expiresAt": "2027-01-01T00:00:00Z"
}'
\`\`\`

## Security Best Practices

✅ **DO**:

- Use the default search key for frontend
- Keep the master key in `.env` (gitignored)
- Use environment variables for all keys
- Rotate keys periodically in production

❌ **DON'T**:

- Expose the master key to the frontend
- Commit API keys to version control
- Use the same key for backend and frontend
- Share keys between environments (dev/staging/prod)

## Troubleshooting

### "The provided API key is invalid"

This means:

1. The key is incorrect or expired
2. The key doesn't have permission for the operation
3. Meilisearch server is not running with `MEILI_MASTER_KEY` set

**Solution**: Verify the key exists and has correct permissions:
\`\`\`bash
curl -X GET 'http://localhost:7700/keys' \\
-H 'Authorization: Bearer YOUR_MASTER_KEY'
\`\`\`

### Frontend can't connect to Meilisearch

1. Check `frontend/.env` exists with `VITE_MEILISEARCH_API_KEY`
2. Restart the frontend dev server (Vite needs restart for `.env` changes)
3. Verify Meilisearch is running: `curl http://localhost:7700/health`

## References

- [Meilisearch API Keys Documentation](https://www.meilisearch.com/docs/reference/api/keys)
- [Meilisearch Security Best Practices](https://www.meilisearch.com/docs/learn/security/basic_security)
