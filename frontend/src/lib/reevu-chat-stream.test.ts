import { describe, expect, it } from 'vitest'

import {
  buildReevuChatStreamRequest,
  parseReevuStreamEvent,
  readReevuStreamEvents,
} from './reevu-chat-stream'

function createStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()

  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }

      controller.close()
    },
  })
}

describe('buildReevuChatStreamRequest', () => {
  it('limits conversation history and merges route context overrides', () => {
    const messages = Array.from({ length: 12 }, (_, index) => ({
      role: index % 2 === 0 ? 'user' as const : 'assistant' as const,
      content: `message-${index + 1}`,
    }))

    const request = buildReevuChatStreamRequest({
      message: 'latest prompt',
      messages,
      pathname: '/trials/BR-2025-A',
      search: '?season=Kharif%202025',
      activeWorkspaceId: 'breeding',
      routeTaskContextOverride: {
        visible_columns: ['name'],
        selected_entity_ids: ['OVERRIDE-1'],
      },
    })

    expect(request.message).toBe('latest prompt')
    expect(request.conversation_history).toHaveLength(10)
    expect(request.conversation_history[0].content).toBe('message-3')
    expect(request.task_context).toMatchObject({
      active_route: '/trials/BR-2025-A',
      workspace: 'Plant Breeding',
      selected_entity_ids: ['OVERRIDE-1'],
      active_filters: {
        season: 'Kharif 2025',
      },
      visible_columns: ['name'],
    })
  })
})

describe('parseReevuStreamEvent', () => {
  it('returns null for unsupported payloads', () => {
    expect(parseReevuStreamEvent({ type: 'noop' })).toBeNull()
    expect(parseReevuStreamEvent('invalid')).toBeNull()
  })

  it('parses stage and error events with safe-failure payloads', () => {
    expect(parseReevuStreamEvent({
      type: 'stage',
      stage: 'policy_validation',
      status: 'completed',
      safe_failure: {
        error_category: 'insufficient_evidence',
        searched: ['retrieved_context'],
        missing: ['grounded evidence'],
        next_steps: ['Narrow the query'],
      },
    })).toEqual({
      type: 'stage',
      stage: 'policy_validation',
      status: 'completed',
      safe_failure: {
        error_category: 'insufficient_evidence',
        searched: ['retrieved_context'],
        missing: ['grounded evidence'],
        next_steps: ['Narrow the query'],
      },
    })

    expect(parseReevuStreamEvent({
      type: 'error',
      message: 'stream failed',
      safe_failure: {
        error_category: 'streaming_error',
        searched: ['stream_response'],
        missing: ['complete answer stream'],
        next_steps: ['Retry the request'],
      },
    })).toEqual({
      type: 'error',
      message: 'stream failed',
      safe_failure: {
        error_category: 'streaming_error',
        searched: ['stream_response'],
        missing: ['complete answer stream'],
        next_steps: ['Retry the request'],
      },
    })
  })

  it('parses summary events with retrieval audit and execution plan metadata', () => {
    expect(parseReevuStreamEvent({
      type: 'summary',
      evidence_envelope: { sources: 1 },
      retrieval_audit: {
        services: ['trial_search_service.search'],
        tables: ['Trial'],
        entities: { crop: 'rice' },
      },
      plan_execution_summary: {
        plan_id: 'plan-1',
        is_compound: true,
        domains_involved: ['trials', 'weather'],
        total_steps: 2,
        metadata: {
          fallback_reasons: ['low_confidence_threshold'],
        },
        missing_domains: ['weather'],
        steps: [
          {
            step_id: 'step-1',
            domain: 'trials',
            description: 'Search trials',
            prerequisites: [],
            expected_outputs: ['trials'],
            deterministic: true,
            completed: true,
            status: 'completed',
            actual_outputs: ['trials'],
            services: ['trial_search_service.search'],
            output_counts: { trials: 1 },
            output_entity_ids: { trials: ['TRIAL-1'] },
            output_metadata: { resolved_location: 'Ludhiana' },
            compute_methods: ['fn:trial_ranker'],
          },
          {
            step_id: 'step-2',
            domain: 'weather',
            description: 'Join weather context',
            prerequisites: ['step-1'],
            completed: false,
            status: 'missing',
            actual_outputs: ['locations'],
            services: ['location_search_service.search', 'weather_service.get_forecast'],
            output_counts: { locations: 1 },
            output_entity_ids: { locations: ['LOC-1'] },
            missing_reason: 'weather service is unavailable',
          },
        ],
      },
    })).toEqual({
      type: 'summary',
      evidence_envelope: { sources: 1 },
      retrieval_audit: {
        services: ['trial_search_service.search'],
        tables: ['Trial'],
        entities: { crop: 'rice' },
      },
      plan_execution_summary: {
        plan_id: 'plan-1',
        is_compound: true,
        domains_involved: ['trials', 'weather'],
        total_steps: 2,
        metadata: {
          fallback_reasons: ['low_confidence_threshold'],
        },
        missing_domains: ['weather'],
        steps: [
          {
            step_id: 'step-1',
            domain: 'trials',
            description: 'Search trials',
            prerequisites: [],
            expected_outputs: ['trials'],
            deterministic: true,
            completed: true,
            status: 'completed',
            actual_outputs: ['trials'],
            services: ['trial_search_service.search'],
            output_counts: { trials: 1 },
            output_entity_ids: { trials: ['TRIAL-1'] },
            output_metadata: { resolved_location: 'Ludhiana' },
            compute_methods: ['fn:trial_ranker'],
          },
          {
            step_id: 'step-2',
            domain: 'weather',
            description: 'Join weather context',
            prerequisites: ['step-1'],
            completed: false,
            status: 'missing',
            actual_outputs: ['locations'],
            services: ['location_search_service.search', 'weather_service.get_forecast'],
            output_counts: { locations: 1 },
            output_entity_ids: { locations: ['LOC-1'] },
            missing_reason: 'weather service is unavailable',
          },
        ],
      },
    })
  })
})

