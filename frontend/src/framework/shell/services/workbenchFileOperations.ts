import type { Dispatch, SetStateAction } from 'react'
import type {
  DirectoryPickerWindow,
  LocalBrowserState,
  FileSaveState,
  WorkbenchTableData,
  WorkbenchFile,
  EditorViewMode,
} from '../workbenchTypes'
import {
  EMPTY_LOCAL_BROWSER_STATE,
  IDLE_FILE_SAVE_STATE,
} from '../workbenchTypes'
import {
  makeLocalDirectoryPath,
  makeLocalFileEntry,
  isLocalWorkbenchFileId,
} from '../workbenchLocalFs'
import { getPreferredEditorViewMode } from '../workbenchExplorer'

export function createWorkbenchFileOperations(options: {
  localBrowserRef: React.MutableRefObject<LocalBrowserState>
  localBrowserRequestRef: React.MutableRefObject<number>
  localBrowserSessionRef: React.MutableRefObject<number>
  localBrowser: LocalBrowserState
  setLocalBrowser: Dispatch<SetStateAction<LocalBrowserState>>
  setExpandedPaths: Dispatch<SetStateAction<string[]>>
  setIsScanningLocalFolder: Dispatch<SetStateAction<boolean>>
  setLocalFolderError: Dispatch<SetStateAction<string | null>>
  expandLocalDirectory: (dirPath: string, token: number, state: LocalBrowserState) => Promise<void>
  resetLocalSessionState: () => void
  hasDirtyLocalFiles: boolean
  canExitWithUnsavedChanges: (actionContext: string, options?: { localOnly?: boolean; fileId?: string }) => boolean

  openFileIds: string[]
  setOpenFileIds: Dispatch<SetStateAction<string[]>>
  activeFileId: string | null
  setActiveFileId: Dispatch<SetStateAction<string | null>>
  setEditorViewMode: Dispatch<SetStateAction<EditorViewMode>>
  setFocusedNodeId: Dispatch<SetStateAction<string | null>>
  fileMap: Map<string, WorkbenchFile>
  activeFile: WorkbenchFile | null

  createDocument: (options?: any) => any
  documents: Record<string, any>
  updateDocument?: any
  updateTableDocument?: any
  setDrafts?: any
  setTableDrafts?: any
  setSaveStateByFileId?: any
  setLocalFileContents?: any
  setLocalTableData?: any
  saveRequestRef?: any
  normalizeWorkbenchTableData?: any
  isBinarySpreadsheetFormat?: any
  exportTableDataToBlob?: any
  inferSpreadsheetFileFormat?: any
}) {
  const {
    localBrowserRef,
    localBrowserRequestRef,
    localBrowserSessionRef,
    localBrowser,
    setLocalBrowser,
    setExpandedPaths,
    setIsScanningLocalFolder,
    setLocalFolderError,
    expandLocalDirectory,
    resetLocalSessionState,
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
  } = options

  const connectLocalFolder = async () => {
    const pickerWindow = window as DirectoryPickerWindow
    if (!pickerWindow.showDirectoryPicker) {
      return
    }

    if (localBrowser.rootName && hasDirtyLocalFiles && !canExitWithUnsavedChanges('Reconnecting this local folder', { localOnly: true })) {
      return
    }

    setIsScanningLocalFolder(true)
    setLocalFolderError(null)

    try {
      const directoryHandle = await pickerWindow.showDirectoryPicker()
      const requestToken = localBrowserRequestRef.current + 1
      localBrowserRequestRef.current = requestToken
      localBrowserSessionRef.current += 1
      resetLocalSessionState()

      const rootPath = makeLocalDirectoryPath(directoryHandle.name)
      const rootDirectory = {
        id: rootPath,
        name: directoryHandle.name,
        path: rootPath,
        relativePath: '',
        handle: directoryHandle,
        loaded: false,
        loading: false,
        error: null,
        childDirectoryPaths: [],
        childFileIds: [],
      }

      const nextLocalBrowser: LocalBrowserState = {
        rootName: directoryHandle.name,
        rootPath,
        directories: { [rootPath]: rootDirectory },
        files: {},
        loadedFileCount: 0,
        skippedDirectoryCount: 0,
      }

      localBrowserRef.current = nextLocalBrowser
      setLocalBrowser(nextLocalBrowser)
      setExpandedPaths((current) => Array.from(new Set([...current.filter((path) => path === 'documents' || path === 'platform' || path === 'system'), 'local', rootPath])))
      await expandLocalDirectory(rootPath, requestToken, nextLocalBrowser)
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }
      console.error('Local folder connection failed:', error)
      setLocalFolderError(error instanceof Error ? error.message : 'Failed to connect folder')
    } finally {
      setIsScanningLocalFolder(false)
    }
  }

  const disconnectLocalFolder = () => {
    if (hasDirtyLocalFiles && !canExitWithUnsavedChanges('Disconnecting this local folder', { localOnly: true })) {
      return
    }

    localBrowserRequestRef.current += 1
    localBrowserSessionRef.current += 1
    localBrowserRef.current = EMPTY_LOCAL_BROWSER_STATE
    setLocalBrowser(EMPTY_LOCAL_BROWSER_STATE)
    resetLocalSessionState()
  }

  const openFile = async (fileId: string) => {
    const file = fileMap.get(fileId)
    if (!file) {
      return
    }

    setOpenFileIds((current) => {
      if (current.includes(file.id)) {
        return current
      }
      return [...current, file.id]
    })

    setActiveFileId(file.id)
    setEditorViewMode(getPreferredEditorViewMode(file))
    setFocusedNodeId(file.path)
  }

  const closeTab = (fileId: string) => {
    if (!canExitWithUnsavedChanges('Closing this tab', { fileId })) {
      return
    }

    setOpenFileIds((current) => {
      const next = current.filter((value) => value !== fileId)

      if (fileId === activeFileId) {
        const nextActiveFileId = next.length > 0 ? next[next.length - 1] : null
        setActiveFileId(nextActiveFileId)

        if (nextActiveFileId) {
          setEditorViewMode(getPreferredEditorViewMode(fileMap.get(nextActiveFileId) ?? null))
        }
      }

      return next
    })
  }

  const handleCreateDocument = () => {
    const document = createDocument()
    setExpandedPaths((current) => (current.includes('documents') ? current : [...current, 'documents']))
    setOpenFileIds((current) => [...current, document.id])
    setActiveFileId(document.id)
    setEditorViewMode('prose')
    setFocusedNodeId(document.path)
  }

  const handleCreateReport = () => {
    const nextIndex = Object.keys(documents).length + 1
    const document = createDocument({
      name: `report-${nextIndex}.md`,
      language: 'markdown',
      type: 'prose',
      content: '# Research Report\n\n## Summary\n\n## Analysis\n\n## Recommendations\n\n',
    })
    setExpandedPaths((current) => (current.includes('documents') ? current : [...current, 'documents']))
    setOpenFileIds((current) => (current.includes(document.id) ? current : [...current, document.id]))
    setActiveFileId(document.id)
    setEditorViewMode('prose')
    setFocusedNodeId(document.path)
  }

  const handleCreateTable = () => {
    const nextIndex = Object.keys(documents).length + 1
    const document = createDocument({
      name: `table-${nextIndex}.csv`,
      language: 'plaintext',
      type: 'table',
    })
    setExpandedPaths((current) => (current.includes('documents') ? current : [...current, 'documents']))
    setOpenFileIds((current) => (current.includes(document.id) ? current : [...current, document.id]))
    setActiveFileId(document.id)
    setEditorViewMode('table')
    setFocusedNodeId(document.path)
  }

  const handleSave = async (
    isDirty: boolean,
    isSavingActiveFile: boolean,
    drafts: Record<string, string>,
    activeTableData: WorkbenchTableData | null
  ) => {
    if (!activeFile || !isDirty || isSavingActiveFile) {
      return
    }

    const nextContent = drafts[activeFile.id] ?? activeFile.content
    const nextTableSnapshot =
      (activeFile.documentType === 'table' || (activeFile as any).type === 'table')
        ? activeTableData ?? normalizeWorkbenchTableData(undefined, nextContent, activeFile.path)
        : null

    if (activeFile.source === 'user') {
      if ((activeFile.documentType === 'table' || (activeFile as any).type === 'table') && nextTableSnapshot) {
        updateTableDocument(activeFile.id, nextTableSnapshot)
        setTableDrafts((current: any) => {
          const { [activeFile.id]: _removed, ...remaining } = current
          return remaining
        })
      } else {
        updateDocument(activeFile.id, nextContent)
      }
      setDrafts((current: any) => {
        const { [activeFile.id]: _removed, ...remaining } = current
        return remaining
      })
      return
    }

    if (activeFile.source === 'local' && activeFile.handle?.createWritable) {
      const saveRequestId = saveRequestRef.current + 1
      saveRequestRef.current = saveRequestId
      const browserSessionId = localBrowserSessionRef.current
      const fileId = activeFile.id
      const savedSnapshot = nextContent

      setSaveStateByFileId((current: any) => ({
        ...current,
        [fileId]: {
          status: 'saving',
          error: null,
          requestId: saveRequestId,
        },
      }))

      try {
        const writer = await activeFile.handle.createWritable()
        const savePayload =
          activeFile.documentType === 'table' && nextTableSnapshot && isBinarySpreadsheetFormat(activeFile.path)
            ? await exportTableDataToBlob(
                nextTableSnapshot,
                (inferSpreadsheetFileFormat(activeFile.path) ?? 'xlsx') as 'xlsx' | 'xls'
              )
            : savedSnapshot

        await writer.write(savePayload)
        await writer.close()

        if (browserSessionId !== localBrowserSessionRef.current) {
          return
        }

        setLocalFileContents((current: any) => ({
          ...current,
          [fileId]: savedSnapshot,
        }))
        if (nextTableSnapshot) {
          setLocalTableData((current: any) => ({
            ...current,
            [fileId]: nextTableSnapshot,
          }))
        }
        setDrafts((current: any) => {
          if (current[fileId] !== savedSnapshot) {
            return current
          }

          const { [fileId]: _removed, ...remaining } = current
          return remaining
        })
        if (nextTableSnapshot) {
          setTableDrafts((current: any) => {
            const { [fileId]: _removed, ...remaining } = current
            return remaining
          })
        }
        setSaveStateByFileId((current: any) => ({
          ...current,
          [fileId]: {
            status: 'idle',
            error: null,
            requestId: saveRequestId,
          },
        }))
      } catch (error) {
        if (browserSessionId !== localBrowserSessionRef.current) {
          return
        }

        setSaveStateByFileId((current: any) => {
          if (current[fileId]?.requestId !== saveRequestId) {
            return current
          }

          return {
            ...current,
            [fileId]: {
              status: 'error',
              error: error instanceof Error ? error.message : 'Failed to save file',
              requestId: saveRequestId,
            },
          }
        })
      }
    }
  }

  return {
    connectLocalFolder,
    disconnectLocalFolder,
    openFile,
    closeTab,
    handleCreateDocument,
    handleCreateReport,
    handleCreateTable,
    handleSave,
  }
}
