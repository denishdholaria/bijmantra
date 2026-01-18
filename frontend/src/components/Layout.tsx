/**
 * Main Layout Component with Mahasarthi Sidebar Navigation
 * Features: Command Palette (⌘K), Mahasarthi Nav, Notifications, Sync Status
 * 
 * Updated: Integrated MahasarthiSidebar with diagonal edge design
 */

import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useState, useEffect, Suspense, lazy, Component, ReactNode } from 'react'
import { 
  HelpCircle, Settings, Search, BarChart3, Wheat, FlaskConical, LineChart, 
  MapPin, Sprout, Package, GitMerge, Microscope, Eye, TestTube2, 
  Menu, X as CloseIcon, 
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

// Mahasarthi sidebar components
import { MahasarthiSidebar } from '@/components/navigation/MahasarthiSidebar'
import { MahasarthiNavigation } from '@/components/navigation/MahasarthiNavigation'
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs'

// Fallback navigation (direct import for critical path)
import SmartNavigation from '@/components/SmartNavigation'

// Lazy load non-critical components
const CommandPalette = lazy(() => 
  import('@/components/CommandPalette').then(m => ({ default: m.CommandPalette }))
)
const UserMenu = lazy(() => 
  import('@/components/UserMenu').then(m => ({ default: m.UserMenu }))
)
const VeenaSidebar = lazy(() => 
  import('@/components/ai/VeenaSidebar').then(m => ({ default: m.VeenaSidebar }))
)
// ASTRA Agent Arsenal - unified agent sidebar (replaces individual agent sidebars)
const AstraSidebar = lazy(() => 
  import('@/components/agents/AstraSidebar')
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
import { PWAInstallPrompt } from '@/components/PWAInstallPrompt'

// Role defaults hook - Per Think-Tank §5.1 P0
import { useApplyRoleDefaults } from '@/hooks/useApplyRoleDefaults'

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
  const location = useLocation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const { showWhatsNew, setShowWhatsNew, dismissWhatsNew } = useWhatsNew()
  const { showShortcuts, setShowShortcuts } = useKeyboardShortcuts()
  const { showTour, setShowTour } = useOnboardingTour()

  // Apply role-based dock defaults on first login - Per Think-Tank §5.1 P0
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
        {/* Right margin (lg:mr-14) accounts for ASTRA sidebar collapsed width (56px) */}
        <div className={`flex-1 transition-all duration-300 ${sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'} lg:mr-14`}>
          {/* Top Bar */}
          <header className="h-14 bg-white/90 dark:bg-prakruti-dhool-900/90 backdrop-blur-md border-b border-prakruti-dhool-200 dark:border-prakruti-dhool-800 sticky top-0 z-40 flex items-center justify-between px-4 lg:px-6">
            <div className="flex items-center gap-4">
              {/* Mobile menu toggle */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 rounded-lg"
                aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              >
                {mobileMenuOpen ? (
                  <CloseIcon className="w-5 h-5 text-prakruti-dhool-700 dark:text-prakruti-dhool-300" />
                ) : (
                  <Menu className="w-5 h-5 text-prakruti-dhool-700 dark:text-prakruti-dhool-300" />
                )}
              </button>
              
              {/* Workspace Switcher */}
              <ComponentErrorBoundary>
                <WorkspaceSwitcher showLabel={true} />
              </ComponentErrorBoundary>
              
              {/* Breadcrumbs - Per Think-Tank §5.1 P0 */}
              <ComponentErrorBoundary>
                <Breadcrumbs className="hidden md:flex" />
              </ComponentErrorBoundary>
              
              {/* Page title (mobile fallback) */}
              <h2 className="text-base font-semibold text-prakruti-dhool-800 dark:text-prakruti-dhool-100 md:hidden">
                {currentPageLabel}
              </h2>
            </div>

            {/* Center - Command Palette Trigger */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300 bg-prakruti-dhool-100 dark:bg-prakruti-dhool-800 hover:bg-prakruti-dhool-200 dark:hover:bg-prakruti-dhool-700 rounded-lg transition-colors border border-prakruti-dhool-200 dark:border-prakruti-dhool-700"
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
                className="sm:hidden p-2 text-prakruti-dhool-600 dark:text-prakruti-dhool-300 hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 rounded-lg"
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
          <main id="main-content" className="p-4 lg:p-6 min-h-[calc(100vh-56px)] pb-20 lg:pb-6" tabIndex={-1}>
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
      
      {/* ASTRA Agent Arsenal (Right side) */}
      <Suspense fallback={null}>
        <ComponentErrorBoundary>
          <AstraSidebar />
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
