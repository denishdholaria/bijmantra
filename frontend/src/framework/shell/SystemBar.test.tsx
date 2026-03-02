import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { SystemBar } from './SystemBar'

const mockNavigate = vi.fn()

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

vi.mock('@/components/UserMenu', () => ({
  UserMenu: () => <div>User</div>,
}))

vi.mock('@/components/ai/ReevuTrigger', () => ({
  ReevuLogo: ({ className }: { className?: string }) => <div className={className}>R</div>,
}))

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
})
