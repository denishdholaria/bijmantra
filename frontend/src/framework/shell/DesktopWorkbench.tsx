import { lazy, Suspense, useDeferredValue, useEffect, useMemo, useRef, useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  FileCode2,
  FileJson2,
  FileText,
  Folder,
  FolderOpen,
  HardDrive,
  LoaderCircle,
  NotebookPen,
  Plus,
  RefreshCcw,
  Route,
  Save,
  Search,
  X,
} from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { divisions } from '@/framework/registry/divisions'
import { workspaceModules, workspaces } from '@/framework/registry/workspaces'
import { useSystemStore, type DesktopToolSurface } from '@/store/systemStore'
import { useWorkbenchStore } from '@/store/workbenchStore'

const MonacoEditor = lazy(() => import('@monaco-editor/react'))

type FileSystemWritableFileStreamLike = {
  write: (data: string) => Promise<void>
  close: () => Promise<void>
}

type FileSystemFileHandleLike = {
  kind: 'file'
  name: string
  getFile: () => Promise<File>
  createWritable?: () => Promise<FileSystemWritableFileStreamLike>
}

type FileSystemDirectoryHandleLike = {
  kind: 'directory'
  name: string
  entries: () => AsyncIterable<[string, FileSystemDirectoryHandleLike | FileSystemFileHandleLike]>
}

type DirectoryPickerWindow = Window & {
  showDirectoryPicker?: () => Promise<FileSystemDirectoryHandleLike>
}

export type LocalFolderScanSummary = {
  indexedFileCount: number
  skippedDirectoryCount: number
  truncated: boolean
  stopReason: 'file-cap' | 'traversal-budget' | null
}

type LocalFolderScanState = {
  files: LocalFileEntry[]
  indexedFileCount: number
  processedEntryCount: number
  skippedDirectoryCount: number
  truncated: boolean
  stopReason: LocalFolderScanSummary['stopReason']
}

export const MAX_INDEXED_LOCAL_FILES = 1200
export const MAX_PROCESSED_LOCAL_ENTRIES = 4000

const LOCAL_SCAN_YIELD_INTERVAL = 100
const SKIPPED_LOCAL_DIRECTORY_NAMES = new Set([
  '.git',
  '.next',
  '.turbo',
  '__pycache__',
  'build',
  'coverage',
  'dist',
  'node_modules',
  'target',
])

type WorkbenchFile = {
  id: string
  name: string
  path: string
  language: string
  content: string
  source: 'virtual' | 'user' | 'local'
  editable: boolean
  route?: string
  updatedAt?: string
  handle?: FileSystemFileHandleLike
}

type LocalFileEntry = Omit<WorkbenchFile, 'content'>

