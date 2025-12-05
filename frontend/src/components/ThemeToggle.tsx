/**
 * Theme Toggle Component
 * Switch between Light and Dark themes
 */

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'

type Theme = 'light' | 'dark'

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('bijmantra-theme')
      // Handle legacy 'nasa' theme by converting to 'dark'
      if (stored === 'nasa') return 'dark'
      if (stored === 'light' || stored === 'dark') return stored
      return 'light'
    }
    return 'light'
  })

  useEffect(() => {
    const root = document.documentElement
    
    // Remove all theme classes
    root.classList.remove('light', 'dark')
    
    // Apply new theme
    root.classList.add(theme)
    
    localStorage.setItem('bijmantra-theme', theme)
  }, [theme])

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
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('bijmantra-theme')
      if (stored === 'nasa') return 'dark'
      if (stored === 'light' || stored === 'dark') return stored
      return 'light'
    }
    return 'light'
  })

  useEffect(() => {
    const handleStorage = () => {
      const stored = localStorage.getItem('bijmantra-theme')
      if (stored === 'nasa') {
        setTheme('dark')
      } else if (stored === 'light' || stored === 'dark') {
        setTheme(stored)
      }
    }
    
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  return { theme, isDark: theme === 'dark' }
}
