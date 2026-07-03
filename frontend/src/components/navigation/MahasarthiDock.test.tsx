import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { MahasarthiDock } from './MahasarthiDock'

vi.mock('@/store/dockStore', () => ({
  useDockStore: () => ({
    unpinItem: vi.fn(),
    reorderPinned: vi.fn(),
  }),
}))

vi.mock('@/hooks/useMahasarthiNavigation', () => ({
  useMahasarthiNavigation: () => ({
    activeWorkspace: null,
    gatewayPinnedItems: [],
    gatewayRecentItems: [],
  }),
}))

function renderMobileDock(initialRoute = '/gateway') {
  render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <MahasarthiDock
        isMobile
        onBrowserOpen={vi.fn()}
        onSearchOpen={vi.fn()}
        onNavigate={vi.fn()}
      />
    </MemoryRouter>
  )
}

describe('MahasarthiDock', () => {
  it('uses the gateway as the mobile Home destination', () => {
    renderMobileDock()

    expect(screen.getByRole('link', { name: 'Gateway Home' })).toHaveAttribute('href', '/gateway')
  })

  it('marks the mobile Home tab active on the gateway shell', () => {
    renderMobileDock('/gateway')

    expect(screen.getByRole('link', { name: 'Gateway Home' })).toHaveAttribute('aria-current', 'page')
  })

  it('does not mark the mobile Home tab active on the dashboard app', () => {
    renderMobileDock('/dashboard')

    expect(screen.getByRole('link', { name: 'Gateway Home' })).not.toHaveAttribute('aria-current')
  })
})
