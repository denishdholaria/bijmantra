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

interface ProtectedRouteProps {
  children: React.ReactNode
  requireSuperuser?: boolean
}

export function ProtectedRoute({ children, requireSuperuser = false }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
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

  if (requireSuperuser && !user?.is_superuser) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center p-6">
        <h2 className="mb-2 text-xl font-semibold text-gray-800 dark:text-gray-200">
          Access Denied
        </h2>
        <p className="text-center text-gray-600 dark:text-gray-400">
          You don&apos;t have permission to access this page.
        </p>
      </div>
    )
  }

  return <>{children}</>
}
