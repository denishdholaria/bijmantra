import { useEffect, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from 'react'
import type { editor as MonacoEditorApi } from 'monaco-editor'
import {
  getWorkbenchTableDelimiter,
  inferWorkbenchDocumentType,
  normalizeWorkbenchTableData,
  serializeDelimitedTable,
  type WorkbenchTableData,
} from '@/lib/workbenchDocuments'
import {
  exportTableDataToBlob,
  inferSpreadsheetFileFormat,
  isBinarySpreadsheetFormat,
  parseTableDataFile,
} from '@/lib/spreadsheet'
import { cn } from '@/lib/utils'
import { useSystemStore, type DesktopToolSurface } from '@/store/systemStore'
import { useWorkbenchStore } from '@/store/workbenchStore'
import { readBlobAsText } from '@/lib/blob'

// ── Extracted module imports ──
import type {
  WorkbenchFile, LocalFileEntry, LocalDirectoryEntry, LocalBrowserState,
  ExplorerNode, ExplorerVisibleNode,
  WorkbenchDensity, EditorViewMode, WorkbenchSessionState,
  FileSaveState, DirectoryPickerWindow,
} from './workbenchTypes'
import {
  EMPTY_LOCAL_BROWSER_STATE, IDLE_FILE_SAVE_STATE,
  WORKBENCH_DENSITY_STORAGE_KEY, WORKBENCH_EXPLORER_COLLAPSED_STORAGE_KEY,
  WORKBENCH_SESSION_STORAGE_KEY,
} from './workbenchTypes'
import {
  inferLanguageFromPath, isLocalWorkbenchFileId,
  makeLocalDirectoryPath, makeLocalFileEntry,
  readDirectoryLevel, scanDirectory,
  describeLocalFolderScanSummary,
} from './workbenchLocalFs'
import {
  isEditorViewMode, getPreferredEditorViewMode,
  getAvailableEditorViewModes, getEditorViewModeLabel, getEditorViewModeDescription,
  getInitialWorkbenchDensity, getInitialWorkbenchExplorerCollapsed, getInitialWorkbenchSession,
  getFileIcon, buildTree, filterTree, flattenVisibleTreeNodes,
  buildLocalExplorerTree, describeFile,
} from './workbenchExplorer'

import {
  useWorkbenchTheme,
  useWorkbenchRuntime,
  useWorkbenchPersistence,
  useWorkbenchState,
} from './hooks'

import { createWorkbenchFileOperations } from './services'

import {
  ShellLayout,
  ShellHeader,
  ShellSidebar,
  ShellEditor,
  ShellFooter,
} from './components'

// Re-export types and functions that are used externally
export type { LocalFolderScanSummary } from './workbenchTypes'
export { MAX_INDEXED_LOCAL_FILES, MAX_PROCESSED_LOCAL_ENTRIES } from './workbenchTypes'
export { readDirectoryLevel, scanDirectory } from './workbenchLocalFs'

export const DESKTOP_WORKBENCH_AGENT_INDEX = `
agent_index_version: 2026-04-13
purpose: Desktop workbench shell for local document browsing, editor mode selection, and session orchestration inside the frontend shell.
module_map:
- workbenchTypes.ts: all type definitions, constants, and initial-state shapes
- workbenchLocalFs.ts: local file-system scan and traversal helpers
- workbenchExplorer.ts: explorer-tree derivation, session persistence, editor mode helpers
- hooks/: Theme, Runtime, Persistence, and State management hooks
- services/: FileOperations service logic
- components/: UI layout and panels (EmptyState, Header, Sidebar, Editor, Footer)
- this file: shell composition, top-level state wiring, and rendering as a thin orchestrator
`

interface DesktopWorkbenchProps {
  surface: DesktopToolSurface | null
  onClose: () => void
  onOpenSurface: (surface: DesktopToolSurface) => void
  onDirtyStateChange?: (isDirty: boolean) => void
}

export function DesktopWorkbench({ surface, onClose, onOpenSurface, onDirtyStateChange }: DesktopWorkbenchProps) {
  const theme = useWorkbenchTheme()
  const runtimeSnapshot = useWorkbenchRuntime()
  const documents = useWorkbenchStore((state) => state.documents)
  const createDocument = useWorkbenchStore((state) => state.createDocument)
  const updateDocument = useWorkbenchStore((state) => state.updateDocument)
  const updateTableDocument = useWorkbenchStore((state) => state.updateTableDocument)

  const state = useWorkbenchState()

  useWorkbenchPersistence({
    workbenchDensity: state.workbenchDensity,
    explorerCollapsed: state.explorerCollapsed,
    expandedPaths: state.expandedPaths,
    openFileIds: state.openFileIds,
    activeFileId: state.activeFileId,
    editorViewMode: state.editorViewMode,
  })

  const {
    query, setQuery, deferredQuery,
    workbenchDensity, setWorkbenchDensity,
    explorerCollapsed, setExplorerCollapsed,
    expandedPaths, setExpandedPaths,
    localBrowser, setLocalBrowser,
    localFileContents, setLocalFileContents,
    localTableData, setLocalTableData,
    openFileIds, setOpenFileIds,
    activeFileId, setActiveFileId,
    drafts, setDrafts,
    tableDrafts, setTableDrafts,
    saveStateByFileId, setSaveStateByFileId,
    editorViewMode, setEditorViewMode,
    focusedNodeId, setFocusedNodeId,
    isScanningLocalFolder, setIsScanningLocalFolder,
    localFolderError, setLocalFolderError,
    isEditorHostReady, setIsEditorHostReady,
    localBrowserRef, localBrowserRequestRef, localBrowserSessionRef, saveRequestRef,
    explorerItemRefs, editorHostRef, monacoEditorRef, editorLayoutFrameRef,
  } = state

  const activeSaveState = activeFileId ? (saveStateByFileId[activeFileId] ?? IDLE_FILE_SAVE_STATE) : IDLE_FILE_SAVE_STATE

  const fileMap = useMemo(() => {
    const map = new Map<string, WorkbenchFile>()
    for (const [id, doc] of Object.entries(documents)) {
      map.set(id, {
        id: doc.id,
        name: doc.name,
        path: doc.path,
        source: 'user',
        language: doc.language,
        documentType: doc.type,
        editable: true,
        content: doc.content ?? '',
        updatedAt: doc.updatedAt,
      })
    }
    for (const [id, localFile] of Object.entries(localBrowser.files)) {
      const content = localFileContents[id] ?? ''
      map.set(id, {
        ...localFile,
        source: 'local',
        language: inferLanguageFromPath(localFile.path),
        documentType: inferWorkbenchDocumentType({ path: localFile.path }),
        editable: Boolean(localFile.handle?.createWritable),
        content,
      })
    }
    return map
  }, [documents, localBrowser.files, localFileContents])

  const activeFile = activeFileId ? (fileMap.get(activeFileId) ?? null) : null
  const activeTableData = activeFileId && activeFile && (activeFile.documentType === 'table' || (activeFile as any).type === 'table') && activeFile.source === 'user' ? documents[activeFileId]?.tableData : (activeFileId ? localTableData[activeFileId] : null)

  const isDirty = activeFile ? drafts[activeFile.id] !== undefined && drafts[activeFile.id] !== activeFile.content : false
  const isSavingActiveFile = activeSaveState.status === 'saving'
  const isCompactDensity = workbenchDensity === 'compact'
  const isExplorerSurface = surface === 'filesystem'
  const isEditorSurface = surface === 'editor'

  const hasDirtyLocalFiles = Object.entries(drafts).some(([fileId, draftContent]) => {
    const file = fileMap.get(fileId)
    return file?.source === 'local' && file.content !== draftContent
  })

  useEffect(() => {
    onDirtyStateChange?.(isDirty)
  }, [isDirty, onDirtyStateChange])

  useEffect(() => {
    const files = Array.from(fileMap.values())
    if (files.length === 0) {
      return
    }

    const validOpenFileIds = openFileIds.filter((fileId) => fileMap.has(fileId))

    if (validOpenFileIds.length !== openFileIds.length) {
      setOpenFileIds(validOpenFileIds)

      if (activeFileId && !validOpenFileIds.includes(activeFileId)) {
        const nextActiveFileId = validOpenFileIds.length > 0 ? validOpenFileIds[validOpenFileIds.length - 1] : null
        setActiveFileId(nextActiveFileId)

        if (nextActiveFileId) {
          setEditorViewMode(getPreferredEditorViewMode(fileMap.get(nextActiveFileId) ?? null))
        }
      }

      return
    }

    if (activeFileId && !fileMap.has(activeFileId)) {
      const nextActiveFileId = validOpenFileIds.length > 0 ? validOpenFileIds[validOpenFileIds.length - 1] : null
      setActiveFileId(nextActiveFileId)

      if (nextActiveFileId) {
        setEditorViewMode(getPreferredEditorViewMode(fileMap.get(nextActiveFileId) ?? null))
      }

      return
    }

    if (!activeFileId && validOpenFileIds.length > 0) {
      const nextActiveFileId = validOpenFileIds[validOpenFileIds.length - 1]
      setActiveFileId(nextActiveFileId)
      setEditorViewMode(getPreferredEditorViewMode(fileMap.get(nextActiveFileId) ?? null))
    }
  }, [activeFileId, fileMap, openFileIds, setOpenFileIds, setActiveFileId, setEditorViewMode])

  useEffect(() => {
    const files = Array.from(fileMap.values())
    if (files.length === 0 || activeFileId || openFileIds.length > 0) {
      return
    }

    const defaultFile = files.find((file) => file.source !== 'virtual') ?? files[0]
    setOpenFileIds([defaultFile.id])
    setActiveFileId(defaultFile.id)
    setEditorViewMode(getPreferredEditorViewMode(defaultFile))
  }, [activeFileId, fileMap, openFileIds.length, setOpenFileIds, setActiveFileId, setEditorViewMode])

  useEffect(() => {
    if (!isEditorSurface || !activeFile || editorViewMode !== 'raw') {
      setIsEditorHostReady(false)
      monacoEditorRef.current = null

      if (typeof window !== 'undefined' && editorLayoutFrameRef.current !== null) {
        window.cancelAnimationFrame(editorLayoutFrameRef.current)
        editorLayoutFrameRef.current = null
      }

      return
    }

    const host = editorHostRef.current
    if (!host) {
      return
    }

    const markReady = () => {
      const bounds = host.getBoundingClientRect()
      if (bounds.width > 0 && bounds.height > 0) {
        setIsEditorHostReady(true)
        scheduleEditorLayout()
      }
    }

    markReady()

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          if (!isEditorHostReady) {
            setIsEditorHostReady(true)
          }
          scheduleEditorLayout()
        }
      }
    })

    observer.observe(host)
    return () => {
      observer.disconnect()
    }
  }, [activeFile, editorViewMode, isEditorSurface])

  const canExitWithUnsavedChanges = (actionContext: string, options?: { localOnly?: boolean; fileId?: string }) => {
    const checkDrafts = options?.fileId
      ? { [options.fileId]: drafts[options.fileId] }
      : drafts

    const hasUnsavedChanges = Object.entries(checkDrafts).some(([fileId, draftContent]) => {
      const file = fileMap.get(fileId)
      if (!file) return false
      if (options?.localOnly && file.source !== 'local') return false
      return file.content !== draftContent
    })

    if (!hasUnsavedChanges) {
      return true
    }

    return window.confirm(
      `${actionContext} will lose unsaved changes in ${
        options?.fileId ? 'this file' : options?.localOnly ? 'local files' : 'open files'
      }. Are you sure you want to continue?`
    )
  }

  const loadLocalFileContent = async (file: LocalFileEntry) => {
    if (localFileContents[file.id] !== undefined) {
      return
    }

    try {
      const browserSessionId = localBrowserSessionRef.current
      const nativeFile = await file.handle?.getFile()
      const content = nativeFile ? await readBlobAsText(nativeFile) : ''

      if (browserSessionId !== localBrowserSessionRef.current) {
        return
      }

      setLocalFileContents((current) => ({
        ...current,
        [file.id]: content,
      }))

      if (inferWorkbenchDocumentType({ path: file.path }) === 'table') {
        const format = inferSpreadsheetFileFormat(file.path)
        if (format === 'csv' || format === 'tsv') {
          const delimiter = format === 'csv' ? ',' : format === 'tsv' ? '\t' : getWorkbenchTableDelimiter(content)
          setLocalTableData((current) => ({
            ...current,
            [file.id]: normalizeWorkbenchTableData(undefined, content, file.path),
          }))
        } else if (isBinarySpreadsheetFormat(file.path)) {
          const tableData = normalizeWorkbenchTableData(undefined, content, file.path)
          setLocalTableData((current) => ({
            ...current,
            [file.id]: tableData,
          }))
          setLocalFileContents((current) => ({
            ...current,
            [file.id]: serializeDelimitedTable(tableData, ','),
          }))
        }
      }
    } catch (error) {
      console.error('Failed to read local file:', error)
      if (localBrowserSessionRef.current === localBrowserSessionRef.current) {
        setLocalFileContents((current) => ({
          ...current,
          [file.id]: `Error reading file: ${error instanceof Error ? error.message : String(error)}`,
        }))
      }
    }
  }

  const expandLocalDirectory = async (dirPath: string, token = localBrowserRequestRef.current, currentState = localBrowserRef.current) => {
    const dir = currentState.directories[dirPath]
    if (!dir || dir.loaded || dir.loading) {
      return
    }

    setLocalBrowser((current) => ({
      ...current,
      directories: {
        ...current.directories,
        [dirPath]: { ...dir, loading: true, error: null },
      },
    }))

    try {
      const { directories: subDirectories = [], files = [] } = await readDirectoryLevel(dir.handle, localBrowser.rootName || "") as any
      const error = null;

      if (token !== localBrowserRequestRef.current) {
        return
      }

      setLocalBrowser((current) => {
        const nextDirs = { ...current.directories }
        const nextFiles = { ...current.files }

        for (const subDir of subDirectories) {
          nextDirs[subDir.id] = subDir
        }
        for (const file of files) {
          nextFiles[file.id] = file
        }

        nextDirs[dirPath] = {
          ...dir,
          loaded: true,
          loading: false,
          error,
          childDirectoryPaths: (subDirectories || []).map((d: any) => d.path),
          childFileIds: (files || []).map((f: any) => f.id),
        }

        const nextState = {
          ...current,
          directories: nextDirs,
          files: nextFiles,
          loadedFileCount: Object.keys(nextFiles).length,
        }
        localBrowserRef.current = nextState
        return nextState
      })
    } catch (error) {
      if (token !== localBrowserRequestRef.current) {
        return
      }

      setLocalBrowser((current) => {
        const nextState = {
          ...current,
          directories: {
            ...current.directories,
            [dirPath]: {
              ...dir,
              loading: false,
              error: error instanceof Error ? error.message : 'Failed to read directory',
            },
          },
        }
        localBrowserRef.current = nextState
        return nextState
      })
    }
  }

  const setDirectoryExpanded = (node: ExplorerNode, expanded: boolean) => {
    if (expandedPaths.includes(node.path) === expanded) {
      return
    }

    setExpandedPaths((current) => {
      if (expanded) {
        return [...current, node.path]
      }
      return current.filter((value) => value !== node.path)
    })

    if (expanded && node.source === 'local' && node.path !== 'local' && node.unloaded) {
      void expandLocalDirectory(node.path)
    }
  }

  useEffect(() => {
    if (!activeFile) return
    if (activeFile.source === 'local') {
      const localEntry = localBrowser.files[activeFile.id]
      if (localEntry && localFileContents[localEntry.id] === undefined) {
        void loadLocalFileContent(localEntry)
      }
    }
  }, [activeFile, localBrowser.files, localFileContents])

  const operations = createWorkbenchFileOperations({
    localBrowserRef,
    localBrowserRequestRef,
    localBrowserSessionRef,
    localBrowser,
    setLocalBrowser,
    setExpandedPaths,
    setIsScanningLocalFolder,
    setLocalFolderError,
    expandLocalDirectory,
    resetLocalSessionState: () => {
      setLocalFileContents({})
      setLocalTableData({})
      setDrafts({})
      setTableDrafts({})
      setSaveStateByFileId({})
    },
    hasDirtyLocalFiles,
    canExitWithUnsavedChanges,
    openFileIds,
    setOpenFileIds,
    activeFileId,
    setActiveFileId,
    setEditorViewMode,
    setFocusedNodeId,
    fileMap,
    activeFile,
    createDocument,
    documents,
    updateDocument,
    updateTableDocument,
    setDrafts,
    setTableDrafts,
    setSaveStateByFileId,
    setLocalFileContents,
    setLocalTableData,
    saveRequestRef,
    normalizeWorkbenchTableData,
    isBinarySpreadsheetFormat,
    exportTableDataToBlob,
    inferSpreadsheetFileFormat,
  })

  const tree = useMemo(() => buildTree(documents, localBrowser, expandedPaths, localFileContents), [documents, localBrowser, expandedPaths, localFileContents])
  const filteredTree = useMemo(() => filterTree(tree, deferredQuery), [tree, deferredQuery])
  const visibleTreeNodes = useMemo(() => flattenVisibleTreeNodes(filteredTree, expandedPaths, deferredQuery !== ""), [filteredTree, expandedPaths, deferredQuery])
  const visibleTreeNodeIndexById = useMemo(() => {
    const map = new Map<string, number>()
    visibleTreeNodes.forEach((item, index) => map.set(item.node.id, index))
    return map
  }, [visibleTreeNodes])

  useEffect(() => {
    if (focusedNodeId && explorerItemRefs.current[focusedNodeId]) {
      explorerItemRefs.current[focusedNodeId]?.focus()
    }
  }, [focusedNodeId])

  const handleTreeItemKeyDown = (visibleItem: ExplorerVisibleNode, event: ReactKeyboardEvent) => {
    const { node } = visibleItem
    const currentIndex = visibleTreeNodeIndexById.get(node.id) ?? -1
    const isExpanded = expandedPaths.includes(node.path)

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        if (currentIndex < visibleTreeNodes.length - 1) {
          setFocusedNodeId(visibleTreeNodes[currentIndex + 1].node.id)
        }
        break
      case 'ArrowUp':
        event.preventDefault()
        if (currentIndex > 0) {
          setFocusedNodeId(visibleTreeNodes[currentIndex - 1].node.id)
        }
        break
      case 'ArrowRight':
        event.preventDefault()
        if (node.kind === 'directory') {
          if (isExpanded) {
            if (currentIndex < visibleTreeNodes.length - 1) {
              setFocusedNodeId(visibleTreeNodes[currentIndex + 1].node.id)
            }
          } else {
            setDirectoryExpanded(node, true)
          }
        }
        break
      case 'ArrowLeft':
        event.preventDefault()
        if (node.kind === 'directory' && isExpanded && !deferredQuery) {
          setDirectoryExpanded(node, false)
        } else if (node.kind === 'directory' || node.kind === 'file') {
          // Find parent
          const parentPath = node.path.split('/').slice(0, -1).join('/')
          if (parentPath && parentPath !== '') {
            const parentIndex = visibleTreeNodes.findIndex((n) => n.node.path === parentPath)
            if (parentIndex !== -1) {
              setFocusedNodeId(visibleTreeNodes[parentIndex].node.id)
            }
          }
        }
        break
      case 'Enter':
      case ' ':
        event.preventDefault()
        if (node.kind === 'directory') {
          setDirectoryExpanded(node, !isExpanded)
        } else if (node.kind === 'file' && node.fileId) {
          void operations.openFile(node.fileId)
        }
        break
      case 'Home':
        event.preventDefault()
        if (visibleTreeNodes.length > 0) {
          setFocusedNodeId(visibleTreeNodes[0].node.id)
        }
        break
      case 'End':
        event.preventDefault()
        if (visibleTreeNodes.length > 0) {
          setFocusedNodeId(visibleTreeNodes[visibleTreeNodes.length - 1].node.id)
        }
        break
    }
  }

  const toggleExpanded = (node: ExplorerNode) => {
    const shouldExpand = deferredQuery ? true : !expandedPaths.includes(node.path)
    setDirectoryExpanded(node, shouldExpand)
  }

  const handleEditorValueChange = (nextValue: string) => {
    if (!activeFile) return
    if (activeFile.documentType === 'table') {
      setTableDrafts((current) => ({
        ...current,
        [activeFile.id]: normalizeWorkbenchTableData(undefined, nextValue, activeFile.path),
      }))
    }
    setDrafts((current) => ({
      ...current,
      [activeFile.id]: nextValue,
    }))
    setSaveStateByFileId((current) => {
      const nextState = current[activeFile.id]
      if (!nextState || nextState.status === 'saving') return current
      return {
        ...current,
        [activeFile.id]: {
          ...nextState,
          status: 'idle',
          error: null,
        },
      }
    })
  }

  const handleTableDataChange = (nextData: WorkbenchTableData) => {
    if (!activeFile) return
    const isLocalBinary = activeFile.source === 'local' && isBinarySpreadsheetFormat(activeFile.path)
    const nextContent = isLocalBinary ? activeFile.content : serializeDelimitedTable(nextData, (nextData as any).delimiter ?? ',')
    setTableDrafts((current) => ({
      ...current,
      [activeFile.id]: nextData,
    }))
    setDrafts((current) => ({
      ...current,
      [activeFile.id]: nextContent,
    }))
    setSaveStateByFileId((current) => {
      const nextState = current[activeFile.id]
      if (!nextState || nextState.status === 'saving') return current
      return {
        ...current,
        [activeFile.id]: { ...nextState, status: 'idle', error: null },
      }
    })
  }

  const scheduleEditorLayout = () => {
    if (editorLayoutFrameRef.current !== null) {
      cancelAnimationFrame(editorLayoutFrameRef.current)
    }
    editorLayoutFrameRef.current = requestAnimationFrame(() => {
      editorLayoutFrameRef.current = null
      if (monacoEditorRef.current) {
        monacoEditorRef.current.layout()
      }
    })
  }

  useEffect(() => {
    scheduleEditorLayout()
  }, [workbenchDensity, explorerCollapsed, surface])

  useEffect(() => {
    const handleResize = () => scheduleEditorLayout()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  if (!surface) return null

  const isProseView = editorViewMode === 'prose'
  const isTableView = editorViewMode === 'table'

  const documentsCount = Object.keys(documents).length
  const totalWorkspaceFileCount = documentsCount + localBrowser.loadedFileCount
  const editorValue = activeFile ? (drafts[activeFile.id] ?? activeFile.content) : ''
  const previewContent = activeFile ? editorValue : ''
  const workspaceLabel = localBrowser.rootName || "Research workspace"
  const workspaceDescription = localBrowser.rootName
    ? 'Connected local files and desktop docs'
    : 'Reports, notes, and attached local folders'

  const activeFileStatusLabel =
    activeSaveState.status === 'saving'
      ? 'Saving...'
      : activeSaveState.status === 'error'
        ? activeSaveState.error ?? 'Save failed'
        : isDirty
          ? 'Unsaved changes'
          : 'Up to date'

  const footerStatusLabel =
    activeSaveState.status === 'saving'
      ? 'Status: Saving...'
      : activeSaveState.status === 'error'
        ? `Status: ${activeSaveState.error ?? 'Save failed'}`
        : isDirty
          ? 'Status: Unsaved changes'
          : 'Status: Up to date'

  const explorerWidthClass = explorerCollapsed
    ? 'w-[68px]'
    : isCompactDensity
      ? 'w-[336px] sm:w-[352px]'
      : 'w-[364px] sm:w-[388px]'

  const canUseDirectoryPicker = typeof window !== 'undefined' && 'showDirectoryPicker' in window
  const availableEditorViewModes = activeFile ? getAvailableEditorViewModes(activeFile) : []

  return (
    <ShellLayout>
      <aside
        className={cn(
          'border-shell bg-[linear-gradient(180deg,rgba(7,18,25,0.96),rgba(8,16,24,0.9))] flex min-h-0 min-w-0 shrink-0 flex-col overflow-hidden border-r backdrop-blur-xl transition-[width] duration-200',
          explorerWidthClass
        )}
      >
        {explorerCollapsed ? (
          <div className="flex h-full w-full flex-col items-center justify-between px-2 py-3">
            <div className="flex flex-col items-center gap-2">
              <button
                type="button"
                onClick={() => setExplorerCollapsed(false)}
                className="rounded-xl border border-white/12 bg-white/8 p-2 text-slate-100 transition hover:bg-white/14"
                aria-label="Expand explorer sidebar"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-4 w-4"
                >
                  <rect width="18" height="18" x="3" y="3" rx="2" />
                  <path d="M9 3v18" />
                  <path d="m14 9 3 3-3 3" />
                </svg>
              </button>
            </div>
          </div>
        ) : (
          <>
            <ShellHeader
              isCompactDensity={isCompactDensity}
              workspaceLabel={workspaceLabel}
              workspaceDescription={workspaceDescription}
              setExplorerCollapsed={setExplorerCollapsed}
              canExitWithUnsavedChanges={canExitWithUnsavedChanges}
              onClose={onClose}
              query={query}
              setQuery={setQuery}
              workbenchDensity={workbenchDensity}
              setWorkbenchDensity={setWorkbenchDensity}
              activeFile={activeFile}
              activeFileStatusLabel={activeFileStatusLabel}
              isDirty={isDirty}
              isSavingActiveFile={isSavingActiveFile}
              handleSave={() => operations.handleSave(isDirty, isSavingActiveFile, drafts, activeTableData ?? null)}
              editorViewMode={editorViewMode}
              setEditorViewMode={setEditorViewMode}
              availableEditorViewModes={availableEditorViewModes}
              getEditorViewModeLabel={getEditorViewModeLabel}
            />
            <ShellSidebar
              tree={filteredTree}
              visibleTreeNodes={visibleTreeNodes}
              visibleTreeNodeIndexById={visibleTreeNodeIndexById}
              focusedNodeId={focusedNodeId}
              setFocusedNodeId={setFocusedNodeId}
              activeFileId={activeFileId}
              openFile={operations.openFile}
              fileMap={fileMap}
              isCompactDensity={isCompactDensity}
              expandedPaths={expandedPaths}
              deferredQuery={deferredQuery}
              toggleExpanded={toggleExpanded}
              handleTreeItemKeyDown={handleTreeItemKeyDown}
              explorerItemRefs={explorerItemRefs}
              isScanningLocalFolder={isScanningLocalFolder}
              localBrowserRootName={localBrowser.rootName ?? undefined}
              handleCreateDocument={operations.handleCreateDocument}
              connectLocalFolder={operations.connectLocalFolder}
              canUseDirectoryPicker={canUseDirectoryPicker}
              disconnectLocalFolder={operations.disconnectLocalFolder}
            />
          </>
        )}
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[hsl(var(--card)/0.72)]">
        <ShellEditor
          isExplorerSurface={isExplorerSurface}
          isCompactDensity={isCompactDensity}
          activeFile={activeFile}
          localBrowserRootName={localBrowser.rootName ?? undefined}
          onOpenSurface={onOpenSurface}
          availableEditorViewModes={availableEditorViewModes}
          editorViewMode={editorViewMode}
          setEditorViewMode={setEditorViewMode}
          isDirty={isDirty}
          isSavingActiveFile={isSavingActiveFile}
          handleSave={() => operations.handleSave(isDirty, isSavingActiveFile, drafts, activeTableData ?? null)}
          openFileIds={openFileIds}
          fileMap={fileMap}
          drafts={drafts}
          activeFileId={activeFileId}
          openFile={operations.openFile}
          closeTab={operations.closeTab}
          activeSaveState={activeSaveState}
          activeFileStatusLabel={activeFileStatusLabel}
          totalWorkspaceFileCount={totalWorkspaceFileCount}
          previewContent={previewContent}
          editorValue={editorValue}
          theme={theme}
          isProseView={isProseView}
          handleEditorValueChange={handleEditorValueChange}
          isTableView={isTableView}
          activeTableData={activeTableData}
          handleTableDataChange={handleTableDataChange}
          isEditorHostReady={isEditorHostReady}
          monacoEditorRef={monacoEditorRef}
          scheduleEditorLayout={scheduleEditorLayout}
          editorHostRef={editorHostRef}
          connectLocalFolder={operations.connectLocalFolder}
          handleCreateReport={operations.handleCreateReport}
          handleCreateTable={operations.handleCreateTable}
          canUseDirectoryPicker={canUseDirectoryPicker}
          isScanningLocalFolder={isScanningLocalFolder}
        />
        <ShellFooter
          activeFile={activeFile}
          footerStatusLabel={footerStatusLabel}
          runtimeSnapshot={runtimeSnapshot}
          localBrowser={localBrowser}
          documentsCount={documentsCount}
        />
      </div>
    </ShellLayout>
  )
}
