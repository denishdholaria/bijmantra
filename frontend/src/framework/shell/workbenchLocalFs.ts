/**
 * Workbench Local File System Helpers
 * Extracted from DesktopWorkbench.tsx — handles local directory scanning,
 * file entry construction, and scan budgeting logic.
 */

import { inferWorkbenchDocumentType } from '@/lib/workbenchDocuments'
import {
  type FileSystemDirectoryHandleLike,
  type FileSystemFileHandleLike,
  type LocalFileEntry,
  type LocalFolderScanState,
  type LocalFolderScanSummary,
  MAX_INDEXED_LOCAL_FILES,
  MAX_PROCESSED_LOCAL_ENTRIES,
  LOCAL_SCAN_YIELD_INTERVAL,
  SKIPPED_LOCAL_DIRECTORY_NAMES,
} from './workbenchTypes'

export function inferLanguageFromPath(path: string) {
  const extension = path.split('.').pop()?.toLowerCase()
  switch (extension) {
    case 'json': return 'json'
    case 'yaml': case 'yml': return 'yaml'
    case 'ts': case 'tsx': return 'typescript'
    case 'js': case 'jsx': return 'javascript'
    case 'md': return 'markdown'
    case 'py': return 'python'
    case 'css': return 'css'
    case 'html': return 'html'
    default: return 'plaintext'
  }
}

export function makeLocalDirectoryPath(rootName: string, relativePath = '') {
  return relativePath ? `local/${rootName}/${relativePath}` : `local/${rootName}`
}

export function makeLocalFileEntry(
  rootName: string,
  relativePath: string,
  handle: FileSystemFileHandleLike,
): LocalFileEntry {
  const path = `local/${rootName}/${relativePath}`
  const language = inferLanguageFromPath(handle.name)
  return {
    id: `local:${rootName}/${relativePath}`,
    name: handle.name,
    path,
    language,
    documentType: inferWorkbenchDocumentType({ name: handle.name, path, language }),
    source: 'local',
    editable: true,
    handle,
    updatedAt: '',
  }
}

export function isLocalWorkbenchFileId(fileId: string) {
  return fileId.startsWith('local:') || fileId.startsWith('local/')
}

export async function readDirectoryLevel(
  handle: FileSystemDirectoryHandleLike,
  rootName: string,
  currentRelativePath = '',
): Promise<{
  directories: Array<{
    id: string; name: string; path: string;
    relativePath: string; handle: FileSystemDirectoryHandleLike;
  }>
  files: LocalFileEntry[]
  skippedDirectoryCount: number
}> {
  const entries: Array<{ name: string; handle: FileSystemDirectoryHandleLike | FileSystemFileHandleLike }> = []
  for await (const [name, entryHandle] of handle.entries()) {
    entries.push({ name, handle: entryHandle })
  }
  entries.sort((left, right) => {
    if (left.handle.kind !== right.handle.kind) return left.handle.kind === 'directory' ? -1 : 1
    return left.name.localeCompare(right.name)
  })

  const directories: Array<{
    id: string; name: string; path: string;
    relativePath: string; handle: FileSystemDirectoryHandleLike;
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
  return { directories, files, skippedDirectoryCount }
}

export async function scanDirectory(
  handle: FileSystemDirectoryHandleLike,
  rootName: string,
  currentRelativePath = '',
  state: LocalFolderScanState = {
    files: [], indexedFileCount: 0, processedEntryCount: 0,
    skippedDirectoryCount: 0, truncated: false, stopReason: null,
  },
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
    if (left.handle.kind !== right.handle.kind) return left.handle.kind === 'directory' ? -1 : 1
    return left.name.localeCompare(right.name)
  })

  for (const entry of entries) {
    if (state.truncated) break
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
    const language = inferLanguageFromPath(entry.name)
    state.files.push({
      id: `local:${rootName}/${relativePath}`,
      name: entry.name, path, language,
      documentType: inferWorkbenchDocumentType({ name: entry.name, path, language }),
      source: 'local', editable: true,
      handle: entry.handle, updatedAt: '',
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

export function describeLocalFolderScanSummary(summary: LocalFolderScanSummary) {
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
    detail, skippedDetail,
  ].filter(Boolean).join(', ')
}
