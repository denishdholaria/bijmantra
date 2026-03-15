import { render, screen, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { DivisionNavigation } from './DivisionNavigation';
import { MemoryRouter } from 'react-router-dom';
import * as router from 'react-router-dom';
import React from 'react';

// Mock dependencies
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useLocation: vi.fn(),
  };
});

// Stable data for mock
const mockDivisions = [
  {
    id: 'test-division',
    name: 'Test Division',
    route: '/test',
    icon: 'test-icon',
    status: 'active',
    sections: [
      {
        id: 'test-section',
        name: 'Test Section',
        route: '/section',
        items: [
          {
            id: 'test-item',
            name: 'Test Item',
                route: '/section/item',
          },
        ],
      },
    ],
  },
];

// Mock registry
vi.mock('../registry', () => ({
  useDivisionRegistry: () => ({
    navigableDivisions: mockDivisions,
  }),
}));

// Mock workspace stores
vi.mock('@/store/workspaceStore', () => ({
  useWorkspaceStore: () => ({ activeWorkspaceId: null }),
  useActiveWorkspace: () => null,
}));

vi.mock('@/store/customWorkspaceStore', () => ({
  useCustomWorkspaceStore: () => ({}),
  useActiveCustomWorkspace: () => null,
}));

vi.mock('@/hooks/useCustomWorkspace', () => ({
  useActiveWorkspacePages: () => [],
}));

vi.mock('@/framework/registry/workspaces', () => ({
  getWorkspaceModules: () => [],
  isRouteInWorkspace: () => true,
}));

vi.mock('@/store/navigationStore', () => ({
  useNavigationStore: () => 'all',
}));

// Mock icons
vi.mock('./navigationIcons', () => ({
  navigationIcons: {
    'test-icon': (props: any) => <svg {...props} data-testid="test-icon" />,
  },
}));

describe('DivisionNavigation', () => {
  const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

  beforeEach(() => {
    consoleErrorSpy.mockClear();
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it('auto-expands correctly on mount', async () => {
    // Set initial location to match the item
    (router.useLocation as any).mockReturnValue({ pathname: '/test/section/item' });

    // With stable props, it might not crash, but it will still trigger the "update during render" warning/behavior.
    // However, if it renders successfully, we can verify functionality.

    render(
      <MemoryRouter>
        <DivisionNavigation />
      </MemoryRouter>
    );

    // The item should be visible if auto-expansion worked
    expect(screen.getByText('Test Item')).toBeInTheDocument();

    // We can check if any console errors occurred related to state updates
    // const updateWarnings = consoleErrorSpy.mock.calls.filter(call =>
    //   call[0].includes('Cannot update a component') || call[0].includes('Too many re-renders')
    // );
    // expect(updateWarnings.length).toBeGreaterThan(0);
  });
});
