import { create } from 'zustand';

export type ViewMode = 'sanctuary' | 'focus' | 'search';

interface OSState {
  mode: ViewMode;
  activeAppId: string | null;
  previousAppId: string | null; // For history navigation

  // Actions
  goHome: () => void;
  openApp: (appId: string) => void;
  toggleSearch: (open?: boolean) => void;
}

export const useOSStore = create<OSState>((set, get) => ({
  mode: 'sanctuary',
  activeAppId: null,
  previousAppId: null,

  goHome: () => set({ mode: 'sanctuary', activeAppId: null }),

  openApp: (appId) => {
    const { activeAppId } = get();
    if (activeAppId === appId) return; // Already open

    set({
      mode: 'focus',
      activeAppId: appId,
      previousAppId: activeAppId
    });
  },

  toggleSearch: (open) => set((state) => {
    const nextState = open ?? (state.mode !== 'search');
    // If closing search, go back to previous mode (sanctuary or focus)
    if (!nextState) {
        return { mode: state.activeAppId ? 'focus' : 'sanctuary' };
    }
    return { mode: 'search' };
  }),
}));
