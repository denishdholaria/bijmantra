/**
 * Main Layout Component with Smart Navigation
 * Features: Command Palette (⌘K), Smart Nav, Notifications, Sync Status
 * Restored with error boundaries for stability
 */

import { Link, useLocation } from 'react-router-dom'
import { useState, useEffect, Suspense, lazy, Component, ReactNode } from 'react'
import { HelpCircle, Settings, Bell, Search } from 'lucide-react'

// Error boundary for lazy components
class ComponentErrorBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode; fallback?: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  render() {
    if (this.state.hasError) {
      return this.props.fallback || null
    }
    return this.props.children
  }
}

// Lazy load components with error handling
const SmartNavigation = lazy(() => import('@/components/SmartNavigation'))
const CommandPalette = lazy(() => 
  import('@/components/CommandPalette').then(m => ({ default: m.CommandPalette }))
)
const UserMenu = lazy(() => 
  import('@/components/UserMenu').then(m => ({ default: m.UserMenu }))
)
const Veena = lazy(() => 
  import('@/components/ai/Veena').then(m => ({ default: m.Veena }))
)

// Direct imports for lightweight components
import { NotificationProvider, NotificationBell } from '@/components/notifications'
import { SyncStatusIndicator, OfflineBanner } from '@/components/SyncStatusIndicator'
import { ToastContainer } from '@/components/ToastContainer'
import { MobileBottomNav } from '@/components/navigation/MobileBottomNav'
import { QuickActionFAB } from '@/components/navigation/QuickActionFAB'
import { WhatsNew, useWhatsNew } from '@/components/WhatsNew'
import { KeyboardShortcuts, useKeyboardShortcuts } from '@/components/KeyboardShortcuts'
import { OnboardingTour, useOnboardingTour } from '@/components/OnboardingTour'
import { WorkspaceSwitcher } from '@/components/navigation/WorkspaceSwitcher'

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center p-4">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-prakruti-patta" />
    </div>
  )
}


