import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, UNSAFE_NavigationContext, useNavigate } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { BijMantraDesktop } from './BijMantraDesktop'

const mockSystemState = {
  isStrataOpen: false,
  desktopToolSurface: 'editor' as 'filesystem' | 'editor' | null,
  lastDesktopToolSurface: 'editor' as 'filesystem' | 'editor' | null,
  setIsInShell: vi.fn(),
  setStrataOpen: vi.fn(),
  openDesktopTool: vi.fn(),
  closeDesktopTool: vi.fn(),
}

const mockAuthState = {
  isAuthenticated: false,
  user: null as { organization_id: number } | null,
}

const mockCapabilityAccessState = {
  loadForOrganization: vi.fn(),
  reset: vi.fn(),
}

const mockDockState = {
  recordVisit: vi.fn(),
}

let mockWorkbenchDirty = false
let capturedBlocker: ((transition: { retry: () => void }) => void) | null = null

vi.mock('@/store/systemStore', () => ({
  useSystemStore: (selector: (state: typeof mockSystemState) => unknown) => selector(mockSystemState),
}))

vi.mock('@/store/auth', () => ({
  useAuthStore: (selector: (state: typeof mockAuthState) => unknown) => selector(mockAuthState),
}))

vi.mock('@/store/capabilityAccessStore', () => ({
  useCapabilityAccessStore: (selector: (state: typeof mockCapabilityAccessState) => unknown) =>
    selector(mockCapabilityAccessState),
}))

vi.mock('@/store/dockStore', () => ({
  useDockStore: (selector: (state: typeof mockDockState) => unknown) => selector(mockDockState),
}))

vi.mock('@/framework/registry', () => ({
  useDivisionRegistry: () => ({
    activeDivisions: [
      {
        id: 'plant-sciences',
        name: 'Plant Sciences',
        description: 'Breeding, genomics, phenotyping, and field operations',
        icon: 'Seedling',
        route: '/programs',
        requiredPermissions: [],
        status: 'active',
        version: '1.0.0',
        sections: [
          {
            id: 'breeding',
            name: 'Breeding',
            route: '/programs',
            icon: 'Wheat',
            isAbsolute: true,
            items: [
              { id: 'programs', name: 'Programs', route: '/programs', isAbsolute: true },
            ],
          },
        ],
      },
    ],
  }),
}))

vi.mock('./SystemBar', async () => {
  return {
    SystemBar: () => <div data-testid="system-bar" />,
  }
})

vi.mock('./ShellSidebar', () => ({
  ShellSidebar: () => <div data-testid="shell-sidebar" />,
}))

vi.mock('./ContextMenu', () => ({
  ContextMenu: () => null,
  useContextMenu: () => ({ onContextMenu: vi.fn() }),
}))

vi.mock('./NotificationCenter', () => ({
  NotificationCenter: () => null,
}))

vi.mock('./CommandPalette', () => ({
  CommandPalette: () => null,
}))

vi.mock('@/store/notificationStore', () => ({
  useNotificationStore: () => ({ addNotification: vi.fn() }),
}))

