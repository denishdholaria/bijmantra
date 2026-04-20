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

let mockWorkbenchDirty = false
let capturedBlocker: ((transition: { retry: () => void }) => void) | null = null

vi.mock('@/store/systemStore', () => ({
  useSystemStore: (selector: (state: typeof mockSystemState) => unknown) => selector(mockSystemState),
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

vi.mock('./DesktopWorkbench', () => ({
  DesktopWorkbench: ({
    surface,
    onDirtyStateChange,
  }: {
    surface: string | null
    onDirtyStateChange?: (isDirty: boolean) => void
  }) => {
    const React = require('react') as typeof import('react')

    React.useEffect(() => {
      onDirtyStateChange?.(mockWorkbenchDirty)
      return () => onDirtyStateChange?.(false)
    }, [onDirtyStateChange])

    return <div data-testid="desktop-workbench">{surface}</div>
  },
}))

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
})

describe('BijMantraDesktop', () => {
  function LeaveDesktopButton() {
    const navigate = useNavigate()

    return <button onClick={() => navigate('/programs')}>Leave Desktop</button>
  }

  it('closes the desktop tool surface when leaving desktop routes', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
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

  it('restores the remembered desktop tool when the desktop opens without an active surface', async () => {
    mockSystemState.desktopToolSurface = null
    mockSystemState.lastDesktopToolSurface = 'filesystem'

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <BijMantraDesktop />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(mockSystemState.openDesktopTool).toHaveBeenCalledWith('filesystem')
    })
  })

  it('blocks route leave when dirty workbench changes are cancelled', async () => {
    mockWorkbenchDirty = true
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const retrySpy = vi.fn()

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
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