/**
 * Keyboard Shortcuts Reference
 * Complete list of keyboard shortcuts
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface ShortcutGroup {
  title: string
  icon: string
  shortcuts: { keys: string[]; description: string; available?: boolean }[]
}

const shortcutGroups: ShortcutGroup[] = [
  {
    title: 'Navigation',
    icon: '🧭',
    shortcuts: [
      { keys: ['⌘', 'K'], description: 'Open quick search / command palette', available: true },
      { keys: ['⌘', '/'], description: 'Open help center', available: true },
      { keys: ['⌘', 'B'], description: 'Toggle sidebar', available: true },
      { keys: ['⌘', 'D'], description: 'Go to Dashboard', available: true },
      { keys: ['G', 'P'], description: 'Go to Programs', available: true },
      { keys: ['G', 'T'], description: 'Go to Trials', available: true },
      { keys: ['G', 'G'], description: 'Go to Germplasm', available: true },
      { keys: ['Esc'], description: 'Close modal / Go back', available: true },
    ]
  },
  {
    title: 'Actions',
    icon: '⚡',
    shortcuts: [
      { keys: ['⌘', 'N'], description: 'Create new item', available: true },
      { keys: ['⌘', 'S'], description: 'Save current form', available: true },
      { keys: ['⌘', 'E'], description: 'Edit selected item', available: true },
      { keys: ['⌘', 'Enter'], description: 'Submit form', available: true },
      { keys: ['Delete'], description: 'Delete selected item (with confirmation)', available: true },
      { keys: ['⌘', 'Z'], description: 'Undo last action', available: false },
      { keys: ['⌘', 'Shift', 'Z'], description: 'Redo last action', available: false },
    ]
  },
  {
    title: 'Lists & Tables',
    icon: '📋',
    shortcuts: [
      { keys: ['↑'], description: 'Move selection up', available: true },
      { keys: ['↓'], description: 'Move selection down', available: true },
      { keys: ['Enter'], description: 'Open selected item', available: true },
      { keys: ['Space'], description: 'Toggle selection', available: true },
      { keys: ['⌘', 'A'], description: 'Select all items', available: true },
      { keys: ['⌘', 'F'], description: 'Focus search/filter', available: true },
      { keys: ['Page Up'], description: 'Previous page', available: true },
      { keys: ['Page Down'], description: 'Next page', available: true },
    ]
  },
  {
    title: 'Data Collection',
    icon: '📝',
    shortcuts: [
      { keys: ['Tab'], description: 'Move to next field', available: true },
      { keys: ['Shift', 'Tab'], description: 'Move to previous field', available: true },
      { keys: ['⌘', 'Enter'], description: 'Save and continue', available: true },
      { keys: ['⌘', '.'], description: 'Mark as missing value', available: true },
      { keys: ['⌘', 'Shift', 'S'], description: 'Save and sync', available: true },
    ]
  },
  {
    title: 'AI Assistant',
    icon: '🤖',
    shortcuts: [
      { keys: ['⌘', 'J'], description: 'Open AI Assistant', available: true },
      { keys: ['Enter'], description: 'Send message', available: true },
      { keys: ['Shift', 'Enter'], description: 'New line in message', available: true },
      { keys: ['⌘', 'L'], description: 'Clear chat history', available: true },
    ]
  },
  {
    title: 'View & Display',
    icon: '👁️',
    shortcuts: [
      { keys: ['⌘', '+'], description: 'Zoom in', available: true },
      { keys: ['⌘', '-'], description: 'Zoom out', available: true },
      { keys: ['⌘', '0'], description: 'Reset zoom', available: true },
      { keys: ['F11'], description: 'Toggle fullscreen', available: true },
      { keys: ['⌘', 'Shift', 'T'], description: 'Toggle dark/light theme', available: false },
    ]
  },
]

export function KeyboardShortcuts() {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0

  // Replace ⌘ with Ctrl on non-Mac systems
  const formatKey = (key: string) => {
    if (key === '⌘' && !isMac) return 'Ctrl'
    return key
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Keyboard Shortcuts</h1>
          <p className="text-muted-foreground mt-1">Speed up your workflow with keyboard shortcuts</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-sm">
            {isMac ? '⌘ = Command' : '⌘ = Ctrl'}
          </Badge>
          <Link to="/help">
            <Button variant="outline">← Back to Help</Button>
          </Link>
        </div>
      </div>

      {/* Quick Reference */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">💡</span>
            <div>
              <p className="font-medium text-blue-800">Pro Tip</p>
              <p className="text-sm text-blue-700">
                Press <kbd className="px-1.5 py-0.5 bg-white border rounded text-xs font-mono mx-1">{formatKey('⌘')}</kbd>
                <kbd className="px-1.5 py-0.5 bg-white border rounded text-xs font-mono mx-1">K</kbd>
                anywhere to open the command palette and quickly navigate or perform actions.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Shortcut Groups */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {shortcutGroups.map(group => (
          <Card key={group.title}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span>{group.icon}</span>
                {group.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {group.shortcuts.map((shortcut, i) => (
                  <div 
                    key={i} 
                    className={`flex items-center justify-between p-2 rounded-lg ${
                      shortcut.available ? 'bg-muted' : 'bg-muted/50 opacity-60'
                    }`}
                  >
                    <span className={`text-sm ${!shortcut.available ? 'text-muted-foreground' : ''}`}>
                      {shortcut.description}
                      {!shortcut.available && (
                        <Badge variant="outline" className="ml-2 text-xs">Coming Soon</Badge>
                      )}
                    </span>
                    <div className="flex gap-1">
                      {shortcut.keys.map((key, j) => (
                        <kbd 
                          key={j} 
                          className="px-2 py-1 bg-white border rounded text-xs font-mono shadow-sm min-w-[24px] text-center"
                        >
                          {formatKey(key)}
                        </kbd>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Legend */}
      <Card>
        <CardHeader>
          <CardTitle>Key Legend</CardTitle>
          <CardDescription>Special keys and their symbols</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <kbd className="px-2 py-1 bg-muted border rounded text-xs font-mono">⌘</kbd>
              <span className="text-sm">{isMac ? 'Command' : 'Control'}</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-2 py-1 bg-muted border rounded text-xs font-mono">⇧</kbd>
              <span className="text-sm">Shift</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-2 py-1 bg-muted border rounded text-xs font-mono">⌥</kbd>
              <span className="text-sm">{isMac ? 'Option' : 'Alt'}</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-2 py-1 bg-muted border rounded text-xs font-mono">↵</kbd>
              <span className="text-sm">Enter/Return</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-2 py-1 bg-muted border rounded text-xs font-mono">⎋</kbd>
              <span className="text-sm">Escape</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-2 py-1 bg-muted border rounded text-xs font-mono">⇥</kbd>
              <span className="text-sm">Tab</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-2 py-1 bg-muted border rounded text-xs font-mono">↑↓</kbd>
              <span className="text-sm">Arrow Keys</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-2 py-1 bg-muted border rounded text-xs font-mono">␣</kbd>
              <span className="text-sm">Space</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Customization Note */}
      <Card className="border-yellow-200 bg-yellow-50">
        <CardContent className="pt-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-medium text-yellow-800">Note</p>
              <p className="text-sm text-yellow-700">
                Some shortcuts may conflict with browser or system shortcuts. 
                Shortcuts marked as "Coming Soon" are planned for future releases.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
