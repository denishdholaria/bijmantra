/**
 * Main Layout Component
 * 
 * Two modes:
 * 1. Shell Mode (isInShell=true): Delegates to ShellLayout — minimal chrome since
 *    BijMantraDesktop provides SystemBar, Sidebar, Dock, etc.
 * 2. Standalone Mode: Full layout with sidebar, header, footer, REEVU, etc.
 *    (For direct URL access without shell, or future standalone pages)
 * 
 * Updated: Clean separation replaces old isInShell conditional hiding
 */

import { Link, useLocation, useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useState, useEffect, Suspense, lazy, Component, ReactNode } from 'react'
import { 
  HelpCircle, Settings, Search, BarChart3, Wheat, FlaskConical, LineChart, 
  MapPin, Sprout, Package, GitMerge, Microscope, Eye, TestTube2, 
  Menu, X as CloseIcon, LogOut,
  type LucideIcon 
} from 'lucide-react'

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

// ShellLayout — imported for shell mode
import { ShellLayout } from '@/components/ShellLayout'

// Mahasarthi sidebar components (standalone mode only)
import { MahasarthiSidebar } from '@/components/navigation/MahasarthiSidebar'
import { MahasarthiNavigation } from '@/components/navigation/MahasarthiNav'
import { Breadcrumbs } from '@/components/navigation/MahasarthiBreadcrumbs'

// Fallback navigation (direct import for critical path)
import SmartNavigation from '@/components/SmartNavigation'

// Lazy load non-critical components
const CommandPalette = lazy(() => 
  import('@/components/CommandPalette').then(m => ({ default: m.CommandPalette }))
)
const UserMenu = lazy(() => 
  import('@/components/UserMenu').then(m => ({ default: m.UserMenu }))
)
const ReevuSidebar = lazy(() => 
  import('@/components/ai/ReevuSidebar').then(m => ({ default: m.ReevuSidebar }))
)

// Direct imports for lightweight components
import { NotificationProvider, NotificationBell } from '@/components/notifications'
import { SyncStatusIndicator, OfflineBanner } from '@/components/SyncStatusIndicator'
import { ToastContainer } from '@/components/ToastContainer'
import { QuickActionFAB } from '@/components/navigation/QuickActionFAB'
import { WhatsNew, useWhatsNew } from '@/components/WhatsNew'
import { KeyboardShortcuts, useKeyboardShortcuts } from '@/components/KeyboardShortcuts'
import { OnboardingTour, useOnboardingTour } from '@/components/OnboardingTour'
import { MahasarthiKshetra } from '@/components/navigation/MahasarthiKshetra'
import { PWAInstallPrompt } from '@/components/PWAInstallPrompt'

// Role defaults hook - Per Think-Tank §5.1 P0
import { useApplyRoleDefaults } from '@/hooks/useApplyRoleDefaults'
import { useSystemStore } from '@/store/systemStore'
import { useAuthStore } from '@/store/auth'

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center p-4">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-prakruti-patta" />
    </div>
  )
}


// Simple nav items for fallback
const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { path: '/programs', label: 'Programs', icon: Wheat },
  { path: '/trials', label: 'Trials', icon: FlaskConical },
  { path: '/studies', label: 'Studies', icon: LineChart },
  { path: '/locations', label: 'Locations', icon: MapPin },
  { path: '/germplasm', label: 'Germplasm', icon: Sprout },
  { path: '/seedlots', label: 'Seed Lots', icon: Package },
  { path: '/crosses', label: 'Crosses', icon: GitMerge },
  { path: '/traits', label: 'Traits', icon: Microscope },
  { path: '/observations', label: 'Observations', icon: Eye },
  { path: '/samples', label: 'Samples', icon: TestTube2 },
  { path: '/settings', label: 'Settings', icon: Settings },
  { path: '/help', label: 'Help', icon: HelpCircle },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const isInShell = useSystemStore((state) => state.isInShell)

  // ─── Shell Mode: Minimal layout (shell provides all chrome) ───
  if (isInShell) {
    return <ShellLayout>{children}</ShellLayout>
  }

  // ─── Standalone Mode: Full layout ───
  return <StandaloneLayout>{children}</StandaloneLayout>
}

/**
 * StandaloneLayout — Full layout for non-shell usage.
 * Sidebar, header, footer, REEVU AI sidebar, command palette, etc.
 */
function StandaloneLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const { showWhatsNew, setShowWhatsNew, dismissWhatsNew } = useWhatsNew()
  const { showShortcuts, setShowShortcuts } = useKeyboardShortcuts()
  const { showTour, setShowTour } = useOnboardingTour()
  const logout = useAuthStore((state) => state.logout)

  // Apply role-based dock defaults on first login
  useApplyRoleDefaults()

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
  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const currentPageLabel = navItems.find(item => 
    location.pathname === item.path || location.pathname.startsWith(item.path + '/')
  )?.label || 'Bijmantra'

  return (
    <NotificationProvider>
    <div className="app-theme-bridge bg-shell min-h-screen flex flex-col">
      {/* Offline Banner */}
      <ComponentErrorBoundary>
        <OfflineBanner />
      </ComponentErrorBoundary>
      
      <div className="flex flex-1">
        {/* Mahasarthi Sidebar */}
        <MahasarthiSidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          mobileOpen={mobileMenuOpen}
          onMobileClose={closeMobileMenu}
        >
          <ComponentErrorBoundary fallback={<SimpleNav items={navItems} collapsed={sidebarCollapsed} onNavigate={closeMobileMenu} currentPath={location.pathname} />}>
            <MahasarthiNavigation collapsed={sidebarCollapsed} onNavigate={closeMobileMenu} />
          </ComponentErrorBoundary>
        </MahasarthiSidebar>

        {/* Main Content Area */}
        <div className={`flex-1 transition-all duration-300 ${sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'} lg:mr-14`}>
          {/* Top Bar */}
          <header className="bg-shell-chrome border-shell shadow-shell sticky top-0 z-40 flex h-14 items-center justify-between border-b px-4 backdrop-blur-xl lg:px-6">
            <div className="flex items-center gap-4">
              {/* Mobile menu toggle */}
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell rounded-xl p-2 transition-colors lg:hidden"
                aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              >
                {mobileMenuOpen ? (
                  <CloseIcon className="h-5 w-5" />
                ) : (
                  <Menu className="h-5 w-5" />
                )}
              </button>
              
              {/* Workspace Switcher */}
              <ComponentErrorBoundary>
                <MahasarthiKshetra showLabel={true} />
              </ComponentErrorBoundary>
              
              {/* Breadcrumbs */}
              <ComponentErrorBoundary>
                <Breadcrumbs className="hidden md:flex" />
              </ComponentErrorBoundary>
              
              {/* Page title (mobile fallback) */}
              <h2 className="text-shell text-base font-semibold md:hidden">
                {currentPageLabel}
              </h2>
            </div>

            {/* Center - Command Palette Trigger */}
            <button
              type="button"
              onClick={() => setCommandPaletteOpen(true)}
              className="bg-[hsl(var(--app-shell-panel)/0.76)] border-shell text-shell-muted hover:bg-[hsl(var(--accent))] hidden items-center gap-2 rounded-2xl border px-3 py-2 text-sm transition-colors sm:flex"
            >
              <Search className="h-4 w-4" />
              <span className="hidden md:inline">Search...</span>
              <kbd className="bg-shell hidden items-center gap-0.5 rounded-lg border border-[hsl(var(--app-shell-border)/0.8)] px-1.5 py-0.5 font-mono text-xs text-shell-muted lg:inline-flex">
                ⌘K
              </kbd>
            </button>

            
            {/* Right side */}
            <div className="flex items-center gap-2">
              {/* Mobile search */}
              <button
                type="button"
                onClick={() => setCommandPaletteOpen(true)}
                className="text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell rounded-xl p-2 transition-colors sm:hidden"
                aria-label="Search"
              >
                <Search className="h-5 w-5" />
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
                className="text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell rounded-xl p-2 transition-colors"
                aria-label="Help"
              >
                <HelpCircle className="h-5 w-5" />
              </Link>
              
              {/* Settings */}
              <Link 
                to="/settings" 
                className="text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell rounded-xl p-2 transition-colors"
                aria-label="Settings"
              >
                <Settings className="h-5 w-5" />
              </Link>

              <button
                type="button"
                onClick={handleLogout}
                className="text-shell-muted hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/30 dark:hover:text-red-400 inline-flex items-center gap-2 rounded-xl px-2.5 py-2 transition-colors"
                aria-label="Logout"
              >
                <LogOut className="h-5 w-5" />
                <span className="hidden text-sm font-medium lg:inline">Logout</span>
              </button>
              
              {/* User Menu */}
              <Suspense fallback={<div className="bg-shell-muted h-8 w-8 animate-pulse rounded-full" />}>
                <ComponentErrorBoundary fallback={
                  <Link to="/profile" className="bg-[linear-gradient(135deg,hsl(var(--primary)/0.12),hsl(var(--app-shell-radiance)/0.18))] text-prakruti-patta dark:text-prakruti-patta-light flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium">
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
          <main
            id="main-content"
            className="min-h-[calc(100vh-56px)] pb-20 lg:pb-6 p-4 lg:p-6"
            tabIndex={-1}
          >
            <Suspense fallback={<LoadingFallback />}>
              {children}
            </Suspense>
          </main>

          {/* Footer */}
          <footer className="bg-shell-chrome border-shell border-t px-4 py-3 lg:px-6">
            <div className="text-shell-muted flex items-center justify-between text-xs">
              <span>© 2025 <Link to="/about" className="text-prakruti-patta hover:underline">Bijmantra</Link> by Denish Dholaria</span>
              <div className="flex items-center gap-3">
                <Link to="/terms" className="hover:text-prakruti-patta">License</Link>
                <Link to="/privacy" className="hover:text-prakruti-patta">Privacy</Link>
                <span className="hidden sm:inline">• PWA • Installable • Field Data Sync</span>
              </div>
            </div>
          </footer>
        </div>
      </div>
      
      {/* Toast Container */}
      <ToastContainer />
      
      {/* Quick Action FAB for mobile */}
      <QuickActionFAB />
      
      {/* PWA Install Prompt */}
      <PWAInstallPrompt />
      
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
      
      {/* REEVU Cognitive Core */}
      <Suspense fallback={null}>
        <ComponentErrorBoundary>
          <ReevuSidebar />
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
            <item.icon className={cn(
              "w-5 h-5 transition-transform duration-200",
              (currentPath === item.path || currentPath.startsWith(item.path + '/')) && "scale-110"
            )} strokeWidth={1.75} />
            {!collapsed && <span className="text-sm">{item.label}</span>}
          </Link>
        ))}
      </nav>
    </div>
  )
}

export default Layout
