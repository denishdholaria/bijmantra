import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { Breadcrumbs } from './MahasarthiBreadcrumbs'

vi.mock('@/store/workspaceStore', () => ({
  useActiveWorkspace: () => null,
}))

vi.mock('@/framework/registry/divisions', () => ({
  divisions: [
    {
      id: 'plant-sciences',
      name: 'Plant Sciences',
      route: '/programs',
      sections: [
        {
          id: 'crossing',
          name: 'Crossing',
          route: '/crosses',
          isAbsolute: true,
          items: [
            { id: 'planned-crosses', name: 'Planned Crosses', route: '/plannedcrosses', isAbsolute: true },
          ],
        },
      ],
    },
    {
      id: 'seed-operations',
      name: 'Seed Commerce',
      route: '/seed-operations',
      sections: [],
    },
  ],
}))

describe('MahasarthiBreadcrumbs', () => {
  it('injects division and section context for absolute section item routes', () => {
    render(
      <MemoryRouter initialEntries={['/plannedcrosses']}>
        <Breadcrumbs />
      </MemoryRouter>
    )

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Plant Sciences')).toBeInTheDocument()
    expect(screen.getByText('Crossing')).toBeInTheDocument()
    expect(screen.getByText('Planned Crosses')).toBeInTheDocument()
  })

  it('injects division context for shorthand division routes like /programs', () => {
    render(
      <MemoryRouter initialEntries={['/programs']}>
        <Breadcrumbs />
      </MemoryRouter>
    )

    expect(screen.getByText('Plant Sciences')).toBeInTheDocument()
    expect(screen.getByText('Programs')).toBeInTheDocument()
  })

  it('does not duplicate division label when first segment already matches division', () => {
    render(
      <MemoryRouter initialEntries={['/seed-operations/quality-gate']}>
        <Breadcrumbs />
      </MemoryRouter>
    )

    expect(screen.getAllByText('Seed Commerce')).toHaveLength(1)
  })
})
