import { act, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { useCapabilityAccessStore } from '@/store/capabilityAccessStore'
import { ShellSidebar } from './ShellSidebar'

vi.mock('@/framework/registry/navigation-source', () => {
  const navigationTree = [
    {
      id: 'plant-sciences',
      label: 'Plant Sciences',
      icon: 'Seedling',
      path: '/programs',
      divisionId: 'plant-sciences',
      description: 'Breeding stack',
      children: [
        {
          id: 'breeding',
          label: 'Breeding',
          path: '/programs',
          parentPath: '/programs',
          divisionId: 'plant-sciences',
          children: [
            {
              id: 'programs',
              label: 'Programs',
              path: '/programs',
              parentPath: '/programs',
              divisionId: 'plant-sciences',
            },
          ],
        },
        {
          id: 'crossing',
          label: 'Crossing',
          path: '/plannedcrosses',
          parentPath: '/programs',
          divisionId: 'plant-sciences',
          children: [
            {
              id: 'crosses',
              label: 'Crosses',
              path: '/crosses',
              parentPath: '/crosses',
              divisionId: 'plant-sciences',
            },
            {
              id: 'planned-crosses',
              label: 'Planned Crosses',
              path: '/plannedcrosses',
              parentPath: '/crosses',
              divisionId: 'plant-sciences',
            },
          ],
        },
      ],
    },
    {
      id: 'knowledge',
      label: 'Knowledge',
      icon: 'BookOpen',
      path: '/knowledge',
      divisionId: 'knowledge',
      description: 'Knowledge apps',
      children: [
        {
          id: 'knowledge-graph',
          label: 'Knowledge Graph',
          path: '/knowledge-graph',
          parentPath: '/knowledge',
          divisionId: 'knowledge',
        },
      ],
    },
  ]

  return {
    navigationTree,
    buildNavigationTree: () => navigationTree,
  }
})

vi.mock('@/store/systemStore', () => ({
  useSystemStore: () => ({
    sidebarCollapsed: false,
    toggleSidebar: vi.fn(),
  }),
}))

describe('ShellSidebar', () => {
  beforeEach(() => {
    useCapabilityAccessStore.getState().reset()
  })

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

  it('filters capability-owned shell entries from install state', () => {
    const { rerender } = render(
      <MemoryRouter initialEntries={['/knowledge']}>
        <ShellSidebar />
      </MemoryRouter>
    )

    expect(screen.queryByText('Knowledge Graph')).not.toBeInTheDocument()

    act(() => {
      useCapabilityAccessStore.setState({
        accessContext: {
          installedCapabilities: ['intelligence_fabric.knowledge_graph'],
          grantedPermissions: [],
          dataScopes: [],
        },
      })
    })

    rerender(
      <MemoryRouter initialEntries={['/knowledge']}>
        <ShellSidebar />
      </MemoryRouter>
    )

    expect(screen.getByText('Knowledge Graph')).toBeInTheDocument()
  })
})
