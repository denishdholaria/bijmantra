/**
 * Theme Toggle Component
 * Switch between Design Systems (Aerospace vs Prakruti)
 * Managed by WorkspaceStore
 */

import { useWorkspaceStore } from '@/store/workspaceStore'
import { cn } from '@/lib/utils'

export function ThemeToggle() {
  const { preferences, setTheme } = useWorkspaceStore()
  const currentTheme = preferences.theme || 'aerospace'

  const themes = [
    { value: 'prakruti', label: 'Classic', icon: '🌿' },
    { value: 'aerospace', label: 'Aerospace', icon: '🚀' },
  ] as const

  return (
    <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
      {themes.map((t) => (
        <button
          key={t.value}
          onClick={() => setTheme(t.value)}
          className={cn(
            'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all',
            currentTheme === t.value
              ? 'bg-white dark:bg-slate-700 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          )}
          title={t.label}
          aria-label={`Switch to ${t.label} theme${currentTheme === t.value ? ' (Active)' : ''}`}
          aria-pressed={currentTheme === t.value}
        >
          <span aria-hidden="true">{t.icon}</span>
          <span className="hidden sm:inline">{t.label}</span>
        </button>
      ))}
    </div>
  )
}
