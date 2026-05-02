/**
 * Hooks Index
 * Central export for all custom hooks
 */

// Navigation hooks
export { usePinnedNav } from './usePinnedNav'
export { useRoleBasedNav, useRoleStore, ROLE_QUICK_ACTIONS } from './useRoleBasedNav'
export type { UserRole } from './useRoleBasedNav'

// Dock sync hooks
export { useDockSync, useDockSyncStatus, useAutoSyncDock } from './useDockSync'
export type { UseDockSyncOptions } from './useDockSync'

// Theme hooks
export { useTheme } from './useTheme'
export type { UseThemeReturn } from './useTheme'

// Utility hooks
export { useDebounce, useDebouncedCallback, useThrottledCallback } from './useDebounce'
export { useMediaQuery } from './useMediaQuery'

// UI hooks
export { useToast, useToastStore } from './useToast'
export type { Toast, ToastType } from './useToast'

// Role defaults hook
export { useApplyRoleDefaults } from './useApplyRoleDefaults'
