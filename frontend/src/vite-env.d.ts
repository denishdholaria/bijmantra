/// <reference types="vite/client" />

interface ImportMetaEnv {
  // API
  readonly VITE_API_URL: string
  
  // Meilisearch
  readonly VITE_MEILISEARCH_HOST: string
  readonly VITE_MEILISEARCH_API_KEY: string
  
  // Socket.io
  readonly VITE_SOCKET_URL: string
  
  // Sentry
  readonly VITE_SENTRY_DSN: string
  readonly VITE_APP_VERSION: string
  
  // PostHog
  readonly VITE_POSTHOG_API_KEY: string
  readonly VITE_POSTHOG_HOST: string
  
  // AI Providers
  readonly VITE_OPENAI_API_KEY: string
  readonly VITE_ANTHROPIC_API_KEY: string
  readonly VITE_GOOGLE_AI_API_KEY: string
  
  // Feature flags
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_ENABLE_REALTIME: string
  readonly VITE_ENABLE_AI: string
  readonly VITE_ENABLE_WEBGPU: string
  readonly VITE_ENABLE_OFFLINE_SYNC: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
