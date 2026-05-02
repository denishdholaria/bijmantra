/**
 * Theme Store
 *
 * Provides explicit light/dark theme selection with synchronous initialization,
 * persistence, and cross-tab synchronization.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================================================
// Types
// ============================================================================

export type ColorMode = 'light' | 'dark';

interface ThemeState {
  /** User's color mode preference */
  colorMode: ColorMode;
  
  /** Active resolved mode */
  resolvedMode: 'light' | 'dark';
  
  /** Actions */
  setColorMode: (mode: ColorMode) => void;
  toggleMode: () => void;
}

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY = 'bijmantra-theme';
const DEFAULT_MODE: ColorMode = 'light';

// ============================================================================
// Utility Functions
// ============================================================================

function getSystemMode(): 'light' | 'dark' {
  if (typeof window === 'undefined') return DEFAULT_MODE;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function resolveMode(mode: ColorMode): 'light' | 'dark' {
  return mode;
}

/**
 * Apply theme to document
 */
function applyTheme(mode: 'light' | 'dark', colorMode?: ColorMode) {
  const root = document.documentElement;
  
  if (mode === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }

  root.dataset.theme = mode === 'dark' ? 'dark' : 'prakruti';
  root.dataset.colorMode = colorMode ?? mode;
  root.style.colorScheme = mode;
  
  // Update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', mode === 'dark' ? '#181810' : '#fafaf8');
  }
}

/**
 * Read theme from localStorage synchronously
 */
function getStoredTheme(): ColorMode {
  if (typeof window === 'undefined') return DEFAULT_MODE;
  
  try {
    // New format
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      const mode = parsed.state?.colorMode;
      if (mode === 'light' || mode === 'dark') {
        return mode;
      }
      if (mode === 'system') {
        return getSystemMode();
      }
    }
    
    // Legacy format (workspace store)
    const legacy = localStorage.getItem('bijmantra-workspace');
    if (legacy) {
      const parsed = JSON.parse(legacy);
      const legacyTheme = parsed.state?.preferences?.theme;
      if (legacyTheme === 'aerospace') {
        return 'dark';
      }
    }
  } catch {
    // Ignore parse errors
  }
  
  return DEFAULT_MODE;
}

// ============================================================================
// Synchronous Theme Initialization (runs before React)
// ============================================================================

if (typeof window !== 'undefined') {
  const colorMode = getStoredTheme();
  applyTheme(colorMode, colorMode);
}

// ============================================================================
// Store
// ============================================================================

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => {
      const initial = getStoredTheme();
      
      return {
        colorMode: initial,
        resolvedMode: initial,
        
        setColorMode: (mode: ColorMode) => {
          applyTheme(mode, mode);
          set({ colorMode: mode, resolvedMode: mode });
        },
        
        toggleMode: () => {
          const current = get().resolvedMode;
          const newMode: ColorMode = current === 'dark' ? 'light' : 'dark';
          applyTheme(newMode, newMode);
          set({ colorMode: newMode, resolvedMode: newMode });
        },
      };
    },
    {
      name: STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ colorMode: state.colorMode }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          applyTheme(state.colorMode, state.colorMode);
        }
      },
    }
  )
);

// ============================================================================
// Cross-Tab Synchronization
// ============================================================================

if (typeof window !== 'undefined') {
  // Listen for storage changes from other tabs
  window.addEventListener('storage', (event) => {
    if (event.key === STORAGE_KEY && event.newValue) {
      try {
        const parsed = JSON.parse(event.newValue);
        const mode = parsed.state?.colorMode;
        if (mode === 'light' || mode === 'dark') {
          applyTheme(mode, mode);
          useThemeStore.setState({ colorMode: mode, resolvedMode: mode });
        } else if (mode === 'system') {
          const resolved = getSystemMode();
          applyTheme(resolved, resolved);
          useThemeStore.setState({ colorMode: resolved, resolvedMode: resolved });
        }
      } catch {
        // Ignore parse errors
      }
    }
  });
}

// ============================================================================
// Selectors & Hooks
// ============================================================================

export const selectColorMode = (state: ThemeState) => state.colorMode;
export const selectResolvedMode = (state: ThemeState) => state.resolvedMode;
export const selectIsDark = (state: ThemeState) => state.resolvedMode === 'dark';

/**
 * Hook to check if dark mode is active
 */
export function useIsDark(): boolean {
  return useThemeStore(selectIsDark);
}

export default useThemeStore;
