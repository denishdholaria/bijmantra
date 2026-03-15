type FetchLike = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>

export interface ReevuBackendStatus {
  reachable: boolean
  provider?: string
  model?: string
  providerSource?: string
  providerSourceLabel?: string
  templateOnly?: boolean
  authRequired?: boolean
}

export interface EffectiveBackend {
  mode: 'cloud' | 'local' | 'none'
  name: string
  ready: boolean
}

interface ReevuBackendStatusRequestOptions {
  force?: boolean
  maxAgeMs?: number
}

interface ReevuStatusProviderState {
  available?: boolean
  configured?: boolean
}

interface ReevuStatusPayload {
  active_provider?: string
  active_model?: string
  active_provider_source?: string
  active_provider_source_label?: string
  providers?: Record<string, ReevuStatusProviderState>
}

const REAL_PROVIDER_IDS = ['ollama', 'groq', 'google', 'huggingface', 'functiongemma', 'openai', 'anthropic'] as const

const PROVIDER_NAMES: Record<string, string> = {
  ollama: 'Ollama (Local)',
  google: 'Google Gemini',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  groq: 'Groq',
  functiongemma: 'FunctionGemma',
  huggingface: 'HuggingFace Inference'
}

const DEFAULT_REEVU_STATUS_CACHE_MS = 5000

let lastStatusCache: { token: string | null | undefined; status: ReevuBackendStatus; timestamp: number } | null = null
let inflightStatusRequest: Promise<ReevuBackendStatus> | null = null
let inflightStatusToken: string | null | undefined = undefined

function isReevuStatusPayload(value: unknown): value is ReevuStatusPayload {
  return Boolean(value) && typeof value === 'object'
}

export function createUnreachableReevuBackendStatus(authRequired = false): ReevuBackendStatus {
  return {
    reachable: false,
    authRequired
  }
}

export function resolveReevuBackendStatus(payload: unknown): ReevuBackendStatus {
  if (!isReevuStatusPayload(payload)) {
    return createUnreachableReevuBackendStatus(false)
  }

  const providers = (payload.providers || {}) as Record<string, ReevuStatusProviderState>
  const hasRealProvider = REAL_PROVIDER_IDS.some(providerId => {
    const providerState = providers[providerId]
    return Boolean(providerState?.available || providerState?.configured)
  })

  return {
    reachable: true,
    provider: payload.active_provider,
    model: payload.active_model,
    providerSource: payload.active_provider_source,
    providerSourceLabel: payload.active_provider_source_label,
    templateOnly: payload.active_provider === 'template' && !hasRealProvider,
    authRequired: false
  }
}

export function getEffectiveReevuBackend(status: ReevuBackendStatus): EffectiveBackend {
  if (status.authRequired) {
    return { mode: 'none', name: 'Authentication required', ready: false }
  }

  if (!status.reachable) {
    return { mode: 'none', name: 'Managed backend unreachable', ready: false }
  }

  if (status.templateOnly) {
    return {
      mode: 'none',
      name: 'Managed backend in template fallback (no provider configured)',
      ready: false
    }
  }

  const providerName = getReevuProviderDisplayName(status.provider, 'Server AI')

  return {
    mode: status.provider === 'ollama' ? 'local' : 'cloud',
    name: `${providerName}${status.model ? ` · ${status.model}` : ''}${status.providerSourceLabel ? ` (${status.providerSourceLabel})` : ''}`,
    ready: true
  }
}

export function getReevuProviderDisplayName(provider?: string, fallback = 'Server AI'): string {
  if (!provider) {
    return fallback
  }

  return PROVIDER_NAMES[provider] || provider
}

function requestReevuBackendStatusUncached(fetcher: FetchLike, token?: string | null): Promise<ReevuBackendStatus> {
  return requestReevuBackendStatus(fetcher, token)
}

export function resetReevuBackendStatusRequestCache(): void {
  lastStatusCache = null
  inflightStatusRequest = null
  inflightStatusToken = undefined
}

export async function requestReevuBackendStatusCached(
  fetcher: FetchLike,
  token?: string | null,
  options: ReevuBackendStatusRequestOptions = {},
): Promise<ReevuBackendStatus> {
  const { force = false, maxAgeMs = DEFAULT_REEVU_STATUS_CACHE_MS } = options
  const now = Date.now()

  if (!force && lastStatusCache && lastStatusCache.token === token && now - lastStatusCache.timestamp <= maxAgeMs) {
    return lastStatusCache.status
  }

  if (!force && inflightStatusRequest && inflightStatusToken === token) {
    return inflightStatusRequest
  }

  inflightStatusToken = token
  inflightStatusRequest = requestReevuBackendStatusUncached(fetcher, token)
    .then(status => {
      lastStatusCache = {
        token,
        status,
        timestamp: Date.now(),
      }
      return status
    })
    .finally(() => {
      inflightStatusRequest = null
      inflightStatusToken = undefined
    })

  return inflightStatusRequest
}

export async function requestReevuBackendStatus(fetcher: FetchLike, token?: string | null): Promise<ReevuBackendStatus> {
  try {
    const response = await fetcher('/api/v2/chat/status', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    if (response.status === 401) {
      return createUnreachableReevuBackendStatus(true)
    }

    if (!response.ok) {
      throw new Error(`Status ${response.status}`)
    }

    const payload = await response.json()
    return resolveReevuBackendStatus(payload)
  } catch {
    return createUnreachableReevuBackendStatus(false)
  }
}