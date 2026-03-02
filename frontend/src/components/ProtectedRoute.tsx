/**
 * Protected Route Component
 * Redirects to login if not authenticated
 * 
 * IMPORTANT: Waits for Zustand persist hydration before checking auth.
 * Zustand's persist middleware hydrates asynchronously from localStorage,
 * so we must wait for hydration to complete before making auth decisions.
 * 
 * Uses a combination of:
 * 1. Zustand's _hasHydrated state (set via onRehydrateStorage)
 * 2. A local effect to handle edge cases where hydration completes after mount
 */

import { Navigate } from 'react-router-dom'
import { useAuthStore, useAuthHydrated } from '@/store/auth'
import { useState, useEffect } from 'react'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const hasHydrated = useAuthHydrated()
  
  // Local state to force re-render after hydration
  const [isReady, setIsReady] = useState(hasHydrated)
  
  useEffect(() => {
    // If already hydrated, we're ready
    if (hasHydrated) {
      setIsReady(true)
      return
    }
    
    // Subscribe to store changes to catch hydration
    const unsubscribe = useAuthStore.subscribe((state) => {
      if (state._hasHydrated) {
        setIsReady(true)
      }
    })
    
    // Also set a maximum wait time (500ms) to prevent infinite loading
    const timeout = setTimeout(() => {
      setIsReady(true)
    }, 500)
    
    return () => {
      unsubscribe()
      clearTimeout(timeout)
    }
  }, [hasHydrated])

  // Wait for hydration to complete
  if (!isReady) {
    // Return a minimal loading state - null causes no flash
    return null
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
