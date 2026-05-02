import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('useWorkbenchStore persistence contract', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })

  it('hydrates persisted documents and keeps document actions operational', async () => {
    localStorage.setItem(
      'bijmantra-workbench-storage',
      JSON.stringify({
        state: {
          documents: {
            'doc-1': {
              id: 'doc-1',
              name: 'alpha.md',
              path: 'documents/alpha.md',
              language: 'markdown',
              content: '# Alpha\n',
              updatedAt: '2026-03-17T00:00:00.000Z',
            },
          },
        },
        version: 0,
      })
    )

    const { useWorkbenchStore } = await import('./workbenchStore')

    expect(useWorkbenchStore.getState().documents['doc-1']?.name).toBe('alpha.md')
    expect(useWorkbenchStore.getState().documents['doc-1']?.type).toBe('prose')

    useWorkbenchStore.getState().updateDocument('doc-1', '# Beta\n')
    expect(useWorkbenchStore.getState().documents['doc-1']?.content).toBe('# Beta\n')

    const created = useWorkbenchStore.getState().createDocument({ name: 'gamma.md', language: 'markdown', content: '# Gamma\n' })
    expect(useWorkbenchStore.getState().documents[created.id]?.path).toBe('documents/gamma.md')
    expect(useWorkbenchStore.getState().documents[created.id]?.type).toBe('prose')

    const table = useWorkbenchStore.getState().createDocument({
      name: 'trial-matrix.csv',
      type: 'table',
    })
    expect(useWorkbenchStore.getState().documents[table.id]?.type).toBe('table')
    expect(useWorkbenchStore.getState().documents[table.id]?.tableData?.columns).toEqual(['column_a', 'column_b', 'column_c'])

    useWorkbenchStore.getState().updateTableDocument(table.id, {
      columns: ['Trait', 'Value'],
      rows: [['Yield', '5.8']],
    })
    expect(useWorkbenchStore.getState().documents[table.id]?.tableData).toEqual({
      columns: ['Trait', 'Value'],
      rows: [['Yield', '5.8']],
    })
    expect(useWorkbenchStore.getState().documents[table.id]?.content).toBe('Trait,Value\nYield,5.8\n')

    useWorkbenchStore.getState().deleteDocument('doc-1')
    expect(useWorkbenchStore.getState().documents['doc-1']).toBeUndefined()
  })
})