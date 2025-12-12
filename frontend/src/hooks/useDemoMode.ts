/**
 * Demo Mode Hook
 * 
 * Allows users to toggle between production data and demo data.
 * Demo mode is useful for:
 * - Learning the application
 * - Training new users
 * - Showcasing features without real data
 * - Development and testing
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface DemoModeState {
  isDemoMode: boolean;
  showDemoBanner: boolean;
  demoDatasets: {
    germplasm: boolean;
    trials: boolean;
    observations: boolean;
    seedBank: boolean;
    sensors: boolean;
    vision: boolean;
  };
  toggleDemoMode: () => void;
  setDemoMode: (enabled: boolean) => void;
  toggleDemoBanner: () => void;
  setDatasetDemo: (dataset: keyof DemoModeState['demoDatasets'], enabled: boolean) => void;
}

export const useDemoMode = create<DemoModeState>()(
  persist(
    (set) => ({
      isDemoMode: true, // Default to demo mode for new users
      showDemoBanner: true,
      demoDatasets: {
        germplasm: true,
        trials: true,
        observations: true,
        seedBank: true,
        sensors: true,
        vision: true,
      },
      toggleDemoMode: () => set((state) => ({ isDemoMode: !state.isDemoMode })),
      setDemoMode: (enabled) => set({ isDemoMode: enabled }),
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

export default useDemoMode;
