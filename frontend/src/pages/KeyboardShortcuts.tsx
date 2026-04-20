/**
 * Keyboard Shortcuts Reference
 * Complete list of keyboard shortcuts
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  APP_SHORTCUTS,
  formatShortcutKeyForPlatform,
  groupShortcutsByCategory,
  SHORTCUT_CATEGORY_ORDER,
} from '@/lib/keyboardShortcuts'

interface ShortcutGroup {
  title: string
  icon: string
  shortcuts: { keys: string[]; description: string }[]
}

const shortcutGroupIcons: Record<string, string> = {
  Navigation: '🧭',
  Actions: '⚡',
  'Desktop Workbench': '🗂️',
}

export function KeyboardShortcuts() {
  // Use userAgent for detection (platform is deprecated)
  const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.userAgent)
  const groupedShortcuts = groupShortcutsByCategory(APP_SHORTCUTS)
  const shortcutGroups: ShortcutGroup[] = SHORTCUT_CATEGORY_ORDER.map((category) => ({
    title: category,
    icon: shortcutGroupIcons[category],
    shortcuts: groupedShortcuts[category] ?? [],
  })).filter((group) => group.shortcuts.length > 0)

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
      <Card className="border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/30">
        <CardContent className="pt-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">💡</span>
            <div>
              <p className="font-medium text-blue-800 dark:text-blue-200">Pro Tip</p>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Press <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 border dark:border-slate-600 rounded text-xs font-mono mx-1">{formatShortcutKeyForPlatform('⌘', isMac)}</kbd>
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 border dark:border-slate-600 rounded text-xs font-mono mx-1">K</kbd>
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
                    className="flex items-center justify-between p-2 rounded-lg bg-muted"
                  >
                    <span className="text-sm">
                      {shortcut.description}
                    </span>
                    <div className="flex gap-1">
                      {shortcut.keys.map((key, j) => (
                        <kbd 
                          key={j} 
                          className="px-2 py-1 bg-white dark:bg-slate-700 border dark:border-slate-600 rounded text-xs font-mono shadow-sm min-w-[24px] text-center"
                        >
                          {formatShortcutKeyForPlatform(key, isMac)}
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
      <Card className="border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/30">
        <CardContent className="pt-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-medium text-yellow-800 dark:text-yellow-200">Note</p>
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                These are the shortcuts currently wired into the active UI. Some browser or OS-level shortcuts may still take precedence.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
