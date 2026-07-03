/**
 * NVIDIA NIM API service (frontend).
 *
 * All requests go through the backend proxy at /api/nim/chat — the frontend
 * NEVER talks to NIM directly so NVIDIA_API_KEY never reaches the browser.
 *
 * Usage:
 *
 *   import { nimChat, nimStream } from '@/services/nimApi'
 *
 *   // Non-streaming
 *   const result = await nimChat({ messages: [...] })
 *   console.log(result.content)
 *
 *   // Streaming
 *   for await (const chunk of nimStream({ messages: [...] })) {
 *     process.stdout.write(chunk)
 *   }
 */

const NIM_PROXY_PATH = '/api/nim/chat'

export interface NimMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface NimChatRequest {
  messages: NimMessage[]
  /** Override the server-default model (must be available on NVIDIA Build). */
  model?: string
  max_tokens?: number
  temperature?: number
}

export interface NimChatResponse {
  content: string
  model: string | null
  input_tokens: number | null
  output_tokens: number | null
  total_tokens: number | null
  latency_ms: number
}

// ---------------------------------------------------------------------------
// Non-streaming chat
// ---------------------------------------------------------------------------

export async function nimChat(request: NimChatRequest): Promise<NimChatResponse> {
  const response = await fetch(NIM_PROXY_PATH, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText)
    throw new Error(`NIM proxy error ${response.status}: ${detail}`)
  }

  return response.json() as Promise<NimChatResponse>
}

// ---------------------------------------------------------------------------
// Streaming chat — yields text chunks from an SSE/newline-delimited stream
// ---------------------------------------------------------------------------

export async function* nimStream(
  request: NimChatRequest,
): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${NIM_PROXY_PATH}?stream=true`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...request, stream: true }),
  })

  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText)
    throw new Error(`NIM proxy stream error ${response.status}: ${detail}`)
  }

  if (!response.body) {
    throw new Error('NIM proxy returned no response body')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      // Keep the last (possibly incomplete) line in the buffer
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') return
          try {
            const parsed = JSON.parse(data) as { chunk?: string }
            if (parsed.chunk) yield parsed.chunk
          } catch {
            // Ignore malformed SSE lines
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
