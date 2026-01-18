/**
 * Dock Sync Hook
 * 
 * Provides optional backend synchronization for the Mahasarthi dock.
 * Uses TanStack Query for API calls with proper caching.
 * 
 * Features:
 * - Sync dock state to backend for cross-device persistence
 * - Load dock state from backend
 * - Reset dock to role-based defaults
 * - Graceful offline handling (localStorage still works)
 * 
 * @see backend/app/api/v2/dock.py for API endpoints
 * @see frontend/src/store/dockStore.ts for local state management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/auth'
import { useDockStore, DockItem, DockPreferences } from '@/store/dockStore'
import { useCallback, useEffect, useState } from 'react'

// ============================================================================
// Types
// ============================================================================

interface DockStateResponse {
  status: string
  data: {
    userId: number
    pinnedItems: DockItem[]
    recentItems: DockItem[]
    preferences: DockPreferences
    updatedAt: string
  }
}

interface UpdateDockRequest {
  pinnedItems?: DockItem[]
  recentItems?: DockItem[]
  preferences?: DockPreferences
}

interface ResetResponse {
  status: string
  message: string
  data: {
    pinnedCount: number
  }
}

interface DefaultsResponse {
  status: string
  data: {
    role: string
    items: DockItem[]
  }
}

// ============================================================================
// API Functions
// ============================================================================

async function fetchDockState(userId: number): Promise<DockStateResponse> {
  const response = await fetch(`/api/v2/dock?user_id=${userId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch dock state: ${response.status}`)
  }
  return response.json()
}

async function updateDockState(
  userId: number,
  organizationId: number,
  data: UpdateDockRequest
): Promise<{ status: string; message: string; data: { updatedAt: string } }> {
  const response = await fetch(
    `/api/v2/dock?user_id=${userId}&organization_id=${organizationId}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  if (!response.ok) {
    throw new Error(`Failed to update dock state: ${response.status}`)
  }
  return response.json()
}

async function resetDockToDefaults(
  userId: number,
  organizationId: number,
  role: string
): Promise<ResetResponse> {
  const response = await fetch(
    `/api/v2/dock/reset?role=${encodeURIComponent(role)}&user_id=${userId}&organization_id=${organizationId}`,
    { method: 'POST' }
  )
  if (!response.ok) {
    throw new Error(`Failed to reset dock: ${response.status}`)
  }
  return response.json()
}

async function fetchRoleDefaults(role: string): Promise<DefaultsResponse> {
  const response = await fetch(`/api/v2/dock/defaults/${encodeURIComponent(role)}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch role defaults: ${response.status}`)
  }
  return response.json()
}

// ============================================================================
// Hook Options
// ============================================================================

export interface UseDockSyncOptions {
  /**
   * Enable automatic sync on mount (loads from backend if available)
   * @default false
   */
  autoSync?: boolean
  
  /**
   * Sync interval in milliseconds (0 = disabled)
   * @default 0
   */
  syncInterval?: number
  
  /**
   * Callback when sync completes successfully
   */
  onSyncSuccess?: () => void
  
  /**
   * Callback when sync fails
   */
  onSyncError?: (error: Error) => void
}

// ============================================================================
// Main Hook
// ============================================================================

/**
 * Hook for syncing dock state with backend API.
 * 
 * This hook is opt-in and additive - localStorage persistence continues
 * to work independently. Backend sync enables cross-device persistence.
 * 
 * @example
 * ```tsx
 * function DockSettings() {
 *   const { 
 *     syncToBackend, 
 *     loadFromBackend, 
 *     resetToDefaults,
 *     isSyncing,
 *     lastSyncedAt 
 *   } = useDockSync({ autoSync: true })
 *   
 *   return (
 *     <Button onClick={syncToBackend} disabled={isSyncing}>
 *       {isSyncing ? 'Syncing...' : 'Sync to Cloud'}
 *     </Button>
 *   )
 * }
 * ```
 */
