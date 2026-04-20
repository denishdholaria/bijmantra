import { FileText } from "lucide-react"
import { lazy, Suspense } from 'react'
import { FileCode2, HardDrive, LoaderCircle, NotebookPen, Save } from 'lucide-react'
import { cn } from '@/lib/utils'
import { EditorViewMode, WorkbenchDensity } from '../workbenchTypes'
import { getFileIcon, getEditorViewModeLabel, getEditorViewModeDescription, describeFile } from '../workbenchExplorer'
import { WorkbenchMarkdownPreview } from '@/components/workbench/WorkbenchMarkdownPreview'
import { WorkbenchProseEditor } from '@/components/workbench/WorkbenchProseEditor'
import { WorkbenchTableEditor } from '@/components/workbench/WorkbenchTableEditor'

const MonacoEditor = lazy(() => import('@monaco-editor/react'))

interface ShellEditorProps {
  isExplorerSurface: boolean
  isCompactDensity: boolean
  activeFile: any
  localBrowserRootName?: string
  onOpenSurface: (surface: 'editor' | 'filesystem') => void
  availableEditorViewModes: EditorViewMode[]
  editorViewMode: EditorViewMode
  setEditorViewMode: (mode: EditorViewMode) => void
  isDirty: boolean
  isSavingActiveFile: boolean
  handleSave: () => Promise<void>
  openFileIds: string[]
  fileMap: Map<string, any>
  drafts: Record<string, string>
  activeFileId: string | null
  openFile: (id: string) => Promise<void>
  closeTab: (id: string) => void
  activeSaveState: any
  activeFileStatusLabel: string
  totalWorkspaceFileCount: number
  previewContent: string
  editorValue: string
  theme: 'vs-dark' | 'vs-light'
  isProseView: boolean
  handleEditorValueChange: (value: string) => void
  isTableView: boolean
  activeTableData: any
  handleTableDataChange: (data: any) => void
  isEditorHostReady: boolean
  monacoEditorRef: React.MutableRefObject<any>
  scheduleEditorLayout: () => void
  editorHostRef: React.MutableRefObject<HTMLDivElement | null>
  connectLocalFolder: () => Promise<void>
  handleCreateReport: () => void
  handleCreateTable: () => void
  canUseDirectoryPicker: boolean
  isScanningLocalFolder: boolean
}

