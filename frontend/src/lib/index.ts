/**
 * Library Index
 * Central export for all utility libraries
 */

// Real-time events (SSE-based)
export { realtime, RealtimeEvents, useRealtimeEvent, useRealtimeConnection } from './realtime'

// Socket.io real-time collaboration
export { socketService, SocketEvents, useSocket, usePresence, useRoom, useSocketStore } from './socket'
export type { OnlineUser, DataChangeEvent, RoomMessage } from './socket'

// Analytics (DuckDB-WASM)
export { analytics, BREEDING_QUERIES, useAnalytics } from './duckdb-analytics'

// Search (local fuzzy search)
export { searchService, useSearch } from './search'

// Meilisearch (instant search)
export { meilisearch, useMeilisearch, INDEXES } from './meilisearch'
export type { GermplasmSearchResult, TraitSearchResult, TrialSearchResult, UnifiedSearchResult } from './meilisearch'

// Sentry (error tracking)
export {
  initSentry,
  setUser,
  clearUser,
  captureException,
  captureMessage,
  addBreadcrumb,
  trackOperation,
  ErrorBoundary as SentryErrorBoundary,
  withErrorBoundary,
  Profiler,
} from './sentry'

// PostHog (product analytics)
export {
  initPostHog,
  identifyUser,
  resetUser,
  trackEvent,
  trackPageView,
  trackBreedingEvent,
  AnalyticsEvents,
  isFeatureEnabled,
  getFeatureFlag,
  FeatureFlags,
  useFeatureFlag,
  useAnalytics as usePostHogAnalytics,
} from './posthog'

// Offline sync (CRDTs)
export {
  offlineSync,
  useOfflineSync,
  useSyncableCollection,
} from './offline-sync'
export type { SyncableDocument, SyncStatus, SyncConflict } from './offline-sync'

// WebGPU (GPU acceleration)
export {
  initWebGPU,
  isWebGPUAvailable,
  getGPUCapabilities,
  gpuMatrixMultiply,
  gpuCorrelationMatrix,
  useWebGPU,
} from './webgpu'
export type { GPUCapabilities, ComputeResult } from './webgpu'
