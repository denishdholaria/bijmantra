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
  patchReevuAssistantSafeFailure,
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
      retrievalAudit: {
        services: ['trial_search_service.search'],
        entities: { crop: 'rice' },
      },
      planExecutionSummary: {
        plan_id: 'plan-1',
        is_compound: true,
        domains_involved: ['trials'],
        steps: [],
      },
    })

    expect(withEvidence[0].metadata).toMatchObject({
      provider: 'Groq',
      model: 'llama',
      proposal: { id: 1, title: 'Draft', status: 'new', description: 'Desc' },
      evidence_envelope: { sources: [] },
      retrieval_audit: {
        services: ['trial_search_service.search'],
        entities: { crop: 'rice' },
      },
      plan_execution_summary: {
        plan_id: 'plan-1',
        is_compound: true,
        domains_involved: ['trials'],
        steps: [],
      },
    })
  })

  it('patches safe-failure metadata without dropping prior fields', () => {
    const withSafeFailure = patchReevuAssistantSafeFailure(base, {
      assistantMessageId: 'a1',
      provider: 'Groq',
      model: 'llama',
      safeFailure: {
        error_category: 'insufficient_evidence',
        searched: ['retrieved_context'],
        missing: ['grounded evidence'],
        next_steps: ['Narrow the query'],
      },
    })

    expect(withSafeFailure[0].metadata).toMatchObject({
      provider: 'Groq',
      model: 'llama',
      safe_failure: {
        error_category: 'insufficient_evidence',
        searched: ['retrieved_context'],
        missing: ['grounded evidence'],
        next_steps: ['Narrow the query'],
      },
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

  it('uses a structured safe-failure summary instead of generic no-response fallback', () => {
    const withSafeFailure = patchReevuAssistantSafeFailure(base, {
      assistantMessageId: 'a1',
      provider: 'Groq',
      model: 'llama',
      safeFailure: {
        error_category: 'insufficient_evidence',
        searched: ['retrieved_context'],
        missing: ['grounded evidence'],
        next_steps: ['Narrow the query'],
      },
    })

    const finalized = finalizeReevuAssistantMessage(withSafeFailure, {
      assistantMessageId: 'a1',
      provider: 'Groq',
      model: 'llama',
      content: '',
    })

    expect(finalized[0].content).toBe('REEVU could not produce a grounded answer from current system state.')
  })
})
