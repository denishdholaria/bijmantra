import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  CustomWorkspaceIndicator,
  DivisionNavigationEmptyState,
  DivisionNavigationLabel,
  SystemWorkspaceIndicator,
} from './DivisionNavigationParts'

describe('DivisionNavigationParts', () => {
  it('renders a custom workspace indicator', () => {
    render(
      <CustomWorkspaceIndicator
        workspace={{
          id: 'custom-1',
          name: 'Field Ops',
          icon: 'Leaf',
          color: 'green',
          pageIds: [],
          createdAt: '2026-03-12T00:00:00.000Z',
          updatedAt: '2026-03-12T00:00:00.000Z',
        }}
      />,
    )

    expect(screen.getByText('Custom')).toBeInTheDocument()
    expect(screen.getByText('Field Ops')).toBeInTheDocument()
  })

  it('renders a system workspace indicator', () => {
    render(
      <SystemWorkspaceIndicator
        workspace={{
          id: 'research',
          name: 'Research',
          description: 'Research workspace',
          icon: 'Microscope',
          color: 'from-purple-500 to-violet-600',
          bgColor: 'bg-purple-50',
          landingRoute: '/research',
          modules: ['analytics'],
          targetUsers: [],
          pageCount: 1,
          isBrAPIAligned: false,
        }}
      />,
    )

    expect(screen.getByText('Research')).toBeInTheDocument()
  })

  it('renders the correct navigation label', () => {
    const { rerender } = render(
      <DivisionNavigationLabel isCustomWorkspaceActive={true} hasActiveWorkspace={false} />,
    )

    expect(screen.getByText('Selected Pages')).toBeInTheDocument()

    rerender(<DivisionNavigationLabel isCustomWorkspaceActive={false} hasActiveWorkspace={true} />)
    expect(screen.getByText('Modules')).toBeInTheDocument()

    rerender(<DivisionNavigationLabel isCustomWorkspaceActive={false} hasActiveWorkspace={false} />)
    expect(screen.getByText('All Modules')).toBeInTheDocument()
  })

  it('renders the appropriate empty state message', () => {
    const { rerender } = render(
      <DivisionNavigationEmptyState
        isCustomWorkspaceActive={true}
        customWorkspaceName="Field Ops"
      />,
    )

    expect(screen.getByText('No pages in Field Ops')).toBeInTheDocument()

    rerender(
      <DivisionNavigationEmptyState
        isCustomWorkspaceActive={false}
        activeWorkspaceName="Research"
      />,
    )

    expect(screen.getByText('No modules available for Research')).toBeInTheDocument()
  })
})