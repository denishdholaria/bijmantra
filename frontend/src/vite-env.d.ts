/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />
/// <reference types="@webgpu/types" />

// Web Speech API Types
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onstart: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

declare var SpeechRecognition: {
  prototype: SpeechRecognition;
  new (): SpeechRecognition;
};

declare var webkitSpeechRecognition: {
  prototype: SpeechRecognition;
  new (): SpeechRecognition;
};

interface Window {
  SpeechRecognition: typeof SpeechRecognition;
  webkitSpeechRecognition: typeof SpeechRecognition;
}

interface ImportMetaEnv {
  // API
  readonly VITE_API_URL: string;

  // Socket.io
  readonly VITE_SOCKET_URL: string;

  // Authentication
  readonly VITE_AUTH_PROVIDER: string;
  readonly VITE_KEYCLOAK_ENABLED: string;
  readonly VITE_KEYCLOAK_URL: string;
  readonly VITE_KEYCLOAK_REALM: string;
  readonly VITE_KEYCLOAK_CLIENT_ID: string;
  readonly VITE_LOCAL_PASSWORD_LOGIN_ENABLED: string;

  // Sentry
  readonly VITE_SENTRY_DSN: string;
  readonly VITE_APP_VERSION: string;

  // PostHog
  readonly VITE_POSTHOG_API_KEY: string;
  readonly VITE_POSTHOG_HOST: string;

  // AI Providers
  readonly VITE_OPENAI_API_KEY: string;
  readonly VITE_ANTHROPIC_API_KEY: string;
  readonly VITE_GOOGLE_AI_API_KEY: string;

  // Feature flags
  readonly VITE_ENABLE_ANALYTICS: string;
  readonly VITE_ENABLE_REALTIME: string;
  readonly VITE_ENABLE_AI: string;
  readonly VITE_ENABLE_WEBGPU: string;
  readonly VITE_ENABLE_OFFLINE_SYNC: string;

  // Logging
  readonly VITE_LOG_LEVEL: "DEBUG" | "INFO" | "WARN" | "ERROR";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module "@google/earthengine";
declare module "react-cytoscapejs";
declare module "cytoscape-dagre";

// React Three Fiber Type Augmentation
import { ThreeElements } from "@react-three/fiber";

declare global {
  namespace JSX {
    // React Three Fiber intentionally augments JSX with the imported element map.
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type
    interface IntrinsicElements extends ThreeElements {}
  }
}
