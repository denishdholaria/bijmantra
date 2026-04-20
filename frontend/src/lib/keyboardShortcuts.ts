export type AppShortcut = {
  id: string
  keys: string[]
  description: string
  category: 'Navigation' | 'Actions' | 'Desktop Workbench'
}

export const APP_SHORTCUTS: AppShortcut[] = [
  {
    id: 'command-palette',
    keys: ['⌘', 'K'],
    description: 'Open command palette',
    category: 'Navigation',
  },
  {
    id: 'keyboard-shortcuts',
    keys: ['?'],
    description: 'Open keyboard shortcuts',
    category: 'Navigation',
  },
  {
    id: 'reevu-toggle',
    keys: ['⌘', '/'],
    description: 'Toggle REEVU',
    category: 'Navigation',
  },
  {
    id: 'sidebar-toggle',
    keys: ['[', ']'],
    description: 'Toggle main sidebar',
    category: 'Navigation',
  },
  {
    id: 'close-dialog',
    keys: ['Esc'],
    description: 'Close dialog or modal',
    category: 'Navigation',
  },
  {
    id: 'save-current-work',
    keys: ['⌘', 'S'],
    description: 'Save current work',
    category: 'Actions',
  },
  {
    id: 'explorer-focus-previous',
    keys: ['↑'],
    description: 'Move explorer focus to previous item',
    category: 'Desktop Workbench',
  },
  {
    id: 'explorer-focus-next',
    keys: ['↓'],
    description: 'Move explorer focus to next item',
    category: 'Desktop Workbench',
  },
  {
    id: 'explorer-expand',
    keys: ['→'],
    description: 'Expand folder or move into children',
    category: 'Desktop Workbench',
  },
  {
    id: 'explorer-collapse',
    keys: ['←'],
    description: 'Collapse folder or move to parent',
    category: 'Desktop Workbench',
  },
  {
    id: 'explorer-open',
    keys: ['Enter'],
    description: 'Open selected file',
    category: 'Desktop Workbench',
  },
  {
    id: 'explorer-toggle',
    keys: ['Space'],
    description: 'Expand or collapse selected folder',
    category: 'Desktop Workbench',
  },
]

export const SHORTCUT_CATEGORY_ORDER: AppShortcut['category'][] = [
  'Navigation',
  'Actions',
  'Desktop Workbench',
]

export const SHORTCUT_HIGHLIGHTS = [
  'command-palette',
  'keyboard-shortcuts',
  'reevu-toggle',
  'save-current-work',
  'close-dialog',
] as const

export function groupShortcutsByCategory(shortcuts: AppShortcut[] = APP_SHORTCUTS) {
  return shortcuts.reduce<Record<string, AppShortcut[]>>((groups, shortcut) => {
    if (!groups[shortcut.category]) {
      groups[shortcut.category] = []
    }

    groups[shortcut.category].push(shortcut)
    return groups
  }, {})
}

export function getShortcutHighlights() {
  return SHORTCUT_HIGHLIGHTS.map((shortcutId) => APP_SHORTCUTS.find((shortcut) => shortcut.id === shortcutId)).filter(
    (shortcut): shortcut is AppShortcut => shortcut !== undefined
  )
}

export function formatShortcutKeyForPlatform(key: string, isMac: boolean) {
  if (key === '⌘' && !isMac) {
    return 'Ctrl'
  }

  return key
}

export function isEditableShortcutTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false
  }

  return target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
}

export function isKeyboardShortcutHelpEvent(event: Pick<KeyboardEvent, 'key' | 'metaKey' | 'ctrlKey' | 'altKey'>) {
  return event.key === '?' && !event.metaKey && !event.ctrlKey && !event.altKey
}