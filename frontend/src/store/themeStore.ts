/**
 * Theme Store — Simplified Light/Dark/System
 * 
 * Industry-standard theme management with:
 * - Synchronous initialization (no flash)
 * - System preference detection
 * - Cross-tab synchronization
 * - localStorage persistence
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================================================
// Types
// ============================================================================

/**
 * Available color modes
 * - light: Force light mode
 * - dark: Force dark mode  
 * - system: Follow OS preference
 */
export type ColorMode = 'light' | 'dark' | 'system';

interface ThemeState {
  /** User's color mode preference */
  colorMode: ColorMode;
  
  /** Resolved mode (accounts for 'system' preference) */
  resolvedMode: 'light' | 'dark';
  
  /** Actions */
  setColorMode: (mode: ColorMode) => void;
  toggleMode: () => void;
}

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY = 'bijmantra-theme';
const DEFAULT_MODE: ColorMode = 'system';

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get system color mode preference
 */
function getSystemMode(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/**
 * Resolve color mode (handle 'system' preference)
 */
function resolveMode(mode: ColorMode): 'light' | 'dark' {
  if (mode === 'system') {
    return getSystemMode();
  }
  return mode;
}

/**
 * Apply theme to document
 */
function applyTheme(mode: 'light' | 'dark') {
  const root = document.documentElement;
  
  if (mode === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
  
  // Update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', mode === 'dark' ? '#0f172a' : '#ffffff');
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
      if (mode === 'light' || mode === 'dark' || mode === 'system') {
        return mode;
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
  const resolved = resolveMode(colorMode);
  applyTheme(resolved);
}

// ============================================================================
// Store
// ============================================================================

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => {
      const initial = getStoredTheme();
      const initialResolved = resolveMode(initial);
      
      return {
        colorMode: initial,
        resolvedMode: initialResolved,
        
        setColorMode: (mode: ColorMode) => {
          const resolved = resolveMode(mode);
          applyTheme(resolved);
          set({ colorMode: mode, resolvedMode: resolved });
        },
        
        toggleMode: () => {
          const current = get().resolvedMode;
          const newMode: ColorMode = current === 'dark' ? 'light' : 'dark';
          applyTheme(newMode);
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
          const resolved = resolveMode(state.colorMode);
          applyTheme(resolved);
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
        if (mode) {
          const resolved = resolveMode(mode);
          applyTheme(resolved);
          useThemeStore.setState({ colorMode: mode, resolvedMode: resolved });
        }
      } catch {
        // Ignore parse errors
      }
    }
  });
  
  // Listen for system color scheme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const state = useThemeStore.getState();
    if (state.colorMode === 'system') {
      const resolved = getSystemMode();
      applyTheme(resolved);
      useThemeStore.setState({ resolvedMode: resolved });
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
