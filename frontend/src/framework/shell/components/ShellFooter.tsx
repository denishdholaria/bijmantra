import { WorkbenchFile, LocalBrowserState } from '../workbenchTypes'

interface ShellFooterProps {
  activeFile: WorkbenchFile | null
  footerStatusLabel: string
  runtimeSnapshot: { online: boolean }
  localBrowser: LocalBrowserState
  documentsCount: number
}

export function ShellFooter({
  activeFile,
  footerStatusLabel,
  runtimeSnapshot,
  localBrowser,
  documentsCount,
}: ShellFooterProps) {
  return (
    <div className="flex h-7 items-center justify-between border-t border-shell px-3 text-[11px] font-medium text-shell-muted">
      <div className="flex items-center gap-3">
        <span className="truncate">{activeFile?.path ?? '/desktop'}</span>
        <span>{activeFile?.source ?? 'workspace'}</span>
        {activeFile && <span>{activeFile.language}</span>}
      </div>
      <div className="flex items-center gap-3">
        <span>{footerStatusLabel}</span>
        <span>{runtimeSnapshot.online ? 'Online' : 'Offline'}</span>
        <span>{localBrowser.loadedFileCount} local files loaded</span>
        <span>{documentsCount} desktop docs</span>
      </div>
    </div>
  )
}
