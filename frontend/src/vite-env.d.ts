/// <reference types="vite/client" />

// Web Speech API Types
interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onend: (() => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onstart: (() => void) | null
  start(): void
  stop(): void
  abort(): void
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
  isFinal: boolean
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message: string
}

/* eslint-disable no-var */
declare var SpeechRecognition: {
  prototype: SpeechRecognition
  new(): SpeechRecognition
}

declare var webkitSpeechRecognition: {
  prototype: SpeechRecognition
  new(): SpeechRecognition
}
/* eslint-enable no-var */

interface Window {
  SpeechRecognition: typeof SpeechRecognition
  webkitSpeechRecognition: typeof SpeechRecognition
}

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
  
  // Logging
  readonly VITE_LOG_LEVEL: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR'
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '@google/earthengine';
declare module 'react-cytoscapejs';
declare module 'cytoscape-dagre';
