import { LEGACY_REEVU_STORAGE_KEY } from '@/lib/legacyReevu'
import {
  DEFAULT_REEVU_BYOK_MODEL,
  DEFAULT_REEVU_BYOK_PROVIDER,
} from '@/lib/ai-model-catalog'

export interface ReevuConfig {
  mode: 'managed' | 'byok'
  byok: {
    provider: string
    apiKey: string
    model: string
  }
}

interface LegacyAIConfig {
  cloud?: {
    provider?: string
    model?: string
  }
}

export interface ReevuStoredMessageBase {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

interface StorageLike {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

type ErrorLogger = (error: unknown) => void

const STORAGE_KEY = 'reevu_conversation_history'
const AI_CONFIG_KEY = 'bijmantra_ai_config_v2'
const REEVU_CONFIG_KEY = 'bijmantra_reevu_config_v1'

export const MAX_STORED_REEVU_MESSAGES = 100

export const defaultReevuConfig: ReevuConfig = {
  mode: 'managed',
  byok: {
    provider: DEFAULT_REEVU_BYOK_PROVIDER,
    apiKey: '',
    model: DEFAULT_REEVU_BYOK_MODEL
  }
}

function getBrowserStorage(storage?: StorageLike): StorageLike {
  return storage || localStorage
}

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object'
}

function normalizeReevuConfig(value: unknown): ReevuConfig | null {
  if (!isObject(value)) {
    return null
  }

  const byok = isObject(value.byok) ? value.byok : null
  const mode = value.mode === 'managed' || value.mode === 'byok' ? value.mode : null
  if (!mode) {
    return null
  }

  return {
    mode: 'managed',
    byok: {
      provider: typeof byok?.provider === 'string' ? byok.provider : defaultReevuConfig.byok.provider,
      apiKey: '',
      model: typeof byok?.model === 'string' ? byok.model : defaultReevuConfig.byok.model,
    }
  }
}

function normalizeLegacyAIConfig(value: unknown): ReevuConfig | null {
  if (!isObject(value)) {
    return null
  }

  const cloud = isObject(value.cloud) ? value.cloud as LegacyAIConfig['cloud'] : null
  if (!cloud) {
    return null
  }

  return {
    mode: 'managed',
    byok: {
      provider: typeof cloud.provider === 'string' ? cloud.provider : defaultReevuConfig.byok.provider,
      apiKey: '',
      model: typeof cloud.model === 'string' ? cloud.model : defaultReevuConfig.byok.model,
    }
  }
}

function parseStoredJson<T>(raw: string | null, onError?: ErrorLogger): T | null {
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as T
  } catch (error) {
    onError?.(error)
    return null
  }
}

export function loadStoredReevuMessages<T extends ReevuStoredMessageBase>(
  initialMessage: T,
  storage?: StorageLike,
  onError?: ErrorLogger,
): T[] {
  const store = getBrowserStorage(storage)
  const parsed = parseStoredJson<Array<Omit<T, 'timestamp'> & { timestamp: Date | string }>>(
    store.getItem(STORAGE_KEY) || store.getItem(LEGACY_REEVU_STORAGE_KEY),
    onError,
  )

  if (!parsed) {
    return [{ ...initialMessage, timestamp: new Date(initialMessage.timestamp) }]
  }

  return parsed.map(message => ({
    ...message,
    timestamp: new Date(message.timestamp),
  } as T))
}

export function persistReevuMessages<T extends { timestamp: Date }>(
  messages: T[],
  storage?: StorageLike,
  maxStoredMessages = MAX_STORED_REEVU_MESSAGES,
): void {
  const store = getBrowserStorage(storage)
  store.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-maxStoredMessages)))
}

export function clearStoredReevuMessages(storage?: StorageLike): void {
  const store = getBrowserStorage(storage)
  store.removeItem(STORAGE_KEY)
  store.removeItem(LEGACY_REEVU_STORAGE_KEY)
}

export function loadStoredReevuConfig(storage?: StorageLike, onError?: ErrorLogger): ReevuConfig {
  const store = getBrowserStorage(storage)
  let resolvedConfig = defaultReevuConfig

  const savedReevu = normalizeReevuConfig(parseStoredJson(store.getItem(REEVU_CONFIG_KEY), onError))
  if (savedReevu) {
    resolvedConfig = savedReevu
    store.setItem(REEVU_CONFIG_KEY, JSON.stringify(savedReevu))
  }

  const legacyAI = normalizeLegacyAIConfig(parseStoredJson(store.getItem(AI_CONFIG_KEY), onError))
  if (legacyAI) {
    resolvedConfig = legacyAI
    store.setItem(REEVU_CONFIG_KEY, JSON.stringify(legacyAI))
  }

  return resolvedConfig
}

export function persistReevuConfig(config: ReevuConfig, storage?: StorageLike): void {
  const store = getBrowserStorage(storage)
  store.setItem(REEVU_CONFIG_KEY, JSON.stringify(config))
}