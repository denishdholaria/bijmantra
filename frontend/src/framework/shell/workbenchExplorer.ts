/**
 * Workbench Explorer Helpers
 * Extracted from DesktopWorkbench.tsx — handles explorer tree building,
 * filtering, node flattening, and editor mode resolution.
 */

import { FileCode2, FileJson2, FileText } from 'lucide-react'
import type {
  WorkbenchFile, ExplorerNode, ExplorerVisibleNode,
  LocalBrowserState, EditorViewMode, WorkbenchDensity,
  WorkbenchSessionState, FileSaveState,
} from './workbenchTypes'
import {
  WORKBENCH_DENSITY_STORAGE_KEY,
  WORKBENCH_EXPLORER_COLLAPSED_STORAGE_KEY,
  WORKBENCH_SESSION_STORAGE_KEY,
} from './workbenchTypes'

// ── Editor View Mode Helpers ──

export function isEditorViewMode(value: unknown): value is EditorViewMode {
  return value === 'prose' || value === 'raw' || value === 'table'
}

export function getPreferredEditorViewMode(file: WorkbenchFile | null): EditorViewMode {
  if (!file) return 'raw'
  if (file.documentType === 'prose' || (file as any).type === 'prose') return 'prose'
  if (file.documentType === 'table' || (file as any).type === 'table') return 'table'
  return 'raw'
}

export function getAvailableEditorViewModes(file: WorkbenchFile | null): EditorViewMode[] {
  if (!file) return ['raw']
  if (file.documentType === 'prose' || (file as any).type === 'prose') return ['prose', 'raw']
  if (file.documentType === 'table' || (file as any).type === 'table') return ['table', 'raw']
  if (file.language === 'json') return ['raw']
  return ['raw']
}

export function getEditorViewModeLabel(mode: EditorViewMode) {
  switch (mode) {
    case 'prose': return 'Write'
    case 'table': return 'Table'
    default: return 'Raw'
  }
}

export function getEditorViewModeDescription(mode: EditorViewMode) {
  switch (mode) {
    case 'prose': return 'Markdown writing surface'
    case 'table': return 'Structured table workspace'
    default: return 'Monaco raw editor'
  }
}

// ── Session Persistence Helpers ──

export function getInitialWorkbenchDensity(): WorkbenchDensity {
  if (typeof window === 'undefined') return 'compact'
  const storedDensity = window.localStorage.getItem(WORKBENCH_DENSITY_STORAGE_KEY)
  return storedDensity === 'comfortable' ? 'comfortable' : 'compact'
}

export function getInitialWorkbenchExplorerCollapsed() {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(WORKBENCH_EXPLORER_COLLAPSED_STORAGE_KEY) === 'true'
}

export function getInitialWorkbenchSession(): WorkbenchSessionState {
  const defaultState: WorkbenchSessionState = {
    openFileIds: [], activeFileId: null,
    expandedPaths: ['documents', 'platform', 'system'],
    editorViewMode: 'raw',
  }
  if (typeof window === 'undefined') return defaultState
  try {
    const rawValue = window.localStorage.getItem(WORKBENCH_SESSION_STORAGE_KEY)
    if (!rawValue) return defaultState
    const parsedValue = JSON.parse(rawValue) as Partial<WorkbenchSessionState>
    return {
      openFileIds: Array.isArray(parsedValue.openFileIds)
        ? parsedValue.openFileIds.filter((value): value is string => typeof value === 'string')
        : defaultState.openFileIds,
      activeFileId: typeof parsedValue.activeFileId === 'string' ? parsedValue.activeFileId : defaultState.activeFileId,
      expandedPaths:
        Array.isArray(parsedValue.expandedPaths) && parsedValue.expandedPaths.length > 0
          ? parsedValue.expandedPaths.filter((value): value is string => typeof value === 'string')
          : defaultState.expandedPaths,
      editorViewMode: isEditorViewMode(parsedValue.editorViewMode) ? parsedValue.editorViewMode : defaultState.editorViewMode,
    }
  } catch {
    return defaultState
  }
}

// ── File Icon Helper ──

export function getFileIcon(path: string) {
  const extension = path.split('.').pop()?.toLowerCase()
  if (extension === 'json' || extension === 'yaml' || extension === 'yml') return FileJson2
  if (extension === 'ts' || extension === 'tsx' || extension === 'js' || extension === 'jsx' || extension === 'py') return FileCode2
  return FileText
}

