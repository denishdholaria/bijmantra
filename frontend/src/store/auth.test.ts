/**
 * Auth Store Tests
 */

import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuthStore, useHydratedSuperuserQueryAccess } from './auth'

// Mock the api-client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    getToken: vi.fn(() => null),
    setToken: vi.fn(),
    validateToken: vi.fn(),
    authService: {
      login: vi.fn(),
    },
  },
}))

import { apiClient } from '@/lib/api-client'

describe('useAuthStore', () => {
  beforeEach(() => {
    window.localStorage.clear()
    // Reset store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      _hasHydrated: false,
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
      vi.mocked(apiClient.authService.login).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ access_token: 'test-token', token_type: 'bearer' }), 100))
      )

      const loginPromise = useAuthStore.getState().login('test@example.com', 'password')
      expect(useAuthStore.getState().isLoading).toBe(true)
      await loginPromise
    })

    it('should set token and isAuthenticated on successful login', async () => {
      vi.mocked(apiClient.authService.login).mockResolvedValue({
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
      expect(apiClient.authService.login).toHaveBeenCalledWith('test@example.com', 'password')
    })

    it('should normalize email before login', async () => {
      vi.mocked(apiClient.authService.login).mockResolvedValue({
        access_token: 'test-token',
        token_type: 'bearer',
      })

      await useAuthStore.getState().login(' Test@Example.Com ', 'password')

      expect(apiClient.authService.login).toHaveBeenCalledWith('test@example.com', 'password')
    })

    it('should set error on failed login', async () => {
      vi.mocked(apiClient.authService.login).mockRejectedValue(new Error('Invalid credentials'))

      await expect(useAuthStore.getState().login('test@example.com', 'wrong')).rejects.toThrow('Invalid credentials')

      const state = useAuthStore.getState()
      expect(state.error).toBe('Invalid credentials')
      expect(state.isAuthenticated).toBe(false)
      expect(state.isLoading).toBe(false)
      expect(apiClient.setToken).toHaveBeenCalledWith(null)
    })
  })

  describe('logout', () => {
    it('should clear auth state on logout', () => {
      window.localStorage.setItem('auth_token', 'test-token')
      window.localStorage.setItem('bijmantra-auth', JSON.stringify({ state: { token: 'test-token' } }))

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
      const persisted = JSON.parse(window.localStorage.getItem('bijmantra-auth') ?? '{}')
      expect(persisted.state).toMatchObject({ token: null, user: null })
    })
  })

  describe('clearError', () => {
    it('should clear error state', () => {
      useAuthStore.setState({ error: 'Some error' })
      useAuthStore.getState().clearError()
      expect(useAuthStore.getState().error).toBeNull()
    })
  })

  describe('useHydratedSuperuserQueryAccess', () => {
    it('should require hydration, authentication, and superuser state', () => {
      const { result } = renderHook(() => useHydratedSuperuserQueryAccess())

      expect(result.current).toBe(false)

      act(() => {
        useAuthStore.setState({
          _hasHydrated: true,
          isAuthenticated: true,
          user: {
            id: 1,
            email: 'admin@example.com',
            full_name: 'Admin User',
            organization_id: 1,
            is_active: true,
            is_superuser: false,
            is_demo: false,
          },
        })
      })

      expect(result.current).toBe(false)

      act(() => {
        useAuthStore.setState({
          user: {
            id: 1,
            email: 'admin@example.com',
            full_name: 'Admin User',
            organization_id: 1,
            is_active: true,
            is_superuser: true,
            is_demo: false,
          },
        })
      })

      expect(result.current).toBe(true)
    })
  })
})
