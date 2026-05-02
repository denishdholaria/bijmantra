import { act, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { SystemBar } from './SystemBar'

const mockNavigate = vi.fn()
const mockLogout = vi.fn()
const mockSystemState = {
  desktopToolSurface: null as 'filesystem' | 'editor' | null,
  openDesktopTool: vi.fn(),
}

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('@/store/notificationStore', () => ({
  useNotificationStore: () => ({
    unreadCount: 0,
    toggleCenter: vi.fn(),
    isCenterOpen: false,
  }),
}))

vi.mock('@/store/reevuSidebarStore', () => ({
  useReevuSidebarStore: () => ({
    isOpen: false,
    toggle: vi.fn(),
  }),
}))

vi.mock('@/store/auth', () => ({
  useAuthStore: (selector: (state: { logout: () => void }) => unknown) =>
    selector({ logout: mockLogout }),
}))

vi.mock('@/components/UserMenu', () => ({
  UserMenu: () => <div>User</div>,
}))

vi.mock('@/components/ai/ReevuTrigger', () => ({
  ReevuLogo: ({ className }: { className?: string }) => <div className={className}>R</div>,
}))

vi.mock('@/store/systemStore', () => ({
  useSystemStore: (selector: (state: typeof mockSystemState) => unknown) => selector(mockSystemState),
}))

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
  mockSystemState.openDesktopTool.mockReset()
  mockSystemState.desktopToolSurface = null
})

describe('SystemBar', () => {
  it('does not render legacy Desktop button in app mode', () => {
    render(
      <MemoryRouter initialEntries={['/programs']}>
        <SystemBar />
      </MemoryRouter>
    )

    expect(screen.queryByRole('button', { name: /desktop/i })).not.toBeInTheDocument()
  })

  it('keeps home/logo button navigation to dashboard', () => {
    render(
      <MemoryRouter initialEntries={['/programs']}>
        <SystemBar />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByTitle('Home'))
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('shows a logout button and signs out to login', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <SystemBar />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /logout/i }))

    expect(mockLogout).toHaveBeenCalledTimes(1)
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  it('opens desktop tools from the system bar on desktop routes', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <SystemBar />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: 'File System' }))
    fireEvent.click(screen.getByRole('button', { name: 'Editor' }))

    expect(mockSystemState.openDesktopTool).toHaveBeenNthCalledWith(1, 'filesystem')
    expect(mockSystemState.openDesktopTool).toHaveBeenNthCalledWith(2, 'editor')
  })

  it('updates the local time label at the next minute boundary', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-03-15T10:05:30Z'))
    vi.spyOn(Date.prototype, 'toLocaleTimeString').mockImplementation(function (this: Date) {
      return `${String(this.getUTCHours()).padStart(2, '0')}:${String(this.getUTCMinutes()).padStart(2, '0')}`
    })

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <SystemBar />
      </MemoryRouter>
    )

    expect(screen.getByText('10:05')).toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(30_001)
    })

    expect(screen.getByText('10:06')).toBeInTheDocument()
  })
})
