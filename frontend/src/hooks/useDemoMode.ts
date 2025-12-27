/**
 * Demo Mode Hook
 * 
 * Tracks whether the current user is in the Demo Organization.
 * Demo data is sandboxed in the database - no in-memory fallbacks needed.
 * 
 * This hook is used for:
 * - Showing a "Demo Mode" banner to demo users
 * - Optionally restricting certain actions for demo users
 * - Analytics filtering (exclude demo org from reports)
 * 
 * Architecture:
 * - Demo data lives in "Demo Organization" in the database
 * - Demo users (demo@bijmantra.org) log into this organization
 * - Production organizations are completely isolated
 * - No in-memory fallbacks or mixed data
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface DemoModeState {
  // Whether the current user is in Demo Organization (legacy: isDemoMode)
  isDemoMode: boolean;
  // Whether to show the demo banner
  showDemoBanner: boolean;
  // Per-dataset demo toggles (legacy - kept for backward compatibility)
  demoDatasets: {
    germplasm: boolean;
    trials: boolean;
    observations: boolean;
    seedBank: boolean;
    sensors: boolean;
    vision: boolean;
  };
  // Legacy: Toggle demo mode (no-op in sandbox architecture - user org determines demo status)
  toggleDemoMode: () => void;
  // Set demo user status (called after login)
  setDemoMode: (isDemo: boolean) => void;
  // Toggle demo banner visibility
  toggleDemoBanner: () => void;
  // Legacy: Set dataset demo mode (no-op in sandbox architecture)
  setDatasetDemo: (dataset: keyof DemoModeState['demoDatasets'], enabled: boolean) => void;
}

export const useDemoMode = create<DemoModeState>()(
  persist(
    (set) => ({
      isDemoMode: false,
      showDemoBanner: true,
      demoDatasets: {
        germplasm: false,
        trials: false,
        observations: false,
        seedBank: false,
        sensors: false,
        vision: false,
      },
      setDemoMode: (isDemo) => set({ 
        isDemoMode: isDemo,
        // When user is in demo org, all datasets are "demo"
        demoDatasets: {
          germplasm: isDemo,
          trials: isDemo,
          observations: isDemo,
          seedBank: isDemo,
          sensors: isDemo,
          vision: isDemo,
        }
      }),
      toggleDemoMode: () => set((state) => ({ 
        isDemoMode: !state.isDemoMode,
        demoDatasets: {
          germplasm: !state.isDemoMode,
          trials: !state.isDemoMode,
          observations: !state.isDemoMode,
          seedBank: !state.isDemoMode,
          sensors: !state.isDemoMode,
          vision: !state.isDemoMode,
        }
      })),
      toggleDemoBanner: () => set((state) => ({ showDemoBanner: !state.showDemoBanner })),
      setDatasetDemo: (dataset, enabled) =>
        set((state) => ({
          demoDatasets: { ...state.demoDatasets, [dataset]: enabled },
        })),
    }),
    {
      name: 'bijmantra-demo-mode',
    }
  )
);

/**
 * Check if user is in demo organization based on their email or org
 */
export function isDemoOrganization(userEmail?: string, orgName?: string): boolean {
  if (userEmail === 'demo@bijmantra.org') return true;
  if (orgName === 'Demo Organization') return true;
  return false;
}

/**
 * Helper hook to check if a specific dataset should show demo data
 * In sandbox architecture, this is determined by whether user is in Demo Org
 */
export function useDatasetDemoMode(dataset: keyof DemoModeState['demoDatasets']): boolean {
  const { isDemoMode, demoDatasets } = useDemoMode();
  return isDemoMode && demoDatasets[dataset];
}

export default useDemoMode;
