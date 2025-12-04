/**
 * Main Layout Component with Smart Navigation
 * Features: Command Palette (⌘K), Smart Nav, Favorites, Recent Pages
 */

import { Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useKeyboardShortcuts } from '@/components/KeyboardShortcuts'
import { CommandPalette } from '@/components/CommandPalette'
import { UserMenu } from '@/components/UserMenu'
import { RoleSwitcher, RoleIndicator } from '@/components/RoleSwitcher'
import { ToastContainer } from '@/components/ToastContainer'
import { PresenceIndicator } from '@/components/PresenceIndicator'
import { SyncStatusIndicator, OfflineBanner } from '@/components/SyncStatusIndicator'
import { Veena } from '@/components/ai/Veena'
import { NotificationBell, NotificationProvider } from '@/components/notifications'
import { SmartNavigation, allNavItems } from '@/components/SmartNavigation'

export function Layout({ children }: { children: React.ReactNode }) {
  useKeyboardShortcuts()
  const location = useLocation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)

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

  // Get current page label for header
  const currentPageLabel = allNavItems.find(item => 
    location.pathname === item.path || location.pathname.startsWith(item.path + '/')
  )?.label || 'Bijmantra'

  return (
    <NotificationProvider>
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-green-50/30 dark:from-slate-900 dark:to-slate-900 flex">
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

        {/* Smart Navigation */}
        <div className="flex-1 overflow-hidden">
          <SmartNavigation 
            collapsed={sidebarCollapsed} 
            onNavigate={closeMobileMenu}
          />
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
            {/* Role indicator */}
            <RoleIndicator />
            
            {/* Role Switcher */}
            <div className="hidden md:block">
              <RoleSwitcher compact />
            </div>
            
            {/* Online presence */}
            <div className="hidden lg:block">
              <PresenceIndicator maxVisible={3} showCount={false} />
            </div>
            
            {/* Sync status */}
            <div className="hidden sm:block">
              <SyncStatusIndicator />
            </div>
            
            {/* Notification Bell */}
            <NotificationBell />
            
            {/* Mobile search */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="sm:hidden p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-lg"
              aria-label="Search"
            >
              <span className="text-lg">🔍</span>
            </button>
            
            {/* User Menu */}
            <UserMenu />
          </div>
        </header>
        
        {/* Command Palette */}
        <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />

        {/* Offline Banner */}
        <OfflineBanner />

        {/* Main Content */}
        <main className="p-4 lg:p-6 min-h-[calc(100vh-56px)]">{children}</main>

        {/* Footer */}
        <footer className="bg-white/80 backdrop-blur-md border-t border-gray-200 px-4 lg:px-6 py-3">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>© 2025 Bijmantra by <Link to="/about" className="text-green-600 hover:underline">R.E.E.V.A.i</Link></span>
            <span className="hidden sm:inline">PWA • Offline Ready • Open Source</span>
          </div>
        </footer>
      </div>
      
      {/* Global Toast Notifications */}
      <ToastContainer />
      
      {/* Veena AI Assistant */}
      <Veena />
    </div>
    </NotificationProvider>
  )
}

export default Layout
