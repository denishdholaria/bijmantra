/**
 * useTheme Hook
 * 
 * Simple hook for accessing theme state.
 * 
 * USAGE:
 *   const { isDark, colorMode, setColorMode, toggleMode } = useTheme();
 */

import { useThemeStore } from '@/store/themeStore';
import type { ColorMode } from '@/store/themeStore';

export interface UseThemeReturn {
  /** Whether dark mode is currently active */
  isDark: boolean;
  
  /** Whether light mode is currently active */
  isLight: boolean;
  
  /** Current color mode setting (light/dark/system) */
  colorMode: ColorMode;
  
  /** Resolved mode (light/dark - accounts for system preference) */
  resolvedMode: 'light' | 'dark';
  
  /** Set color mode */
  setColorMode: (mode: ColorMode) => void;
  
  /** Toggle between light and dark */
  toggleMode: () => void;
}

/**
 * Hook to access and control theme settings
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { isDark, toggleMode } = useTheme();
 *   
 *   return (
 *     <button onClick={toggleMode}>
 *       {isDark ? '☀️ Light' : '🌙 Dark'}
 *     </button>
 *   );
 * }
 * ```
 */
export function useTheme(): UseThemeReturn {
  const { colorMode, resolvedMode, setColorMode, toggleMode } = useThemeStore();
  
  return {
    isDark: resolvedMode === 'dark',
    isLight: resolvedMode === 'light',
    colorMode,
    resolvedMode,
    setColorMode,
    toggleMode,
  };
}

export default useTheme;
