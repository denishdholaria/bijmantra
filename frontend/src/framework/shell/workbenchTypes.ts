/**
 * Workbench Types
 * Shared type definitions for the DesktopWorkbench shell.
 * Extracted from DesktopWorkbench.tsx to reduce shell file responsibility density.
 */

import type { WorkbenchDocumentType, WorkbenchTableData as LibWorkbenchTableData } from '@/lib/workbenchDocuments'
export type WorkbenchTableData = LibWorkbenchTableData

// ── File System Handle Types ──

export type FileSystemWritableFileStreamLike = {
  write: (data: string | Blob | ArrayBuffer | Uint8Array) => Promise<void>
  close: () => Promise<void>
}

export type FileSystemFileHandleLike = {
  kind: 'file'
  name: string
  getFile: () => Promise<File>
  createWritable?: () => Promise<FileSystemWritableFileStreamLike>
}

export type FileSystemDirectoryHandleLike = {
  kind: 'directory'
  name: string
  entries: () => AsyncIterable<[string, FileSystemDirectoryHandleLike | FileSystemFileHandleLike]>
}

export type DirectoryPickerWindow = Window & {
  showDirectoryPicker?: () => Promise<FileSystemDirectoryHandleLike>
}

// ── Scan Types ──

export type LocalFolderScanSummary = {
  indexedFileCount: number
  skippedDirectoryCount: number
  truncated: boolean
  stopReason: 'file-cap' | 'traversal-budget' | null
}

export type LocalFolderScanState = {
  files: LocalFileEntry[]
  indexedFileCount: number
  processedEntryCount: number
  skippedDirectoryCount: number
  truncated: boolean
  stopReason: LocalFolderScanSummary['stopReason']
}

// ── Workbench Document Types ──

export type WorkbenchFile = {
  id: string
  name: string
  path: string
  language: string
  documentType: WorkbenchDocumentType
  content: string
  source: 'virtual' | 'user' | 'local'
  editable: boolean
  route?: string
  updatedAt?: string
  handle?: FileSystemFileHandleLike
  tableData?: WorkbenchTableData
}

export type LocalFileEntry = Omit<WorkbenchFile, 'content'>

export type LocalDirectoryEntry = {
  id: string
  name: string
  path: string
  relativePath: string
  handle: FileSystemDirectoryHandleLike
  loaded: boolean
  loading: boolean
  error: string | null
  childDirectoryPaths: string[]
  childFileIds: string[]
}

export type LocalBrowserState = {
  rootName: string | null
  rootPath: string | null
  directories: Record<string, LocalDirectoryEntry>
  files: Record<string, LocalFileEntry>
  loadedFileCount: number
  skippedDirectoryCount: number
}

export type FileSaveState = {
  status: 'idle' | 'saving' | 'error'
  error: string | null
  requestId: number
}

// ── Explorer Tree Types ──

export type ExplorerNode = {
  id: string
  name: string
  path: string
  kind: 'directory' | 'file'
  fileId?: string
  children?: ExplorerNode[]
  source?: 'local' | 'default'
  loading?: boolean
  unloaded?: boolean
  error?: string | null
}

export type WorkbenchDensity = 'compact' | 'comfortable'
export type EditorViewMode = 'prose' | 'raw' | 'table'

export type WorkbenchSessionState = {
  openFileIds: string[]
  activeFileId: string | null
  expandedPaths: string[]
  editorViewMode: EditorViewMode
}

export type ExplorerVisibleNode = {
  id: string
  node: ExplorerNode
  depth: number
  isExpanded: boolean
  parentId: string | null
}

// ── Constants ──

export const MAX_INDEXED_LOCAL_FILES = 1200
export const MAX_PROCESSED_LOCAL_ENTRIES = 4000
export const LOCAL_SCAN_YIELD_INTERVAL = 100

export const SKIPPED_LOCAL_DIRECTORY_NAMES = new Set([
  '.git', '.next', '.turbo', '__pycache__',
  'build', 'coverage', 'dist', 'node_modules', 'target',
])

export const EMPTY_LOCAL_BROWSER_STATE: LocalBrowserState = {
  rootName: null, rootPath: null,
  directories: {}, files: {},
  loadedFileCount: 0, skippedDirectoryCount: 0,
}

export const IDLE_FILE_SAVE_STATE: FileSaveState = {
  status: 'idle', error: null, requestId: 0,
}

export const WORKBENCH_DENSITY_STORAGE_KEY = 'bijmantra-workbench-density'
export const WORKBENCH_EXPLORER_COLLAPSED_STORAGE_KEY = 'bijmantra-workbench-explorer-collapsed'
export const WORKBENCH_SESSION_STORAGE_KEY = 'bijmantra-workbench-session'







export const DEFAULT_WORKBENCH_DENSITY: WorkbenchDensity = 'compact'

export const DEFAULT_WORKBENCH_EXPANDED_PATHS: string[] = ['documents', 'platform', 'system']
