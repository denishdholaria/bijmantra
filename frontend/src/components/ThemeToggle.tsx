/**
 * Theme Toggle Component
 * Switch between Light and Dark themes
 * Theme is persisted in localStorage and initialized in index.html
 */

import { useState, useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'

type Theme = 'light' | 'dark'

// Get initial theme from DOM (set by index.html script)
function getInitialTheme(): Theme {
  if (typeof window !== 'undefined') {
    // First check the DOM class (most reliable, set by index.html)
    if (document.documentElement.classList.contains('dark')) {
      return 'dark'
    }
    if (document.documentElement.classList.contains('light')) {
      return 'light'
    }
    // Fallback to localStorage
    const stored = localStorage.getItem('bijmantra-theme')
    if (stored === 'nasa') return 'dark'
    if (stored === 'light' || stored === 'dark') return stored
  }
  return 'light'
}

export function ThemeToggle() {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme)

  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme)
    
    // Update DOM
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(newTheme)
    
    // Persist to localStorage
    localStorage.setItem('bijmantra-theme', newTheme)
    
    // Dispatch custom event for other components
    window.dispatchEvent(new CustomEvent('theme-change', { detail: newTheme }))
  }, [])

  // Sync with DOM on mount (in case index.html script ran)
  useEffect(() => {
    const currentDOMTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light'
    if (currentDOMTheme !== theme) {
      setThemeState(currentDOMTheme)
    }
  }, [])

  const themes: { value: Theme; label: string; icon: string }[] = [
    { value: 'light', label: 'Light', icon: '☀️' },
    { value: 'dark', label: 'Dark', icon: '🌙' },
  ]

  return (
    <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
      {themes.map((t) => (
        <button
          key={t.value}
          onClick={() => setTheme(t.value)}
          className={cn(
            'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all',
            theme === t.value
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          )}
          title={t.label}
        >
          <span>{t.icon}</span>
          <span className="hidden sm:inline">{t.label}</span>
        </button>
      ))}
    </div>
  )
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme)

  useEffect(() => {
    // Listen for theme changes from ThemeToggle
    const handleThemeChange = (e: CustomEvent<Theme>) => {
      setTheme(e.detail)
    }
    
    // Listen for storage changes (cross-tab sync)
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'bijmantra-theme') {
        const newTheme = e.newValue
        if (newTheme === 'light' || newTheme === 'dark') {
          setTheme(newTheme)
        }
      }
    }
    
    // Watch for class changes on document (fallback)
    const checkTheme = () => {
      const isDark = document.documentElement.classList.contains('dark')
      setTheme(isDark ? 'dark' : 'light')
    }

    window.addEventListener('theme-change', handleThemeChange as EventListener)
    window.addEventListener('storage', handleStorage)
    
    const observer = new MutationObserver(checkTheme)
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    })

    return () => {
      window.removeEventListener('theme-change', handleThemeChange as EventListener)
      window.removeEventListener('storage', handleStorage)
      observer.disconnect()
    }
  }, [])

  return { theme, isDark: theme === 'dark' }
}