describe('readReevuStreamEvents', () => {
  it('decodes recognized SSE events across chunk boundaries', async () => {
    const stream = createStream([
      'data: {"type":"start","provider":"Groq","model":"llama"}\n\n',
      'data: {"type":"chunk","content":"Hello"}\n\n',
      'data: {"type":"proposal_created","data":{"id":1,"title":"T","status":"draft","description":"D"}}\n',
      '\n',
      'data: {"type":"stage","stage":"policy_validation","status":"completed","safe_failure":{"error_category":"insufficient_evidence","searched":["retrieved_context"],"missing":["grounded evidence"],"next_steps":["Narrow the query"]}}\n\n',
      'data: {"type":"summary","evidence_envelope":{"sources":1},"retrieval_audit":{"services":["trial_search_service.search"],"entities":{"crop":"rice"}},"plan_execution_summary":{"plan_id":"plan-1","is_compound":true,"domains_involved":["trials"],"total_steps":1,"steps":[{"step_id":"step-1","domain":"trials","description":"Search trials","status":"completed","actual_outputs":["trials"],"services":["trial_search_service.search"],"output_counts":{"trials":1}}]}}\n\n',
      'data: {"type":"error","message":"Stream error","safe_failure":{"error_category":"streaming_error","searched":["stream_response"],"missing":["complete answer stream"],"next_steps":["Retry the request"]}}\n\n',
    ])

    const events = []
    for await (const event of readReevuStreamEvents(stream)) {
      events.push(event)
    }

    expect(events).toEqual([
      { type: 'start', provider: 'Groq', model: 'llama' },
      { type: 'chunk', content: 'Hello' },
      { type: 'proposal_created', data: { id: 1, title: 'T', status: 'draft', description: 'D' } },
      {
        type: 'stage',
        stage: 'policy_validation',
        status: 'completed',
        safe_failure: {
          error_category: 'insufficient_evidence',
          searched: ['retrieved_context'],
          missing: ['grounded evidence'],
          next_steps: ['Narrow the query'],
        },
      },
      {
        type: 'summary',
        evidence_envelope: { sources: 1 },
        retrieval_audit: {
          services: ['trial_search_service.search'],
          entities: { crop: 'rice' },
        },
        plan_execution_summary: {
          plan_id: 'plan-1',
          is_compound: true,
          domains_involved: ['trials'],
          total_steps: 1,
          steps: [
            {
              step_id: 'step-1',
              domain: 'trials',
              description: 'Search trials',
              status: 'completed',
              actual_outputs: ['trials'],
              services: ['trial_search_service.search'],
              output_counts: { trials: 1 },
            },
          ],
        },
      },
      {
        type: 'error',
        message: 'Stream error',
        safe_failure: {
          error_category: 'streaming_error',
          searched: ['stream_response'],
          missing: ['complete answer stream'],
          next_steps: ['Retry the request'],
        },
      },
    ])
  })

  it('ignores invalid SSE payloads and non-data lines', async () => {
    const stream = createStream([
      ':keepalive\n\n',
      'data: not-json\n\n',
      'data: {"type":"chunk","content":"ok"}\n\n',
    ])

    const events = []
    for await (const event of readReevuStreamEvents(stream)) {
      events.push(event)
    }

    expect(events).toEqual([{ type: 'chunk', content: 'ok' }])
  })
})
