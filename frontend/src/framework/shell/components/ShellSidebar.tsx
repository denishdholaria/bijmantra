import React from 'react'
import { Folder, FolderOpen, LoaderCircle, ChevronDown, ChevronRight, HardDrive } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ExplorerNode, ExplorerVisibleNode } from '../workbenchTypes'
import { getFileIcon } from '../workbenchExplorer'

export interface ShellSidebarProps {
  tree: ExplorerNode[]
  visibleTreeNodes: ExplorerVisibleNode[]
  visibleTreeNodeIndexById: Map<string, number>
  focusedNodeId: string | null
  setFocusedNodeId: (id: string | null) => void
  activeFileId: string | null
  openFile: (id: string) => Promise<void>
  fileMap: Map<string, any>
  isCompactDensity: boolean
  expandedPaths: string[]
  deferredQuery: string
  toggleExpanded: (node: ExplorerNode) => void
  handleTreeItemKeyDown: (item: ExplorerVisibleNode, event: React.KeyboardEvent) => void
  explorerItemRefs: React.MutableRefObject<Record<string, HTMLElement | null>>
  isScanningLocalFolder: boolean
  localBrowserRootName?: string
  handleCreateDocument: () => void
  connectLocalFolder: () => Promise<void>
  canUseDirectoryPicker: boolean
  disconnectLocalFolder: () => void
}

