import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { ShellSidebar } from './ShellSidebar'

vi.mock('@/framework/registry', () => ({
  useDivisionRegistry: () => ({
    navigableDivisions: [
      {
        id: 'plant-sciences',
        name: 'Plant Sciences',
        icon: 'Seedling',
        route: '/programs',
        status: 'active',
        description: 'Breeding stack',
        sections: [
          {
            id: 'breeding',
            name: 'Breeding',
            route: '/programs',
            isAbsolute: true,
            items: [
              { id: 'programs', name: 'Programs', route: '/programs', isAbsolute: true },
            ],
          },
          {
            id: 'crossing',
            name: 'Crossing',
            route: '/crosses',
            isAbsolute: true,
            items: [
              { id: 'crosses', name: 'Crosses', route: '/crosses', isAbsolute: true },
              { id: 'planned-crosses', name: 'Planned Crosses', route: '/plannedcrosses', isAbsolute: true },
            ],
          },
        ],
      },
    ],
  }),
}))

vi.mock('@/store/systemStore', () => ({
  useSystemStore: () => ({
    sidebarCollapsed: false,
    toggleSidebar: vi.fn(),
  }),
}))

describe('ShellSidebar', () => {
  it('shows only active section sub-pages on absolute app routes', () => {
    render(
      <MemoryRouter initialEntries={['/plannedcrosses']}>
        <ShellSidebar />
      </MemoryRouter>
    )

    expect(screen.getByText('Section')).toBeInTheDocument()
    expect(screen.getByText('Crossing')).toBeInTheDocument()
    expect(screen.getByText('Crosses')).toBeInTheDocument()
    expect(screen.getByText('Planned Crosses')).toBeInTheDocument()
    expect(screen.queryByText('Breeding')).not.toBeInTheDocument()
  })
})
