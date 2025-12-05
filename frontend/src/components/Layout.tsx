/**
 * Main Layout Component with Smart Navigation
 * Features: Command Palette (⌘K), Smart Nav, Favorites, Recent Pages
 * Restored: RoleSwitcher, ToastContainer, PresenceIndicator, SyncStatus, Notifications
 */

import { Link, useLocation } from 'react-router-dom'
import { useState, useEffect, Suspense, lazy } from 'react'

// Lazy load heavy components to prevent blocking
const SmartNavigation = lazy(() => import('@/components/SmartNavigation').then(m => ({ default: m.SmartNavigation })))
const CommandPalette = lazy(() => import('@/components/CommandPalette').then(m => ({ default: m.CommandPalette })))
const UserMenu = lazy(() => import('@/components/UserMenu').then(m => ({ default: m.UserMenu })))
const Veena = lazy(() => import('@/components/ai/Veena').then(m => ({ default: m.Veena })))

// Import lighter components directly
import { useKeyboardShortcuts } from '@/components/KeyboardShortcuts'
import { RoleIndicator } from '@/components/RoleSwitcher'
import { ToastContainer } from '@/components/ToastContainer'
import { PresenceIndicator } from '@/components/PresenceIndicator'
import { SyncStatusIndicator, OfflineBanner } from '@/components/SyncStatusIndicator'
import { NotificationProvider, NotificationBell } from '@/components/notifications'

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center p-4">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600" />
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
  useKeyboardShortcuts()
  const location = useLocation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [useSmartNav] = useState(true)

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

  // Get current page label
  const currentPageLabel = navItems.find(item => 
    location.pathname === item.path || location.pathname.startsWith(item.path + '/')
  )?.label || 'Bijmantra'

  return (
    <NotificationProvider>
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-green-50/30 dark:from-slate-900 dark:to-slate-900 flex flex-col">
      {/* Offline Banner - shows when offline */}
      <OfflineBanner />
      
      <div className="flex flex-1">
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={closeMobileMenu} />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-800 shadow-xl transition-all duration-300 z-50 flex flex-col
          ${sidebarCollapsed ? 'w-16' : 'w-64'}
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="h-14 flex items-center justify-between px-3 border-b border-gray-200 dark:border-slate-800 flex-shrink-0">
          {!sidebarCollapsed ? (
            <Link to="/dashboard" className="flex items-center gap-2 group">
              <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-md">
                <span className="text-lg">🌱</span>
              </div>
              <span className="text-base font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                Bijmantra
              </span>
            </Link>
          ) : (
            <Link to="/dashboard" className="mx-auto">
              <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-md">
                <span className="text-lg">🌱</span>
              </div>
            </Link>
          )}
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto">
          {useSmartNav ? (
            <Suspense fallback={<SimpleNav items={navItems} collapsed={sidebarCollapsed} onNavigate={closeMobileMenu} currentPath={location.pathname} />}>
              <SmartNavigation collapsed={sidebarCollapsed} onNavigate={closeMobileMenu} />
            </Suspense>
          ) : (
            <SimpleNav items={navItems} collapsed={sidebarCollapsed} onNavigate={closeMobileMenu} currentPath={location.pathname} />
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="flex-shrink-0 p-2 border-t border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full flex items-center justify-center gap-2 px-2 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-md hidden lg:flex"
          >
            <span>{sidebarCollapsed ? '→' : '←'}</span>
            {!sidebarCollapsed && <span>Collapse</span>}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className={`flex-1 transition-all duration-300 ${sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'}`}>
        {/* Top Bar */}
        <header className="h-14 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-gray-200 dark:border-slate-800 sticky top-0 z-40 flex items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-4">
            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg"
              aria-label="Toggle menu"
            >
              <svg className="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
            
            {/* Page title */}
            <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100 hidden sm:block">
              {currentPageLabel}
            </h2>
          </div>

          {/* Center - Command Palette Trigger */}
          <button
            onClick={() => setCommandPaletteOpen(true)}
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-lg transition-colors border border-gray-200 dark:border-slate-700"
          >
            <span>🔍</span>
            <span className="hidden md:inline">Search anything...</span>
            <kbd className="hidden lg:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-xs bg-white dark:bg-slate-700 text-gray-600 dark:text-gray-300 rounded border border-gray-300 dark:border-slate-600 font-mono">
              ⌘K
            </kbd>
          </button>
          
          {/* Right side */}
          <div className="flex items-center gap-2">
            {/* Mobile search */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="sm:hidden p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg"
              aria-label="Search"
            >
              <span className="text-lg">🔍</span>
            </button>
            
            {/* Role Indicator - shows current role view */}
            <RoleIndicator />
            
            {/* Sync Status */}
            <SyncStatusIndicator />
            
            {/* Presence Indicator - shows online users */}
            <PresenceIndicator maxVisible={3} showCount={false} />
            
            {/* Notification Bell */}
            <NotificationBell />
            
            {/* User Menu */}
            <Suspense fallback={<div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse" />}>
              <UserMenu />
            </Suspense>
          </div>
        </header>
        
        {/* Command Palette */}
        <Suspense fallback={null}>
          <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />
        </Suspense>

        {/* Main Content */}
        <main className="p-4 lg:p-6 min-h-[calc(100vh-56px)]">
          <Suspense fallback={<LoadingFallback />}>
            {children}
          </Suspense>
        </main>

        {/* Footer */}
        <footer className="bg-white/80 backdrop-blur-md border-t border-gray-200 px-4 lg:px-6 py-3">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>© 2025 Bijmantra by <Link to="/about" className="text-green-600 hover:underline">R.E.E.V.A.i</Link></span>
            <div className="flex items-center gap-3">
              <Link to="/terms" className="hover:text-green-600">License</Link>
              <Link to="/privacy" className="hover:text-green-600">Privacy</Link>
              <span className="hidden sm:inline">• PWA • Offline Ready</span>
            </div>
          </div>
        </footer>
      </div>
      
      {/* Veena AI Assistant */}
      <Suspense fallback={null}>
        <Veena />
      </Suspense>
      </div>{/* End flex wrapper */}
      
      {/* Toast Container - renders all active toasts */}
      <ToastContainer />
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
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-700 dark:text-gray-300'
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
