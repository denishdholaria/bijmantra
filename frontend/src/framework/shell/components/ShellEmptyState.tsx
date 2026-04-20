import { FileText, HardDrive, LoaderCircle, NotebookPen } from 'lucide-react'

interface ShellEmptyStateProps {
  canUseDirectoryPicker: boolean
  isScanningLocalFolder: boolean
  connectLocalFolder: () => Promise<void>
  handleCreateReport: () => void
  handleCreateTable: () => void
}

export function ShellEmptyState({
  canUseDirectoryPicker,
  isScanningLocalFolder,
  connectLocalFolder,
  handleCreateReport,
  handleCreateTable,
}: ShellEmptyStateProps) {
  return (
    <div className="mx-auto flex h-full min-h-[24rem] w-full max-w-4xl flex-col justify-center gap-6">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-shell-muted">Research workspace</p>
        <h3 className="mt-2 text-2xl font-semibold text-shell">Keep files, notes, and analysis in one place.</h3>
        <p className="mt-2 max-w-2xl text-sm text-shell-muted">
          Attach a local folder for grounded file work, keep working notes inside desktop documents, and move into the editor only when you want to refine a result.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <button
          type="button"
          onClick={() => void connectLocalFolder()}
          disabled={!canUseDirectoryPicker || isScanningLocalFolder}
          aria-label="Attach research folder"
          className="flex items-start gap-3 rounded-2xl border border-slate-200/70 bg-white/80 px-4 py-4 text-left text-shell transition hover:border-emerald-300 hover:bg-white dark:border-slate-800 dark:bg-slate-950/60 dark:hover:border-emerald-700"
        >
          {isScanningLocalFolder ? <LoaderCircle className="mt-0.5 h-4 w-4 animate-spin text-emerald-600" /> : <HardDrive className="mt-0.5 h-4 w-4 text-emerald-600" />}
          <div>
            <div className="text-sm font-semibold">Connect Local Folder</div>
            <div className="mt-1 text-xs text-shell-muted">Work against a real research folder without leaving the app.</div>
          </div>
        </button>
        <button
          type="button"
          onClick={handleCreateReport}
          className="flex items-start gap-3 rounded-2xl border border-slate-200/70 bg-white/80 px-4 py-4 text-left text-shell transition hover:border-emerald-300 hover:bg-white dark:border-slate-800 dark:bg-slate-950/60 dark:hover:border-emerald-700"
        >
          <NotebookPen className="mt-0.5 h-4 w-4 text-emerald-600" />
          <div>
            <div className="text-sm font-semibold">New Report</div>
            <div className="mt-1 text-xs text-shell-muted">Start a narrative analysis document for AI-assisted editing.</div>
          </div>
        </button>
        <button
          type="button"
          onClick={handleCreateTable}
          className="flex items-start gap-3 rounded-2xl border border-slate-200/70 bg-white/80 px-4 py-4 text-left text-shell transition hover:border-emerald-300 hover:bg-white dark:border-slate-800 dark:bg-slate-950/60 dark:hover:border-emerald-700"
        >
          <FileText className="mt-0.5 h-4 w-4 text-emerald-600" />
          <div>
            <div className="text-sm font-semibold">New Table</div>
            <div className="mt-1 text-xs text-shell-muted">Draft a simple CSV-style worksheet that can later be exported.</div>
          </div>
        </button>
      </div>

      <div className="grid gap-3 text-sm text-shell-muted md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200/70 bg-white/70 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/40">
          Explorer stays dense and close to VS Code, so scanning large research folders is fast.
        </div>
        <div className="rounded-2xl border border-slate-200/70 bg-white/70 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/40">
          TipTap now handles reports in the primary writing view while Monaco stays available for raw inspection and machine-friendly files.
        </div>
        <div className="rounded-2xl border border-slate-200/70 bg-white/70 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/40">
          Local-first folders keep data sovereignty intact while the app stays task-specific for scientists.
        </div>
      </div>
    </div>
  )
}