export function ShellSidebar({
  tree,
  visibleTreeNodes,
  visibleTreeNodeIndexById,
  focusedNodeId,
  setFocusedNodeId,
  activeFileId,
  openFile,
  fileMap,
  isCompactDensity,
  expandedPaths,
  deferredQuery,
  toggleExpanded,
  handleTreeItemKeyDown,
  explorerItemRefs,
  isScanningLocalFolder,
  localBrowserRootName,
  handleCreateDocument,
  connectLocalFolder,
  canUseDirectoryPicker,
  disconnectLocalFolder,
}: ShellSidebarProps) {
  const renderNode = (node: ExplorerNode, depth = 0) => {
    const treeLevel = depth + 1
    const indentWidthClass = isCompactDensity ? 'w-3' : 'w-3.5'
    const renderIndent = (count: number) =>
      Array.from({ length: count }, (_, index) => (
        <span key={`${node.id}-indent-${index}`} aria-hidden="true" className={cn('shrink-0', indentWidthClass)} />
      ))

    if (node.kind === 'file') {
      const file = node.fileId ? fileMap.get(node.fileId) ?? null : null
      const Icon = getFileIcon(node.name)
      const isActive = file?.id === activeFileId
      const visibleItem = visibleTreeNodes[visibleTreeNodeIndexById.get(node.id) ?? -1]

      return (
        <div
          key={node.id}
          role="treeitem"
          aria-label={node.name}
          aria-level={treeLevel}
          aria-selected={isActive ? 'true' : 'false'}
          tabIndex={focusedNodeId === node.id ? 0 : -1}
          onClick={() => node.fileId && void openFile(node.fileId)}
          onFocus={(event) => {
            if (event.currentTarget !== event.target) {
              return
            }
            setFocusedNodeId(node.id)
          }}
          onKeyDown={(event) => {
            if (event.currentTarget !== event.target) {
              return
            }
            visibleItem && handleTreeItemKeyDown(visibleItem, event)
          }}
          ref={(element) => {
            explorerItemRefs.current[node.id] = element
          }}
          className="outline-none"
        >
          <div
            className={cn(
              'flex w-full items-center text-left transition',
              isCompactDensity
                ? 'min-h-7 gap-1.5 rounded-md px-2 py-1 text-[12px] leading-5'
                : 'gap-2 rounded-xl px-3 py-2 text-sm',
              isActive
                ? 'bg-emerald-500/15 text-emerald-100 ring-1 ring-emerald-400/30 dark:text-emerald-100'
                : focusedNodeId === node.id
                  ? 'bg-white/8 text-white ring-1 ring-white/15'
                  : 'text-slate-200/80 hover:bg-white/8 hover:text-white'
            )}
          >
            {renderIndent(depth)}
            <Icon className={cn('shrink-0 text-emerald-300/80', isCompactDensity ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
            <span className="truncate">{node.name}</span>
          </div>
        </div>
      )
    }

    const isExpanded = deferredQuery ? true : expandedPaths.includes(node.path)
    const visibleItem = visibleTreeNodes[visibleTreeNodeIndexById.get(node.id) ?? -1]
    const canExpand = Boolean(node.children?.length) || Boolean(node.loading) || Boolean(node.unloaded)

    return (
      <div
        key={node.id}
        role="treeitem"
        aria-label={node.name}
        aria-level={treeLevel}
        aria-expanded={canExpand ? (isExpanded ? 'true' : 'false') : undefined}
        tabIndex={focusedNodeId === node.id ? 0 : -1}
        onClick={(event) => {
          if (event.currentTarget !== event.target) {
            return
          }
          toggleExpanded(node)
        }}
        onFocus={(event) => {
          if (event.currentTarget !== event.target) {
            return
          }
          setFocusedNodeId(node.id)
        }}
        onKeyDown={(event) => {
          if (event.currentTarget !== event.target) {
            return
          }
          visibleItem && handleTreeItemKeyDown(visibleItem, event)
        }}
        ref={(element) => {
          explorerItemRefs.current[node.id] = element
        }}
        className="outline-none"
      >
        <div
          onClick={() => toggleExpanded(node)}
          className={cn(
            'flex w-full items-center text-left text-slate-100 transition hover:bg-white/8',
            isCompactDensity
              ? 'min-h-7 gap-1.5 rounded-md px-2 py-1 text-[12px] leading-5'
              : 'gap-2 rounded-xl px-3 py-2 text-sm',
            focusedNodeId === node.id && 'bg-white/8 ring-1 ring-white/15'
          )}
        >
          {renderIndent(depth)}
          {isExpanded ? (
            <ChevronDown className={cn('shrink-0 text-slate-400', isCompactDensity ? 'h-3 w-3' : 'h-4 w-4')} />
          ) : (
            <ChevronRight className={cn('shrink-0 text-slate-400', isCompactDensity ? 'h-3 w-3' : 'h-4 w-4')} />
          )}
          {isExpanded ? (
            <FolderOpen className={cn('shrink-0 text-amber-300', isCompactDensity ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
          ) : (
            <Folder className={cn('shrink-0 text-amber-300', isCompactDensity ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
          )}
          <span className="truncate">{node.name}</span>
          {node.loading && <LoaderCircle className={cn('shrink-0 animate-spin text-slate-400', isCompactDensity ? 'h-3 w-3' : 'h-3.5 w-3.5')} />}
        </div>
        {isExpanded && node.children && <div role="group">{node.children.map((child) => renderNode(child, depth + 1))}</div>}
        {isExpanded && node.error && (
          <div className={cn('flex items-start gap-1.5 text-rose-300', isCompactDensity ? 'px-2 py-1 text-[11px]' : 'px-3 py-1 text-xs')} role="presentation">
            {renderIndent(depth + 1)}
            <span className="leading-5">{node.error}</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">

      <div className={cn('border-shell overflow-x-hidden border-b', isCompactDensity ? 'px-3 py-3' : 'px-4 py-4')}>
        <div className="flex flex-col gap-2 mb-3">
          <button
            type="button"
            onClick={handleCreateDocument}
            className="flex w-full min-w-0 items-center justify-center gap-2 rounded-xl border border-emerald-400/35 bg-emerald-400/12 px-3 py-2 text-[12px] font-medium text-emerald-100 transition hover:bg-emerald-400/18"
           aria-label="Create desktop document">
            New desktop document
          </button>

          <button
            type="button"
            onClick={() => void connectLocalFolder()}
            disabled={!canUseDirectoryPicker || isScanningLocalFolder}
            className="flex w-full min-w-0 items-center justify-center gap-2 rounded-xl border border-white/12 bg-white/8 px-3 py-2 text-[12px] font-medium text-slate-100 transition hover:bg-white/12 disabled:cursor-not-allowed disabled:opacity-60"
            aria-label={localBrowserRootName ? 'Reconnect Folder' : 'Connect Local Folder'}
          >
            {isScanningLocalFolder ? (
              <LoaderCircle className={cn('animate-spin', isCompactDensity ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
            ) : (
              <HardDrive className={cn(isCompactDensity ? 'h-3.5 w-3.5' : 'h-4 w-4')} />
            )}
            <span className="truncate">{localBrowserRootName ? 'Reconnect Folder' : 'Connect Local Folder'}</span>
          </button>

          {localBrowserRootName && (
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => void connectLocalFolder()}
                className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-white/12 bg-white/5 px-3 py-2 text-[11px] font-medium text-slate-300 transition hover:bg-white/8"
              >
                Refresh
              </button>
              <button
                type="button"
                onClick={disconnectLocalFolder}
                disabled={isScanningLocalFolder}
                className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-rose-400/25 bg-rose-400/6 px-3 py-2 text-[11px] font-medium text-rose-200 transition hover:bg-rose-400/10 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Detach
              </button>
            </div>
          )}
        </div>

          <div className="mt-3">
            <p className={cn('text-slate-400', isCompactDensity ? 'text-[11px] leading-5' : 'text-xs leading-5')}>
              {canUseDirectoryPicker
                ? localBrowserRootName
                  ? `Local workspace attached: ${localBrowserRootName}`
                  : 'Attach a local folder to inspect and work with real files when needed.'
                : 'Local folder attachment depends on the File System Access API and is not available in this browser.'}
            </p>
          </div>
      </div>
      <div className={cn('min-h-0 flex-1 overflow-y-auto outline-none', isCompactDensity ? 'p-3' : 'p-4')}>
      {isScanningLocalFolder && !localBrowserRootName ? (
        <div className="flex items-center gap-2 px-3 py-2 text-[11px] text-slate-400">
          <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
          Requesting local folder access...
        </div>
      ) : tree.length === 0 || (tree.length === 1 && tree[0].id === 'documents' && (!tree[0].children || tree[0].children.length === 0)) ? (
        <div className="px-3 py-4 text-[12px] leading-5 text-slate-400">
          {deferredQuery
            ? 'No explorer entries match the current filter.'
            : 'No desktop files yet. Create a note or connect a local folder.'}
        </div>
      ) : (
        <div role="tree" aria-label="Workbench explorer" className="space-y-0.5">
          {tree.map((node) => renderNode(node))}
        </div>
      )}
          </div>
    </div>
  )
}
