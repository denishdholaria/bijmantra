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
    })

    it('should remove token from localStorage when set to null', async () => {
      const { apiClient } = await import('./api-client')
      
      localStorage.setItem('auth_token', 'existing-token')
      apiClient.setToken(null)
      expect(localStorage.getItem('auth_token')).toBeNull()
    })

    it('should return stored token', async () => {
      const { apiClient } = await import('./api-client')
      
      apiClient.setToken('my-token')
      expect(apiClient.getToken()).toBe('my-token')
    })
  })

  describe('login', () => {
    it('should return demo token when backend is unavailable', async () => {
      globalThis.fetch = vi.fn().mockRejectedValue(new Error('Network error')) as typeof fetch
      
      // Re-import to get fresh instance
      vi.resetModules()
      const { apiClient } = await import('./api-client')
      
      const result = await apiClient.login('demo@example.com', 'password')
      
      expect(result.access_token).toMatch(/^demo_/)
      expect(result.token_type).toBe('bearer')
    })

    it('should return demo token on server error (5xx)', async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        json: () => Promise.resolve({ detail: 'Bad Gateway' }),
      })
      
      vi.resetModules()
      const { apiClient } = await import('./api-client')
      
      const result = await apiClient.login('demo@example.com', 'password')
      
      expect(result.access_token).toMatch(/^demo_/)
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

      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      }) as typeof fetch

      vi.resetModules()
      const { apiClient } = await import('./api-client')
      apiClient.setToken('test-token')
      
      const result = await apiClient.getPrograms()
      
      expect(result.metadata).toBeDefined()
      expect(result.metadata.pagination).toBeDefined()
      expect(result.result.data).toBeInstanceOf(Array)
    })
  })
})
