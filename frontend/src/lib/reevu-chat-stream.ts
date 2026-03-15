import type { WorkspaceId } from '@/types/workspace'
import { buildReevuTaskContext, mergeReevuTaskContext } from '@/lib/reevu-task-context'
import type { ReevuTaskContextOverride } from '@/lib/reevu-task-context'

export interface ReevuConversationHistoryEntry {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface BuildReevuChatStreamRequestOptions {
  message: string
  messages: ReevuConversationHistoryEntry[]
  pathname: string
  search?: string
  activeWorkspaceId?: WorkspaceId | null
  routeTaskContextOverride?: ReevuTaskContextOverride | null
}

export interface ReevuChatStreamRequestBody {
  message: string
  conversation_history: ReevuConversationHistoryEntry[]
  include_context: boolean
  context_limit: number
  task_context: ReturnType<typeof mergeReevuTaskContext>
}

export interface ReevuProposalSummary {
  id: number
  title: string
  status: string
  description: string
}

export interface ReevuStreamStartEvent {
  type: 'start'
  provider?: string
  model?: string
}

export interface ReevuStreamChunkEvent {
  type: 'chunk'
  content: string
}

export interface ReevuStreamProposalCreatedEvent {
  type: 'proposal_created'
  data: ReevuProposalSummary
}

export interface ReevuStreamSummaryEvent {
  type: 'summary'
  evidence_envelope: unknown
}

export interface ReevuStreamErrorEvent {
  type: 'error'
  message?: string
}

export type ReevuStreamEvent =
  | ReevuStreamStartEvent
  | ReevuStreamChunkEvent
  | ReevuStreamProposalCreatedEvent
  | ReevuStreamSummaryEvent
  | ReevuStreamErrorEvent

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object'
}

function isProposalSummary(value: unknown): value is ReevuProposalSummary {
  return isObject(value)
    && typeof value.id === 'number'
    && typeof value.title === 'string'
    && typeof value.status === 'string'
    && typeof value.description === 'string'
}

export function buildReevuChatStreamRequest({
  message,
  messages,
  pathname,
  search,
  activeWorkspaceId,
  routeTaskContextOverride,
}: BuildReevuChatStreamRequestOptions): ReevuChatStreamRequestBody {
  return {
    message,
    conversation_history: messages.slice(-10).map(entry => ({
      role: entry.role,
      content: entry.content,
    })),
    include_context: true,
    context_limit: 5,
    task_context: mergeReevuTaskContext(
      buildReevuTaskContext({
        pathname,
        search,
        activeWorkspaceId,
      }),
      routeTaskContextOverride,
    ),
  }
}

export function parseReevuStreamEvent(payload: unknown): ReevuStreamEvent | null {
  if (!isObject(payload) || typeof payload.type !== 'string') {
    return null
  }

  if (payload.type === 'start') {
    return {
      type: 'start',
      provider: typeof payload.provider === 'string' ? payload.provider : undefined,
      model: typeof payload.model === 'string' ? payload.model : undefined,
    }
  }

  if (payload.type === 'chunk' && typeof payload.content === 'string') {
    return {
      type: 'chunk',
      content: payload.content,
    }
  }

  if (payload.type === 'proposal_created' && isProposalSummary(payload.data)) {
    return {
      type: 'proposal_created',
      data: payload.data,
    }
  }

  if (payload.type === 'summary' && 'evidence_envelope' in payload) {
    return {
      type: 'summary',
      evidence_envelope: payload.evidence_envelope,
    }
  }

  if (payload.type === 'error') {
    return {
      type: 'error',
      message: typeof payload.message === 'string' ? payload.message : undefined,
    }
  }

  return null
}

export async function* readReevuStreamEvents(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<ReevuStreamEvent, void, unknown> {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let sseBuffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }

      sseBuffer += decoder.decode(value, { stream: true })

      let eventBoundary = sseBuffer.indexOf('\n\n')
      while (eventBoundary !== -1) {
        const rawEvent = sseBuffer.slice(0, eventBoundary)
        sseBuffer = sseBuffer.slice(eventBoundary + 2)

        const dataLines = rawEvent
          .split('\n')
          .filter(line => line.startsWith('data: '))
          .map(line => line.slice(6))

        if (dataLines.length > 0) {
          try {
            const payload = JSON.parse(dataLines.join('\n'))
            const event = parseReevuStreamEvent(payload)
            if (event) {
              yield event
            }
          } catch {
            // Ignore keepalive/comments/non-JSON payloads
          }
        }

        eventBoundary = sseBuffer.indexOf('\n\n')
      }
    }
  } finally {
    reader.releaseLock()
  }
}