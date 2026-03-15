import { describe, expect, it } from 'vitest'

import {
  MAX_INDEXED_LOCAL_FILES,
  MAX_PROCESSED_LOCAL_ENTRIES,
  readDirectoryLevel,
  scanDirectory,
} from './DesktopWorkbench'

type TestFileHandle = {
  kind: 'file'
  name: string
  getFile: () => Promise<File>
}

type TestDirectoryHandle = {
  kind: 'directory'
  name: string
  entries: () => AsyncIterable<[string, TestDirectoryHandle | TestFileHandle]>
}

function createFileHandle(name: string): TestFileHandle {
  return {
    kind: 'file',
    name,
    getFile: async () => new File([''], name),
  }
}

function createDirectoryHandle(
  name: string,
  entries: Array<[string, TestDirectoryHandle | TestFileHandle]>
): TestDirectoryHandle {
  return {
    kind: 'directory',
    name,
    entries: async function* () {
      for (const entry of entries) {
        yield entry
      }
    },
  }
}

describe('scanDirectory', () => {
  it('reads one directory level without recursing into child folders', async () => {
    const handle = createDirectoryHandle('workspace', [
      ['README.md', createFileHandle('README.md')],
      [
        'src',
        createDirectoryHandle('src', [
          ['nested.ts', createFileHandle('nested.ts')],
        ]),
      ],
      [
        'node_modules',
        createDirectoryHandle('node_modules', [['ignored.js', createFileHandle('ignored.js')]]),
      ],
    ])

    const result = await readDirectoryLevel(handle, handle.name)

    expect(result.skippedDirectoryCount).toBe(1)
    expect(result.directories.map((directory) => directory.path)).toEqual(['local/workspace/src'])
    expect(result.files.map((file) => file.path)).toEqual(['local/workspace/README.md'])
  })

  it('indexes normal files and skips heavy generated directories', async () => {
    const handle = createDirectoryHandle('workspace', [
      ['README.md', createFileHandle('README.md')],
      [
        'src',
        createDirectoryHandle('src', [
          ['main.ts', createFileHandle('main.ts')],
          ['config.json', createFileHandle('config.json')],
        ]),
      ],
      [
        'node_modules',
        createDirectoryHandle('node_modules', [['ignored.js', createFileHandle('ignored.js')]]),
      ],
    ])

    const result = await scanDirectory(handle, handle.name)

    expect(result.summary.truncated).toBe(false)
    expect(result.summary.indexedFileCount).toBe(3)
    expect(result.summary.skippedDirectoryCount).toBe(1)
    expect(result.summary.stopReason).toBeNull()
    expect(result.files.map((file) => file.path)).toEqual([
      'local/workspace/src/config.json',
      'local/workspace/src/main.ts',
      'local/workspace/README.md',
    ])
  })

  it('caps very large folder indexes to keep the shell bounded', async () => {
    const entries = Array.from({ length: MAX_INDEXED_LOCAL_FILES + 25 }, (_, index) => {
      const name = `file-${index}.ts`
      return [name, createFileHandle(name)] as [string, TestFileHandle]
    })
    const handle = createDirectoryHandle('big-workspace', entries)

    const result = await scanDirectory(handle, handle.name)

    expect(result.summary.truncated).toBe(true)
    expect(result.summary.indexedFileCount).toBe(MAX_INDEXED_LOCAL_FILES)
    expect(result.summary.stopReason).toBe('file-cap')
    expect(result.files).toHaveLength(MAX_INDEXED_LOCAL_FILES)
    expect(result.files.every((file) => file.path.startsWith('local/big-workspace/'))).toBe(true)
  })

  it('caps traversal work before indexing an unbounded folder tree', async () => {
    const entries = Array.from({ length: MAX_PROCESSED_LOCAL_ENTRIES + 25 }, (_, index) => {
      const name = `dir-${index}`
      return [name, createDirectoryHandle(name, [])] as [string, TestDirectoryHandle]
    })
    const handle = createDirectoryHandle('wide-workspace', entries)

    const result = await scanDirectory(handle, handle.name)

    expect(result.summary.truncated).toBe(true)
    expect(result.summary.stopReason).toBe('traversal-budget')
    expect(result.summary.indexedFileCount).toBe(0)
    expect(result.files).toHaveLength(0)
  })
})