export function useDockSync(options: UseDockSyncOptions = {}) {
  const { autoSync = false, syncInterval = 0, onSyncSuccess, onSyncError } = options
  
  const queryClient = useQueryClient()
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  
  // Local state for tracking sync status
  const [lastSyncedAt, setLastSyncedAt] = useState<Date | null>(null)
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  )
  
  // Get dock store state and actions
  const pinnedItems = useDockStore((state) => state.pinnedItems)
  const recentItems = useDockStore((state) => state.recentItems)
  const preferences = useDockStore((state) => state.preferences)
  
  // Derived values
  const userId = user?.id
  const organizationId = user?.organization_id
  const canSync = isAuthenticated && !!userId && !!organizationId && isOnline
  
  // ============================================================================
  // Online/Offline Detection
  // ============================================================================
  
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])
  
  // ============================================================================
  // Query: Load dock state from backend
  // ============================================================================
  
  const {
    data: backendState,
    isLoading: isLoadingFromBackend,
    error: loadError,
    refetch: refetchBackendState,
  } = useQuery({
    queryKey: ['dock-state', userId],
    queryFn: () => fetchDockState(userId!),
    enabled: canSync && autoSync,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    refetchOnWindowFocus: false,
  })
  
  // ============================================================================
  // Mutation: Sync to backend
  // ============================================================================
  
  const syncMutation = useMutation({
    mutationFn: async () => {
      if (!userId || !organizationId) {
        throw new Error('User not authenticated')
      }
      return updateDockState(userId, organizationId, {
        pinnedItems,
        recentItems,
        preferences,
      })
    },
    onSuccess: () => {
      setLastSyncedAt(new Date())
      queryClient.invalidateQueries({ queryKey: ['dock-state', userId] })
      onSyncSuccess?.()
    },
    onError: (error: Error) => {
      onSyncError?.(error)
    },
  })
  
  // ============================================================================
  // Mutation: Reset to defaults
  // ============================================================================
  
  const resetMutation = useMutation({
    mutationFn: async (role: string) => {
      if (!userId || !organizationId) {
        throw new Error('User not authenticated')
      }
      return resetDockToDefaults(userId, organizationId, role)
    },
    onSuccess: (_, role) => {
      // Refetch to get the new state
      queryClient.invalidateQueries({ queryKey: ['dock-state', userId] })
      // Also update local store
      loadFromBackend()
    },
    onError: (error: Error) => {
      onSyncError?.(error)
    },
  })
  
  // ============================================================================
  // Query: Get role defaults (for preview)
  // ============================================================================
  
  const getRoleDefaults = useCallback(async (role: string) => {
    try {
      const response = await fetchRoleDefaults(role)
      return response.data.items
    } catch (error) {
      console.error('Failed to fetch role defaults:', error)
      return null
    }
  }, [])
  
  // ============================================================================
  // Actions
  // ============================================================================
  
  /**
   * Sync current local dock state to backend
   */
  const syncToBackend = useCallback(async () => {
    if (!canSync) {
      console.warn('Cannot sync: user not authenticated or offline')
      return false
    }
    
    try {
      await syncMutation.mutateAsync()
      return true
    } catch (error) {
      console.error('Sync to backend failed:', error)
      return false
    }
  }, [canSync, syncMutation])
  
  /**
   * Load dock state from backend and apply to local store
   */
  const loadFromBackend = useCallback(async () => {
    if (!canSync) {
      console.warn('Cannot load: user not authenticated or offline')
      return false
    }
    
    try {
      const response = await refetchBackendState()
      
      if (response.data?.data) {
        const { pinnedItems, recentItems, preferences } = response.data.data
        
        // Apply to local store
        // Note: We're directly setting state here - the store's persist middleware
        // will automatically save to localStorage
        useDockStore.setState({
          pinnedItems,
          recentItems,
          preferences,
        })
        
        setLastSyncedAt(new Date())
        return true
      }
      return false
    } catch (error) {
      console.error('Load from backend failed:', error)
      return false
    }
  }, [canSync, refetchBackendState])
  
  /**
   * Reset dock to role-based defaults (both backend and local)
   */
  const resetToDefaults = useCallback(async (role: string = 'default') => {
    if (!canSync) {
      // Offline fallback: reset local store only
      const { defaultDocksByRole } = await import('@/store/dockStore')
      const defaults = defaultDocksByRole[role] || defaultDocksByRole.default
      
      useDockStore.setState({
        pinnedItems: defaults.map(item => ({ ...item, isPinned: true })),
        recentItems: [],
      })
      return true
    }
    
    try {
      await resetMutation.mutateAsync(role)
      // Load the new state from backend
      await loadFromBackend()
      return true
    } catch (error) {
      console.error('Reset to defaults failed:', error)
      return false
    }
  }, [canSync, resetMutation, loadFromBackend])
  
  // ============================================================================
  // Auto-sync on interval
  // ============================================================================
  
  useEffect(() => {
    if (!syncInterval || syncInterval <= 0 || !canSync) return
    
    const intervalId = setInterval(() => {
      syncToBackend()
    }, syncInterval)
    
    return () => clearInterval(intervalId)
  }, [syncInterval, canSync, syncToBackend])
  
  // ============================================================================
  // Return
  // ============================================================================
  
  return {
    // Actions
    syncToBackend,
    loadFromBackend,
    resetToDefaults,
    getRoleDefaults,
    
    // Status
    isSyncing: syncMutation.isPending,
    isLoading: isLoadingFromBackend,
    isResetting: resetMutation.isPending,
    
    // State
    lastSyncedAt,
    isOnline,
    canSync,
    
    // Errors
    syncError: syncMutation.error,
    loadError,
    resetError: resetMutation.error,
    
    // Backend state (if loaded)
    backendState: backendState?.data,
  }
}

// ============================================================================
// Convenience Hooks
// ============================================================================

/**
 * Hook to check if dock is synced with backend
 * Compares local state with backend state
 */
export function useDockSyncStatus() {
  const { backendState, lastSyncedAt, isOnline, canSync } = useDockSync({ autoSync: true })
  const pinnedItems = useDockStore((state) => state.pinnedItems)
  const recentItems = useDockStore((state) => state.recentItems)
  
  const isSynced = backendState
    ? JSON.stringify(pinnedItems) === JSON.stringify(backendState.pinnedItems) &&
      JSON.stringify(recentItems) === JSON.stringify(backendState.recentItems)
    : false
  
  return {
    isSynced,
    lastSyncedAt,
    isOnline,
    canSync,
    hasBackendState: !!backendState,
  }
}

/**
 * Hook for auto-syncing dock changes to backend
 * Debounces changes to avoid excessive API calls
 */
export function useAutoSyncDock(debounceMs: number = 5000) {
  const { syncToBackend, canSync } = useDockSync()
  const pinnedItems = useDockStore((state) => state.pinnedItems)
  const recentItems = useDockStore((state) => state.recentItems)
  const preferences = useDockStore((state) => state.preferences)
  
  useEffect(() => {
    if (!canSync) return
    
    const timeoutId = setTimeout(() => {
      syncToBackend()
    }, debounceMs)
    
    return () => clearTimeout(timeoutId)
  }, [pinnedItems, recentItems, preferences, canSync, syncToBackend, debounceMs])
}

export default useDockSync
