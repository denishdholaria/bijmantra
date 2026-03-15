import { describe, expect, it } from 'vitest'

import {
  appendReevuAssistantError,
  createPendingReevuAssistantMessage,
  createReevuSystemMessage,
  createReevuUserMessage,
  finalizeReevuAssistantMessage,
  patchReevuAssistantChunk,
  patchReevuAssistantEvidence,
  patchReevuAssistantProposal,
} from './reevu-message-state'
import { DEFAULT_REEVU_BYOK_MODEL } from './ai-model-catalog'

describe('REEVU message factories', () => {
  it('creates user and system messages with expected defaults', () => {
    expect(createReevuUserMessage({ id: 'u1', content: 'hello' })).toMatchObject({
      id: 'u1',
      role: 'user',
      content: 'hello',
    })

    expect(createReevuSystemMessage({ id: 's1', content: 'Login required', model: 'Unauthorized' })).toMatchObject({
      id: 's1',
      role: 'assistant',
      content: 'Login required',
      metadata: {
        provider: 'System',
        model: 'Unauthorized',
      },
    })
  })

  it('creates pending assistant messages with connecting metadata', () => {
    expect(createPendingReevuAssistantMessage({ id: 'a1', providerName: 'Google Gemini', model: DEFAULT_REEVU_BYOK_MODEL })).toMatchObject({
      id: 'a1',
      role: 'assistant',
      content: '',
      metadata: {
        provider: 'Connecting to Google Gemini...',
        model: DEFAULT_REEVU_BYOK_MODEL,
      },
    })
  })
})

describe('REEVU assistant patch helpers', () => {
  const base = [createPendingReevuAssistantMessage({ id: 'a1', providerName: 'Google Gemini', model: 'auto' })]

  it('patches chunk content and metadata', () => {
    expect(patchReevuAssistantChunk(base, {
      assistantMessageId: 'a1',
      provider: 'Groq',
      model: 'llama',
      content: 'partial',
    })[0]).toMatchObject({
      content: 'partial',
      metadata: {
        provider: 'Groq',
        model: 'llama',
      },
    })
  })

  it('patches proposal and evidence metadata without dropping prior fields', () => {
    const withProposal = patchReevuAssistantProposal(base, {
      assistantMessageId: 'a1',
      provider: 'Groq',
      model: 'llama',
      proposal: { id: 1, title: 'Draft', status: 'new', description: 'Desc' },
    })

    const withEvidence = patchReevuAssistantEvidence(withProposal, {
      assistantMessageId: 'a1',
      provider: 'Groq',
      model: 'llama',
      evidenceEnvelope: { sources: [] } as any,
    })

    expect(withEvidence[0].metadata).toMatchObject({
      provider: 'Groq',
      model: 'llama',
      proposal: { id: 1, title: 'Draft', status: 'new', description: 'Desc' },
      evidence_envelope: { sources: [] },
    })
  })

  it('finalizes content fallback and appends system errors', () => {
    const finalized = finalizeReevuAssistantMessage(base, {
      assistantMessageId: 'a1',
      provider: 'Groq',
      model: 'llama',
      content: '',
    })

    expect(finalized[0].content).toBe('No response received.')

    const withError = appendReevuAssistantError(finalized, 'a1', 'Stream error')
    expect(withError[0].content).toContain('[System Error: Stream error. Please check your connection.]')
  })
})