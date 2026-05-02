import { describe, expect, it, vi } from 'vitest'
import { DEFAULT_REEVU_BYOK_MODEL } from './ai-model-catalog'

import {
  clearStoredReevuMessages,
  defaultReevuConfig,
  loadStoredReevuConfig,
  loadStoredReevuMessages,
  MAX_STORED_REEVU_MESSAGES,
  persistReevuConfig,
  persistReevuMessages,
} from './reevu-local-state'

function createStorage(initial: Record<string, string> = {}) {
  const values = new Map(Object.entries(initial))

  return {
    getItem: vi.fn((key: string) => values.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => {
      values.set(key, value)
    }),
    removeItem: vi.fn((key: string) => {
      values.delete(key)
    }),
  }
}

describe('loadStoredReevuMessages', () => {
  it('loads stored messages and restores timestamps', () => {
    const storage = createStorage({
      reevu_conversation_history: JSON.stringify([
        { id: '1', role: 'assistant', content: 'Hi', timestamp: '2026-03-12T10:00:00.000Z' },
      ]),
    })

    const messages = loadStoredReevuMessages({
      id: 'init',
      role: 'assistant',
      content: 'Init',
      timestamp: new Date('2026-03-12T09:00:00.000Z'),
    }, storage)

    expect(messages[0]).toMatchObject({ id: '1', content: 'Hi' })
    expect(messages[0].timestamp).toBeInstanceOf(Date)
  })

  it('falls back to the initial message and reports parse errors', () => {
    const storage = createStorage({
      reevu_conversation_history: '{invalid',
    })
    const onError = vi.fn()

    const messages = loadStoredReevuMessages({
      id: 'init',
      role: 'assistant',
      content: 'Init',
      timestamp: new Date('2026-03-12T09:00:00.000Z'),
    }, storage, onError)

    expect(messages).toHaveLength(1)
    expect(messages[0].id).toBe('init')
    expect(onError).toHaveBeenCalledTimes(1)
  })
})

describe('persistReevuMessages', () => {
  it('caps stored message history', () => {
    const storage = createStorage()
    const messages = Array.from({ length: MAX_STORED_REEVU_MESSAGES + 5 }, (_, index) => ({
      id: `${index + 1}`,
      role: 'assistant' as const,
      content: `message-${index + 1}`,
      timestamp: new Date('2026-03-12T09:00:00.000Z'),
    }))

    persistReevuMessages(messages, storage)

    const stored = JSON.parse(storage.setItem.mock.calls[0][1])
    expect(stored).toHaveLength(MAX_STORED_REEVU_MESSAGES)
    expect(stored[0].id).toBe('6')
  })
})

describe('loadStoredReevuConfig', () => {
  it('returns normalized REEVU config when present', () => {
    const storage = createStorage({
      bijmantra_reevu_config_v1: JSON.stringify({
        mode: 'byok',
        byok: {
          provider: 'openai',
          apiKey: 'secret',
          model: 'gpt-4.1',
        },
      }),
    })

    expect(loadStoredReevuConfig(storage)).toEqual({
      mode: 'managed',
      byok: {
        provider: 'openai',
        apiKey: '',
        model: 'gpt-4.1',
      },
    })
  })

  it('lets legacy AI config override stored REEVU config to preserve migration precedence', () => {
    const storage = createStorage({
      bijmantra_reevu_config_v1: JSON.stringify({
        mode: 'managed',
        byok: {
          provider: 'openai',
          model: 'gpt-4.1',
        },
      }),
      bijmantra_ai_config_v2: JSON.stringify({
        cloud: {
          provider: 'google',
          model: DEFAULT_REEVU_BYOK_MODEL,
        },
      }),
    })

    expect(loadStoredReevuConfig(storage)).toEqual({
      mode: 'managed',
      byok: {
        provider: 'google',
        apiKey: '',
        model: DEFAULT_REEVU_BYOK_MODEL,
      },
    })
  })

  it('falls back to the default config when nothing valid is stored', () => {
    expect(loadStoredReevuConfig(createStorage())).toEqual(defaultReevuConfig)
  })
})

describe('config and history persistence helpers', () => {
  it('persists config and clears both new and legacy history keys', () => {
    const storage = createStorage()

    persistReevuConfig(defaultReevuConfig, storage)
    clearStoredReevuMessages(storage)

    expect(storage.setItem).toHaveBeenCalledWith('bijmantra_reevu_config_v1', JSON.stringify(defaultReevuConfig))
    expect(storage.removeItem).toHaveBeenCalledWith('reevu_conversation_history')
    expect(storage.removeItem).toHaveBeenCalledWith('bijmantra_legacy_reevu_conversation')
  })
})