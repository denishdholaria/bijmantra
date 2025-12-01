/**
 * Main Layout Component with Vertical Sidebar
 * Organized with collapsible module sections
 */

import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { useState } from 'react'
import { useKeyboardShortcuts } from '@/components/KeyboardShortcuts'

interface NavSection {
  title: string
  icon: string
  items: { path: string; label: string; icon: string }[]
}

export function Layout({ children }: { children: React.ReactNode }) {
  useKeyboardShortcuts()
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuthStore()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [expandedSections, setExpandedSections] = useState<string[]>(['core', 'germplasm'])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const closeMobileMenu = () => setMobileMenuOpen(false)

  const toggleSection = (section: string) => {
    setExpandedSections(prev => 
      prev.includes(section) ? prev.filter(s => s !== section) : [...prev, section]
    )
  }

  const navSections: NavSection[] = [
    {
      title: 'AI',
      icon: '🤖',
      items: [
        { path: '/ai-assistant', label: 'AI Assistant', icon: '💬' },
        { path: '/chrome-ai', label: 'Chrome AI', icon: '🌐' },
        { path: '/ai-settings', label: 'AI Settings', icon: '⚙️' },
      ],
    },
    {
      title: 'Core',
      icon: '🏠',
      items: [
        { path: '/dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/search', label: 'Search', icon: '🔍' },
        { path: '/programs', label: 'Programs', icon: '🌾' },
        { path: '/trials', label: 'Trials', icon: '🧪' },
        { path: '/studies', label: 'Studies', icon: '📈' },
        { path: '/locations', label: 'Locations', icon: '📍' },
        { path: '/people', label: 'People', icon: '👥' },
        { path: '/seasons', label: 'Seasons', icon: '📅' },
      ],
    },
    {
      title: 'Germplasm',
      icon: '🌱',
      items: [
        { path: '/germplasm', label: 'Germplasm', icon: '🌱' },
        { path: '/seedlots', label: 'Seed Lots', icon: '📦' },
        { path: '/crosses', label: 'Crosses', icon: '🧬' },
        { path: '/crossingprojects', label: 'Projects', icon: '🔀' },
        { path: '/plannedcrosses', label: 'Planned', icon: '📋' },
        { path: '/progeny', label: 'Progeny', icon: '🌿' },
        { path: '/attributevalues', label: 'Attributes', icon: '📝' },
      ],
    },
    {
      title: 'Phenotyping',
      icon: '🔬',
      items: [
        { path: '/traits', label: 'Traits', icon: '🔬' },
        { path: '/observations', label: 'Observations', icon: '📋' },
        { path: '/observationunits', label: 'Units', icon: '🌿' },
        { path: '/events', label: 'Events', icon: '📆' },
        { path: '/images', label: 'Images', icon: '📷' },
        { path: '/ontologies', label: 'Ontologies', icon: '📖' },
      ],
    },
    {
      title: 'Genotyping',
      icon: '🧬',
      items: [
        { path: '/samples', label: 'Samples', icon: '🧫' },
        { path: '/variants', label: 'Variants', icon: '🔀' },
        { path: '/allelematrix', label: 'Matrix', icon: '📐' },
        { path: '/plates', label: 'Plates', icon: '🧪' },
        { path: '/references', label: 'References', icon: '📚' },
        { path: '/genomemaps', label: 'Maps', icon: '🗺️' },
      ],
    },
    {
      title: 'Tools',
      icon: '🛠️',
      items: [
        { path: '/fieldlayout', label: 'Field Layout', icon: '🗺️' },
        { path: '/trialdesign', label: 'Trial Design', icon: '🎲' },
        { path: '/selectionindex', label: 'Selection Index', icon: '📊' },
        { path: '/geneticgain', label: 'Genetic Gain', icon: '📈' },
        { path: '/pedigree', label: 'Pedigree Viewer', icon: '🌳' },
        { path: '/pipeline', label: 'Pipeline', icon: '🔀' },
        { path: '/harvest', label: 'Harvest Planner', icon: '🌾' },
        { path: '/inventory', label: 'Seed Inventory', icon: '📦' },
        { path: '/crossingplanner', label: 'Crossing Planner', icon: '💑' },
        { path: '/comparison', label: 'Compare', icon: '⚖️' },
        { path: '/statistics', label: 'Statistics', icon: '📉' },
        { path: '/nursery', label: 'Nursery', icon: '🌱' },
        { path: '/labels', label: 'Labels', icon: '🏷️' },
        { path: '/calculator', label: 'Calculator', icon: '🧮' },
        { path: '/collections', label: 'Collections', icon: '🗃️' },
        { path: '/phenology', label: 'Phenology', icon: '🌿' },
        { path: '/soil', label: 'Soil Analysis', icon: '🧪' },
        { path: '/fertilizer', label: 'Fertilizer', icon: '🧫' },
        { path: '/fieldbook', label: 'Field Book', icon: '📓' },
        { path: '/varietycomparison', label: 'Variety Compare', icon: '🔬' },
        { path: '/yieldmap', label: 'Yield Map', icon: '🗺️' },
        { path: '/seedrequest', label: 'Seed Request', icon: '📬' },
        { path: '/trialplanning', label: 'Trial Planning', icon: '📅' },
        { path: '/scanner', label: 'Scanner', icon: '📱' },
        { path: '/weather', label: 'Weather', icon: '🌤️' },
        { path: '/import-export', label: 'Import/Export', icon: '🔄' },
        { path: '/reports', label: 'Reports', icon: '📋' },
        { path: '/dataquality', label: 'Data Quality', icon: '✅' },
      ],
    },
    {
      title: 'Help',
      icon: '❓',
      items: [
        { path: '/help', label: 'Help Center', icon: '📚' },
        { path: '/quick-guide', label: 'Quick Start', icon: '🚀' },
        { path: '/glossary', label: 'Glossary', icon: '📖' },
        { path: '/faq', label: 'FAQ', icon: '❓' },
        { path: '/keyboard-shortcuts', label: 'Shortcuts', icon: '⌨️' },
        { path: '/whats-new', label: "What's New", icon: '🎉' },
        { path: '/tips', label: 'Tips & Tricks', icon: '💡' },
        { path: '/changelog', label: 'Changelog', icon: '📝' },
        { path: '/contact', label: 'Contact', icon: '📧' },
        { path: '/privacy', label: 'Privacy', icon: '🔒' },
        { path: '/terms', label: 'Terms', icon: '📜' },
        { path: '/feedback', label: 'Feedback', icon: '💬' },
      ],
    },
  ]

  // Check if any item in a section is active
  const isSectionActive = (section: NavSection) => 
    section.items.some(item => location.pathname.startsWith(item.path))

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-green-50/30 flex">
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={closeMobileMenu} />
      )}

      {/* Vertical Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full bg-white/95 backdrop-blur-md border-r border-gray-200 shadow-xl transition-all duration-300 z-50 flex flex-col
          ${sidebarCollapsed ? 'w-16' : 'w-60'}
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="h-14 flex items-center justify-between px-3 border-b border-gray-200 flex-shrink-0">
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

        {/* Scrollable Navigation */}
        <nav className="flex-1 overflow-y-auto p-2 space-y-1">
          {navSections.map((section) => {
            const isExpanded = expandedSections.includes(section.title.toLowerCase())
            const isActive = isSectionActive(section)
            
            return (
              <div key={section.title}>
                {/* Section Header */}
                <button
                  onClick={() => !sidebarCollapsed && toggleSection(section.title.toLowerCase())}
                  className={`w-full flex items-center gap-2 px-2 py-2 rounded-lg text-left transition-all
                    ${isActive ? 'bg-green-50 text-green-700' : 'text-gray-600 hover:bg-gray-50'}
                  `}
                  title={sidebarCollapsed ? section.title : ''}
                >
                  <span className="text-lg flex-shrink-0">{section.icon}</span>
                  {!sidebarCollapsed && (
                    <>
                      <span className="flex-1 font-medium text-sm">{section.title}</span>
                      <span className="text-xs">{isExpanded ? '▼' : '▶'}</span>
                    </>
                  )}
                </button>

                {/* Section Items */}
                {(isExpanded || sidebarCollapsed) && (
                  <div className={`${sidebarCollapsed ? '' : 'ml-2 mt-1'} space-y-0.5`}>
                    {section.items.map((item) => {
                      const isItemActive = location.pathname.startsWith(item.path)
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={closeMobileMenu}
                          className={`flex items-center gap-2 px-2 py-1.5 rounded-md transition-all text-sm
                            ${isItemActive
                              ? 'bg-green-500 text-white shadow-sm'
                              : 'text-gray-600 hover:bg-gray-100'
                            }
                          `}
                          title={sidebarCollapsed ? item.label : ''}
                        >
                          <span className="text-base flex-shrink-0">{item.icon}</span>
                          {!sidebarCollapsed && <span>{item.label}</span>}
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </nav>

        {/* Sidebar Footer - Fixed at bottom */}
        <div className="flex-shrink-0 p-2 border-t border-gray-200 bg-white space-y-0.5">
          <Link
            to="/about"
            onClick={closeMobileMenu}
            className="flex items-center gap-2 px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
            title={sidebarCollapsed ? 'About' : ''}
          >
            <span>ℹ️</span>
            {!sidebarCollapsed && <span>About</span>}
          </Link>
          <Link
            to="/notifications"
            onClick={closeMobileMenu}
            className="flex items-center gap-2 px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
            title={sidebarCollapsed ? 'Notifications' : ''}
          >
            <span>🔔</span>
            {!sidebarCollapsed && <span>Notifications</span>}
          </Link>
          <Link
            to="/profile"
            onClick={closeMobileMenu}
            className="flex items-center gap-2 px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
            title={sidebarCollapsed ? 'Profile' : ''}
          >
            <span>👤</span>
            {!sidebarCollapsed && <span>Profile</span>}
          </Link>
          <Link
            to="/settings"
            onClick={closeMobileMenu}
            className="flex items-center gap-2 px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
            title={sidebarCollapsed ? 'Settings' : ''}
          >
            <span>⚙️</span>
            {!sidebarCollapsed && <span>Settings</span>}
          </Link>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md hidden lg:flex"
          >
            <span>{sidebarCollapsed ? '→' : '←'}</span>
            {!sidebarCollapsed && <span>Collapse</span>}
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-md"
          >
            <span>🚪</span>
            {!sidebarCollapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>


      {/* Main Content Area */}
      <div className={`flex-1 transition-all duration-300 ${sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-60'}`}>
        {/* Top Bar */}
        <header className="h-14 bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-40 flex items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 hover:bg-gray-100 rounded-lg"
              aria-label="Toggle menu"
            >
              <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
            <h2 className="text-base font-semibold text-gray-800">
              {navSections.flatMap(s => s.items).find(item => location.pathname.startsWith(item.path))?.label || 'Bijmantra'}
            </h2>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="hidden sm:flex items-center gap-1.5 text-gray-600">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Online
            </span>
            <span className="text-gray-400 hidden sm:inline">|</span>
            <span className="text-gray-600 font-medium">BrAPI v2.1</span>
          </div>
        </header>

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
    </div>
  )
}
