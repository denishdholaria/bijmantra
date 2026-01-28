/**
 * Theme Toggle Component
 * 
 * Simple Light / Dark / System toggle.
 * Industry-standard theme switching.
 */

import { useThemeStore } from '@/store/themeStore';
import type { ColorMode } from '@/store/themeStore';
import { cn } from '@/lib/utils';
import { Sun, Moon, Monitor } from 'lucide-react';

/**
 * Full theme toggle with Light/Dark/System options
 */
export function ThemeToggle() {
  const { colorMode, setColorMode } = useThemeStore();

  const modes: { value: ColorMode; label: string; icon: React.ReactNode }[] = [
    { value: 'light', label: 'Light', icon: <Sun className="h-4 w-4" /> },
    { value: 'dark', label: 'Dark', icon: <Moon className="h-4 w-4" /> },
    { value: 'system', label: 'System', icon: <Monitor className="h-4 w-4" /> },
  ];

  return (
    <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
      {modes.map((mode) => (
        <button
          key={mode.value}
          onClick={() => setColorMode(mode.value)}
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all',
            colorMode === mode.value
              ? 'bg-white dark:bg-slate-700 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          )}
          aria-label={`Switch to ${mode.label} mode${colorMode === mode.value ? ' (Active)' : ''}`}
          aria-pressed={colorMode === mode.value}
        >
          {mode.icon}
          <span>{mode.label}</span>
        </button>
      ))}
    </div>
  );
}

/**
 * Compact theme toggle - icon only
 * For use in headers or tight spaces
 */
export function ThemeToggleCompact() {
  const { resolvedMode, toggleMode } = useThemeStore();
  const isDark = resolvedMode === 'dark';

  return (
    <button
      onClick={toggleMode}
      className={cn(
        'p-2 rounded-lg transition-all',
        'bg-gray-100 dark:bg-gray-800',
        'text-gray-600 dark:text-gray-400',
        'hover:bg-gray-200 dark:hover:bg-gray-700',
        'hover:text-gray-900 dark:hover:text-white'
      )}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}

/**
 * Minimal toggle - just sun/moon icon with no background
 * For inline use
 */
export function ThemeToggleMinimal() {
  const { resolvedMode, toggleMode } = useThemeStore();
  const isDark = resolvedMode === 'dark';

  return (
    <button
      onClick={toggleMode}
      className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}

export default ThemeToggle;
