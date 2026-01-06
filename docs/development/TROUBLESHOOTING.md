# Bijmantra Troubleshooting Guide

> Common issues and solutions for Bijmantra development

---

## 🔴 White Screen / App Not Loading

### Symptom
The app shows a blank white screen after loading.

### Common Causes & Solutions

#### 1. Invalid Icon Import
**Error**: `Seedling` icon not found in lucide-react

**Fix**: Use `Sprout` instead of `Seedling`
```tsx
// ❌ Wrong
import { Seedling } from 'lucide-react'

// ✅ Correct
import { Sprout } from 'lucide-react'
```

**File**: `frontend/src/framework/shell/DivisionNavigation.tsx`

---

#### 2. Lazy Import Pattern for Named Exports
**Error**: Component doesn't render, React.lazy fails silently

**Cause**: Pages use named exports but lazy() expects default exports

**Fix**: Transform named exports to default exports in the lazy import
```tsx
// ❌ Wrong - assumes default export
const Dashboard = lazy(() => import('@/pages/Dashboard'))

// ✅ Correct - handles named export
const Dashboard = lazy(() => import('@/pages/Dashboard').then(m => ({ default: m.Dashboard })))
```

**Files**: All `frontend/src/divisions/*/routes.tsx` files

---

#### 3. NodeJS.Timeout Type Error
**Error**: `Cannot find namespace 'NodeJS'`

**Fix**: Use `ReturnType<typeof setTimeout>` instead
```tsx
// ❌ Wrong
const timer = useRef<NodeJS.Timeout | null>(null)

// ✅ Correct
const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
```

**Files**: 
- `frontend/src/components/ai/VoiceCommand.tsx`
- `frontend/src/pages/FieldScanner.tsx`

---

## 🟠 Backend Errors

### 1. Greenlet Module Missing
**Error**: `ValueError: the greenlet library is required to use this function`

**Fix**: Install greenlet
```bash
cd backend
./venv/bin/pip install greenlet
```

Then restart the backend server.

---

### 2. Database Connection Failed
**Error**: `Connection refused` or `could not connect to server`

**Fix**: Ensure PostgreSQL is running
```bash
/opt/podman/bin/podman ps | grep postgres
# If not running:
/opt/podman/bin/podman compose up -d postgres
```

---

### 3. Authentication Errors (401)
**Symptom**: API calls return "Not authenticated"

**Cause**: Token expired or not set

**Fix**: The frontend has demo mode fallback. For real auth:
1. Ensure backend is running
2. Login at `/login`
3. Check localStorage for `auth_token`

---

## 🟡 Build Errors

### 1. TypeScript Compilation Fails
**Fix**: Run type check to see all errors
```bash
cd frontend
npx tsc --noEmit
```

Common fixes:
- Add missing type annotations
- Fix import paths
- Use correct generic types

---

### 2. Large Chunk Warning
**Warning**: `Some chunks are larger than 500 kB`

**Note**: This is a warning, not an error. The build still succeeds.

**Future optimization**: Add manual chunks in `vite.config.ts`:
```ts
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
      }
    }
  }
}
```

---

## 🟢 Development Tips

### Check Services Status
```bash
# Frontend dev server
curl -s http://localhost:5173 | head -5

# Backend API
curl -s http://localhost:8000/brapi/v2/serverinfo | head -20

# Infrastructure
/opt/podman/bin/podman ps
```

### Run Tests
```bash
cd frontend
npm run test:run  # Single run
npm test          # Watch mode
```

### Check TypeScript
```bash
cd frontend
npx tsc --noEmit
```

### Build for Production
```bash
cd frontend
npm run build
```

---

## 📞 Getting Help

1. Check this troubleshooting guide
2. Search existing GitHub issues
3. Create a new issue with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Node version, etc.)

---

*Built with 💚 for the global plant breeding community*
