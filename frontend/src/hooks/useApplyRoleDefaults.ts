/**
 * useApplyRoleDefaults Hook
 * 
 * Applies role-based dock defaults on first login.
 * Per Think-Tank §5.1: "Apply role-based dock on first login" - Priority P0
 * 
 * This hook should be called in Layout.tsx to ensure role defaults
 * are applied when the user first logs in.
 * 
 * @see docs/gupt/think-tank/think-tank.md §5.1 Implementation Roadmap
 */

import { useEffect } from 'react';
import { useAuthStore } from '@/store/auth';
import { useDockStore } from '@/store/dockStore';

/**
 * Applies role-based dock defaults when user logs in for the first time.
 * 
 * Role mapping:
 * - breeder → Breeding-focused dock (Programs, Trials, Germplasm, etc.)
 * - seed_company → Seed Operations dock (Lab Samples, Quality Gate, etc.)
 * - genebank_curator → Seed Bank dock (Vault, Accessions, Viability, etc.)
 * - researcher → Research dock (Genomic Selection, WASM, QTL, etc.)
 * - default → Basic dock (Dashboard, Programs, Trials, Germplasm)
 */
export function useApplyRoleDefaults(): void {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const applyRoleDefaults = useDockStore((state) => state.applyRoleDefaults);
  const hasAppliedRoleDefaults = useDockStore((state) => state.hasAppliedRoleDefaults);

  useEffect(() => {
    // Only apply if:
    // 1. User is authenticated
    // 2. User data is available
    // 3. Role defaults haven't been applied yet
    if (isAuthenticated && user && !hasAppliedRoleDefaults) {
      // Get the primary role from user roles array
      // Default to 'default' if no roles are assigned
      const primaryRole = user.roles?.[0] || 'default';
      
      applyRoleDefaults(primaryRole);
    }
  }, [isAuthenticated, user, hasAppliedRoleDefaults, applyRoleDefaults]);
}

export default useApplyRoleDefaults;
