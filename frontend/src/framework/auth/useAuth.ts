/**
 * Parashakti Framework - Auth Hook
 * 
 * Wraps the existing auth store and adds permission/division access checking.
 */

import { useAuthStore } from '@/store/auth';
import { useFeatureFlags } from '../features';
import { useDivisionRegistry } from '../registry';

/**
 * Extended auth hook with permission and division access checking
 */
export function useAuth() {
  const authStore = useAuthStore();
  const { isEnabled: _isEnabled } = useFeatureFlags();
  const { isDivisionAccessible } = useDivisionRegistry();

  /**
   * Check if user has a specific permission
   */
  const hasPermission = (permission: string): boolean => {
    if (!authStore.isAuthenticated || !authStore.user) return false;
    
    // Superusers have all permissions
    if (authStore.user.is_superuser) return true;
    
    // Check against backend-provided permissions
    return authStore.user.permissions?.includes(permission) ?? false;
  };

  /**
   * Check if user has all specified permissions
   */
  const hasAllPermissions = (permissions: string[]): boolean => {
    return permissions.every(p => hasPermission(p));
  };

  /**
   * Check if user has any of the specified permissions
   */
  const hasAnyPermission = (permissions: string[]): boolean => {
    return permissions.some(p => hasPermission(p));
  };

  /**
   * Check if user can access a specific division
   */
  const canAccessDivision = (divisionId: string): boolean => {
    if (!authStore.isAuthenticated) return false;
    return isDivisionAccessible(divisionId);
  };

  /**
   * Get current user's organization ID
   */
  const getOrganizationId = (): string | null => {
    return authStore.user?.organization_id?.toString() ?? null;
  };

  return {
    // Pass through from auth store
    user: authStore.user,
    token: authStore.token,
    isAuthenticated: authStore.isAuthenticated,
    isLoading: authStore.isLoading,
    error: authStore.error,
    login: authStore.login,
    logout: authStore.logout,
    clearError: authStore.clearError,

    // Extended functionality
    hasPermission,
    hasAllPermissions,
    hasAnyPermission,
    canAccessDivision,
    getOrganizationId,
    
    // Convenience
    isSuperuser: authStore.user?.is_superuser ?? false,
  };
}
