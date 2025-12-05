/**
 * Layout Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock heavy components to speed up tests
vi.mock('@/components/SmartNavigation', () => ({
  SmartNavigation: () => <nav data-testid="smart-nav">Smart Navigation</nav>,
}))

vi.mock('@/components/CommandPalette', () => ({
  CommandPalette: () => null,
}))

vi.mock('@/components/UserMenu', () => ({
  UserMenu: () => <div data-testid="user-menu">User Menu</div>,
}))

vi.mock('@/components/ai/Veena', () => ({
  Veena: () => <div data-testid="veena">Veena AI</div>,
}))

vi.mock('@/components/KeyboardShortcuts', () => ({
  useKeyboardShortcuts: () => {},
}))

vi.mock('@/components/RoleSwitcher', () => ({
  RoleIndicator: () => <div data-testid="role-indicator">Role</div>,
}))

vi.mock('@/components/ToastContainer', () => ({
  ToastContainer: () => null,
}))

vi.mock('@/components/PresenceIndicator', () => ({
  PresenceIndicator: () => <div data-testid="presence">Presence</div>,
}))

vi.mock('@/components/SyncStatusIndicator', () => ({
  SyncStatusIndicator: () => <div data-testid="sync-status">Sync</div>,
  OfflineBanner: () => null,
}))

vi.mock('@/components/notifications', () => ({
  NotificationProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  NotificationBell: () => <div data-testid="notification-bell">Bell</div>,
}))

import { Layout } from './Layout'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the layout with children', () => {
    renderWithProviders(
      <Layout>
        <div data-testid="child-content">Test Content</div>
      </Layout>
    )

    expect(screen.getByTestId('child-content')).toBeInTheDocument()
  })

  it('should render the Bijmantra logo/brand', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )

    // Multiple instances exist (sidebar + footer), so use getAllByText
    const brandElements = screen.getAllByText(/Bijmantra/)
    expect(brandElements.length).toBeGreaterThan(0)
  })

  it('should render the command palette trigger with keyboard shortcut', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )

    expect(screen.getByText('⌘K')).toBeInTheDocument()
  })

  it('should render header components', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )

    expect(screen.getByTestId('role-indicator')).toBeInTheDocument()
    expect(screen.getByTestId('sync-status')).toBeInTheDocument()
    expect(screen.getByTestId('presence')).toBeInTheDocument()
    expect(screen.getByTestId('notification-bell')).toBeInTheDocument()
  })

  it('should render footer with copyright', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )

    expect(screen.getByText(/© 2025 Bijmantra/)).toBeInTheDocument()
  })

  it('should render Veena AI assistant', () => {
    renderWithProviders(
      <Layout>
        <div>Content</div>
      </Layout>
    )

    expect(screen.getByTestId('veena')).toBeInTheDocument()
  })
})
