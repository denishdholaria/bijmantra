/**
 * Authentication Store (Zustand)
 * 
 * Handles user authentication and organization context.
 * The login response now includes organization info to determine:
 * - Whether user is in Demo Organization (sees demo data)
 * - Whether user is in Production Organization (sees real/empty data)
 * 
 * HYDRATION: Uses Zustand persist middleware with proper hydration tracking.
 * The _hasHydrated flag is set via onRehydrateStorage callback AND a fallback
 * subscription to ensure it's always set even if the callback timing varies.
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { apiClient } from '@/lib/api-client'

interface User {
  id: number
  email: string
  full_name: string
  organization_id: number
  organization_name?: string
  is_demo: boolean  // Server-determined demo status
  is_active: boolean
  is_superuser: boolean
  roles?: string[]
  permissions?: string[]
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  _hasHydrated: boolean  // Track hydration state
  isDemoUser: () => boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  clearError: () => void
  validateToken: () => Promise<boolean>
  setHasHydrated: (state: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: apiClient.getToken(),
      isAuthenticated: !!apiClient.getToken(),
      isLoading: false,
      error: null,
      _hasHydrated: false,

      // Server-determined demo status - no client-side guessing
      isDemoUser: () => {
        const user = get().user
        return user?.is_demo ?? false
      },

      setHasHydrated: (state: boolean) => {
        set({ _hasHydrated: state })
      },

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await apiClient.login(email, password)
          apiClient.setToken(response.access_token)
          
          // Extract user info from login response
          const userData = response.user as User | undefined
          
          set({
            token: response.access_token,
            user: userData || null,
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
            user: null,
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
    }),
    {
      name: 'bijmantra-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ 
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        // This callback fires when rehydration completes
        // Set _hasHydrated directly on the store
        useAuthStore.setState({ _hasHydrated: true })
      },
    }
  )
)

// Selector for hydration state
export const useAuthHydrated = () => {
  return useAuthStore((state) => state._hasHydrated)
}

// Ensure hydration flag is set even if onRehydrateStorage doesn't fire
// This handles edge cases like empty localStorage or SSR
if (typeof window !== 'undefined') {
  // Use requestAnimationFrame to ensure we're after React's first render cycle
  // and after Zustand's synchronous hydration attempt
  const ensureHydrated = () => {
    const state = useAuthStore.getState()
    if (!state._hasHydrated) {
      useAuthStore.setState({ _hasHydrated: true })
    }
  }
  
  // Try multiple timing strategies to catch hydration
  // 1. Microtask (Promise.resolve) - fires after current execution
  Promise.resolve().then(ensureHydrated)
  
  // 2. requestAnimationFrame - fires before next paint
  requestAnimationFrame(ensureHydrated)
  
  // 3. setTimeout 0 - fires after current event loop
  setTimeout(ensureHydrated, 0)
}
