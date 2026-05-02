import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { readBlobAsArrayBuffer } from '@/lib/blob'

const SAMPLE_XLSX_BASE64 = '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'

const mockMonacoLayout = vi.fn()

const { mockWorkbenchProseEditor, mockWorkbenchTableEditor } = vi.hoisted(() => ({
  mockWorkbenchProseEditor: vi.fn(function MockWorkbenchProseEditor(props: {
    value?: string
    onChange?: (value: string) => void
  }) {
    return (
      <div data-testid="desktop-prose-editor">
        <textarea
          aria-label="Desktop prose input"
          data-testid="desktop-prose-input"
          value={props.value ?? ''}
          onChange={(event) => props.onChange?.(event.target.value)}
        />
      </div>
    )
  }),
  mockWorkbenchTableEditor: vi.fn(function MockWorkbenchTableEditor(props: {
    value?: string
    onChange?: (value: string) => void
  }) {
    return (
      <div data-testid="desktop-table-editor">
        <textarea
          aria-label="Desktop table input"
          data-testid="desktop-table-input"
          value={props.value ?? ''}
          onChange={(event) => props.onChange?.(event.target.value)}
        />
      </div>
    )
  }),
}))

const mockMonacoEditor = vi.fn(function MockMonacoEditor(props: {
  onMount?: (editor: { layout: () => void }) => void
  options?: { automaticLayout?: boolean }
  value?: string
  onChange?: (value: string) => void
}) {
  props.onMount?.({ layout: mockMonacoLayout })

  return (
    <div data-testid="desktop-monaco-editor" data-automatic-layout={String(props.options?.automaticLayout)}>
      <textarea
        aria-label="Desktop Monaco input"
        data-testid="desktop-monaco-input"
        value={props.value ?? ''}
        onChange={(event) => props.onChange?.(event.target.value)}
      />
    </div>
  )
})

class MockResizeObserver {
  observe = vi.fn()
  disconnect = vi.fn()
  unobserve = vi.fn()
}

const mockSystemState = {
  shortcutOrder: [],
  desktopToolSurface: 'filesystem' as const,
  openDesktopTool: vi.fn(),
  closeDesktopTool: vi.fn(),
}

type MockWorkbenchDocument = {
  id: string
  name: string
  path: string
  language: string
  content: string
  updatedAt: string
  type?: 'code' | 'prose' | 'table'
  tableData?: {
    columns: string[]
    rows: string[][]
  }
}

const mockWorkbenchState = {
  documents: {} as Record<string, MockWorkbenchDocument>,
  createDocument: vi.fn(),
  updateDocument: vi.fn(),
  updateTableDocument: vi.fn(),
  deleteDocument: vi.fn(),
}

vi.mock('@/store/systemStore', () => ({
  useSystemStore: (selector: (state: typeof mockSystemState) => unknown) => selector(mockSystemState),
}))

vi.mock('@/store/workbenchStore', () => ({
  useWorkbenchStore: (selector: (state: typeof mockWorkbenchState) => unknown) => selector(mockWorkbenchState),
}))

vi.mock('@monaco-editor/react', () => ({
  default: mockMonacoEditor,
}))

vi.mock('@/components/workbench/WorkbenchProseEditor', () => ({
  WorkbenchProseEditor: mockWorkbenchProseEditor,
}))

vi.mock('@/components/workbench/WorkbenchTableEditor', () => ({
  WorkbenchTableEditor: mockWorkbenchTableEditor,
}))

import {
  DesktopWorkbench,
  MAX_INDEXED_LOCAL_FILES,
  MAX_PROCESSED_LOCAL_ENTRIES,
  readDirectoryLevel,
  scanDirectory,
} from './DesktopWorkbench'
import { parseTableDataFile } from '@/lib/spreadsheet'

type WritablePayload = string | Blob | ArrayBuffer | Uint8Array

function normalizeBlobPart(payload: WritablePayload): BlobPart {
  if (typeof payload === 'string' || payload instanceof Blob || payload instanceof ArrayBuffer) {
    return payload
  }

  return Uint8Array.from(payload)
}

