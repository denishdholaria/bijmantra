import type { WorkspaceId } from '@/types/workspace'
import { isReevuSafeFailure, type ReevuSafeFailure } from '@/lib/reevu-safe-failure'
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

export interface ReevuPlanExecutionStep {
  step_id: string
  domain: string
  description: string
  prerequisites?: string[]
  expected_outputs?: string[]
  deterministic?: boolean
  completed?: boolean
  status?: string
  actual_outputs?: string[]
  services?: string[]
  output_counts?: Record<string, number>
  output_entity_ids?: Record<string, unknown>
  output_metadata?: Record<string, unknown>
  compute_methods?: string[]
  missing_reason?: string
}

export interface ReevuPlanExecutionSummary {
  plan_id: string
  is_compound: boolean
  domains_involved: string[]
  total_steps?: number
  deterministic_routing?: Record<string, unknown>
  metadata?: Record<string, unknown>
  missing_domains?: string[]
  steps: ReevuPlanExecutionStep[]
}

export interface ReevuRetrievalAudit {
  services: string[]
  tables?: string[]
  entities: Record<string, unknown>
  plan?: ReevuPlanExecutionSummary
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
  retrieval_audit?: ReevuRetrievalAudit
  plan_execution_summary?: ReevuPlanExecutionSummary
}

export interface ReevuStreamStageEvent {
  type: 'stage'
  stage: string
  status: string
  safe_failure?: ReevuSafeFailure
}

export interface ReevuStreamErrorEvent {
  type: 'error'
  message?: string
  safe_failure?: ReevuSafeFailure
}

export type ReevuStreamEvent =
  | ReevuStreamStartEvent
  | ReevuStreamChunkEvent
  | ReevuStreamProposalCreatedEvent
  | ReevuStreamSummaryEvent
  | ReevuStreamStageEvent
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

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(item => typeof item === 'string')
}

function isNumberRecord(value: unknown): value is Record<string, number> {
  return isObject(value) && Object.values(value).every(item => typeof item === 'number')
}

function isPlanExecutionStep(value: unknown): value is ReevuPlanExecutionStep {
  return isObject(value)
    && typeof value.step_id === 'string'
    && typeof value.domain === 'string'
    && typeof value.description === 'string'
    && (value.prerequisites === undefined || isStringArray(value.prerequisites))
    && (value.expected_outputs === undefined || isStringArray(value.expected_outputs))
    && (value.deterministic === undefined || typeof value.deterministic === 'boolean')
    && (value.completed === undefined || typeof value.completed === 'boolean')
    && (value.status === undefined || typeof value.status === 'string')
    && (value.actual_outputs === undefined || isStringArray(value.actual_outputs))
    && (value.services === undefined || isStringArray(value.services))
    && (value.output_counts === undefined || isNumberRecord(value.output_counts))
    && (value.output_entity_ids === undefined || isObject(value.output_entity_ids))
    && (value.output_metadata === undefined || isObject(value.output_metadata))
    && (value.compute_methods === undefined || isStringArray(value.compute_methods))
    && (value.missing_reason === undefined || typeof value.missing_reason === 'string')
}

function isPlanExecutionSummary(value: unknown): value is ReevuPlanExecutionSummary {
  return isObject(value)
    && typeof value.plan_id === 'string'
    && typeof value.is_compound === 'boolean'
    && isStringArray(value.domains_involved)
    && (value.total_steps === undefined || typeof value.total_steps === 'number')
    && (value.deterministic_routing === undefined || isObject(value.deterministic_routing))
    && (value.metadata === undefined || isObject(value.metadata))
    && (value.missing_domains === undefined || isStringArray(value.missing_domains))
    && Array.isArray(value.steps)
    && value.steps.every(isPlanExecutionStep)
}

function isRetrievalAudit(value: unknown): value is ReevuRetrievalAudit {
  return isObject(value)
    && isStringArray(value.services)
    && (value.tables === undefined || isStringArray(value.tables))
    && isObject(value.entities)
    && (value.plan === undefined || isPlanExecutionSummary(value.plan))
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
      retrieval_audit: isRetrievalAudit(payload.retrieval_audit) ? payload.retrieval_audit : undefined,
      plan_execution_summary: isPlanExecutionSummary(payload.plan_execution_summary)
        ? payload.plan_execution_summary
        : undefined,
    }
  }

  if (payload.type === 'stage' && typeof payload.stage === 'string' && typeof payload.status === 'string') {
    return {
      type: 'stage',
      stage: payload.stage,
      status: payload.status,
      safe_failure: isReevuSafeFailure(payload.safe_failure) ? payload.safe_failure : undefined,
    }
  }

  if (payload.type === 'error') {
    return {
      type: 'error',
      message: typeof payload.message === 'string' ? payload.message : undefined,
      safe_failure: isReevuSafeFailure(payload.safe_failure) ? payload.safe_failure : undefined,
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
