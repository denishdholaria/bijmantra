import type { EvidenceEnvelope } from '@/components/ai/EvidenceTraceCard'
import type { ReevuProposalSummary } from '@/lib/reevu-chat-stream'

export interface ReevuMessageState {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    provider?: string
    model?: string
    proposal?: ReevuProposalSummary
    evidence_envelope?: EvidenceEnvelope
  }
}

interface CreateUserMessageOptions {
  id: string
  content: string
  timestamp?: Date
}

interface CreateSystemMessageOptions {
  id: string
  content: string
  provider?: string
  model?: string
  timestamp?: Date
}

interface CreatePendingAssistantMessageOptions {
  id: string
  providerName: string
  model?: string
  timestamp?: Date
}

interface PatchAssistantMessageOptions {
  assistantMessageId: string
  provider: string
  model: string
}

export function createReevuUserMessage({
  id,
  content,
  timestamp = new Date(),
}: CreateUserMessageOptions): ReevuMessageState {
  return {
    id,
    role: 'user',
    content,
    timestamp,
  }
}

export function createReevuSystemMessage({
  id,
  content,
  provider = 'System',
  model,
  timestamp = new Date(),
}: CreateSystemMessageOptions): ReevuMessageState {
  return {
    id,
    role: 'assistant',
    content,
    timestamp,
    metadata: {
      provider,
      model,
    },
  }
}

export function createPendingReevuAssistantMessage({
  id,
  providerName,
  model = 'auto',
  timestamp = new Date(),
}: CreatePendingAssistantMessageOptions): ReevuMessageState {
  return {
    id,
    role: 'assistant',
    content: '',
    timestamp,
    metadata: {
      provider: `Connecting to ${providerName}...`,
      model,
    },
  }
}

function patchAssistantMessage(
  messages: ReevuMessageState[],
  { assistantMessageId, provider, model }: PatchAssistantMessageOptions,
  patch: (message: ReevuMessageState) => ReevuMessageState,
): ReevuMessageState[] {
  return messages.map(message => {
    if (message.id !== assistantMessageId) {
      return message
    }

    return patch({
      ...message,
      metadata: {
        ...message.metadata,
        provider,
        model,
      },
    })
  })
}

export function patchReevuAssistantChunk(
  messages: ReevuMessageState[],
  options: PatchAssistantMessageOptions & { content: string },
): ReevuMessageState[] {
  return patchAssistantMessage(messages, options, message => ({
    ...message,
    content: options.content,
  }))
}

export function patchReevuAssistantProposal(
  messages: ReevuMessageState[],
  options: PatchAssistantMessageOptions & { proposal: ReevuProposalSummary },
): ReevuMessageState[] {
  return patchAssistantMessage(messages, options, message => ({
    ...message,
    metadata: {
      ...message.metadata,
      provider: options.provider,
      model: options.model,
      proposal: options.proposal,
    },
  }))
}

export function patchReevuAssistantEvidence(
  messages: ReevuMessageState[],
  options: PatchAssistantMessageOptions & { evidenceEnvelope: EvidenceEnvelope },
): ReevuMessageState[] {
  return patchAssistantMessage(messages, options, message => ({
    ...message,
    metadata: {
      ...message.metadata,
      provider: options.provider,
      model: options.model,
      evidence_envelope: options.evidenceEnvelope,
    },
  }))
}

export function finalizeReevuAssistantMessage(
  messages: ReevuMessageState[],
  options: PatchAssistantMessageOptions & { content: string },
): ReevuMessageState[] {
  return patchAssistantMessage(messages, options, message => ({
    ...message,
    content: options.content || 'No response received.',
  }))
}

export function appendReevuAssistantError(
  messages: ReevuMessageState[],
  assistantMessageId: string,
  errorMessage: string,
): ReevuMessageState[] {
  return messages.map(message =>
    message.id === assistantMessageId
      ? { ...message, content: `${message.content}\n\n[System Error: ${errorMessage}. Please check your connection.]` }
      : message,
  )
}