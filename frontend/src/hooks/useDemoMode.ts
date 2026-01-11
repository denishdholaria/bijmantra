/**
 * Demo Mode Hook
 * 
 * ARCHITECTURE (Production-Ready):
 * ================================
 * Demo status is determined SERVER-SIDE at login time, not client-side.
 * 
 * - admin@bijmantra.org → is_demo: false → sees REAL data (empty if no data)
 * - demo@bijmantra.org → is_demo: true → sees DEMO data (seeded in Demo Organization)
 * 
 * The server checks:
 * 1. User email (demo@bijmantra.org)
 * 2. Organization name ("Demo Organization")
 * 
 * This ensures:
 * - No client-side guessing or hardcoded checks
 * - Admin users NEVER see demo data
 * - Demo users ONLY see demo data
 * - Clear separation for development vs production testing
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { useAuthStore } from '@/store/auth';

interface DemoModeState {
  // UI preference: whether to show the demo banner
  showDemoBanner: boolean;
  // Toggle demo banner visibility
  toggleDemoBanner: () => void;
}

// Minimal store - just UI preferences, not demo status
export const useDemoModeStore = create<DemoModeState>()(
  persist(
    (set) => ({
      showDemoBanner: true,
      toggleDemoBanner: () => set((state) => ({ showDemoBanner: !state.showDemoBanner })),
    }),
    {
      name: 'bijmantra-demo-ui',
    }
  )
);

/**
 * Primary hook for checking demo mode.
 * Uses server-determined status from auth store.
 */
export function useDemoMode() {
  const user = useAuthStore((state) => state.user);
  const isDemoUser = useAuthStore((state) => state.isDemoUser);
  const { showDemoBanner, toggleDemoBanner } = useDemoModeStore();
  
  // Server-determined demo status
  const isDemoMode = isDemoUser();
  
  return {
    // Core status (server-determined)
    isDemoMode,
    isProductionUser: !isDemoMode,
    
    // User info
    organizationName: user?.organization_name || 'Unknown',
    organizationId: user?.organization_id,
    
    // UI preferences
    showDemoBanner: isDemoMode && showDemoBanner,
    toggleDemoBanner,
    
    // Legacy compatibility (deprecated - use isDemoMode instead)
    demoDatasets: {
      germplasm: isDemoMode,
      trials: isDemoMode,
      observations: isDemoMode,
      seedBank: isDemoMode,
      sensors: isDemoMode,
      vision: isDemoMode,
    },
    
    // Legacy no-ops (deprecated)
    setDemoMode: () => console.warn('setDemoMode is deprecated - demo status is server-determined'),
    toggleDemoMode: () => console.warn('toggleDemoMode is deprecated - demo status is server-determined'),
    setDatasetDemo: () => console.warn('setDatasetDemo is deprecated - demo status is server-determined'),
  };
}

/**
 * Check if user is in demo organization.
 * DEPRECATED: Use useDemoMode().isDemoMode instead.
 */
export function isDemoOrganization(userEmail?: string, orgName?: string): boolean {
  console.warn('isDemoOrganization is deprecated - use useDemoMode().isDemoMode instead');
  if (userEmail === 'demo@bijmantra.org') return true;
  if (orgName === 'Demo Organization') return true;
  return false;
}

/**
 * Helper hook to check if a specific dataset should show demo data.
 * DEPRECATED: Demo status is now all-or-nothing based on user's organization.
 */
export function useDatasetDemoMode(dataset: string): boolean {
  const { isDemoMode } = useDemoMode();
  return isDemoMode;
}

export default useDemoMode;