vi.mock('./ShellSubsystemBoundary', () => ({
  ShellSubsystemBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock('./DesktopWorkbench', async () => {
  const React = await vi.importActual<typeof import('react')>('react')

  return {
    DesktopWorkbench: ({
      surface,
      onDirtyStateChange,
    }: {
      surface: string | null
      onDirtyStateChange?: (isDirty: boolean) => void
    }) => {
      React.useEffect(() => {
        onDirtyStateChange?.(mockWorkbenchDirty)
        return () => onDirtyStateChange?.(false)
      }, [onDirtyStateChange])

      return <div data-testid="desktop-workbench">{surface}</div>
    },
  }
})

vi.mock('@/components/navigation/MahasarthiStrata', () => ({
  MahasarthiStrata: () => null,
}))

vi.mock('@/components/ai/ReevuSidebar', () => ({
  ReevuSidebar: () => null,
}))

afterEach(() => {
  vi.restoreAllMocks()
  mockWorkbenchDirty = false
  capturedBlocker = null
  mockSystemState.isStrataOpen = false
  mockSystemState.desktopToolSurface = 'editor'
  mockSystemState.lastDesktopToolSurface = 'editor'
  mockSystemState.setIsInShell.mockReset()
  mockSystemState.setStrataOpen.mockReset()
  mockSystemState.openDesktopTool.mockReset()
  mockSystemState.closeDesktopTool.mockReset()
  mockAuthState.isAuthenticated = false
  mockAuthState.user = null
  mockCapabilityAccessState.loadForOrganization.mockReset()
  mockCapabilityAccessState.reset.mockReset()
  mockDockState.recordVisit.mockReset()
})

describe('BijMantraDesktop', () => {
  function LeaveDesktopButton() {
    const navigate = useNavigate()

    return <button onClick={() => navigate('/programs')}>Leave Desktop</button>
  }

  it('closes the desktop tool surface when leaving desktop routes', async () => {
    render(
      <MemoryRouter initialEntries={['/gateway']}>
        <BijMantraDesktop />
        <LeaveDesktopButton />
      </MemoryRouter>
    )

    expect(mockSystemState.openDesktopTool).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Leave Desktop' }))

    await waitFor(() => {
      expect(mockSystemState.closeDesktopTool).toHaveBeenCalledTimes(1)
    })
  })

  it('shows a clean desktop wallpaper when no desktop tool is active', async () => {
    mockSystemState.desktopToolSurface = null
    mockSystemState.lastDesktopToolSurface = 'filesystem'

    render(
      <MemoryRouter initialEntries={['/gateway']}>
        <BijMantraDesktop />
      </MemoryRouter>
    )

    expect(mockSystemState.openDesktopTool).not.toHaveBeenCalled()
    expect(screen.getByText('BijMantra')).toBeInTheDocument()
    expect(screen.getByText('Agricultural Intelligence System')).toBeInTheDocument()
    expect(screen.queryByTestId('desktop-workbench')).not.toBeInTheDocument()
  })

  it('renders dashboard content as an app route instead of the desktop workbench', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <BijMantraDesktop>
          <div data-testid="dashboard-app">Dashboard app</div>
        </BijMantraDesktop>
      </MemoryRouter>
    )

    expect(screen.getByTestId('dashboard-app')).toBeInTheDocument()
    expect(screen.getByTestId('shell-sidebar')).toBeInTheDocument()
    expect(screen.queryByTestId('desktop-workbench')).not.toBeInTheDocument()
  })

  it('records app route visits from the active shell for recent context', async () => {
    render(
      <MemoryRouter initialEntries={['/programs']}>
        <BijMantraDesktop>
          <div>Programs app</div>
        </BijMantraDesktop>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(mockDockState.recordVisit).toHaveBeenCalledWith({
        id: 'plant-sciences-breeding-programs',
        path: '/programs',
        label: 'Programs',
        icon: 'Wheat',
      })
    })
  })

  it('loads capability access for the authenticated organization', async () => {
    mockAuthState.isAuthenticated = true
    mockAuthState.user = { organization_id: 7 }

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <BijMantraDesktop />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(mockCapabilityAccessState.loadForOrganization).toHaveBeenCalledWith(7)
    })
    expect(mockCapabilityAccessState.reset).not.toHaveBeenCalled()
  })

  it('resets capability access when the shell has no authenticated organization', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <BijMantraDesktop />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(mockCapabilityAccessState.reset).toHaveBeenCalled()
    })
  })

  it('blocks route leave when dirty workbench changes are cancelled', async () => {
    mockWorkbenchDirty = true
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const retrySpy = vi.fn()

    render(
      <MemoryRouter initialEntries={['/gateway']}>
        <UNSAFE_NavigationContext.Provider
          value={{
            basename: '/',
            navigator: {
              block: (blocker: (transition: { retry: () => void }) => void) => {
                capturedBlocker = blocker
                return vi.fn()
              },
            },
            static: false,
            future: {},
          } as never}
        >
          <BijMantraDesktop />
        </UNSAFE_NavigationContext.Provider>
      </MemoryRouter>
    )

    capturedBlocker?.({ retry: retrySpy })

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalled()
    })

    expect(mockSystemState.closeDesktopTool).not.toHaveBeenCalled()
    expect(retrySpy).not.toHaveBeenCalled()
    expect(screen.getByTestId('desktop-workbench')).toHaveTextContent('editor')
  })
})
