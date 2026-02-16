# PWA Strategy

## Goals
- Keep field workflows usable without connectivity.
- Prioritize observation entry reliability and eventual consistency.
- Reduce core shell size and defer heavy scientific visualizations.

## Offline Data Strategy
- Service worker uses Workbox with `StaleWhileRevalidate` for metadata/datasets.
- Draft observations are stored in IndexedDB (`draft_observations`).
- Background sync pushes drafts to `/api/v2/pwa/drafts/sync` when online.

## Conflict Resolution
- Sync conflicts are surfaced in a dedicated frontend panel (`SyncConflict`) and existing conflict dialog.
- Default policy is manual confirmation for conflicting fields.

## Performance Plan
- Core shell is pre-cached using inject manifest.
- Dataset and image caches use bounded expiration.
- ECharts remains tree-shaken; route-level lazy loading should be expanded across heavy modules.

## Mobile Awareness
- Battery guard: sync is skipped if battery <20% and not charging.
- Network guard: heavy sync is skipped on 2G/3G conditions.
- Trial pages include explicit "Download Offline" action for field prep.

## Notifications
- Service worker supports push events and notification click deep links.
- Backend endpoints manage push subscriptions and queued payloads.

## Verification Checklist
- `npm run build` includes generated `manifest.webmanifest` and service worker.
- IndexedDB CRUD and sync tests run via Vitest.
- PWA install and Lighthouse checks are pending manual device validation.
