import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { defaultDeveloperMasterBoard } from '../../contracts/board'
import { Tabs } from '@/components/ui/tabs'
import { ArielmaTab } from './ArielmaTab'

const initializeMock = vi.fn()
const renderMock = vi.fn(async () => ({ svg: '<svg data-testid="arielma-rendered-svg"></svg>' }))

vi.mock('arielma', () => ({
  default: {
    initialize: initializeMock,
    render: renderMock,
  },
}))

describe('ArielmaTab', () => {
  const originalCreateObjectURL = window.URL.createObjectURL
  const originalRevokeObjectURL = window.URL.revokeObjectURL

  beforeEach(() => {
    initializeMock.mockClear()
    renderMock.mockClear()
    window.localStorage.clear()
  })

  afterEach(() => {
    window.URL.createObjectURL = originalCreateObjectURL
    window.URL.revokeObjectURL = originalRevokeObjectURL
    vi.restoreAllMocks()
  })

  it('renders a diagram preview and generated source from the canonical board', async () => {
    const { container } = render(
      <Tabs value="arielma" onValueChange={() => {}}>
        <ArielmaTab parsedBoard={defaultDeveloperMasterBoard} jsonError={null} />
      </Tabs>
    )

    expect(screen.getByText('Diagram View')).toBeInTheDocument()
    expect(screen.getByDisplayValue(/flowchart LR/)).toBeInTheDocument()

    await waitFor(() => {
      expect(renderMock).toHaveBeenCalled()
    })

    expect(container.querySelector('[data-testid="arielma-rendered-svg"]')).not.toBeNull()
  })

  it('renders pasted diagram code without requiring a valid board payload', async () => {
    render(
      <Tabs value="arielma" onValueChange={() => {}}>
        <ArielmaTab parsedBoard={null} jsonError="Invalid developer master board JSON" />
      </Tabs>
    )

    fireEvent.click(screen.getByRole('button', { name: 'Paste code' }))
    fireEvent.change(screen.getByLabelText('Editable diagram source'), {
      target: {
        value: 'flowchart TD\n  A[Paste] --> B[Preview]\n',
      },
    })

    await waitFor(() => {
      expect(renderMock).toHaveBeenCalledWith(expect.any(String), 'flowchart TD\n  A[Paste] --> B[Preview]\n')
    })

    expect(screen.getByLabelText('Editable diagram source')).toHaveValue(
      'flowchart TD\n  A[Paste] --> B[Preview]\n'
    )
  })

  it('hydrates the pasted diagram draft from local storage after refresh', async () => {
    window.localStorage.setItem(
      'bijmantra-dev-arielma-diagram-state',
      JSON.stringify({
        sourceMode: 'pasted',
        pastedSource: 'flowchart TD\n  Draft[Saved] --> Preview[Restored]\n',
      })
    )

    render(
      <Tabs value="arielma" onValueChange={() => {}}>
        <ArielmaTab parsedBoard={defaultDeveloperMasterBoard} jsonError={null} />
      </Tabs>
    )

    expect(screen.getByRole('button', { name: 'Paste code' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByLabelText('Editable diagram source')).toHaveValue(
      'flowchart TD\n  Draft[Saved] --> Preview[Restored]\n'
    )

    await waitFor(() => {
      expect(renderMock).toHaveBeenCalledWith(
        expect.any(String),
        'flowchart TD\n  Draft[Saved] --> Preview[Restored]\n'
      )
    })
  })

  it('exports the rendered diagram as an svg file', async () => {
    const createObjectURL = vi.fn(() => 'blob:diagram')
    const revokeObjectURL = vi.fn()
    const anchorClicks = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    const createdAnchors: HTMLAnchorElement[] = []
    const createElement = document.createElement.bind(document)

    vi.spyOn(document, 'createElement').mockImplementation(((tagName: string) => {
      const element = createElement(tagName)
      if (tagName === 'a') {
        createdAnchors.push(element as HTMLAnchorElement)
      }
      return element
    }) as typeof document.createElement)

    window.URL.createObjectURL = createObjectURL
    window.URL.revokeObjectURL = revokeObjectURL

    render(
      <Tabs value="arielma" onValueChange={() => {}}>
        <ArielmaTab parsedBoard={defaultDeveloperMasterBoard} jsonError={null} />
      </Tabs>
    )

    await waitFor(() => {
      expect(renderMock).toHaveBeenCalled()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Export SVG' }))

    expect(createObjectURL).toHaveBeenCalledTimes(1)
    expect(createdAnchors[0]?.download).toBe('bijmantra-developer-control-plane-system-topology.svg')
    expect(createdAnchors[0]?.href).toBe('blob:diagram')
    expect(anchorClicks).toHaveBeenCalledTimes(1)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:diagram')
  })
})