export const TRACE_ID_HEADER = 'X-Trace-Id'

function fallbackRandomHex(length: number): string {
  let value = ''

  while (value.length < length) {
    value += Math.floor(Math.random() * 0xffffffff)
      .toString(16)
      .padStart(8, '0')
  }

  return value.slice(0, length)
}

export function createTraceId(): string {
  if (typeof crypto !== 'undefined') {
    if (typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID().replace(/-/g, '')
    }

    if (typeof crypto.getRandomValues === 'function') {
      const bytes = new Uint8Array(16)
      crypto.getRandomValues(bytes)
      return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
    }
  }

  return `${Date.now().toString(16)}${fallbackRandomHex(32)}`.slice(0, 32).padEnd(32, '0')
}

function mergeHeaders(...sources: Array<HeadersInit | undefined>): Headers {
  const headers = new Headers()

  for (const source of sources) {
    if (!source) {
      continue
    }

    new Headers(source).forEach((value, key) => {
      headers.set(key, value)
    })
  }

  return headers
}

export function withTraceHeaders(headers?: HeadersInit, traceId?: string): Headers {
  const mergedHeaders = mergeHeaders(headers)

  if (!mergedHeaders.has(TRACE_ID_HEADER)) {
    mergedHeaders.set(TRACE_ID_HEADER, traceId ?? createTraceId())
  }

  return mergedHeaders
}

function buildTracedFetchArgs(
  input: RequestInfo | URL,
  init?: RequestInit,
): [RequestInfo | URL, RequestInit | undefined] {
  if (input instanceof Request) {
    const headers = withTraceHeaders(mergeHeaders(input.headers, init?.headers))
    return [new Request(input, { ...init, headers }), undefined]
  }

  return [input, { ...init, headers: withTraceHeaders(init?.headers) }]
}

let fetchTracingInstalled = false

export function installFetchTracing(): void {
  if (fetchTracingInstalled || typeof globalThis.fetch !== 'function') {
    return
  }

  const originalFetch = globalThis.fetch.bind(globalThis)

  globalThis.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
    const [tracedInput, tracedInit] = buildTracedFetchArgs(input, init)
    return originalFetch(tracedInput, tracedInit)
  }) as typeof globalThis.fetch

  fetchTracingInstalled = true
}