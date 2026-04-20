import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { createDefaultDeveloperMasterBoardJson } from '../../contracts/board'
import { Tabs } from '@/components/ui/tabs'
import { JsonTab } from './JsonTab'

describe('JsonTab', () => {
  it('wires JSON actions and raw text editing through container callbacks', () => {
    const onRawBoardJsonChange = vi.fn()
    const onFormatJson = vi.fn()
    const onExport = vi.fn()
    const onTriggerImport = vi.fn()
    const onResetBoard = vi.fn()

    render(
      <Tabs value="json" onValueChange={() => {}}>
        <JsonTab
          jsonError={null}
          rawBoardJson={createDefaultDeveloperMasterBoardJson()}
          onRawBoardJsonChange={onRawBoardJsonChange}
          onFormatJson={onFormatJson}
          onExport={onExport}
          onTriggerImport={onTriggerImport}
          onResetBoard={onResetBoard}
          persistenceStatus={{
            tone: 'fallback',
            label: 'Local fallback only',
            description:
              'The canonical board is currently persisted in this browser only and is not yet backed by shared backend persistence.',
          }}
        />
      </Tabs>
    )

    fireEvent.click(screen.getByRole('button', { name: 'Format JSON' }))
    fireEvent.click(screen.getByRole('button', { name: 'Export' }))
    fireEvent.click(screen.getByRole('button', { name: 'Import' }))
    fireEvent.click(screen.getByRole('button', { name: 'Reset Seed' }))
    fireEvent.change(screen.getByRole('textbox'), { target: { value: '{\n  "board_id": "changed"\n}' } })

    expect(onFormatJson).toHaveBeenCalledOnce()
    expect(onExport).toHaveBeenCalledOnce()
    expect(onTriggerImport).toHaveBeenCalledOnce()
    expect(onResetBoard).toHaveBeenCalledOnce()
    expect(screen.getByText('Canonical Control-Plane JSON')).toBeInTheDocument()
    expect(screen.getByText(/Persistence status:/)).toBeInTheDocument()
    expect(screen.getByText(/Local fallback only/)).toBeInTheDocument()
    expect(onRawBoardJsonChange).toHaveBeenCalledWith(`{
  "board_id": "changed"
}`)
  })

  it('shows the invalid JSON warning and disables formatting when JSON is invalid', () => {
    render(
      <Tabs value="json" onValueChange={() => {}}>
        <JsonTab
          jsonError="Unexpected token"
          rawBoardJson="{"
          onRawBoardJsonChange={() => {}}
          onFormatJson={() => {}}
          onExport={() => {}}
          onTriggerImport={() => {}}
          onResetBoard={() => {}}
          persistenceStatus={{
            tone: 'fallback',
            label: 'Local fallback only',
            description:
              'The canonical board is currently persisted in this browser only and is not yet backed by shared backend persistence.',
          }}
        />
      </Tabs>
    )

    expect(screen.getByText('Invalid board JSON')).toBeInTheDocument()
    expect(screen.getByText('Unexpected token')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Format JSON' })).toBeDisabled()
  })
})