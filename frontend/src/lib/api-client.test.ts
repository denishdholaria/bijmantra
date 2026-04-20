/**
 * API Client Tests
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

// We need to test the actual implementation, so we'll create a fresh instance
describe('APIClient', () => {
  let originalFetch: typeof globalThis.fetch

  beforeEach(() => {
    originalFetch = globalThis.fetch
    localStorage.clear()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.clearAllMocks()
  })

  describe('token management', () => {
    it('should store token in localStorage', async () => {
      // Import fresh instance
      const { apiClient } = await import('./api-client')
      
      apiClient.setToken('test-token')
      expect(localStorage.getItem('auth_token')).toBe('test-token')
    }, 15000)

    it('should remove token from localStorage when set to null', async () => {
      const { apiClient } = await import('./api-client')
      
      localStorage.setItem('auth_token', 'existing-token')
      apiClient.setToken(null)
      expect(localStorage.getItem('auth_token')).toBeNull()
    }, 15000)

    it('should return stored token', async () => {
      const { apiClient } = await import('./api-client')
      
      apiClient.setToken('my-token')
      expect(apiClient.getToken()).toBe('my-token')
    }, 15000)
  })

  describe('login', () => {
    it('should fail closed when backend is unavailable', async () => {
      globalThis.fetch = vi.fn().mockRejectedValue(new Error('Network error')) as typeof fetch
      
      // Re-import to get fresh instance
      vi.resetModules()
      const { apiClient } = await import('./api-client')
      
      await expect(apiClient.authService.login('demo@example.com', 'password')).rejects.toThrow(
        'Unable to reach the server. Check connectivity and try again.'
      )
    })

    it('should fail closed on server error (5xx)', async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        json: () => Promise.resolve({ detail: 'Bad Gateway' }),
      })
      
      vi.resetModules()
      const { apiClient } = await import('./api-client')
      
      await expect(apiClient.authService.login('demo@example.com', 'password')).rejects.toThrow(
        'Bad Gateway'
      )
    })

    it('should discard legacy demo tokens during initialization', async () => {
      localStorage.setItem('auth_token', 'demo_legacy-token')

      vi.resetModules()
      const { apiClient } = await import('./api-client')

      expect(apiClient.getToken()).toBeNull()
      expect(localStorage.getItem('auth_token')).toBeNull()
    })
  })

  describe('BrAPI response types', () => {
    it('should have correct BrAPIResponse structure', async () => {
      const mockResponse = {
        metadata: {
          datafiles: [],
          pagination: { currentPage: 0, pageSize: 10, totalCount: 1, totalPages: 1 },
          status: [{ message: 'Success', messageType: 'INFO' }],
        },
        result: { data: [{ programDbId: '1', programName: 'Test' }] },
      }

      globalThis.fetch = vi.fn().mockResolvedValue(
        new Response(JSON.stringify(mockResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      ) as typeof fetch

      vi.resetModules()
      const { apiClient } = await import('./api-client')
      apiClient.setToken('test-token')
      
      const result = await apiClient.programService.getPrograms()
      
      expect(result.metadata).toBeDefined()
      expect(result.metadata.pagination).toBeDefined()
      expect(result.result.data).toBeInstanceOf(Array)
    })

    it('should attach a trace id header to API requests', async () => {
      const fetchMock = vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ result: { ok: true } }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      )
      globalThis.fetch = fetchMock as typeof fetch

      vi.resetModules()
      const { apiClient } = await import('./api-client')

      await apiClient.get('/api/test')

      const [, init] = fetchMock.mock.calls[0]
      const headers = new Headers(init?.headers)

      expect(headers.get('X-Trace-Id')).toMatch(/^[a-f0-9]{32}$/)
    })
  })

  describe('auth error handling', () => {
    it('should clear token and dispatch unauthorized event on 401', async () => {
      const response = new Response(JSON.stringify({ message: 'Unauthorized' }), {
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'X-Trace-Id': 'unauthorized-trace-1234',
        },
      })
      globalThis.fetch = vi.fn().mockResolvedValue(response) as typeof fetch

      vi.resetModules()
      const dispatchEventSpy = vi.spyOn(window, 'dispatchEvent')
      const { apiClient } = await import('./api-client')

      apiClient.setToken('test-token')

      await expect(apiClient.get('/api/test')).rejects.toMatchObject({
        statusCode: 401,
        context: {
          traceId: 'unauthorized-trace-1234',
        },
      })

      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(dispatchEventSpy).toHaveBeenCalledWith(expect.objectContaining({ type: 'auth:unauthorized' }))
    })

    it('should preserve token and avoid unauthorized event on 403', async () => {
      const response = new Response(JSON.stringify({ message: 'Forbidden' }), {
        status: 403,
        headers: {
          'Content-Type': 'application/json',
          'X-Trace-Id': 'forbidden-trace-5678',
        },
      })
      globalThis.fetch = vi.fn().mockResolvedValue(response) as typeof fetch

      vi.resetModules()
      const dispatchEventSpy = vi.spyOn(window, 'dispatchEvent')
      const { apiClient } = await import('./api-client')

      apiClient.setToken('test-token')

      await expect(apiClient.get('/api/test')).rejects.toMatchObject({
        statusCode: 403,
        context: {
          traceId: 'forbidden-trace-5678',
        },
      })

      expect(localStorage.getItem('auth_token')).toBe('test-token')
      expect(dispatchEventSpy).not.toHaveBeenCalledWith(expect.objectContaining({ type: 'auth:unauthorized' }))
    })
  })
})