type LocalDirectoryEntry = {
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

type LocalBrowserState = {
  rootName: string | null
  rootPath: string | null
  directories: Record<string, LocalDirectoryEntry>
  files: Record<string, LocalFileEntry>
  loadedFileCount: number
  skippedDirectoryCount: number
}

type ExplorerNode = {
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

const EMPTY_LOCAL_BROWSER_STATE: LocalBrowserState = {
  rootName: null,
  rootPath: null,
  directories: {},
  files: {},
  loadedFileCount: 0,
  skippedDirectoryCount: 0,
}

function inferLanguageFromPath(path: string) {
  const extension = path.split('.').pop()?.toLowerCase()

  switch (extension) {
    case 'json':
      return 'json'
    case 'yaml':
    case 'yml':
      return 'yaml'
    case 'ts':
    case 'tsx':
      return 'typescript'
    case 'js':
    case 'jsx':
      return 'javascript'
    case 'md':
      return 'markdown'
    case 'py':
      return 'python'
    case 'css':
      return 'css'
    case 'html':
      return 'html'
    default:
      return 'plaintext'
  }
}

function getFileIcon(path: string) {
  const extension = path.split('.').pop()?.toLowerCase()

  if (extension === 'json' || extension === 'yaml' || extension === 'yml') {
    return FileJson2
  }

  if (extension === 'ts' || extension === 'tsx' || extension === 'js' || extension === 'jsx' || extension === 'py') {
    return FileCode2
  }

  return FileText
}

function buildTree(files: WorkbenchFile[]) {
  const root: ExplorerNode = {
    id: 'root',
    name: 'root',
    path: '',
    kind: 'directory',
    children: [],
  }

  const nodeMap = new Map<string, ExplorerNode>([['', root]])

  for (const file of files) {
    const segments = file.path.split('/').filter(Boolean)
    let currentPath = ''

    for (let index = 0; index < segments.length; index += 1) {
      const segment = segments[index]
      const nextPath = currentPath ? `${currentPath}/${segment}` : segment
      const isFile = index === segments.length - 1

      if (!nodeMap.has(nextPath)) {
        const node: ExplorerNode = {
          id: nextPath,
          name: segment,
          path: nextPath,
          kind: isFile ? 'file' : 'directory',
          fileId: isFile ? file.id : undefined,
          children: isFile ? undefined : [],
        }
        nodeMap.set(nextPath, node)
        nodeMap.get(currentPath)?.children?.push(node)
      }

      currentPath = nextPath
    }
  }

  const sortNodes = (nodes: ExplorerNode[]) => {
    nodes.sort((left, right) => {
      const rootOrder = ['local', 'documents', 'platform', 'system']
      const leftRootRank = rootOrder.indexOf(left.path.split('/')[0] ?? '')
      const rightRootRank = rootOrder.indexOf(right.path.split('/')[0] ?? '')

      if (leftRootRank !== rightRootRank) {
        return (leftRootRank === -1 ? 99 : leftRootRank) - (rightRootRank === -1 ? 99 : rightRootRank)
      }

      if (left.kind !== right.kind) {
        return left.kind === 'directory' ? -1 : 1
      }

      return left.name.localeCompare(right.name)
    })

    for (const node of nodes) {
      if (node.children) {
        sortNodes(node.children)
      }
    }
  }

  sortNodes(root.children ?? [])
  return root.children ?? []
}

function filterTree(nodes: ExplorerNode[], query: string): ExplorerNode[] {
  if (!query) {
    return nodes
  }

  return nodes
    .map((node) => {
      if (node.kind === 'file') {
        return node.name.toLowerCase().includes(query) ? node : null
      }

      const children = filterTree(node.children ?? [], query)
      if (node.name.toLowerCase().includes(query) || children.length > 0) {
        return {
          ...node,
          children,
        }
      }

      return null
    })
    .filter((node): node is ExplorerNode => node !== null)
}

function makeLocalDirectoryPath(rootName: string, relativePath = '') {
  return relativePath ? `local/${rootName}/${relativePath}` : `local/${rootName}`
}

function makeLocalFileEntry(rootName: string, relativePath: string, handle: FileSystemFileHandleLike): LocalFileEntry {
  const path = `local/${rootName}/${relativePath}`
  return {
    id: `local:${rootName}/${relativePath}`,
    name: handle.name,
    path,
    language: inferLanguageFromPath(handle.name),
    source: 'local',
    editable: true,
    handle,
    updatedAt: '',
  }
}

export async function readDirectoryLevel(
  handle: FileSystemDirectoryHandleLike,
  rootName: string,
  currentRelativePath = ''
): Promise<{
  directories: Array<{
    id: string
    name: string
    path: string
    relativePath: string
    handle: FileSystemDirectoryHandleLike
  }>
  files: LocalFileEntry[]
  skippedDirectoryCount: number
}> {
  const entries: Array<{ name: string; handle: FileSystemDirectoryHandleLike | FileSystemFileHandleLike }> = []

  for await (const [name, entryHandle] of handle.entries()) {
    entries.push({ name, handle: entryHandle })
  }

  entries.sort((left, right) => {
    if (left.handle.kind !== right.handle.kind) {
      return left.handle.kind === 'directory' ? -1 : 1
    }

    return left.name.localeCompare(right.name)
  })

  const directories: Array<{
    id: string
    name: string
    path: string
    relativePath: string
    handle: FileSystemDirectoryHandleLike
  }> = []
  const files: LocalFileEntry[] = []
  let skippedDirectoryCount = 0

  for (const entry of entries) {
    const relativePath = currentRelativePath ? `${currentRelativePath}/${entry.name}` : entry.name

    if (entry.handle.kind === 'directory') {
      if (SKIPPED_LOCAL_DIRECTORY_NAMES.has(entry.name.toLowerCase())) {
        skippedDirectoryCount += 1
        continue
      }

      directories.push({
        id: makeLocalDirectoryPath(rootName, relativePath),
        name: entry.name,
        path: makeLocalDirectoryPath(rootName, relativePath),
        relativePath,
        handle: entry.handle,
      })
      continue
    }

    files.push(makeLocalFileEntry(rootName, relativePath, entry.handle))
  }

  return {
    directories,
    files,
    skippedDirectoryCount,
  }
}

export async function scanDirectory(
  handle: FileSystemDirectoryHandleLike,
  rootName: string,
  currentRelativePath = '',
  state: LocalFolderScanState = {
    files: [],
    indexedFileCount: 0,
    processedEntryCount: 0,
    skippedDirectoryCount: 0,
    truncated: false,
    stopReason: null,
  }
): Promise<{ files: LocalFileEntry[]; summary: LocalFolderScanSummary }> {
  const entries: Array<{ name: string; handle: FileSystemDirectoryHandleLike | FileSystemFileHandleLike }> = []

  for await (const [name, entryHandle] of handle.entries()) {
    if (state.processedEntryCount >= MAX_PROCESSED_LOCAL_ENTRIES) {
      state.truncated = true
      state.stopReason = 'traversal-budget'
      break
    }

    state.processedEntryCount += 1
    if (state.processedEntryCount % LOCAL_SCAN_YIELD_INTERVAL === 0) {
      await new Promise<void>((resolve) => window.setTimeout(resolve, 0))
    }

    entries.push({ name, handle: entryHandle })
  }

  entries.sort((left, right) => {
    if (left.handle.kind !== right.handle.kind) {
      return left.handle.kind === 'directory' ? -1 : 1
    }

    return left.name.localeCompare(right.name)
  })

  for (const entry of entries) {
    if (state.truncated) {
      break
    }

    const relativePath = currentRelativePath ? `${currentRelativePath}/${entry.name}` : entry.name

    if (entry.handle.kind === 'directory') {
      if (SKIPPED_LOCAL_DIRECTORY_NAMES.has(entry.name.toLowerCase())) {
        state.skippedDirectoryCount += 1
        continue
      }

      await scanDirectory(entry.handle, rootName, relativePath, state)
      continue
    }

    if (state.indexedFileCount >= MAX_INDEXED_LOCAL_FILES) {
      state.truncated = true
      state.stopReason = 'file-cap'
      break
    }

    const path = `local/${rootName}/${relativePath}`
    state.files.push({
      id: `local:${rootName}/${relativePath}`,
      name: entry.name,
      path,
      language: inferLanguageFromPath(entry.name),
      source: 'local',
      editable: true,
      handle: entry.handle,
      updatedAt: '',
    })
    state.indexedFileCount += 1
  }

  return {
    files: state.files,
    summary: {
      indexedFileCount: state.indexedFileCount,
      skippedDirectoryCount: state.skippedDirectoryCount,
      truncated: state.truncated,
      stopReason: state.stopReason,
    },
  }
}

function describeLocalFolderScanSummary(summary: LocalFolderScanSummary) {
  const detail =
    summary.stopReason === 'file-cap'
      ? `first scan window capped at ${MAX_INDEXED_LOCAL_FILES} files`
      : summary.stopReason === 'traversal-budget'
        ? `first scan window capped after ${MAX_PROCESSED_LOCAL_ENTRIES} traversed entries`
        : null

  const skippedDetail =
    summary.skippedDirectoryCount > 0
      ? `${summary.skippedDirectoryCount} heavy director${summary.skippedDirectoryCount === 1 ? 'y was' : 'ies were'} skipped`
      : null

  return [
    `Indexed ${summary.indexedFileCount} files`,
    detail,
    skippedDetail,
  ]
    .filter(Boolean)
    .join(', ')
}

function buildLocalExplorerTree(localBrowser: LocalBrowserState): ExplorerNode | null {
  if (!localBrowser.rootPath || !localBrowser.rootName) {
    return null
  }

  const buildDirectoryNode = (directoryPath: string): ExplorerNode | null => {
    const directory = localBrowser.directories[directoryPath]
    if (!directory) {
      return null
    }

    const childDirectories = directory.childDirectoryPaths
      .map((childPath) => buildDirectoryNode(childPath))
      .filter((node): node is ExplorerNode => node !== null)

    const childFiles: ExplorerNode[] = []
    for (const fileId of directory.childFileIds) {
      const file = localBrowser.files[fileId]
      if (!file) {
        continue
      }

      childFiles.push({
        id: file.path,
        name: file.name,
        path: file.path,
        kind: 'file',
        fileId: file.id,
        source: 'local',
      })
    }

    const children = [...childDirectories, ...childFiles].sort((left, right) => {
      if (left.kind !== right.kind) {
        return left.kind === 'directory' ? -1 : 1
      }

      return left.name.localeCompare(right.name)
    })

    return {
      id: directory.path,
      name: directory.name,
      path: directory.path,
      kind: 'directory',
      children,
      source: 'local',
      loading: directory.loading,
      unloaded: !directory.loaded,
      error: directory.error,
    }
  }

  const rootDirectory = buildDirectoryNode(localBrowser.rootPath)
  if (!rootDirectory) {
    return null
  }

  return {
    id: 'local',
    name: 'local',
    path: 'local',
    kind: 'directory',
    children: [rootDirectory],
    source: 'local',
  }
}

function describeFile(file: WorkbenchFile | null) {
  if (!file) {
    return 'Choose a file or create a desktop document.'
  }

  if (file.source === 'local') {
    return 'Connected local file'
  }

  if (file.source === 'user') {
    return 'Desktop document'
  }

  return 'Platform system file'
}

function useWorkbenchTheme() {
  const [theme, setTheme] = useState<'vs-dark' | 'vs-light'>(() =>
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark') ? 'vs-dark' : 'vs-light'
  )

  useEffect(() => {
    if (typeof document === 'undefined') {
      return
    }

    const root = document.documentElement
    const observer = new MutationObserver(() => {
      setTheme(root.classList.contains('dark') ? 'vs-dark' : 'vs-light')
    })

    observer.observe(root, {
      attributes: true,
      attributeFilter: ['class'],
    })

    return () => observer.disconnect()
  }, [])

  return theme
}

interface DesktopWorkbenchProps {
  surface: DesktopToolSurface | null
  onClose: () => void
  onOpenSurface: (surface: DesktopToolSurface) => void
}

export function DesktopWorkbench({ surface, onClose, onOpenSurface }: DesktopWorkbenchProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const theme = useWorkbenchTheme()
  const shortcutOrder = useSystemStore((state) => state.shortcutOrder)
  const documents = useWorkbenchStore((state) => state.documents)
  const createDocument = useWorkbenchStore((state) => state.createDocument)
  const updateDocument = useWorkbenchStore((state) => state.updateDocument)
  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query.trim().toLowerCase())
  const [expandedPaths, setExpandedPaths] = useState<string[]>(['documents', 'platform', 'system'])
  const [localBrowser, setLocalBrowser] = useState<LocalBrowserState>(EMPTY_LOCAL_BROWSER_STATE)
  const [localFileContents, setLocalFileContents] = useState<Record<string, string>>({})
  const [openFileIds, setOpenFileIds] = useState<string[]>([])
  const [activeFileId, setActiveFileId] = useState<string | null>(null)
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [isScanningLocalFolder, setIsScanningLocalFolder] = useState(false)
  const [localFolderError, setLocalFolderError] = useState<string | null>(null)
  const localBrowserRef = useRef<LocalBrowserState>(EMPTY_LOCAL_BROWSER_STATE)
  const localBrowserRequestRef = useRef(0)
  const [runtimeSnapshot, setRuntimeSnapshot] = useState(() => ({
    online: typeof navigator !== 'undefined' ? navigator.onLine : true,
    language: typeof navigator !== 'undefined' ? navigator.language : 'en-US',
    platform: typeof navigator !== 'undefined' ? navigator.platform : 'unknown',
    viewport: {
      width: typeof window !== 'undefined' ? window.innerWidth : 0,
      height: typeof window !== 'undefined' ? window.innerHeight : 0,
    },
  }))

  useEffect(() => {
    const updateRuntimeSnapshot = () => {
      setRuntimeSnapshot({
        online: navigator.onLine,
        language: navigator.language,
        platform: navigator.platform,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
      })
    }

    updateRuntimeSnapshot()
    window.addEventListener('resize', updateRuntimeSnapshot)
    window.addEventListener('online', updateRuntimeSnapshot)
    window.addEventListener('offline', updateRuntimeSnapshot)

    return () => {
      window.removeEventListener('resize', updateRuntimeSnapshot)
      window.removeEventListener('online', updateRuntimeSnapshot)
      window.removeEventListener('offline', updateRuntimeSnapshot)
    }
  }, [])

  useEffect(() => {
    localBrowserRef.current = localBrowser
  }, [localBrowser])

  useEffect(() => {
    return () => {
      localBrowserRequestRef.current += 1
    }
  }, [])

  const documentFiles = useMemo<WorkbenchFile[]>(() => {
    return Object.values(documents)
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
      .map((document) => ({
        id: document.id,
        name: document.name,
        path: document.path,
        language: document.language,
        content: document.content,
        source: 'user',
        editable: true,
        updatedAt: document.updatedAt,
      }))
  }, [documents])

  const virtualFiles = useMemo<WorkbenchFile[]>(() => {
    const workspaceFiles = workspaces.map((workspace) => ({
      id: `virtual:workspace:${workspace.id}`,
      name: `${workspace.id}.workspace.json`,
      path: `platform/workspaces/${workspace.id}.workspace.json`,
      language: 'json',
      content: JSON.stringify(workspace, null, 2),
      source: 'virtual' as const,
      editable: false,
      route: workspace.landingRoute,
    }))

    const moduleFiles = workspaceModules.map((module) => ({
      id: `virtual:module:${module.id}`,
      name: `${module.id}.module.json`,
      path: `platform/modules/${module.id}.module.json`,
      language: 'json',
      content: JSON.stringify(module, null, 2),
      source: 'virtual' as const,
      editable: false,
      route: module.route,
    }))

    const divisionFiles = divisions.map((division) => ({
      id: `virtual:division:${division.id}`,
      name: `${division.id}.division.json`,
      path: `platform/divisions/${division.id}.division.json`,
      language: 'json',
      content: JSON.stringify(division, null, 2),
      source: 'virtual' as const,
      editable: false,
      route: division.route,
    }))

    const systemFiles: WorkbenchFile[] = [
      {
        id: 'virtual:system:runtime',
        name: 'desktop-runtime.json',
        path: 'system/runtime/desktop-runtime.json',
        language: 'json',
        content: JSON.stringify(
          {
            route: location.pathname,
            online: runtimeSnapshot.online,
            language: runtimeSnapshot.language,
            platform: runtimeSnapshot.platform,
            viewport: runtimeSnapshot.viewport,
            timestamp: new Date().toISOString(),
          },
          null,
          2
        ),
        source: 'virtual',
        editable: false,
      },
      {
        id: 'virtual:system:shortcuts',
        name: 'desktop-shortcuts.json',
        path: 'system/desktop/desktop-shortcuts.json',
        language: 'json',
        content: JSON.stringify(
          {
            shortcutOrder,
            shortcutCount: shortcutOrder.length,
          },
          null,
          2
        ),
        source: 'virtual',
        editable: false,
      },
      {
        id: 'virtual:system:navigation',
        name: 'workspace-routes.json',
        path: 'system/navigation/workspace-routes.json',
        language: 'json',
        content: JSON.stringify(
          workspaceModules.map((module) => ({
            id: module.id,
            route: module.route,
            pageCount: module.pages.length,
            pages: module.pages.map((page) => page.route),
          })),
          null,
          2
        ),
        source: 'virtual',
        editable: false,
      },
    ]

    return [...workspaceFiles, ...moduleFiles, ...divisionFiles, ...systemFiles]
  }, [location.pathname, runtimeSnapshot, shortcutOrder])

  const localFiles = useMemo<WorkbenchFile[]>(() => {
    return Object.values(localBrowser.files).map((entry) => ({
      ...entry,
      content: localFileContents[entry.id] ?? '',
    }))
  }, [localBrowser.files, localFileContents])

  const baseFiles = useMemo(() => [...documentFiles, ...virtualFiles], [documentFiles, virtualFiles])
  const files = useMemo(() => [...baseFiles, ...localFiles], [baseFiles, localFiles])
  const fileMap = useMemo(() => new Map(files.map((file) => [file.id, file])), [files])
  const localExplorerTree = useMemo(() => buildLocalExplorerTree(localBrowser), [localBrowser])
  const tree = useMemo(() => {
    const combinedRoots = localExplorerTree ? [localExplorerTree, ...buildTree(baseFiles)] : buildTree(baseFiles)
    return filterTree(combinedRoots, deferredQuery)
  }, [baseFiles, deferredQuery, localExplorerTree])
  const activeFile = activeFileId ? fileMap.get(activeFileId) ?? null : null
  const editorValue = activeFile ? drafts[activeFile.id] ?? activeFile.content : ''
  const isDirty = activeFile ? drafts[activeFile.id] !== undefined && drafts[activeFile.id] !== activeFile.content : false
  const canUseDirectoryPicker = typeof window !== 'undefined' && typeof (window as DirectoryPickerWindow).showDirectoryPicker === 'function'
  const isExplorerSurface = surface === 'filesystem'
  const isEditorSurface = surface === 'editor'

  useEffect(() => {
    if (files.length === 0 || activeFileId) {
      return
    }

    const defaultFile = files.find((file) => file.id === 'virtual:system:runtime') ?? files[0]
    setOpenFileIds([defaultFile.id])
    setActiveFileId(defaultFile.id)
  }, [activeFileId, files])

  const toggleExpanded = (path: string) => {
    setExpandedPaths((current) =>
      current.includes(path) ? current.filter((value) => value !== path) : [...current, path]
    )
  }

  const expandLocalDirectory = async (directoryPath: string, requestToken = localBrowserRequestRef.current) => {
    const directory = localBrowserRef.current.directories[directoryPath]
    const rootName = localBrowserRef.current.rootName

    if (!directory || !rootName || directory.loaded || directory.loading) {
      return
    }

    setLocalBrowser((current) => {
      const target = current.directories[directoryPath]
      if (!target) {
        return current
      }

      return {
        ...current,
        directories: {
          ...current.directories,
          [directoryPath]: {
            ...target,
            loading: true,
            error: null,
          },
        },
      }
    })

    try {
      const result = await readDirectoryLevel(directory.handle, rootName, directory.relativePath)
      if (requestToken !== localBrowserRequestRef.current) {
        return
      }

      setLocalBrowser((current) => {
        const target = current.directories[directoryPath]
        if (!target) {
          return current
        }

        const nextDirectories = { ...current.directories }
        for (const childDirectory of result.directories) {
          const existing = nextDirectories[childDirectory.path]
          nextDirectories[childDirectory.path] = existing ?? {
            id: childDirectory.id,
            name: childDirectory.name,
            path: childDirectory.path,
            relativePath: childDirectory.relativePath,
            handle: childDirectory.handle,
            loaded: false,
            loading: false,
            error: null,
            childDirectoryPaths: [],
            childFileIds: [],
          }
        }

        nextDirectories[directoryPath] = {
          ...target,
          loaded: true,
          loading: false,
          error: null,
          childDirectoryPaths: result.directories.map((childDirectory) => childDirectory.path),
          childFileIds: result.files.map((file) => file.id),
        }

        const nextFiles = { ...current.files }
        for (const file of result.files) {
          nextFiles[file.id] = file
        }

        return {
          ...current,
          directories: nextDirectories,
          files: nextFiles,
          loadedFileCount: Object.keys(nextFiles).length,
          skippedDirectoryCount: current.skippedDirectoryCount + result.skippedDirectoryCount,
        }
      })
    } catch (error) {
      if (requestToken !== localBrowserRequestRef.current) {
        return
      }

      setLocalBrowser((current) => {
        const target = current.directories[directoryPath]
        if (!target) {
          return current
        }

        return {
          ...current,
          directories: {
            ...current.directories,
            [directoryPath]: {
              ...target,
              loading: false,
              error: error instanceof Error ? error.message : 'Unable to load this folder',
            },
          },
        }
      })
    }
  }

  const openFile = async (fileId: string) => {
    const file = fileMap.get(fileId)
    if (!file) {
      return
    }

    if (file.source === 'local' && file.handle && localFileContents[file.id] === undefined) {
      const localFile = await file.handle.getFile()
      const text = await localFile.text()
      setLocalFileContents((current) => ({
        ...current,
        [file.id]: text,
      }))
    }

    setOpenFileIds((current) => (current.includes(file.id) ? current : [...current, file.id]))
    setActiveFileId(file.id)
  }

  const closeTab = (fileId: string) => {
    setOpenFileIds((current) => {
      const next = current.filter((value) => value !== fileId)

      if (fileId === activeFileId) {
        setActiveFileId(next.length > 0 ? next[next.length - 1] : null)
      }

      return next
    })
  }

  const handleCreateDocument = () => {
    const document = createDocument()
    setExpandedPaths((current) => (current.includes('documents') ? current : [...current, 'documents']))
    setOpenFileIds((current) => [...current, document.id])
    setActiveFileId(document.id)
  }

  const handleSave = async () => {
    if (!activeFile || !isDirty) {
      return
    }

    const nextContent = drafts[activeFile.id] ?? activeFile.content

    if (activeFile.source === 'user') {
      updateDocument(activeFile.id, nextContent)
      setDrafts((current) => {
        const { [activeFile.id]: _removed, ...remaining } = current
        return remaining
      })
      return
    }

    if (activeFile.source === 'local' && activeFile.handle?.createWritable) {
      const writer = await activeFile.handle.createWritable()
      await writer.write(nextContent)
      await writer.close()
      setLocalFileContents((current) => ({
        ...current,
        [activeFile.id]: nextContent,
      }))
      setDrafts((current) => {
        const { [activeFile.id]: _removed, ...remaining } = current
        return remaining
      })
    }
  }

  const connectLocalFolder = async () => {
    const pickerWindow = window as DirectoryPickerWindow
    if (!pickerWindow.showDirectoryPicker) {
      return
    }

    setIsScanningLocalFolder(true)
    setLocalFolderError(null)

    try {
      const directoryHandle = await pickerWindow.showDirectoryPicker()
      const requestToken = localBrowserRequestRef.current + 1
      localBrowserRequestRef.current = requestToken

      const rootPath = makeLocalDirectoryPath(directoryHandle.name)
      const rootDirectory: LocalDirectoryEntry = {
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

      setLocalBrowser({
        rootName: directoryHandle.name,
        rootPath,
        directories: { [rootPath]: rootDirectory },
        files: {},
        loadedFileCount: 0,
        skippedDirectoryCount: 0,
      })
      setExpandedPaths((current) => Array.from(new Set([...current.filter((path) => path === 'documents' || path === 'platform' || path === 'system'), 'local', rootPath])))
      await expandLocalDirectory(rootPath, requestToken)
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }

      setLocalFolderError(error instanceof Error ? error.message : 'Unable to connect local folder')
      setLocalBrowser(EMPTY_LOCAL_BROWSER_STATE)
    } finally {
      setIsScanningLocalFolder(false)
    }
  }

  const renderNode = (node: ExplorerNode, depth = 0) => {
    if (node.kind === 'file') {
      const file = node.fileId ? fileMap.get(node.fileId) ?? null : null
      const Icon = getFileIcon(node.name)
      const isActive = file?.id === activeFileId

      return (
        <button
          key={node.id}
          type="button"
          onClick={() => node.fileId && void openFile(node.fileId)}
          className={cn(
            'flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm transition',
            isActive
              ? 'bg-emerald-500/15 text-emerald-100 ring-1 ring-emerald-400/30 dark:text-emerald-100'
              : 'text-slate-200/80 hover:bg-white/8 hover:text-white'
          )}
          style={{ paddingLeft: `${depth * 14 + 12}px` }}
        >
          <Icon className="h-4 w-4 shrink-0 text-emerald-300/80" />
          <span className="truncate">{node.name}</span>
        </button>
      )
    }

    const isExpanded = deferredQuery ? true : expandedPaths.includes(node.path)
    const isLazyLocalDirectory = node.source === 'local' && node.path !== 'local'

    return (
      <div key={node.id}>
        <button
          type="button"
          onClick={() => {
            const shouldExpand = deferredQuery ? true : !expandedPaths.includes(node.path)
            toggleExpanded(node.path)
            if (isLazyLocalDirectory && shouldExpand && node.unloaded) {
              void expandLocalDirectory(node.path)
            }
          }}
          className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-slate-100 transition hover:bg-white/8"
          style={{ paddingLeft: `${depth * 14 + 12}px` }}
        >
          {isExpanded ? <ChevronDown className="h-4 w-4 shrink-0 text-slate-400" /> : <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" />}
          {isExpanded ? <FolderOpen className="h-4 w-4 shrink-0 text-amber-300" /> : <Folder className="h-4 w-4 shrink-0 text-amber-300" />}
          <span className="truncate">{node.name}</span>
          {node.loading && <LoaderCircle className="h-3.5 w-3.5 shrink-0 animate-spin text-slate-400" />}
        </button>
        {isExpanded && node.children?.map((child) => renderNode(child, depth + 1))}
        {isExpanded && node.error && (
          <div className="px-3 py-1 text-xs text-rose-300" style={{ paddingLeft: `${depth * 14 + 26}px` }}>
            {node.error}
          </div>
        )}
      </div>
    )
  }

  if (!surface) {
    return null
  }

  const previewContent = activeFile ? editorValue : ''

  return (
    <section className="absolute inset-0 z-20 flex min-h-0 items-stretch justify-center bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.18),transparent_48%),rgba(7,18,25,0.16)] p-4 backdrop-blur-[10px] sm:p-6">
      <div
        className={cn(
          'shadow-shell border-shell flex h-full w-full min-h-0 overflow-hidden rounded-[32px] border bg-[hsl(var(--app-shell-panel)/0.94)]',
          isExplorerSurface ? 'max-w-6xl' : 'max-w-[1500px]'
        )}
      >
        <aside className="bg-[linear-gradient(180deg,rgba(7,18,25,0.94),rgba(8,16,24,0.82))] border-shell flex min-h-0 w-[320px] shrink-0 flex-col border-r backdrop-blur-xl">
          <div className="border-shell flex items-start justify-between gap-3 border-b px-4 py-4">
            <div>
              <p className="text-[10px] uppercase tracking-[0.38em] text-slate-400">
                {isExplorerSurface ? 'Files' : 'Editor'}
              </p>
              <h2 className="mt-1 text-lg font-semibold text-white">
                {isExplorerSurface ? 'File System' : 'Editor'}
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                {isExplorerSurface
                  ? 'Browse files and connected folders.'
                  : 'Edit the selected file.'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleCreateDocument}
                className="rounded-full border border-emerald-400/35 bg-emerald-400/12 p-2 text-emerald-100 transition hover:bg-emerald-400/18"
                aria-label="Create desktop document"
              >
                <Plus className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full border border-white/12 bg-white/8 p-2 text-slate-200 transition hover:bg-white/14"
                aria-label="Close desktop tool"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="border-shell border-b px-4 py-3">
            <label className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/6 px-3 py-2 text-sm text-slate-200">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Filter files, workspaces, system"
                className="w-full bg-transparent outline-none placeholder:text-slate-500"
              />
            </label>
          </div>

          <div className="border-shell border-b px-4 py-3">
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => void connectLocalFolder()}
                disabled={!canUseDirectoryPicker || isScanningLocalFolder}
                className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/8 px-3 py-2 text-xs font-medium text-slate-100 transition hover:bg-white/12 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isScanningLocalFolder ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : <HardDrive className="h-3.5 w-3.5" />}
                {localBrowser.rootName ? 'Reconnect Folder' : 'Connect Local Folder'}
              </button>

              {localBrowser.rootName && (
                <button
                  type="button"
                  onClick={() => void connectLocalFolder()}
                  className="inline-flex items-center gap-2 rounded-full border border-white/12 px-3 py-2 text-xs text-slate-300 transition hover:bg-white/8"
                >
                  <RefreshCcw className="h-3.5 w-3.5" />
                  Refresh
                </button>
              )}
            </div>
            <p className="mt-2 text-xs text-slate-400">
              {canUseDirectoryPicker
                ? localBrowser.rootName
                  ? `Local workspace attached: ${localBrowser.rootName}`
                  : 'Attach a local folder to inspect and work with real files when needed.'
                : 'Local folder attachment depends on the File System Access API and is not available in this browser.'}
            </p>
            {localBrowser.rootName && (
              <p className="mt-2 text-xs text-slate-400">
                Loaded {localBrowser.loadedFileCount} files from expanded directories
                {localBrowser.skippedDirectoryCount > 0 ? `, skipped ${localBrowser.skippedDirectoryCount} heavy directories` : ''}.
                {deferredQuery ? ' Local search covers loaded directories only.' : ''}
              </p>
            )}
            {localFolderError && <p className="mt-2 text-xs text-rose-300">{localFolderError}</p>}
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto px-2 py-3">
            {tree.length === 0 ? (
              <div className="px-3 py-8 text-sm text-slate-400">No explorer entries match the current filter.</div>
            ) : (
              tree.map((node) => renderNode(node))
            )}
          </div>
        </aside>

        <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <div className="border-shell flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
            <div>
              <p className="text-[10px] uppercase tracking-[0.34em] text-shell-muted">
                {isExplorerSurface ? 'Browser' : 'Editor'}
              </p>
              <h2 className="mt-1 text-lg font-semibold text-shell">
                {isExplorerSurface ? 'Files' : activeFile?.name ?? 'Editor'}
              </h2>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {isExplorerSurface ? (
                <button
                  type="button"
                  onClick={() => onOpenSurface('editor')}
                  className="inline-flex items-center gap-2 rounded-full border border-emerald-300/60 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100 dark:border-emerald-700/60 dark:bg-emerald-900/25 dark:text-emerald-200 dark:hover:bg-emerald-900/40"
                >
                  <FileCode2 className="h-3.5 w-3.5" />
                  Open Editor
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => onOpenSurface('filesystem')}
                  className="inline-flex items-center gap-2 rounded-full border border-slate-200/70 px-3 py-2 text-xs font-medium text-shell transition hover:border-emerald-300 hover:text-emerald-700 dark:border-slate-700 dark:hover:border-emerald-600 dark:hover:text-emerald-200"
                >
                  <HardDrive className="h-3.5 w-3.5" />
                  File System
                </button>
              )}

              {activeFile?.route && (
                <button
                  type="button"
                  onClick={() => navigate(activeFile.route ?? '/dashboard')}
                  className="inline-flex items-center gap-2 rounded-full border border-slate-200/70 px-3 py-2 text-xs font-medium text-shell transition hover:border-emerald-300 hover:text-emerald-700 dark:border-slate-700 dark:hover:border-emerald-600 dark:hover:text-emerald-200"
                >
                  <Route className="h-3.5 w-3.5" />
                  Open Route
                </button>
              )}

              {isEditorSurface && (
                <button
                  type="button"
                  onClick={() => void handleSave()}
                  disabled={!activeFile?.editable || !isDirty}
                  className="inline-flex items-center gap-2 rounded-full border border-emerald-300/60 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-emerald-700/60 dark:bg-emerald-900/25 dark:text-emerald-200 dark:hover:bg-emerald-900/40"
                >
                  <Save className="h-3.5 w-3.5" />
                  Save
                </button>
              )}
            </div>
          </div>

          {isEditorSurface && (
            <div className="border-shell flex gap-2 overflow-x-auto border-b px-3 py-2">
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
                      'flex items-center gap-2 rounded-2xl border px-3 py-2 text-sm transition',
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

          {isExplorerSurface ? (
            <div className="grid min-h-0 flex-1 gap-0 xl:grid-cols-[minmax(0,1fr)_280px]">
              <div className="min-h-0 overflow-y-auto p-5">
                {activeFile ? (
                  <div className="flex h-full flex-col gap-4">
                    <div className="rounded-[28px] border border-slate-200/70 bg-white/80 p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950/50">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="text-[10px] uppercase tracking-[0.3em] text-shell-muted">Selected File</p>
                          <h3 className="mt-2 text-xl font-semibold text-shell">{activeFile.name}</h3>
                          <p className="mt-2 break-all text-sm text-shell-muted">{activeFile.path}</p>
                        </div>
                        <div className="rounded-full border border-slate-200/70 px-3 py-1 text-xs font-medium text-shell-muted dark:border-slate-700">
                          {describeFile(activeFile)}
                        </div>
                      </div>
                    </div>

                    <div className="min-h-0 flex-1 rounded-[28px] border border-slate-200/70 bg-slate-950 p-4 text-slate-100 shadow-sm dark:border-slate-800">
                      <div className="mb-3 flex items-center justify-between gap-3 text-xs uppercase tracking-[0.26em] text-slate-400">
                        <span>Preview</span>
                        <span>{activeFile.language}</span>
                      </div>
                      <pre className="h-full min-h-[18rem] overflow-auto whitespace-pre-wrap break-words text-sm leading-6 text-slate-200">
                        {previewContent.slice(0, 8000) || 'Empty file'}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <div className="flex h-full min-h-[24rem] flex-col items-center justify-center gap-4 text-shell-muted">
                    <HardDrive className="h-10 w-10 opacity-70" />
                    <div className="text-center">
                      <p className="text-base font-medium text-shell">No file selected</p>
                      <p className="mt-1 text-sm">Choose a platform file, connect a local folder, or create a desktop document.</p>
                    </div>
                  </div>
                )}
              </div>

              <aside className="bg-shell-muted/30 border-shell flex min-h-[14rem] flex-col gap-4 border-t px-4 py-4 xl:border-l xl:border-t-0">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.34em] text-shell-muted">Inspector</p>
                  <h3 className="mt-1 text-base font-semibold text-shell">{activeFile?.name ?? 'Filesystem State'}</h3>
                </div>

                <div className="space-y-3 text-sm text-shell-muted">
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.28em]">Source</div>
                    <div className="mt-1 text-shell">{describeFile(activeFile)}</div>
                  </div>

                  <div>
                    <div className="text-[10px] uppercase tracking-[0.28em]">Path</div>
                    <div className="mt-1 break-all text-shell">{activeFile?.path ?? '/desktop'}</div>
                  </div>

                  <div>
                    <div className="text-[10px] uppercase tracking-[0.28em]">Language</div>
                    <div className="mt-1 text-shell">{activeFile?.language ?? 'n/a'}</div>
                  </div>

                  <div>
                    <div className="text-[10px] uppercase tracking-[0.28em]">Edit Mode</div>
                    <div className="mt-1 text-shell">{activeFile ? (activeFile.editable ? 'Writable' : 'Read only') : 'Idle'}</div>
                  </div>
                </div>

                <div className="mt-auto rounded-3xl border border-slate-200/70 bg-white/70 p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-300">
                  <p className="font-medium text-shell">Desktop Capabilities</p>
                  <p className="mt-2">
                    Explorer data is backed by live platform registries and desktop state. Open the editor only when you need to make changes.
                  </p>
                </div>
              </aside>
            </div>
          ) : (
            <div className="grid min-h-0 flex-1 gap-0 xl:grid-cols-[minmax(0,1fr)_260px]">
              <div className="min-h-0 border-b border-shell xl:border-b-0 xl:border-r">
                {activeFile ? (
                  <Suspense
                    fallback={
                      <div className="flex h-full min-h-[24rem] items-center justify-center gap-3 text-shell-muted">
                        <LoaderCircle className="h-5 w-5 animate-spin" />
                        Loading editor...
                      </div>
                    }
                  >
                    <MonacoEditor
                      height="100%"
                      language={activeFile.language}
                      theme={theme}
                      value={editorValue}
                      onChange={(value) => {
                        setDrafts((current) => ({
                          ...current,
                          [activeFile.id]: value ?? '',
                        }))
                      }}
                      options={{
                        fontSize: 13,
                        fontFamily: 'JetBrains Mono, Fira Code, SF Mono, Monaco, monospace',
                        minimap: { enabled: true },
                        smoothScrolling: true,
                        wordWrap: 'on',
                        readOnly: !activeFile.editable,
                        automaticLayout: true,
                        padding: { top: 16, bottom: 16 },
                        scrollBeyondLastLine: false,
                      }}
                    />
                  </Suspense>
                ) : (
                  <div className="flex h-full min-h-[24rem] flex-col items-center justify-center gap-4 text-shell-muted">
                    <NotebookPen className="h-10 w-10 opacity-70" />
                    <div className="text-center">
                      <p className="text-base font-medium text-shell">No file selected</p>
                      <p className="mt-1 text-sm">Choose a file from the File System or create a desktop document to start editing.</p>
                    </div>
                    <div className="flex flex-wrap justify-center gap-2">
                      <button
                        type="button"
                        onClick={() => onOpenSurface('filesystem')}
                        className="inline-flex items-center gap-2 rounded-full border border-slate-200/70 px-3 py-2 text-xs font-medium text-shell transition hover:border-emerald-300 hover:text-emerald-700 dark:border-slate-700 dark:hover:border-emerald-600 dark:hover:text-emerald-200"
                      >
                        <HardDrive className="h-3.5 w-3.5" />
                        Browse File System
                      </button>
                      <button
                        type="button"
                        onClick={handleCreateDocument}
                        className="inline-flex items-center gap-2 rounded-full border border-emerald-300/60 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100 dark:border-emerald-700/60 dark:bg-emerald-900/25 dark:text-emerald-200 dark:hover:bg-emerald-900/40"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        New Desktop Document
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <aside className="bg-shell-muted/30 border-shell flex min-h-[14rem] flex-col gap-4 px-4 py-4">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.34em] text-shell-muted">Inspector</p>
                  <h3 className="mt-1 text-base font-semibold text-shell">{activeFile?.name ?? 'Editor State'}</h3>
                </div>

                <div className="space-y-3 text-sm text-shell-muted">
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.28em]">Source</div>
                    <div className="mt-1 text-shell">{describeFile(activeFile)}</div>
                  </div>

                  <div>
                    <div className="text-[10px] uppercase tracking-[0.28em]">Path</div>
                    <div className="mt-1 break-all text-shell">{activeFile?.path ?? '/desktop'}</div>
                  </div>

                  <div>
                    <div className="text-[10px] uppercase tracking-[0.28em]">Language</div>
                    <div className="mt-1 text-shell">{activeFile?.language ?? 'n/a'}</div>
                  </div>

                  <div>
                    <div className="text-[10px] uppercase tracking-[0.28em]">Edit Mode</div>
                    <div className="mt-1 text-shell">{activeFile ? (activeFile.editable ? 'Writable' : 'Read only') : 'Idle'}</div>
                  </div>

                  {activeFile?.updatedAt && (
                    <div>
                      <div className="text-[10px] uppercase tracking-[0.28em]">Updated</div>
                      <div className="mt-1 text-shell">{new Date(activeFile.updatedAt).toLocaleString()}</div>
                    </div>
                  )}
                </div>

                <div className="mt-auto rounded-3xl border border-slate-200/70 bg-white/70 p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-300">
                  <p className="font-medium text-shell">Desktop Capabilities</p>
                  <p className="mt-2">
                    The editor stays off the desktop until requested. Your active file, route context, and desktop documents stay available inside this surface.
                  </p>
                </div>
              </aside>
            </div>
          )}

          <div className="border-shell bg-shell-chrome flex items-center justify-between gap-3 border-t px-4 py-2 text-xs text-shell-muted">
            <div className="flex items-center gap-3">
              <span>{activeFile?.path ?? '/desktop'}</span>
              <span>{activeFile?.source ?? 'system'}</span>
            </div>
            <div className="flex items-center gap-3">
              <span>{runtimeSnapshot.online ? 'Online' : 'Offline'}</span>
              <span>
                {localBrowser.loadedFileCount} local files loaded
              </span>
              <span>{Object.keys(documents).length} desktop docs</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}