// ── Explorer Tree Builders ──


export function buildTree(
  documents: Record<string, any>,
  localBrowser: LocalBrowserState,
  expandedPaths: string[],
  localFileContents: Record<string, string>
): ExplorerNode[] {
  const tree: ExplorerNode[] = []

  const documentsRoot: ExplorerNode = {
    id: 'documents',
    name: 'Desktop docs',
    path: 'documents',
    kind: 'directory',
    source: 'default',
    children: [],
  }
  tree.push(documentsRoot)

  const documentFiles = Object.values(documents).sort((a, b) => a.name.localeCompare(b.name))
  for (const doc of documentFiles) {
    documentsRoot.children!.push({
      id: doc.path,
      name: doc.name,
      path: doc.path,
      kind: 'file',
      source: 'default',
      fileId: doc.id,
    })
  }

  if (localBrowser.rootName && localBrowser.rootPath) {
    const localRootNode = buildLocalExplorerTree(localBrowser)
    if (localRootNode) {
      tree.push(localRootNode)
    }
  }

  return tree
}

export function filterTree(nodes: ExplorerNode[], query: string): ExplorerNode[] {
  if (!query) return nodes
  return nodes
    .map((node) => {
      if (node.kind === 'file') return node.name.toLowerCase().includes(query) ? node : null
      const children = filterTree(node.children ?? [], query)
      if (node.name.toLowerCase().includes(query) || children.length > 0) return { ...node, children }
      return null
    })
    .filter((node): node is ExplorerNode => node !== null)
}

export function flattenVisibleTreeNodes(
  nodes: ExplorerNode[], expandedPaths: string[], forceExpanded: boolean,
  depth = 1, parentId: string | null = null, items: ExplorerVisibleNode[] = [],
) {
  for (const node of nodes) {
    const isExpanded = node.kind === 'directory' ? forceExpanded || expandedPaths.includes(node.path) : false
    items.push({ id: node.id, node, depth, isExpanded, parentId })
    if (node.kind === 'directory' && isExpanded && node.children) {
      flattenVisibleTreeNodes(node.children, expandedPaths, forceExpanded, depth + 1, node.id, items)
    }
  }
  return items
}

export function buildLocalExplorerTree(localBrowser: LocalBrowserState): ExplorerNode | null {
  if (!localBrowser.rootPath || !localBrowser.rootName) return null
  const buildDirectoryNode = (directoryPath: string): ExplorerNode | null => {
    const directory = localBrowser.directories[directoryPath]
    if (!directory) return null
    const childDirectories = (directory.childDirectoryPaths || [])
      .map((childPath) => buildDirectoryNode(childPath))
      .filter((node): node is ExplorerNode => node !== null)
    const childFiles: ExplorerNode[] = []
    for (const fileId of (directory.childFileIds || [])) {
      const file = localBrowser.files[fileId]
      if (!file) continue
      childFiles.push({ id: file.path, name: file.name, path: file.path, kind: 'file', fileId: file.id, source: 'local' })
    }
    const children = [...childDirectories, ...childFiles].sort((left, right) => {
      if (left.kind !== right.kind) return left.kind === 'directory' ? -1 : 1
      return left.name.localeCompare(right.name)
    })
    return {
      id: directory.path, name: directory.name, path: directory.path,
      kind: 'directory', children, source: 'local',
      loading: directory.loading, unloaded: !directory.loaded, error: directory.error,
    }
  }
  const rootDirectory = buildDirectoryNode(localBrowser.rootPath)
  if (!rootDirectory) return null
  return { id: 'local', name: 'local', path: 'local', kind: 'directory', children: [rootDirectory], source: 'local' }
}

export function describeFile(file: WorkbenchFile | null) {
  if (!file) return 'Choose a file or create a desktop document.'
  if (file.source === 'local') {
    return (file.documentType === 'table' || (file as any).type === 'table') ? 'Connected local table'
      : (file.documentType === 'prose' || (file as any).type === 'prose') ? 'Connected local document' : 'Connected local file'
  }
  if (file.source === 'user') {
    return (file.documentType === 'table' || (file as any).type === 'table') ? 'Desktop table' : 'Desktop document'
  }
  return 'Internal platform file'
}