function createFileLike(name: string, payload: WritablePayload, type = '') {
  const normalizedPayload = normalizeBlobPart(payload)
  const blob = new Blob([normalizedPayload], { type })
  const getArrayBuffer = async () => {
    if (normalizedPayload instanceof Blob && typeof normalizedPayload.arrayBuffer === 'function') {
      return normalizedPayload.arrayBuffer()
    }

    if (normalizedPayload instanceof ArrayBuffer) {
      return normalizedPayload.slice(0)
    }

    if (ArrayBuffer.isView(normalizedPayload)) {
      const bytes = new Uint8Array(normalizedPayload.byteLength)
      bytes.set(
        new Uint8Array(
          normalizedPayload.buffer,
          normalizedPayload.byteOffset,
          normalizedPayload.byteLength
        )
      )
      return bytes.buffer
    }

    return new TextEncoder().encode(String(normalizedPayload)).buffer
  }

  return Object.assign(blob, {
    name,
    lastModified: Date.now(),
    arrayBuffer: getArrayBuffer,
    text: async () => new TextDecoder().decode(await getArrayBuffer()),
  }) as File
}

function decodeBase64ToBytes(base64: string) {
  return Uint8Array.from(atob(base64), (character) => character.charCodeAt(0))
}

type TestFileHandle = {
  kind: 'file'
  name: string
  getFile: () => Promise<File>
  createWritable?: () => Promise<{ write: (data: WritablePayload) => Promise<void>; close: () => Promise<void> }>
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
    getFile: async () => createFileLike(name, ''),
  }
}

function payloadToFile(name: string, payload: WritablePayload) {
  if (payload instanceof Blob) {
    return createFileLike(name, payload, payload.type)
  }

  return createFileLike(name, payload)
}

