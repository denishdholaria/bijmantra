import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import {
  createDefaultWorkbenchTableData,
  getWorkbenchTableDelimiter,
  inferWorkbenchDocumentType,
  normalizeWorkbenchTableData,
  serializeDelimitedTable,
  type WorkbenchDocumentType,
  type WorkbenchTableData,
} from '@/lib/workbenchDocuments'

export type WorkbenchDocument = {
  id: string
  name: string
  path: string
  language: string
  content: string
  updatedAt: string
  type: WorkbenchDocumentType
  tableData?: WorkbenchTableData
}

type CreateDocumentParams = {
  name?: string
  language?: string
  content?: string
  type?: WorkbenchDocumentType
  tableData?: WorkbenchTableData
}

interface WorkbenchStore {
  documents: Record<string, WorkbenchDocument>
  createDocument: (params?: CreateDocumentParams) => WorkbenchDocument
  updateDocument: (id: string, content: string) => void
  updateTableDocument: (id: string, tableData: WorkbenchTableData) => void
  deleteDocument: (id: string) => void
}

function extensionForLanguage(language: string, type: WorkbenchDocumentType) {
  if (type === 'table') {
    return 'csv'
  }

  switch (language) {
    case 'json':
      return 'json'
    case 'yaml':
      return 'yaml'
    case 'typescript':
      return 'ts'
    case 'javascript':
      return 'js'
    default:
      return 'md'
  }
}

function defaultContentForDocument(language: string, type: WorkbenchDocumentType) {
  if (type === 'table') {
    return serializeDelimitedTable(createDefaultWorkbenchTableData())
  }

  switch (language) {
    case 'json':
      return '{\n  "title": "New Specification"\n}\n'
    case 'yaml':
      return 'title: New Specification\n'
    case 'typescript':
      return 'export function main() {\n  return "ready"\n}\n'
    case 'javascript':
      return 'export function main() {\n  return "ready"\n}\n'
    default:
      return '# New Document\n\n'
  }
}

function safeDocumentId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  return `doc-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function migrateDocuments(documents: unknown) {
  if (!documents || typeof documents !== 'object') {
    return {} as Record<string, WorkbenchDocument>
  }

  const nextDocuments: Record<string, WorkbenchDocument> = {}

  for (const [id, value] of Object.entries(documents as Record<string, Partial<WorkbenchDocument>>)) {
    if (!value || typeof value !== 'object') {
      continue
    }

    const name = typeof value.name === 'string' ? value.name : `document-${id}.md`
    const path = typeof value.path === 'string' ? value.path : `documents/${name}`
    const language = typeof value.language === 'string' ? value.language : 'markdown'
    const content = typeof value.content === 'string' ? value.content : defaultContentForDocument(language, 'prose')
    const type = inferWorkbenchDocumentType({
      name,
      path,
      language,
      type: value.type,
      tableData: value.tableData,
    })
    const tableData = type === 'table' ? normalizeWorkbenchTableData(value.tableData, content, path) : undefined

    nextDocuments[id] = {
      id: typeof value.id === 'string' ? value.id : id,
      name,
      path,
      language,
      content: type === 'table' ? serializeDelimitedTable(tableData ?? createDefaultWorkbenchTableData()) : content,
      updatedAt: typeof value.updatedAt === 'string' ? value.updatedAt : new Date().toISOString(),
      type,
      tableData,
    }
  }

  return nextDocuments
}

export const useWorkbenchStore = create<WorkbenchStore>()(
  persist(
    (set, get) => ({
      documents: {},

      createDocument: (params) => {
        const nextType = inferWorkbenchDocumentType({
          name: params?.name,
          language: params?.language,
          type: params?.type ?? null,
          tableData: params?.tableData ?? null,
        })
        const language = params?.language ?? (nextType === 'table' ? 'plaintext' : 'markdown')
        const extension = extensionForLanguage(language, nextType)
        const existingCount = Object.keys(get().documents).length + 1
        const name = params?.name ?? `untitled-${existingCount}.${extension}`
        const timestamp = new Date().toISOString()
        const tableData =
          nextType === 'table'
            ? normalizeWorkbenchTableData(params?.tableData, params?.content, name)
            : undefined
        const document: WorkbenchDocument = {
          id: safeDocumentId(),
          name,
          path: `documents/${name}`,
          language,
          content:
            nextType === 'table'
              ? serializeDelimitedTable(tableData ?? createDefaultWorkbenchTableData())
              : params?.content ?? defaultContentForDocument(language, nextType),
          updatedAt: timestamp,
          type: nextType,
          tableData,
        }

        set((state) => ({
          documents: {
            ...state.documents,
            [document.id]: document,
          },
        }))

        return document
      },

      updateDocument: (id, content) => {
        set((state) => {
          const existing = state.documents[id]
          if (!existing) {
            return state
          }

          const nextTableData = existing.type === 'table' ? normalizeWorkbenchTableData(existing.tableData, content, existing.path) : undefined

          return {
            documents: {
              ...state.documents,
              [id]: {
                ...existing,
                content: existing.type === 'table' ? serializeDelimitedTable(nextTableData ?? createDefaultWorkbenchTableData()) : content,
                tableData: nextTableData,
                updatedAt: new Date().toISOString(),
              },
            },
          }
        })
      },

      updateTableDocument: (id, tableData) => {
        set((state) => {
          const existing = state.documents[id]
          if (!existing) {
            return state
          }

          const nextTableData = normalizeWorkbenchTableData(tableData, existing.content, existing.path)

          return {
            documents: {
              ...state.documents,
              [id]: {
                ...existing,
                type: 'table',
                content: serializeDelimitedTable(nextTableData, getWorkbenchTableDelimiter(existing.path)),
                tableData: nextTableData,
                updatedAt: new Date().toISOString(),
              },
            },
          }
        })
      },

      deleteDocument: (id) => {
        set((state) => {
          const { [id]: _removed, ...remaining } = state.documents
          return { documents: remaining }
        })
      },
    }),
    {
      name: 'bijmantra-workbench-storage',
      version: 1,
      migrate: (persistedState) => {
        const typedState = persistedState as { documents?: Record<string, Partial<WorkbenchDocument>> }

        return {
          ...typedState,
          documents: migrateDocuments(typedState.documents),
        }
      },
    }
  )
)