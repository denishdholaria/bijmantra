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
})

describe('readReevuStreamEvents', () => {
  it('decodes recognized SSE events across chunk boundaries', async () => {
    const stream = createStream([
      'data: {"type":"start","provider":"Groq","model":"llama"}\n\n',
      'data: {"type":"chunk","content":"Hello"}\n\n',
      'data: {"type":"proposal_created","data":{"id":1,"title":"T","status":"draft","description":"D"}}\n',
      '\n',
      'data: {"type":"summary","evidence_envelope":{"sources":1}}\n\n',
      'data: {"type":"error","message":"Stream error"}\n\n',
    ])

    const events = []
    for await (const event of readReevuStreamEvents(stream)) {
      events.push(event)
    }

    expect(events).toEqual([
      { type: 'start', provider: 'Groq', model: 'llama' },
      { type: 'chunk', content: 'Hello' },
      { type: 'proposal_created', data: { id: 1, title: 'T', status: 'draft', description: 'D' } },
      { type: 'summary', evidence_envelope: { sources: 1 } },
      { type: 'error', message: 'Stream error' },
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