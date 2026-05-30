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
import { AUTH_PROVIDER, type AuthProvider } from '@/config'
import { clearTenantClientState } from '@/lib/auth-lifecycle'
import { apiClient } from '@/lib/api-client'
import {
  clearKeycloakSession,
  initializeKeycloakAuth,
  isKeycloakAuthEnabled,
  loginWithKeycloak,
  logoutFromKeycloak,
  subscribeKeycloakToken,
} from '@/lib/keycloak-auth'

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
  authProvider: AuthProvider
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  isAuthInitialized: boolean
  error: string | null
  _hasHydrated: boolean  // Track hydration state
  isExternalAuthEnabled: () => boolean
  isDemoUser: () => boolean
  initializeAuth: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  loginWithIdentityProvider: () => Promise<void>
  logout: () => Promise<void>
  clearError: () => void
  validateToken: () => Promise<boolean>
  setHasHydrated: (state: boolean) => void
}

let unsubscribeKeycloakToken: (() => void) | null = null

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      authProvider: AUTH_PROVIDER,
      user: null,
      token: apiClient.getToken(),
      isAuthenticated: !!apiClient.getToken(),
      isLoading: false,
      isAuthInitialized: AUTH_PROVIDER !== 'keycloak',
      error: null,
      _hasHydrated: false,

      isExternalAuthEnabled: () => get().authProvider === 'keycloak',

      // Server-determined demo status - no client-side guessing
      isDemoUser: () => {
        const user = get().user
        return user?.is_demo ?? false
      },

      setHasHydrated: (state: boolean) => {
        set({ _hasHydrated: state })
      },

      initializeAuth: async () => {
        if (!isKeycloakAuthEnabled()) {
          set({ authProvider: 'local', isAuthInitialized: true })
          return
        }

        if (get().isAuthInitialized) {
          return
        }

        set({ authProvider: 'keycloak', isLoading: true, error: null })

        try {
          if (!unsubscribeKeycloakToken) {
            unsubscribeKeycloakToken = subscribeKeycloakToken((token) => {
              apiClient.setToken(token)
              set({
                token,
                isAuthenticated: Boolean(token),
              })
            })
          }

          const session = await initializeKeycloakAuth()
          if (!session.authenticated || !session.token) {
            apiClient.setToken(null)
            set({
              user: null,
              token: null,
              isAuthenticated: false,
              isAuthInitialized: true,
              isLoading: false,
            })
            return
          }

          apiClient.setToken(session.token)
          const userData = await apiClient.authService.me()
          set({
            token: session.token,
            user: userData as User,
            isAuthenticated: true,
            isAuthInitialized: true,
            isLoading: false,
            error: null,
          })
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Keycloak session initialization failed'
          apiClient.setToken(null)
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isAuthInitialized: true,
            isLoading: false,
            error: message,
          })
        }
      },

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const normalizedEmail = email.trim().toLowerCase()
          const response = await apiClient.authService.login(normalizedEmail, password)
          await clearTenantClientState()
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
          apiClient.setToken(null)
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

      loginWithIdentityProvider: async () => {
        set({ isLoading: true, error: null })
        try {
          await loginWithKeycloak()
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unable to start Keycloak login'
          set({ isLoading: false, error: message })
          throw error
        }
      },

      logout: async () => {
        const shouldLogoutFromKeycloak = get().authProvider === 'keycloak'
        apiClient.setToken(null)
        try {
          localStorage.removeItem('bijmantra-auth')
        } catch {
          // localStorage may not be available
        }
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        })
        await clearTenantClientState()

        if (shouldLogoutFromKeycloak) {
          try {
            await logoutFromKeycloak()
          } catch {
            clearKeycloakSession()
          }
        }
      },

      clearError: () => set({ error: null }),

      validateToken: async () => {
        if (get().authProvider === 'keycloak') {
          await get().initializeAuth()
        }

        const token = get().token
        if (!token) {
          set({ isAuthenticated: false })
          return false
        }
        
        const isValid = await apiClient.validateToken()
        if (!isValid) {
          await clearTenantClientState()
          apiClient.setToken(null)
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
      }),
      merge: (persistedState, currentState) => {
        const persisted = persistedState as Partial<AuthState> | undefined
        const persistedToken = typeof persisted?.token === 'string' ? persisted.token : null
        const token = persistedToken || currentState.token || null
        const user = token ? (persisted?.user ?? currentState.user) : null

        if (token && token !== apiClient.getToken()) {
          apiClient.setToken(token)
        }

        return {
          ...currentState,
          ...persisted,
          token,
          user,
          isAuthenticated: Boolean(token),
          isAuthInitialized: AUTH_PROVIDER !== 'keycloak',
          isLoading: false,
          error: null,
        }
      },
      onRehydrateStorage: () => () => {
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

export const useHydratedSuperuserQueryAccess = () => {
  const hasHydrated = useAuthHydrated()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const isSuperuser = useAuthStore((state) => state.user?.is_superuser ?? false)

  return hasHydrated && isAuthenticated && isSuperuser
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

  // Listen for unauthorized events from API client to sync state
  window.addEventListener('auth:unauthorized', () => {
    const state = useAuthStore.getState()
    // Only logout if currently authenticated to avoid loops
    if (state.isAuthenticated) {
      console.debug('Auth store: Received unauthorized event, logging out')
      void state.logout()
      // Force reload to clear any stale state
      window.location.href = '/login'
    }
  })
}