function createWritableFileHandle(
  name: string,
  initialContent: WritablePayload,
  options?: { failWrite?: boolean; failClose?: boolean }
): {
  handle: TestFileHandle
  writeSpy: ReturnType<typeof vi.fn>
  closeSpy: ReturnType<typeof vi.fn>
} {
  let currentFile = payloadToFile(name, initialContent)
  let pendingWrite = initialContent

  const writeSpy = vi.fn(async (data: WritablePayload) => {
    if (options?.failWrite) {
      throw new Error('Disk full')
    }

    pendingWrite = data
  })

  const closeSpy = vi.fn(async () => {
    if (options?.failClose) {
      throw new Error('Close failed')
    }

    currentFile = payloadToFile(name, pendingWrite)
  })

  return {
    handle: {
      kind: 'file',
      name,
      getFile: async () => currentFile,
      createWritable: async () => ({
        write: writeSpy,
        close: closeSpy,
      }),
    },
    writeSpy,
    closeSpy,
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

async function createSpreadsheetFile(name: string, rows: Array<Array<string | number>>) {
  return createFileLike(
    name,
    decodeBase64ToBytes(SAMPLE_XLSX_BASE64),
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  )
}

beforeEach(() => {
  window.localStorage.removeItem('bijmantra-workbench-density')
  window.localStorage.removeItem('bijmantra-workbench-explorer-collapsed')
  window.localStorage.removeItem('bijmantra-workbench-session')
  mockSystemState.openDesktopTool.mockReset()
  mockSystemState.closeDesktopTool.mockReset()
  mockWorkbenchState.documents = {}
  mockWorkbenchState.createDocument.mockReset()
  mockWorkbenchState.updateDocument.mockReset()
  mockWorkbenchState.updateTableDocument.mockReset()
  mockWorkbenchState.deleteDocument.mockReset()
  mockMonacoLayout.mockReset()
  mockMonacoEditor.mockClear()
  mockWorkbenchProseEditor.mockClear()
  mockWorkbenchTableEditor.mockClear()
  mockWorkbenchState.createDocument.mockImplementation((params?: {
    name?: string
    language?: string
    content?: string
    type?: 'code' | 'prose' | 'table'
  }) => {
    const documentCount = Object.keys(mockWorkbenchState.documents).length + 1
    const type = params?.type ?? (params?.name?.endsWith('.csv') ? 'table' : 'prose')
    const name = params?.name ?? (type === 'table' ? `table-${documentCount}.csv` : `untitled-${documentCount}.md`)
    const document = {
      id: `doc-${documentCount}`,
      name,
      path: `documents/${name}`,
      language: params?.language ?? (type === 'table' ? 'plaintext' : 'markdown'),
      content: params?.content ?? (type === 'table' ? 'column_a,column_b,column_c\n,,\n' : '# New Document\n\n'),
      updatedAt: '2026-03-17T00:00:00.000Z',
      type,
    }
    mockWorkbenchState.documents = {
      ...mockWorkbenchState.documents,
      [document.id]: document,
    }

    return document
  })
  ;(window as Window & { showDirectoryPicker?: () => Promise<TestDirectoryHandle> }).showDirectoryPicker = undefined
  global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(
    () =>
      ({
        width: 1200,
        height: 720,
        top: 0,
        right: 1200,
        bottom: 720,
        left: 0,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }) as DOMRect
  )
})

afterEach(() => {
  vi.restoreAllMocks()
})

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

describe('DesktopWorkbench local explorer', () => {
  it('defaults to compact density and persists density changes for the explorer rail', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    expect(screen.getByRole('button', { name: 'Compact density' })).toHaveAttribute('aria-pressed', 'true')
    expect(window.localStorage.getItem('bijmantra-workbench-density')).toBe('compact')

    fireEvent.click(screen.getByRole('button', { name: 'Comfortable density' }))

    expect(screen.getByRole('button', { name: 'Comfortable density' })).toHaveAttribute('aria-pressed', 'true')
    expect(window.localStorage.getItem('bijmantra-workbench-density')).toBe('comfortable')
  })

  it('restores the previous editor session from local storage', async () => {
    mockWorkbenchState.documents = {
      'doc-prose': {
        id: 'doc-prose',
        name: 'research-notes.md',
        path: 'documents/research-notes.md',
        language: 'markdown',
        content: '# Research Notes\n\nSome content here.',
        updatedAt: '2026-03-17T00:00:00.000Z',
        type: 'prose',
      },
    }

    window.localStorage.setItem(
      'bijmantra-workbench-session',
      JSON.stringify({
        openFileIds: ['doc-prose'],
        activeFileId: 'doc-prose',
        expandedPaths: ['documents'],
        editorViewMode: 'prose',
      })
    )

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getAllByRole('heading', { name: 'research-notes.md' }).length).toBeGreaterThan(0)
    })

    expect(screen.getByTestId('desktop-prose-editor')).toBeInTheDocument()
  })

  it('supports keyboard navigation and semantic tree roles in the explorer', async () => {
    mockWorkbenchState.documents = {
      'doc-1': {
        id: 'doc-1',
        name: 'notes.md',
        path: 'documents/notes.md',
        language: 'markdown',
        content: '# Notes\n',
        updatedAt: '2026-03-17T00:00:00.000Z',
        type: 'prose',
      },
    }

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    const explorerTree = screen.getByRole('tree', { name: 'Workbench explorer' })
    expect(explorerTree).toBeInTheDocument()

    const documentsNode = screen.getByRole('treeitem', { name: 'documents' })
    expect(documentsNode).toHaveAttribute('aria-expanded', 'true')
    documentsNode.focus()

    fireEvent.keyDown(documentsNode, { key: 'ArrowRight' })

    await waitFor(() => {
      expect(screen.getByRole('treeitem', { name: 'notes.md' })).toHaveFocus()
    })

    fireEvent.keyDown(screen.getByRole('treeitem', { name: 'notes.md' }), { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getAllByRole('heading', { name: 'notes.md' }).length).toBeGreaterThan(0)
    })

    expect(screen.getByRole('treeitem', { name: 'notes.md' })).toHaveAttribute('aria-selected', 'true')
  })

  it('saves user table documents through the structured table update path', async () => {
    mockWorkbenchState.documents = {
      'doc-table': {
        id: 'doc-table',
        name: 'trial-matrix.csv',
        path: 'documents/trial-matrix.csv',
        language: 'plaintext',
        content: 'Trait,Value\nYield,5.2\n',
        updatedAt: '2026-03-17T00:00:00.000Z',
        type: 'table',
        tableData: {
          columns: ['Trait', 'Value'],
          rows: [['Yield', '5.2']],
        },
      },
    }

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-table-input')).toHaveValue('Trait,Value\nYield,5.2\n')
    })

    fireEvent.change(screen.getByTestId('desktop-table-input'), {
      target: { value: 'Trait,Value\nYield,6.1\n' },
    })

    expect(screen.getByText('Unsaved changes')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(mockWorkbenchState.updateDocument).not.toHaveBeenCalled()
    expect(mockWorkbenchState.updateTableDocument).toHaveBeenCalledWith('doc-table', {
      columns: ['Trait', 'Value'],
      rows: [['Yield', '6.1']],
    })
  })

  it('mounts the editor surface with controlled Monaco layout after switching surfaces', async () => {
    mockWorkbenchState.documents = {
      'doc-1': {
        id: 'doc-1',
        name: 'analysis.py',
        path: 'documents/analysis.py',
        language: 'python',
        content: 'print("ready")\n',
        updatedAt: '2026-03-17T00:00:00.000Z',
        type: 'code',
      },
    }

    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-monaco-editor')).toBeInTheDocument()
    })

    expect(screen.getByTestId('desktop-monaco-editor')).toHaveAttribute('data-automatic-layout', 'false')
    expect(mockMonacoLayout).toHaveBeenCalled()
  })

  it('does not render internal platform or system roots in the desktop explorer', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    expect(screen.queryByRole('treeitem', { name: 'platform' })).not.toBeInTheDocument()
    expect(screen.queryByRole('treeitem', { name: 'system' })).not.toBeInTheDocument()
    expect(screen.getByText('No desktop files yet. Create a note or connect a local folder.')).toBeInTheDocument()
  })

  it('loads only the root directory on connect and lazily expands nested folders', async () => {
    const rootHandle = createDirectoryHandle('workspace', [
      ['root-only.md', createFileHandle('root-only.md')],
      [
        'src',
        createDirectoryHandle('src', [
          ['nested.ts', createFileHandle('nested.ts')],
        ]),
      ],
    ])

    ;(window as Window & { showDirectoryPicker?: () => Promise<TestDirectoryHandle> }).showDirectoryPicker = vi
      .fn()
      .mockResolvedValue(rootHandle)

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /connect local folder/i }))

    await waitFor(() => {
      expect(screen.getByText('root-only.md')).toBeInTheDocument()
    })
    expect(screen.getByText('src')).toBeInTheDocument()
    expect(screen.queryByText('nested.ts')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('treeitem', { name: 'src' }))

    await waitFor(() => {
      expect(screen.getByText('nested.ts')).toBeInTheDocument()
    })
  })

  it('saves a local file and clears the dirty state after a successful write', async () => {
    const { handle, writeSpy, closeSpy } = createWritableFileHandle('notes.md', 'initial content')
    const rootHandle = createDirectoryHandle('workspace', [['notes.md', handle]])
    ;(window as Window & { showDirectoryPicker?: () => Promise<TestDirectoryHandle> }).showDirectoryPicker = vi
      .fn()
      .mockResolvedValue(rootHandle)

    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /connect local folder/i }))
    await waitFor(() => {
      expect(screen.getByText('notes.md')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('treeitem', { name: 'notes.md' }))
    await waitFor(() => {
      expect(screen.getAllByRole('heading', { name: 'notes.md' }).length).toBeGreaterThan(0)
    })

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-prose-input')).toHaveValue('initial content')
    })

    fireEvent.change(screen.getByTestId('desktop-prose-input'), {
      target: { value: 'updated content' },
    })

    expect(screen.getByText('Unsaved changes')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(writeSpy).toHaveBeenCalledWith('updated content')
      expect(closeSpy).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
    })
    expect(screen.getByText('Up to date')).toBeInTheDocument()
  })

  it('preserves the local draft and surfaces an error when save fails', async () => {
    const { handle, writeSpy, closeSpy } = createWritableFileHandle('notes.md', 'initial content', { failWrite: true })
    const rootHandle = createDirectoryHandle('workspace', [['notes.md', handle]])
    ;(window as Window & { showDirectoryPicker?: () => Promise<TestDirectoryHandle> }).showDirectoryPicker = vi
      .fn()
      .mockResolvedValue(rootHandle)

    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /connect local folder/i }))
    await waitFor(() => {
      expect(screen.getByText('notes.md')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('treeitem', { name: 'notes.md' }))
    await waitFor(() => {
      expect(screen.getAllByRole('heading', { name: 'notes.md' }).length).toBeGreaterThan(0)
    })

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-prose-input')).toHaveValue('initial content')
    })

    fireEvent.change(screen.getByTestId('desktop-prose-input'), {
      target: { value: 'unsaved content' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(writeSpy).toHaveBeenCalledWith('unsaved content')
    })

    expect(closeSpy).not.toHaveBeenCalled()
    expect(await screen.findByText('Disk full')).toBeInTheDocument()
    expect(screen.getByTestId('desktop-prose-input')).toHaveValue('unsaved content')
    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled()
  })

  it('reconnect replaces the previous local tree with the new folder contents', async () => {
    const firstHandle = createDirectoryHandle('workspace-a', [
      ['old-file.md', createFileHandle('old-file.md')],
    ])
    const secondHandle = createDirectoryHandle('workspace-b', [
      ['new-file.md', createFileHandle('new-file.md')],
    ])

    ;(window as Window & { showDirectoryPicker?: () => Promise<TestDirectoryHandle> }).showDirectoryPicker = vi
      .fn()
      .mockResolvedValueOnce(firstHandle)
      .mockResolvedValueOnce(secondHandle)

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /connect local folder/i }))
    await waitFor(() => {
      expect(screen.getByText('old-file.md')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /reconnect folder/i }))
    await waitFor(() => {
      expect(screen.getByText('new-file.md')).toBeInTheDocument()
    })

    expect(screen.queryByText('old-file.md')).not.toBeInTheDocument()
  })

  it('reconnect clears stale local save errors and drafts before loading the next folder', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const firstFile = createWritableFileHandle('notes.md', 'initial content', { failWrite: true })
    const secondFile = createWritableFileHandle('notes.md', 'fresh content')
    const firstHandle = createDirectoryHandle('workspace', [['notes.md', firstFile.handle]])
    const secondHandle = createDirectoryHandle('workspace', [['notes.md', secondFile.handle]])

    ;(window as Window & { showDirectoryPicker?: () => Promise<TestDirectoryHandle> }).showDirectoryPicker = vi
      .fn()
      .mockResolvedValueOnce(firstHandle)
      .mockResolvedValueOnce(secondHandle)

    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /connect local folder/i }))
    await waitFor(() => {
      expect(screen.getByText('notes.md')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('treeitem', { name: 'notes.md' }))
    await waitFor(() => {
      expect(screen.getAllByRole('heading', { name: 'notes.md' }).length).toBeGreaterThan(0)
    })

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-prose-input')).toHaveValue('initial content')
    })

    fireEvent.change(screen.getByTestId('desktop-prose-input'), {
      target: { value: 'unsaved content' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('Disk full')).toBeInTheDocument()

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /reconnect folder/i }))
    await waitFor(() => {
      expect(screen.getByRole('treeitem', { name: 'notes.md' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('treeitem', { name: 'notes.md' }))

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-prose-input')).toHaveValue('fresh content')
    })

    expect(screen.queryByText('Disk full')).not.toBeInTheDocument()
    expect(screen.getByText('Up to date')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
  })

  it('opens and saves local xlsx files through the structured table workspace', async () => {
    const workbookFile = await createSpreadsheetFile('trial-matrix.xlsx', [
      ['Variety', 'Yield'],
      ['IR64', 5.2],
      ['Swarna', 4.8],
    ])
    const { handle, writeSpy, closeSpy } = createWritableFileHandle(
      'trial-matrix.xlsx',
      workbookFile
    )
    const rootHandle = createDirectoryHandle('workspace', [['trial-matrix.xlsx', handle]])

    ;(window as Window & { showDirectoryPicker?: () => Promise<TestDirectoryHandle> }).showDirectoryPicker = vi
      .fn()
      .mockResolvedValue(rootHandle)

    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /connect local folder/i }))
    await waitFor(() => {
      expect(screen.getByText('trial-matrix.xlsx')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('treeitem', { name: 'trial-matrix.xlsx' }))
    await waitFor(() => {
      expect(screen.getAllByRole('heading', { name: 'trial-matrix.xlsx' }).length).toBeGreaterThan(0)
    })

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-table-input')).toHaveValue(
        'Variety,Yield\nIR64,5.2\nSwarna,4.8\n'
      )
    })

    fireEvent.change(screen.getByTestId('desktop-table-input'), {
      target: { value: 'Variety,Yield\nIR64,5.4\nSwarna,4.8\n' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => {
      expect(writeSpy).toHaveBeenCalled()
      expect(closeSpy).toHaveBeenCalled()
    })

    const savedPayload = writeSpy.mock.calls[writeSpy.mock.calls.length - 1]?.[0]
    expect(savedPayload).toBeInstanceOf(Blob)

    expect((savedPayload as Blob).size).toBeGreaterThan(0)
  })

  it('keeps a dirty tab open when tab close is cancelled', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: 'Create desktop document' }))

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-prose-input')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByTestId('desktop-prose-input'), {
      target: { value: '# changed\n' },
    })

    fireEvent.click(screen.getByRole('button', { name: /close untitled-1\.md/i }))

    expect(confirmSpy).toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /close untitled-1\.md/i })).toBeInTheDocument()
    expect(screen.getByText('Unsaved changes')).toBeInTheDocument()
  })

  it('keeps the desktop tool open when close is cancelled with dirty drafts', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const onClose = vi.fn()

    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={onClose} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: 'Create desktop document' }))

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={onClose} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-prose-input')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByTestId('desktop-prose-input'), {
      target: { value: '# changed\n' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Close desktop tool' }))

    expect(confirmSpy).toHaveBeenCalled()
    expect(onClose).not.toHaveBeenCalled()
    expect(screen.getByText('Unsaved changes')).toBeInTheDocument()
  })

  it('keeps the current local folder and draft when reconnect is cancelled', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const fileHandle = createWritableFileHandle('notes.md', 'initial content')
    const rootHandle = createDirectoryHandle('workspace', [['notes.md', fileHandle.handle]])

    ;(window as Window & { showDirectoryPicker?: () => Promise<TestDirectoryHandle> }).showDirectoryPicker = vi
      .fn()
      .mockResolvedValue(rootHandle)

    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /connect local folder/i }))
    await waitFor(() => {
      expect(screen.getByText('notes.md')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('treeitem', { name: 'notes.md' }))
    await waitFor(() => {
      expect(screen.getAllByRole('heading', { name: 'notes.md' }).length).toBeGreaterThan(0)
    })

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('desktop-prose-input')).toHaveValue('initial content')
    })

    fireEvent.change(screen.getByTestId('desktop-prose-input'), {
      target: { value: 'unsaved content' },
    })

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="filesystem" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /reconnect folder/i }))

    expect(confirmSpy).toHaveBeenCalled()
    expect(screen.getByText('Local workspace attached: workspace')).toBeInTheDocument()

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <DesktopWorkbench surface="editor" onClose={vi.fn()} onOpenSurface={vi.fn()} />
      </MemoryRouter>
    )

    expect(screen.getByTestId('desktop-prose-input')).toHaveValue('unsaved content')
  })
})