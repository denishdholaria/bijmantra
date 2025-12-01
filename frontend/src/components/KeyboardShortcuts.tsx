/**
 * Keyboard Shortcuts Component
 * Global keyboard navigation
 */

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export function useKeyboardShortcuts() {
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only trigger if not in an input field
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return
      }

      // Cmd/Ctrl + K for search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        navigate('/search')
        return
      }

      // G + key shortcuts (press g then another key)
      if (e.key === 'g') {
        const handleSecondKey = (e2: KeyboardEvent) => {
          switch (e2.key) {
            case 'd':
              navigate('/dashboard')
              break
            case 'p':
              navigate('/programs')
              break
            case 'g':
              navigate('/germplasm')
              break
            case 't':
              navigate('/traits')
              break
            case 's':
              navigate('/studies')
              break
            case 'l':
              navigate('/locations')
              break
            case 'h':
              navigate('/help')
              break
          }
          document.removeEventListener('keydown', handleSecondKey)
        }
        document.addEventListener('keydown', handleSecondKey, { once: true })
        setTimeout(() => {
          document.removeEventListener('keydown', handleSecondKey)
        }, 1000)
      }

      // ? for help
      if (e.key === '?' && !e.shiftKey) {
        navigate('/help')
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [navigate])
}

export function KeyboardShortcutsHelp() {
  const shortcuts = [
    { keys: ['⌘', 'K'], description: 'Open search' },
    { keys: ['G', 'D'], description: 'Go to Dashboard' },
    { keys: ['G', 'P'], description: 'Go to Programs' },
    { keys: ['G', 'G'], description: 'Go to Germplasm' },
    { keys: ['G', 'T'], description: 'Go to Traits' },
    { keys: ['G', 'S'], description: 'Go to Studies' },
    { keys: ['G', 'L'], description: 'Go to Locations' },
    { keys: ['G', 'H'], description: 'Go to Help' },
    { keys: ['?'], description: 'Show help' },
  ]

  return (
    <div className="space-y-2">
      {shortcuts.map((shortcut, i) => (
        <div key={i} className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">{shortcut.description}</span>
          <div className="flex gap-1">
            {shortcut.keys.map((key, j) => (
              <kbd
                key={j}
                className="px-2 py-1 bg-muted rounded text-xs font-mono"
              >
                {key}
              </kbd>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
