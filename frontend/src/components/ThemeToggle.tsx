/**
 * Theme Toggle Component
 *
 * Explicit Light / Dark toggle.
 */

import { useThemeStore } from '@/store/themeStore';
import type { ColorMode } from '@/store/themeStore';
import { cn } from '@/lib/utils';
import { Sun, Moon } from 'lucide-react';

/**
 * Full theme toggle with Light/Dark options
 */
export function ThemeToggle() {
  const { colorMode, setColorMode } = useThemeStore();

  const modes: { value: ColorMode; label: string; icon: React.ReactNode }[] = [
    { value: 'light', label: 'Light', icon: <Sun className="h-4 w-4" /> },
    { value: 'dark', label: 'Dark', icon: <Moon className="h-4 w-4" /> },
  ];

  return (
    <div className="bg-shell-muted border-shell shadow-shell flex items-center gap-1 rounded-2xl border p-1.5">
      {modes.map((mode) => (
        <button
          key={mode.value}
          type="button"
          onClick={() => setColorMode(mode.value)}
          className={cn(
            'flex flex-1 items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-sm font-medium transition-all duration-200',
            colorMode === mode.value
              ? 'bg-shell-panel text-shell shadow-shell'
              : 'text-shell-muted hover:bg-shell-chrome hover:text-shell'
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
      type="button"
      onClick={toggleMode}
      className={cn(
        'bg-shell-muted border-shell text-shell-muted hover:text-shell hover:bg-[hsl(var(--accent))] rounded-lg border p-2 transition-all'
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
      type="button"
      onClick={toggleMode}
      className="text-shell-muted hover:text-shell p-1.5 transition-colors"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}

export default ThemeToggle;
