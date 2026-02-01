/**
 * Keyboard Shortcuts Help Modal
 * 
 * Shows available keyboard shortcuts to users.
 * Can be triggered with ? key or from help menu.
 */

import { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Keyboard } from 'lucide-react'

interface Shortcut {
  keys: string[]
  description: string
  category: string
}

const shortcuts: Shortcut[] = [
  // Navigation
  { keys: ['⌘', 'K'], description: 'Open command palette', category: 'Navigation' },
  { keys: ['⌘', '/'], description: 'Focus search', category: 'Navigation' },
  { keys: ['G', 'H'], description: 'Go to Home/Dashboard', category: 'Navigation' },
  { keys: ['G', 'P'], description: 'Go to Programs', category: 'Navigation' },
  { keys: ['G', 'T'], description: 'Go to Trials', category: 'Navigation' },
  { keys: ['G', 'G'], description: 'Go to Germplasm', category: 'Navigation' },
  { keys: ['G', 'S'], description: 'Go to Settings', category: 'Navigation' },
  
  // Actions
  { keys: ['N'], description: 'New item (context-aware)', category: 'Actions' },
  { keys: ['E'], description: 'Edit selected item', category: 'Actions' },
  { keys: ['D'], description: 'Delete selected item', category: 'Actions' },
  { keys: ['⌘', 'S'], description: 'Save current form', category: 'Actions' },
  { keys: ['Esc'], description: 'Close modal/cancel', category: 'Actions' },
  
  // View
  { keys: ['⌘', 'B'], description: 'Toggle sidebar', category: 'View' },
  { keys: ['⌘', '\\'], description: 'Toggle dark mode', category: 'View' },
  { keys: ['?'], description: 'Show keyboard shortcuts', category: 'View' },
  
  // Data
  { keys: ['⌘', 'E'], description: 'Export data', category: 'Data' },
  { keys: ['⌘', 'I'], description: 'Import data', category: 'Data' },
  { keys: ['R'], description: 'Refresh data', category: 'Data' },
]

// Group shortcuts by category
const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
  if (!acc[shortcut.category]) {
    acc[shortcut.category] = []
  }
  acc[shortcut.category].push(shortcut)
  return acc
}, {} as Record<string, Shortcut[]>)

interface KeyboardShortcutsProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function KeyboardShortcuts({ open, onOpenChange }: KeyboardShortcutsProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="w-5 h-5" />
            Keyboard Shortcuts
          </DialogTitle>
          <DialogDescription>
            Use these shortcuts to navigate and work faster
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          {Object.entries(groupedShortcuts).map(([category, categoryShortcuts]) => (
            <div key={category}>
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                {category}
              </h3>
              <div className="space-y-2">
                {categoryShortcuts.map((shortcut, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-1.5"
                  >
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {shortcut.description}
                    </span>
                    <div className="flex items-center gap-1">
                      {shortcut.keys.map((key, keyIndex) => (
                        <kbd
                          key={keyIndex}
                          className="px-2 py-1 text-xs font-mono bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded border border-gray-300 dark:border-gray-600"
                        >
                          {key}
                        </kbd>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Press <kbd className="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600">?</kbd> anytime to show this help
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// Hook to manage keyboard shortcuts modal
export function useKeyboardShortcuts() {
  const [showShortcuts, setShowShortcuts] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Show shortcuts on ? key (Shift + /)
      if (e.key === '?' && !e.metaKey && !e.ctrlKey && !e.altKey) {
        // Don't trigger if user is typing in an input
        const target = e.target as HTMLElement
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
          return
        }
        e.preventDefault()
        setShowShortcuts(true)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  return {
    showShortcuts,
    setShowShortcuts,
  }
}

export default KeyboardShortcuts
