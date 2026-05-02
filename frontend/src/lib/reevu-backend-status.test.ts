import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  createUnreachableReevuBackendStatus,
  getEffectiveReevuBackend,
  requestReevuBackendStatusCached,
  requestReevuBackendStatus,
  resetReevuBackendStatusRequestCache,
  resolveReevuBackendStatus,
} from './reevu-backend-status'
import { DEFAULT_REEVU_BYOK_MODEL } from './ai-model-catalog'

describe('requestReevuBackendStatusCached', () => {
  beforeEach(() => {
    resetReevuBackendStatusRequestCache()
  })

  it('reuses an inflight request for the same token', async () => {
    const fetcher = vi.fn().mockImplementation(async () => {
      await Promise.resolve()
      return {
        status: 200,
        ok: true,
        json: vi.fn().mockResolvedValue({
          active_provider: 'google',
          active_model: DEFAULT_REEVU_BYOK_MODEL,
          providers: { google: { available: true } },
        }),
      }
    })

    const [first, second] = await Promise.all([
      requestReevuBackendStatusCached(fetcher, 'token'),
      requestReevuBackendStatusCached(fetcher, 'token'),
    ])

    expect(first).toEqual(second)
    expect(fetcher).toHaveBeenCalledTimes(1)
  })

  it('returns cached status within the max age window and bypasses it when forced', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: vi.fn().mockResolvedValue({
          active_provider: 'google',
          active_model: DEFAULT_REEVU_BYOK_MODEL,
          providers: { google: { available: true } },
        }),
      })
      .mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: vi.fn().mockResolvedValue({
          active_provider: 'groq',
          active_model: 'llama',
          providers: { groq: { available: true } },
        }),
      })

    const initial = await requestReevuBackendStatusCached(fetcher, 'token', { maxAgeMs: 10000 })
    const cached = await requestReevuBackendStatusCached(fetcher, 'token', { maxAgeMs: 10000 })
    const forced = await requestReevuBackendStatusCached(fetcher, 'token', { force: true, maxAgeMs: 10000 })

    expect(initial.provider).toBe('google')
    expect(cached.provider).toBe('google')
    expect(forced.provider).toBe('groq')
    expect(fetcher).toHaveBeenCalledTimes(2)
  })
})

describe('resolveReevuBackendStatus', () => {
  it('marks template-only backends as not AI-ready when no real provider is configured', () => {
    expect(resolveReevuBackendStatus({
      active_provider: 'template',
      active_model: 'fallback',
      providers: {
        template: { available: true },
      },
    })).toEqual({
      reachable: true,
      provider: 'template',
      model: 'fallback',
      providerSource: undefined,
      providerSourceLabel: undefined,
      templateOnly: true,
      authRequired: false,
    })
  })

  it('treats template provider as acceptable when a real provider is configured', () => {
    expect(resolveReevuBackendStatus({
      active_provider: 'template',
      active_model: 'fallback',
      providers: {
        google: { configured: true },
      },
    })).toEqual({
      reachable: true,
      provider: 'template',
      model: 'fallback',
      providerSource: undefined,
      providerSourceLabel: undefined,
      templateOnly: false,
      authRequired: false,
    })
  })

  it('preserves runtime provider source details when available', () => {
    expect(resolveReevuBackendStatus({
      active_provider: 'google',
      active_model: DEFAULT_REEVU_BYOK_MODEL,
      active_provider_source: 'server_env',
      active_provider_source_label: 'Server env key',
      providers: {
        google: { available: true },
      },
    })).toEqual({
      reachable: true,
      provider: 'google',
      model: DEFAULT_REEVU_BYOK_MODEL,
      providerSource: 'server_env',
      providerSourceLabel: 'Server env key',
      templateOnly: false,
      authRequired: false,
    })
  })

  it('treats ollama as a real provider instead of template-only fallback', () => {
    expect(resolveReevuBackendStatus({
      active_provider: 'ollama',
      active_model: 'llama3.2:3b',
      active_provider_source: 'local_runtime',
      active_provider_source_label: 'Local Ollama host',
      providers: {
        ollama: { available: true },
      },
    })).toEqual({
      reachable: true,
      provider: 'ollama',
      model: 'llama3.2:3b',
      providerSource: 'local_runtime',
      providerSourceLabel: 'Local Ollama host',
      templateOnly: false,
      authRequired: false,
    })
  })
})

describe('getEffectiveReevuBackend', () => {
  it('returns a blocked backend for auth-required status', () => {
    expect(getEffectiveReevuBackend(createUnreachableReevuBackendStatus(true))).toEqual({
      mode: 'none',
      name: 'Authentication required',
      ready: false,
    })
  })

  it('formats provider and model names for ready backends', () => {
    expect(getEffectiveReevuBackend({
      reachable: true,
      provider: 'google',
      model: DEFAULT_REEVU_BYOK_MODEL,
      providerSource: 'server_env',
      providerSourceLabel: 'Server env key',
      templateOnly: false,
      authRequired: false,
    })).toEqual({
      mode: 'cloud',
      name: `Google Gemini · ${DEFAULT_REEVU_BYOK_MODEL} (Server env key)`,
      ready: true,
    })
  })

  it('formats human-readable names for extended managed providers', () => {
    expect(getEffectiveReevuBackend({
      reachable: true,
      provider: 'huggingface',
      model: 'mistralai/Mistral-7B-Instruct-v0.2',
      providerSource: 'server_env',
      providerSourceLabel: 'Server env key',
      templateOnly: false,
      authRequired: false,
    })).toEqual({
      mode: 'cloud',
      name: 'HuggingFace Inference · mistralai/Mistral-7B-Instruct-v0.2 (Server env key)',
      ready: true,
    })
  })

  it('reports ollama as a local backend when selected', () => {
    expect(getEffectiveReevuBackend({
      reachable: true,
      provider: 'ollama',
      model: 'llama3.2:3b',
      providerSource: 'local_runtime',
      providerSourceLabel: 'Local Ollama host',
      templateOnly: false,
      authRequired: false,
    })).toEqual({
      mode: 'local',
      name: 'Ollama (Local) · llama3.2:3b (Local Ollama host)',
      ready: true,
    })
  })
})

describe('requestReevuBackendStatus', () => {
  it('returns auth-required status for 401 responses', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      status: 401,
      ok: false,
      json: vi.fn(),
    })

    await expect(requestReevuBackendStatus(fetcher, 'token')).resolves.toEqual({
      reachable: false,
      authRequired: true,
    })
  })

  it('returns unreachable status when the request fails', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('offline'))

    await expect(requestReevuBackendStatus(fetcher)).resolves.toEqual({
      reachable: false,
      authRequired: false,
    })
  })
})