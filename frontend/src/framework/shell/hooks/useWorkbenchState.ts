import { useState, useDeferredValue, useRef } from 'react'
import type { editor as MonacoEditorApi } from 'monaco-editor'
import type {
  LocalBrowserState,
  WorkbenchDensity,
  EditorViewMode,
  WorkbenchSessionState,
  FileSaveState,
  WorkbenchTableData,
} from '../workbenchTypes'
import {
  EMPTY_LOCAL_BROWSER_STATE,
} from '../workbenchTypes'
import {
  getInitialWorkbenchDensity,
  getInitialWorkbenchExplorerCollapsed,
  getInitialWorkbenchSession,
} from '../workbenchExplorer'

export function useWorkbenchState() {
  const [persistedSession] = useState<WorkbenchSessionState>(getInitialWorkbenchSession)
  const [query, setQuery] = useState('')
  const [workbenchDensity, setWorkbenchDensity] = useState<WorkbenchDensity>(getInitialWorkbenchDensity)
  const [explorerCollapsed, setExplorerCollapsed] = useState(getInitialWorkbenchExplorerCollapsed)
  const deferredQuery = useDeferredValue(query.trim().toLowerCase())
  const [expandedPaths, setExpandedPaths] = useState<string[]>(persistedSession.expandedPaths)
  const [localBrowser, setLocalBrowser] = useState<LocalBrowserState>(EMPTY_LOCAL_BROWSER_STATE)
  const [localFileContents, setLocalFileContents] = useState<Record<string, string>>({})
  const [localTableData, setLocalTableData] = useState<Record<string, WorkbenchTableData>>({})
  const [openFileIds, setOpenFileIds] = useState<string[]>(persistedSession.openFileIds)
  const [activeFileId, setActiveFileId] = useState<string | null>(persistedSession.activeFileId)
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [tableDrafts, setTableDrafts] = useState<Record<string, WorkbenchTableData>>({})
  const [saveStateByFileId, setSaveStateByFileId] = useState<Record<string, FileSaveState>>({})
  const [editorViewMode, setEditorViewMode] = useState<EditorViewMode>(persistedSession.editorViewMode)
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null)
  const [isScanningLocalFolder, setIsScanningLocalFolder] = useState(false)
  const [localFolderError, setLocalFolderError] = useState<string | null>(null)
  const [isEditorHostReady, setIsEditorHostReady] = useState(false)

  const localBrowserRef = useRef<LocalBrowserState>(EMPTY_LOCAL_BROWSER_STATE)
  const localBrowserRequestRef = useRef(0)
  const localBrowserSessionRef = useRef(0)
  const saveRequestRef = useRef(0)
  const explorerItemRefs = useRef<Record<string, HTMLElement | null>>({})
  const editorHostRef = useRef<HTMLDivElement | null>(null)
  const monacoEditorRef = useRef<MonacoEditorApi.IStandaloneCodeEditor | null>(null)
  const editorLayoutFrameRef = useRef<number | null>(null)

  return {
    persistedSession,
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

    localBrowserRef,
    localBrowserRequestRef,
    localBrowserSessionRef,
    saveRequestRef,
    explorerItemRefs,
    editorHostRef,
    monacoEditorRef,
    editorLayoutFrameRef,
  }
}
