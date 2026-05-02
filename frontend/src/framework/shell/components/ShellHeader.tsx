import { PanelLeftClose, Search, X, Save, RefreshCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { EditorViewMode, WorkbenchDensity } from '../workbenchTypes'

interface ShellHeaderProps {
  isCompactDensity: boolean
  workspaceLabel: string
  workspaceDescription: string
  setExplorerCollapsed: (collapsed: boolean) => void
  canExitWithUnsavedChanges: (actionContext: string) => boolean
  onClose: () => void
  query: string
  setQuery: (query: string) => void
  workbenchDensity: WorkbenchDensity
  setWorkbenchDensity: (density: WorkbenchDensity) => void
  activeFile: any
  activeFileStatusLabel: string
  isDirty: boolean
  isSavingActiveFile: boolean
  handleSave: () => Promise<void>
  editorViewMode: EditorViewMode
  setEditorViewMode: (mode: EditorViewMode) => void
  availableEditorViewModes: EditorViewMode[]
  getEditorViewModeLabel: (mode: EditorViewMode) => string
}

export function ShellHeader({
  isCompactDensity,
  workspaceLabel,
  workspaceDescription,
  setExplorerCollapsed,
  canExitWithUnsavedChanges,
  onClose,
  query,
  setQuery,
  workbenchDensity,
  setWorkbenchDensity,
  activeFile,
  activeFileStatusLabel,
  isDirty,
  isSavingActiveFile,
  handleSave,
  editorViewMode,
  setEditorViewMode,
  availableEditorViewModes,
  getEditorViewModeLabel,
}: ShellHeaderProps) {
  return (
    <>
      <div className={cn('border-shell flex items-start justify-between gap-3 border-b', isCompactDensity ? 'px-3 py-3' : 'px-4 py-3.5')}>
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-[0.34em] text-slate-500">Explorer</p>
          <h2 className={cn('mt-1 truncate font-semibold text-white', isCompactDensity ? 'text-sm' : 'text-base')}>
            {workspaceLabel}
          </h2>
          <p className={cn('mt-1 text-slate-400', isCompactDensity ? 'text-[11px] leading-4' : 'text-xs')}>
            {workspaceDescription}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setExplorerCollapsed(true)}
            className="rounded-xl border border-white/12 bg-white/8 p-2 text-slate-100 transition hover:bg-white/14"
            aria-label="Collapse explorer sidebar"
          >
            <PanelLeftClose className={cn(isCompactDensity ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
          </button>
          <button
            type="button"
            onClick={() => {
              if (!canExitWithUnsavedChanges('Closing the desktop tool')) {
                return
              }
              onClose()
            }}
            className="rounded-xl border border-white/12 bg-white/8 p-2 text-slate-200 transition hover:bg-white/14"
            aria-label="Close desktop tool"
          >
            <X className={cn(isCompactDensity ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
          </button>
        </div>
      </div>

      <div className={cn('border-shell overflow-x-hidden border-b', isCompactDensity ? 'px-3 py-3' : 'px-4 py-4')}>
        <label
          className={cn(
            'flex min-w-0 items-center gap-2 rounded-xl border border-white/10 bg-white/6 text-slate-200',
            isCompactDensity ? 'px-2.5 py-2 text-[12px]' : 'px-3 py-2.5 text-sm'
          )}
        >
          <Search className={cn('shrink-0 text-slate-400', isCompactDensity ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Filter files and folders"
            className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-slate-500"
          />
        </label>

        <div className="mt-3 space-y-3">
          <div>
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-500">
              Density
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setWorkbenchDensity('compact')}
                className={cn(
                  'rounded-xl border px-3 py-2 text-[11px] font-medium transition',
                  workbenchDensity === 'compact'
                    ? 'border-white/15 bg-white/14 text-white'
                    : 'border-white/10 bg-white/5 text-slate-400 hover:text-slate-200'
                )}
                aria-label="Compact density"
                aria-pressed={workbenchDensity === 'compact' ? 'true' : 'false'}
              >
                Compact
              </button>
              <button
                type="button"
                onClick={() => setWorkbenchDensity('comfortable')}
                className={cn(
                  'rounded-xl border px-3 py-2 text-[11px] font-medium transition',
                  workbenchDensity === 'comfortable'
                    ? 'border-white/15 bg-white/14 text-white'
                    : 'border-white/10 bg-white/5 text-slate-400 hover:text-slate-200'
                )}
                aria-label="Comfortable density"
                aria-pressed={workbenchDensity === 'comfortable' ? 'true' : 'false'}
              >
                Comfortable
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