export function ShellEditor({
  isExplorerSurface,
  isCompactDensity,
  activeFile,
  localBrowserRootName,
  onOpenSurface,
  availableEditorViewModes,
  editorViewMode,
  setEditorViewMode,
  isDirty,
  isSavingActiveFile,
  handleSave,
  openFileIds,
  fileMap,
  drafts,
  activeFileId,
  openFile,
  closeTab,
  activeSaveState,
  activeFileStatusLabel,
  totalWorkspaceFileCount,
  previewContent,
  editorValue,
  theme,
  isProseView,
  handleEditorValueChange,
  isTableView,
  activeTableData,
  handleTableDataChange,
  isEditorHostReady,
  monacoEditorRef,
  scheduleEditorLayout,
  editorHostRef,
  connectLocalFolder,
  handleCreateReport,
  handleCreateTable,
  canUseDirectoryPicker,
  isScanningLocalFolder,
}: ShellEditorProps) {
  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[hsl(var(--card)/0.72)]">
      <div className={cn('border-shell flex flex-wrap items-center justify-between gap-3 border-b bg-[hsl(var(--app-shell-chrome)/0.66)]', isCompactDensity ? 'px-3 py-2.5' : 'px-4 py-3')}>
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-[0.28em] text-shell-muted">
            {isExplorerSurface ? 'Preview' : 'Editor'}
          </p>
          <div className="mt-1 flex items-center gap-2">
            <h2 className={cn('truncate font-semibold text-shell', isCompactDensity ? 'text-base' : 'text-lg')}>
              {activeFile?.name ?? (isExplorerSurface ? 'Workspace preview' : 'Workspace editor')}
            </h2>
            {activeFile && (
              <span className="rounded-full border border-slate-200/70 bg-white/70 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.18em] text-shell-muted dark:border-slate-800 dark:bg-slate-950/60">
                {activeFile.language}
              </span>
            )}
          </div>
          <p className="mt-1 truncate text-xs text-shell-muted">
            {activeFile?.path ?? (localBrowserRootName ? `Local workspace attached: ${localBrowserRootName}` : 'Start with a folder, a report, or a table.')}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {isExplorerSurface ? (
            <button
              type="button"
              onClick={() => onOpenSurface('editor')}
              disabled={!activeFile}
              className={cn(
                'inline-flex items-center gap-2 border border-emerald-300/60 bg-emerald-50 font-semibold text-emerald-700 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-emerald-700/60 dark:bg-emerald-900/25 dark:text-emerald-200 dark:hover:bg-emerald-900/40',
                isCompactDensity ? 'rounded-xl px-2.5 py-1.5 text-[11px]' : 'rounded-xl px-3 py-2 text-xs'
              )}
            >
              <FileCode2 className="h-3.5 w-3.5" />
              Open Editor
            </button>
          ) : (
            <button
              type="button"
              onClick={() => onOpenSurface('filesystem')}
              className={cn(
                'inline-flex items-center gap-2 border border-slate-200/70 font-medium text-shell transition hover:border-emerald-300 hover:text-emerald-700 dark:border-slate-700 dark:hover:border-emerald-600 dark:hover:text-emerald-200',
                isCompactDensity ? 'rounded-xl px-2.5 py-1.5 text-[11px]' : 'rounded-xl px-3 py-2 text-xs'
              )}
            >
              <HardDrive className="h-3.5 w-3.5" />
              File System
            </button>
          )}

          {!isExplorerSurface && activeFile && availableEditorViewModes.length > 1 && (
            <div className={cn('inline-flex items-center border border-slate-200/70 bg-white/80 p-1 text-xs dark:border-slate-700 dark:bg-slate-950/60', isCompactDensity ? 'rounded-xl' : 'rounded-xl')}>
              {availableEditorViewModes.map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setEditorViewMode(mode)}
                  className={cn(
                    isCompactDensity ? 'rounded-lg px-2.5 py-1 text-[11px] font-medium transition' : 'rounded-lg px-3 py-1.5 font-medium transition',
                    editorViewMode === mode ? 'bg-emerald-500 text-white shadow-sm' : 'text-shell-muted hover:text-shell'
                  )}
                >
                  {getEditorViewModeLabel(mode)}
                </button>
              ))}
            </div>
          )}

          {!isExplorerSurface && (
            <button
              type="button"
              onClick={() => void handleSave()}
              disabled={!activeFile?.editable || !isDirty || isSavingActiveFile}
              className={cn(
                'inline-flex items-center gap-2 border border-emerald-300/60 bg-emerald-50 font-semibold text-emerald-700 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-emerald-700/60 dark:bg-emerald-900/25 dark:text-emerald-200 dark:hover:bg-emerald-900/40',
                isCompactDensity ? 'rounded-xl px-2.5 py-1.5 text-[11px]' : 'rounded-xl px-3 py-2 text-xs'
              )}
            >
              <Save className="h-3.5 w-3.5" />
              {isSavingActiveFile ? 'Saving...' : 'Save'}
            </button>
          )}
        </div>
      </div>

      {!isExplorerSurface && openFileIds.length > 0 && (
        <div className={cn('border-shell flex gap-1 overflow-x-auto border-b bg-[hsl(var(--app-shell-panel)/0.72)]', isCompactDensity ? 'px-2 py-1.5' : 'px-3 py-2')}>
          {openFileIds.map((fileId) => {
            const file = fileMap.get(fileId)
            if (!file) {
              return null
            }

            const Icon = getFileIcon(file.path)
            const tabDirty = drafts[file.id] !== undefined && drafts[file.id] !== file.content

            return (
              <div
                key={file.id}
                className={cn(
                  'flex items-center gap-2 border transition',
                  isCompactDensity ? 'rounded-lg px-2 py-1 text-[12px]' : 'rounded-xl px-3 py-1.5 text-sm',
                  activeFileId === file.id
                    ? 'border-emerald-300/70 bg-emerald-50 text-emerald-900 dark:border-emerald-700/60 dark:bg-emerald-900/30 dark:text-emerald-100'
                    : 'border-transparent bg-shell-muted/40 text-shell-muted hover:border-slate-200/70 hover:text-shell dark:hover:border-slate-700'
                )}
              >
                <button type="button" onClick={() => void openFile(file.id)} className="inline-flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  <span className="max-w-[14rem] truncate">{file.name}</span>
                  {tabDirty && <span className="h-2 w-2 rounded-full bg-amber-500" aria-hidden="true" />}
                </button>
                <button
                  type="button"
                  onClick={() => closeTab(file.id)}
                  className="rounded-full px-1 text-shell-muted transition hover:bg-black/5 hover:text-shell dark:hover:bg-white/10"
                  aria-label={`Close ${file.name}`}
                >
                  ×
                </button>
              </div>
            )
          })}
        </div>
      )}

      {!isExplorerSurface && (
        <div className="border-shell flex flex-wrap items-center gap-2 border-b px-3 py-2 text-[11px] text-shell-muted">
          <span className="rounded-full border border-slate-200/70 bg-white/70 px-2.5 py-1 text-shell dark:border-slate-800 dark:bg-slate-950/60">
            {describeFile(activeFile)}
          </span>
          {activeFile && (
            <span className="rounded-full border border-slate-200/70 bg-white/70 px-2.5 py-1 dark:border-slate-800 dark:bg-slate-950/60">
              {activeFile.editable ? 'Writable' : 'Read only'}
            </span>
          )}
          {activeFile && (
            <span className="rounded-full border border-slate-200/70 bg-white/70 px-2.5 py-1 dark:border-slate-800 dark:bg-slate-950/60">
              {getEditorViewModeDescription(editorViewMode)}
            </span>
          )}
          <span
            className={cn(
              'rounded-full border px-2.5 py-1',
              activeSaveState.status === 'error'
                ? 'border-rose-300/70 bg-rose-50 text-rose-600 dark:border-rose-700/60 dark:bg-rose-950/30 dark:text-rose-300'
                : isDirty
                  ? 'border-amber-300/70 bg-amber-50 text-amber-700 dark:border-amber-700/60 dark:bg-amber-950/30 dark:text-amber-200'
                  : 'border-slate-200/70 bg-white/70 text-shell dark:border-slate-800 dark:bg-slate-950/60'
            )}
          >
            {activeFileStatusLabel}
          </span>
          <span className="ml-auto truncate text-shell-muted">
            {localBrowserRootName ? `Workspace: ${localBrowserRootName}` : 'Workspace: desktop docs only'}
          </span>
        </div>
      )}

      {isExplorerSurface ? (
        <div className="flex min-h-0 flex-1 flex-col bg-[hsl(var(--background)/0.65)]">
          <div className="border-shell flex items-center justify-between gap-3 border-b px-3 py-2 text-xs text-shell-muted">
            <span className="uppercase tracking-[0.26em]">{activeFile ? (activeFile.source === 'local' ? 'Live file preview' : 'Document preview') : 'Workspace preview'}</span>
            <span>{activeFile?.updatedAt ? `Updated ${new Date(activeFile.updatedAt).toLocaleString()}` : `${totalWorkspaceFileCount} files visible in workspace`}</span>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-5">
            {activeFile ? (
              <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-[20px] border border-slate-200/70 bg-slate-950 shadow-sm dark:border-slate-800">
                <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3 text-xs uppercase tracking-[0.24em] text-slate-400">
                  <span>{activeFile.name}</span>
                  <span>{activeFile.language}</span>
                </div>
                {activeFile.documentType === 'prose' ? (
                  <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
                    <WorkbenchMarkdownPreview value={previewContent || 'Empty file'} />
                  </div>
                ) : (
                  <pre className="min-h-full flex-1 overflow-auto whitespace-pre-wrap break-words px-4 py-4 text-[13px] leading-6 text-slate-200">
                    {previewContent.slice(0, 12000) || 'Empty file'}
                  </pre>
                )}
              </div>
            ) : (
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
            )}
          </div>
        </div>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col bg-[hsl(var(--background)/0.65)]">
          <div className="min-h-0 flex-1 border-b border-shell xl:border-b-0">
            {activeFile ? (
              <div ref={editorHostRef} className="h-full min-h-[24rem] w-full">
                {isProseView ? (
                  <div className="h-full min-h-[24rem] overflow-y-auto">
                    <WorkbenchProseEditor
                      value={editorValue}
                      onChange={handleEditorValueChange}
                      readOnly={!activeFile.editable}
                    />
                  </div>
                ) : isTableView ? (
                  <div className="h-full min-h-[24rem] overflow-y-auto">
                    <WorkbenchTableEditor
                      value={editorValue}
                      onChange={handleEditorValueChange}
                      tableData={activeTableData ?? undefined}
                      onTableDataChange={handleTableDataChange}
                      filePath={activeFile.path}
                      readOnly={!activeFile.editable}
                    />
                  </div>
                ) : isEditorHostReady ? (
                  <Suspense
                    fallback={
                      <div className="flex h-full min-h-[24rem] items-center justify-center gap-3 text-shell-muted">
                        <LoaderCircle className="h-5 w-5 animate-spin" />
                        Loading editor...
                      </div>
                    }
                  >
                    <MonacoEditor
                      data-testid="desktop-monaco-editor"
                      data-automatic-layout="false"
                      height="100%"
                      language={activeFile.language}
                      theme={theme}
                      value={editorValue}
                      onMount={(editor) => {
                        monacoEditorRef.current = editor
                        scheduleEditorLayout()
                      }}
                      onChange={(value) => handleEditorValueChange(value ?? '')}
                      options={{
                        fontSize: isCompactDensity ? 12 : 13,
                        fontFamily: 'JetBrains Mono, Fira Code, SF Mono, Monaco, monospace',
                        minimap: { enabled: true },
                        smoothScrolling: true,
                        wordWrap: 'on',
                        readOnly: !activeFile.editable,
                        automaticLayout: false,
                        padding: { top: isCompactDensity ? 12 : 16, bottom: isCompactDensity ? 12 : 16 },
                        scrollBeyondLastLine: false,
                      }}
                    />
                  </Suspense>
                ) : (
                  <div className="flex h-full min-h-[24rem] items-center justify-center gap-3 text-shell-muted">
                    <LoaderCircle className="h-5 w-5 animate-spin" />
                    Preparing editor...
                  </div>
                )}
              </div>
            ) : (
              <div className="flex h-full min-h-[24rem] flex-col items-center justify-center gap-4 text-shell-muted">
                <NotebookPen className="h-10 w-10 opacity-70" />
                <div className="text-center">
                  <p className="text-base font-medium text-shell">No file selected</p>
                  <p className="mt-1 text-sm">Select a file from the explorer to begin editing</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
