import type { ShellModule } from './types'

type DesktopShortcutsProps = {
  shortcuts: ShellModule[]
  onRemoveShortcut: (id: string) => void
}

export function DesktopShortcuts({ shortcuts, onRemoveShortcut }: DesktopShortcutsProps) {
  if (shortcuts.length === 0) {
    return null
  }

  return (
    <div className="flex flex-col gap-4">
      {shortcuts.map((shortcut) => {
        const Icon = shortcut.icon
        return (
          <button
            key={shortcut.id}
            type="button"
            className="group flex w-28 flex-col items-center gap-2 rounded-2xl px-3 py-2 text-center text-xs text-slate-700 transition hover:bg-white/60 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400 dark:text-slate-200 dark:hover:bg-slate-900/60"
            aria-label={shortcut.title}
            onContextMenu={(event) => {
              event.preventDefault()
              onRemoveShortcut(shortcut.id)
            }}
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/80 text-emerald-700 shadow-sm dark:bg-slate-900/70 dark:text-emerald-200">
              <Icon className="h-5 w-5" />
            </span>
            <span className="line-clamp-2 text-[11px] font-medium">
              {shortcut.title}
            </span>
          </button>
        )
      })}
    </div>
  )
}
