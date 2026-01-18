/**
 * Auth Store Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuthStore } from './auth'

// Mock the api-client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    getToken: vi.fn(() => null),
    setToken: vi.fn(),
    login: vi.fn(),
  },
}))

import { apiClient } from '@/lib/api-client'

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    })
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(state.isLoading).toBe(false)
      expect(state.error).toBeNull()
    })
  })

  describe('login', () => {
    it('should set isLoading to true during login', async () => {
      vi.mocked(apiClient.login).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ access_token: 'test-token', token_type: 'bearer' }), 100))
      )

      const loginPromise = useAuthStore.getState().login('test@example.com', 'password')
      expect(useAuthStore.getState().isLoading).toBe(true)
      await loginPromise
    })

    it('should set token and isAuthenticated on successful login', async () => {
      vi.mocked(apiClient.login).mockResolvedValue({
        access_token: 'test-token',
        token_type: 'bearer',
      })

      await useAuthStore.getState().login('test@example.com', 'password')

      const state = useAuthStore.getState()
      expect(state.token).toBe('test-token')
      expect(state.isAuthenticated).toBe(true)
      expect(state.isLoading).toBe(false)
      expect(state.error).toBeNull()
      expect(apiClient.setToken).toHaveBeenCalledWith('test-token')
    })

    it('should set error on failed login', async () => {
      vi.mocked(apiClient.login).mockRejectedValue(new Error('Invalid credentials'))

      await expect(useAuthStore.getState().login('test@example.com', 'wrong')).rejects.toThrow('Invalid credentials')

      const state = useAuthStore.getState()
      expect(state.error).toBe('Invalid credentials')
      expect(state.isAuthenticated).toBe(false)
      expect(state.isLoading).toBe(false)
    })
  })

  describe('logout', () => {
    it('should clear auth state on logout', () => {
      // Set authenticated state first
      useAuthStore.setState({
        user: { id: 1, email: 'test@example.com', full_name: 'Test', organization_id: 1, is_active: true, is_superuser: false, is_demo: false },
        token: 'test-token',
        isAuthenticated: true,
      })

      useAuthStore.getState().logout()

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
      expect(apiClient.setToken).toHaveBeenCalledWith(null)
    })
  })

  describe('clearError', () => {
    it('should clear error state', () => {
      useAuthStore.setState({ error: 'Some error' })
      useAuthStore.getState().clearError()
      expect(useAuthStore.getState().error).toBeNull()
    })
  })
})
