import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type WorkbenchDocument = {
  id: string
  name: string
  path: string
  language: string
  content: string
  updatedAt: string
}

type CreateDocumentParams = {
  name?: string
  language?: string
  content?: string
}

interface WorkbenchStore {
  documents: Record<string, WorkbenchDocument>
  createDocument: (params?: CreateDocumentParams) => WorkbenchDocument
  updateDocument: (id: string, content: string) => void
  deleteDocument: (id: string) => void
}

function extensionForLanguage(language: string) {
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

function defaultContentForLanguage(language: string) {
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

export const useWorkbenchStore = create<WorkbenchStore>()(
  persist(
    (set, get) => ({
      documents: {},

      createDocument: (params) => {
        const language = params?.language ?? 'markdown'
        const extension = extensionForLanguage(language)
        const existingCount = Object.keys(get().documents).length + 1
        const name = params?.name ?? `untitled-${existingCount}.${extension}`
        const timestamp = new Date().toISOString()
        const document: WorkbenchDocument = {
          id: safeDocumentId(),
          name,
          path: `documents/${name}`,
          language,
          content: params?.content ?? defaultContentForLanguage(language),
          updatedAt: timestamp,
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

          return {
            documents: {
              ...state.documents,
              [id]: {
                ...existing,
                content,
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
    }
  )
)