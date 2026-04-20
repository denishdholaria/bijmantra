import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { MahasarthiStrata } from './MahasarthiStrata'

const mockSystemState = {
  openDesktopTool: vi.fn(),
}

vi.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div {...props}>{children}</div>,
  },
}))

vi.mock('@/framework/registry', () => ({
  useDivisionRegistry: () => ({ navigableDivisions: [] }),
}))

vi.mock('@/store/workspaceStore', () => ({
  useActiveWorkspace: () => null,
  useWorkspaceStore: () => null,
}))

vi.mock('@/store/dockStore', () => ({
  useDockStore: () => ({ pinnedItems: [], recentItems: [] }),
}))

vi.mock('@/framework/registry/futureDivisions', () => ({
  futureDivisions: [],
}))

vi.mock('@/store/systemStore', () => ({
  useSystemStore: (selector: (state: typeof mockSystemState) => unknown) => selector(mockSystemState),
}))

vi.mock('./StrataFolder', () => ({
  StrataFolder: () => <div data-testid="strata-folder" />,
}))

afterEach(() => {
  vi.restoreAllMocks()
  mockSystemState.openDesktopTool.mockReset()
})

describe('MahasarthiStrata', () => {
  it('opens desktop tools from STRATA on desktop routes', () => {
    const onClose = vi.fn()
    const onNavigate = vi.fn()

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <MahasarthiStrata isOpen={true} onClose={onClose} onNavigate={onNavigate} />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: 'File System' }))
    fireEvent.click(screen.getByRole('button', { name: 'Editor' }))

    expect(mockSystemState.openDesktopTool).toHaveBeenNthCalledWith(1, 'filesystem')
    expect(mockSystemState.openDesktopTool).toHaveBeenNthCalledWith(2, 'editor')
    expect(onClose).toHaveBeenCalledTimes(2)
    expect(onNavigate).toHaveBeenCalledTimes(2)
  })
})