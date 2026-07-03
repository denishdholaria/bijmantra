import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  TRACE_ID_HEADER,
  installFetchTracing,
  resetFetchTracingForTests,
  withTraceHeaders,
} from './http'

describe('HTTP tracing', () => {
  let originalFetch: typeof globalThis.fetch

  beforeEach(() => {
    originalFetch = globalThis.fetch
    resetFetchTracingForTests()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('adds a generated trace id when headers do not already provide one', async () => {
    const headers = withTraceHeaders({ Authorization: 'Bearer test-token' })

    expect(headers.get('Authorization')).toBe('Bearer test-token')
    expect(headers.get(TRACE_ID_HEADER)).toMatch(/^[a-f0-9]{32}$/)
  })

  it('preserves an explicit trace id header', async () => {
    const headers = withTraceHeaders({ [TRACE_ID_HEADER]: 'existing-trace-12345678' })

    expect(headers.get(TRACE_ID_HEADER)).toBe('existing-trace-12345678')
  })

  it('patches global fetch to include a trace id header', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    globalThis.fetch = fetchMock as typeof fetch

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

  it('does not add trace headers to Keycloak token requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    globalThis.fetch = fetchMock as typeof fetch

    installFetchTracing()
    await globalThis.fetch(
      'http://localhost:8084/realms/bijmantra/protocol/openid-connect/token',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      },
    )

    expect(fetchMock).toHaveBeenCalledTimes(1)

    const [, init] = fetchMock.mock.calls[0]
    const headers = new Headers(init?.headers)

    expect(headers.get('Content-Type')).toBe('application/x-www-form-urlencoded')
    expect(headers.has(TRACE_ID_HEADER)).toBe(false)
  })

  it('does not add trace headers to non-API document requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    globalThis.fetch = fetchMock as typeof fetch

    installFetchTracing()
    await globalThis.fetch('/silent-check-sso.html')

    expect(fetchMock).toHaveBeenCalledTimes(1)

    const [, init] = fetchMock.mock.calls[0]
    const headers = new Headers(init?.headers)

    expect(headers.has(TRACE_ID_HEADER)).toBe(false)
  })

  it('keeps tracing same-origin BrAPI requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    globalThis.fetch = fetchMock as typeof fetch

    installFetchTracing()
    await globalThis.fetch('/brapi/v2/germplasm')

    expect(fetchMock).toHaveBeenCalledTimes(1)

    const [, init] = fetchMock.mock.calls[0]
    const headers = new Headers(init?.headers)

    expect(headers.get(TRACE_ID_HEADER)).toMatch(/^[a-f0-9]{32}$/)
  })
})