// Simple nav items for fallback
const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/programs', label: 'Programs', icon: '🌾' },
  { path: '/trials', label: 'Trials', icon: '🧪' },
  { path: '/studies', label: 'Studies', icon: '📈' },
  { path: '/locations', label: 'Locations', icon: '📍' },
  { path: '/germplasm', label: 'Germplasm', icon: '🌱' },
  { path: '/seedlots', label: 'Seed Lots', icon: '📦' },
  { path: '/crosses', label: 'Crosses', icon: '🧬' },
  { path: '/traits', label: 'Traits', icon: '🔬' },
  { path: '/observations', label: 'Observations', icon: '📋' },
  { path: '/samples', label: 'Samples', icon: '🧫' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
  { path: '/help', label: 'Help', icon: '❓' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const { showWhatsNew, setShowWhatsNew, dismissWhatsNew } = useWhatsNew()
  const { showShortcuts, setShowShortcuts } = useKeyboardShortcuts()
  const { showTour, setShowTour } = useOnboardingTour()

  // Global keyboard shortcut for Command Palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen(true)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const closeMobileMenu = () => setMobileMenuOpen(false)

  const currentPageLabel = navItems.find(item => 
    location.pathname === item.path || location.pathname.startsWith(item.path + '/')
  )?.label || 'Bijmantra'

  return (
    <NotificationProvider>
    <div className="min-h-screen bg-gradient-to-br from-prakruti-dhool-50 to-prakruti-patta-50/30 dark:from-prakruti-dhool-900 dark:to-prakruti-dhool-900 flex flex-col">
      {/* Offline Banner */}
      <ComponentErrorBoundary>
        <OfflineBanner />
      </ComponentErrorBoundary>
      
      <div className="flex flex-1">
        {/* Mobile Overlay */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={closeMobileMenu} />
        )}

        {/* Sidebar */}
        <aside className={`fixed left-0 top-0 h-full bg-white dark:bg-prakruti-dhool-900 border-r border-prakruti-dhool-200 dark:border-prakruti-dhool-800 shadow-xl transition-all duration-300 z-50 flex flex-col
          ${sidebarCollapsed ? 'w-16' : 'w-64'}
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
        >
          {/* Logo */}
          <div className="h-14 flex items-center justify-between px-3 border-b border-prakruti-dhool-200 dark:border-prakruti-dhool-800 flex-shrink-0">
            {!sidebarCollapsed ? (
              <Link to="/dashboard" className="flex items-center gap-2 group">
                <div className="w-8 h-8 bg-gradient-to-br from-prakruti-patta to-prakruti-patta-dark rounded-lg flex items-center justify-center shadow-md">
                  <span className="text-lg">🌱</span>
                </div>
                <span className="text-base font-bold bg-gradient-to-r from-prakruti-patta to-prakruti-patta-dark bg-clip-text text-transparent">
                  Bijmantra
                </span>
              </Link>
            ) : (
              <Link to="/dashboard" className="mx-auto">
                <div className="w-8 h-8 bg-gradient-to-br from-prakruti-patta to-prakruti-patta-dark rounded-lg flex items-center justify-center shadow-md">
                  <span className="text-lg">🌱</span>
                </div>
              </Link>
            )}
          </div>


          {/* Navigation */}
          <div className="flex-1 overflow-y-auto">
            <Suspense fallback={<SimpleNav items={navItems} collapsed={sidebarCollapsed} onNavigate={closeMobileMenu} currentPath={location.pathname} />}>
              <ComponentErrorBoundary fallback={<SimpleNav items={navItems} collapsed={sidebarCollapsed} onNavigate={closeMobileMenu} currentPath={location.pathname} />}>
                <SmartNavigation collapsed={sidebarCollapsed} onNavigate={closeMobileMenu} />
              </ComponentErrorBoundary>
            </Suspense>
          </div>

          {/* Sidebar Footer */}
          <div className="flex-shrink-0 p-2 border-t border-prakruti-dhool-200 dark:border-prakruti-dhool-800 bg-white dark:bg-prakruti-dhool-900">
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="w-full flex items-center justify-center gap-2 px-2 py-1.5 text-sm text-prakruti-dhool-600 dark:text-prakruti-dhool-400 hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 rounded-md hidden lg:flex"
            >
              <span>{sidebarCollapsed ? '→' : '←'}</span>
              {!sidebarCollapsed && <span>Collapse</span>}
            </button>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className={`flex-1 transition-all duration-300 ${sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'}`}>
          {/* Top Bar */}
          <header className="h-14 bg-white/90 dark:bg-prakruti-dhool-900/90 backdrop-blur-md border-b border-prakruti-dhool-200 dark:border-prakruti-dhool-800 sticky top-0 z-40 flex items-center justify-between px-4 lg:px-6">
            <div className="flex items-center gap-4">
              {/* Mobile menu toggle */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 rounded-lg"
                aria-label="Toggle menu"
              >
                <svg className="w-5 h-5 text-prakruti-dhool-700 dark:text-prakruti-dhool-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {mobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
              
              {/* Workspace Switcher */}
              <ComponentErrorBoundary>
                <WorkspaceSwitcher showLabel={true} />
              </ComponentErrorBoundary>
              
              {/* Page title */}
              <h2 className="text-base font-semibold text-prakruti-dhool-800 dark:text-prakruti-dhool-100 hidden sm:block">
                {currentPageLabel}
              </h2>
            </div>

            {/* Center - Command Palette Trigger */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-400 bg-prakruti-dhool-100 dark:bg-prakruti-dhool-800 hover:bg-prakruti-dhool-200 dark:hover:bg-prakruti-dhool-700 rounded-lg transition-colors border border-prakruti-dhool-200 dark:border-prakruti-dhool-700"
            >
              <Search className="w-4 h-4" />
              <span className="hidden md:inline">Search...</span>
              <kbd className="hidden lg:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-xs bg-white dark:bg-prakruti-dhool-700 text-prakruti-dhool-600 dark:text-prakruti-dhool-300 rounded border border-prakruti-dhool-300 dark:border-prakruti-dhool-600 font-mono">
                ⌘K
              </kbd>
            </button>

            
            {/* Right side */}
            <div className="flex items-center gap-2">
              {/* Mobile search */}
              <button
                onClick={() => setCommandPaletteOpen(true)}
                className="sm:hidden p-2 text-prakruti-dhool-600 dark:text-prakruti-dhool-400 hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 rounded-lg"
                aria-label="Search"
              >
                <Search className="w-5 h-5" />
              </button>
              
              {/* Sync Status */}
              <ComponentErrorBoundary>
                <SyncStatusIndicator />
              </ComponentErrorBoundary>
              
              {/* Notification Bell */}
              <ComponentErrorBoundary>
                <NotificationBell />
              </ComponentErrorBoundary>
              
              {/* Help */}
              <Link 
                to="/help" 
                className="p-2 text-prakruti-dhool-600 dark:text-prakruti-dhool-400 hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 rounded-lg"
                aria-label="Help"
              >
                <HelpCircle className="w-5 h-5" />
              </Link>
              
              {/* Settings */}
              <Link 
                to="/settings" 
                className="p-2 text-prakruti-dhool-600 dark:text-prakruti-dhool-400 hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 rounded-lg"
                aria-label="Settings"
              >
                <Settings className="w-5 h-5" />
              </Link>
              
              {/* User Menu */}
              <Suspense fallback={<div className="w-8 h-8 bg-prakruti-dhool-200 dark:bg-prakruti-dhool-700 rounded-full animate-pulse" />}>
                <ComponentErrorBoundary fallback={
                  <Link to="/profile" className="w-8 h-8 bg-prakruti-patta-pale dark:bg-prakruti-patta/20 rounded-full flex items-center justify-center text-prakruti-patta dark:text-prakruti-patta-light text-sm font-medium">
                    U
                  </Link>
                }>
                  <UserMenu />
                </ComponentErrorBoundary>
              </Suspense>
            </div>
          </header>
          
          {/* Command Palette */}
          <Suspense fallback={null}>
            <ComponentErrorBoundary>
              <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />
            </ComponentErrorBoundary>
          </Suspense>

          {/* Main Content */}
          <main className="p-4 lg:p-6 min-h-[calc(100vh-56px)] pb-20 lg:pb-6">
            <Suspense fallback={<LoadingFallback />}>
              {children}
            </Suspense>
          </main>

          {/* Footer */}
          <footer className="bg-white/80 dark:bg-prakruti-dhool-900/80 backdrop-blur-md border-t border-prakruti-dhool-200 dark:border-prakruti-dhool-800 px-4 lg:px-6 py-3">
            <div className="flex items-center justify-between text-xs text-prakruti-dhool-500 dark:text-prakruti-dhool-400">
              <span>© 2025 <Link to="/about" className="text-prakruti-patta hover:underline">Bijmantra</Link> by Denish Dholaria</span>
              <div className="flex items-center gap-3">
                <Link to="/terms" className="hover:text-prakruti-patta">License</Link>
                <Link to="/privacy" className="hover:text-prakruti-patta">Privacy</Link>
                <span className="hidden sm:inline">• PWA • Offline Ready</span>
              </div>
            </div>
          </footer>
        </div>
      </div>
      
      {/* Toast Container */}
      <ToastContainer />
      
      {/* Mobile Bottom Navigation */}
      <MobileBottomNav />
      
      {/* Quick Action FAB for mobile */}
      <QuickActionFAB />
      
      {/* What's New Sheet */}
      <WhatsNew 
        open={showWhatsNew} 
        onOpenChange={(open) => {
          if (!open) dismissWhatsNew()
          else setShowWhatsNew(open)
        }} 
      />
      
      {/* Keyboard Shortcuts Help */}
      <KeyboardShortcuts 
        open={showShortcuts} 
        onOpenChange={setShowShortcuts} 
      />
      
      {/* Onboarding Tour */}
      <OnboardingTour 
        open={showTour} 
        onOpenChange={setShowTour} 
      />
      
      {/* Veena AI Assistant */}
      <Suspense fallback={null}>
        <ComponentErrorBoundary>
          <Veena />
        </ComponentErrorBoundary>
      </Suspense>
    </div>
    </NotificationProvider>
  )
}


// Simple navigation fallback
function SimpleNav({ items, collapsed, onNavigate, currentPath }: { 
  items: typeof navItems
  collapsed: boolean
  onNavigate: () => void
  currentPath: string
}) {
  return (
    <div className="p-2">
      <nav className="space-y-1">
        {items.map(item => (
          <Link
            key={item.path}
            to={item.path}
            onClick={onNavigate}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
              currentPath === item.path || currentPath.startsWith(item.path + '/')
                ? 'bg-prakruti-patta-pale text-prakruti-patta dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light'
                : 'hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 text-prakruti-dhool-700 dark:text-prakruti-dhool-300'
            }`}
          >
            <span>{item.icon}</span>
            {!collapsed && <span className="text-sm">{item.label}</span>}
          </Link>
        ))}
      </nav>
    </div>
  )
}

export default Layout
