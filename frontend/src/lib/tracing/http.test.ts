import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

describe('HTTP tracing', () => {
  let originalFetch: typeof globalThis.fetch

  beforeEach(() => {
    originalFetch = globalThis.fetch
    vi.resetModules()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('adds a generated trace id when headers do not already provide one', async () => {
    const { TRACE_ID_HEADER, withTraceHeaders } = await import('./http')

    const headers = withTraceHeaders({ Authorization: 'Bearer test-token' })

    expect(headers.get('Authorization')).toBe('Bearer test-token')
    expect(headers.get(TRACE_ID_HEADER)).toMatch(/^[a-f0-9]{32}$/)
  })

  it('preserves an explicit trace id header', async () => {
    const { TRACE_ID_HEADER, withTraceHeaders } = await import('./http')

    const headers = withTraceHeaders({ [TRACE_ID_HEADER]: 'existing-trace-12345678' })

    expect(headers.get(TRACE_ID_HEADER)).toBe('existing-trace-12345678')
  })

  it('patches global fetch to include a trace id header', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    globalThis.fetch = fetchMock as typeof fetch

    const { TRACE_ID_HEADER, installFetchTracing } = await import('./http')

    installFetchTracing()
    await globalThis.fetch('/api/v2/observations', {
      method: 'POST',
      headers: {
        Authorization: 'Bearer traced-token',
      },
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)

    const [, init] = fetchMock.mock.calls[0]
    const headers = new Headers(init?.headers)

    expect(headers.get('Authorization')).toBe('Bearer traced-token')
    expect(headers.get(TRACE_ID_HEADER)).toMatch(/^[a-f0-9]{32}$/)
  })
})