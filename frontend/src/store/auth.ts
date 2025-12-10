/**
 * Authentication Store (Zustand)
 */

import { create } from 'zustand'
import { apiClient } from '@/lib/api-client'

interface User {
  id: number
  email: string
  full_name: string
  organization_id: number
  is_active: boolean
  is_superuser: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  clearError: () => void
  validateToken: () => Promise<boolean>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: apiClient.getToken(),
  isAuthenticated: !!apiClient.getToken(),
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.login(email, password)
      apiClient.setToken(response.access_token)
      
      set({
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed'
      set({
        error: message,
        isLoading: false,
        isAuthenticated: false,
        token: null,
      })
      throw error
    }
  },

  logout: () => {
    apiClient.setToken(null)
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null,
    })
  },

  clearError: () => set({ error: null }),

  validateToken: async () => {
    const token = get().token
    if (!token) {
      set({ isAuthenticated: false })
      return false
    }
    
    const isValid = await apiClient.validateToken()
    if (!isValid) {
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      })
    }
    return isValid
  },
}))
