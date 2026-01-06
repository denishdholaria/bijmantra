/**
 * Hooks Index
 * Central export for all custom hooks
 */

// Navigation hooks
export { usePinnedNav } from './usePinnedNav'
export { useRoleBasedNav, useRoleStore, ROLE_QUICK_ACTIONS } from './useRoleBasedNav'
export type { UserRole } from './useRoleBasedNav'

// Utility hooks
export { useDebounce, useDebouncedCallback, useThrottledCallback } from './useDebounce'

// UI hooks
export { useToast, useToastStore } from './useToast'
export type { Toast, ToastType } from './useToast'
