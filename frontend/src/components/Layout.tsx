/**
 * Main Layout Component with Vertical Sidebar
 * Organized with collapsible module sections
 * Features: Command Palette (⌘K), Unified User Menu, Smart Navigation
 */

import { Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useKeyboardShortcuts } from '@/components/KeyboardShortcuts'
import { CommandPalette } from '@/components/CommandPalette'
import { UserMenu } from '@/components/UserMenu'
import { usePinnedNav } from '@/hooks/usePinnedNav'
import { RoleSwitcher, RoleIndicator } from '@/components/RoleSwitcher'
import { ContextSidebar } from '@/components/ContextSidebar'
import { ToastContainer } from '@/components/ToastContainer'
import { PresenceIndicator } from '@/components/PresenceIndicator'
import { SyncStatusIndicator, OfflineBanner } from '@/components/SyncStatusIndicator'

interface NavSection {
  title: string
  icon: string
  items: { path: string; label: string; icon: string }[]
}

export function Layout({ children }: { children: React.ReactNode }) {
  useKeyboardShortcuts()
  const location = useLocation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [expandedSections, setExpandedSections] = useState<string[]>(['core', 'germplasm'])
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const { pinnedItems, togglePin, isPinned } = usePinnedNav()

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
        { path: '/plant-vision', label: 'Plant Vision', icon: '🌿' },
        { path: '/field-scanner', label: 'Field Scanner', icon: '📱' },
        { path: '/disease-atlas', label: 'Disease Atlas', icon: '🦠' },
        { path: '/crop-health', label: 'Crop Health', icon: '🌾' },
        { path: '/yield-predictor', label: 'Yield Predictor', icon: '🎯' },
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
      title: 'Genomics',
      icon: '🔬',
      items: [
        { path: '/genetic-diversity', label: 'Diversity', icon: '🌈' },
        { path: '/breeding-values', label: 'Breeding Values', icon: '📊' },
        { path: '/qtl-mapping', label: 'QTL Mapping', icon: '🎯' },
        { path: '/genomic-selection', label: 'Genomic Selection', icon: '🧬' },
        { path: '/marker-assisted-selection', label: 'MAS', icon: '🔖' },
        { path: '/haplotype-analysis', label: 'Haplotypes', icon: '🔗' },
        { path: '/linkage-disequilibrium', label: 'LD Analysis', icon: '📈' },
        { path: '/population-genetics', label: 'Pop Genetics', icon: '👥' },
        { path: '/parentage-analysis', label: 'Parentage', icon: '👨‍👩‍👧' },
        { path: '/genetic-correlation', label: 'Correlations', icon: '🔄' },
        { path: '/gxe-interaction', label: 'G×E', icon: '🌍' },
        { path: '/stability-analysis', label: 'Stability', icon: '⚖️' },
      ],
    },
    {
      title: 'Advanced',
      icon: '🚀',
      items: [
        { path: '/molecular-breeding', label: 'Molecular Breeding', icon: '🧪' },
        { path: '/phenomic-selection', label: 'Phenomics', icon: '📷' },
        { path: '/speed-breeding', label: 'Speed Breeding', icon: '⚡' },
        { path: '/doubled-haploid', label: 'Doubled Haploid', icon: '🔬' },
        { path: '/breeding-simulator', label: 'Simulator', icon: '🎮' },
        { path: '/genetic-gain-calculator', label: 'Gain Calculator', icon: '📈' },
        { path: '/cross-prediction', label: 'Cross Prediction', icon: '🔮' },
        { path: '/parent-selection', label: 'Parent Selection', icon: '👨‍👩‍👧' },
        { path: '/selection-decision', label: 'Selection Decision', icon: '✅' },
        { path: '/performance-ranking', label: 'Rankings', icon: '🏆' },
      ],
    },
    {
      title: 'Analytics',
      icon: '📊',
      items: [
        { path: '/analytics', label: 'Dashboard', icon: '📊' },
        { path: '/trial-summary', label: 'Trial Summary', icon: '📋' },
        { path: '/trial-comparison', label: 'Trial Compare', icon: '⚖️' },
        { path: '/trial-network', label: 'Trial Network', icon: '🌐' },
        { path: '/visualization', label: 'Visualization', icon: '📈' },
        { path: '/advanced-reports', label: 'Reports', icon: '📑' },
        { path: '/activity', label: 'Activity', icon: '📜' },
      ],
    },
    {
      title: 'Planning',
      icon: '📅',
      items: [
        { path: '/season-planning', label: 'Season Planning', icon: '🗓️' },
        { path: '/field-planning', label: 'Field Planning', icon: '🗺️' },
        { path: '/resource-allocation', label: 'Resources', icon: '💰' },
        { path: '/breeding-history', label: 'History', icon: '📚' },
        { path: '/breeding-goals', label: 'Goals', icon: '🎯' },
        { path: '/resource-calendar', label: 'Calendar', icon: '📆' },
      ],
    },
    {
      title: 'Automation',
      icon: '⚡',
      items: [
        { path: '/workflows', label: 'Workflows', icon: '🔄' },
        { path: '/notification-center', label: 'Notifications', icon: '🔔' },
        { path: '/data-validation', label: 'Validation', icon: '✓' },
        { path: '/export-templates', label: 'Export Templates', icon: '📤' },
        { path: '/batch-operations', label: 'Batch Ops', icon: '📦' },
        { path: '/quick-entry', label: 'Quick Entry', icon: '⚡' },
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
      title: 'Collaboration',
      icon: '👥',
      items: [
        { path: '/collaboration', label: 'Hub', icon: '🤝' },
        { path: '/team-management', label: 'Team', icon: '👥' },
        { path: '/data-sync', label: 'Data Sync', icon: '🔄' },
        { path: '/stakeholders', label: 'Stakeholders', icon: '🤝' },
        { path: '/publications', label: 'Publications', icon: '📰' },
        { path: '/training', label: 'Training', icon: '🎓' },
      ],
    },
    {
      title: 'System',
      icon: '⚙️',
      items: [
        { path: '/system-health', label: 'System Health', icon: '💚' },
        { path: '/offline', label: 'Offline Mode', icon: '📴' },
        { path: '/languages', label: 'Languages', icon: '🌍' },
        { path: '/data-dictionary', label: 'Data Dictionary', icon: '📖' },
        { path: '/api-explorer', label: 'API Explorer', icon: '🔌' },
        { path: '/backup', label: 'Backup', icon: '💾' },
        { path: '/auditlog', label: 'Audit Log', icon: '📋' },
        { path: '/users', label: 'Users', icon: '👤' },
      ],
    },
    {
      title: 'WASM Engine',
      icon: '🦀',
      items: [
        { path: '/wasm-genomics', label: 'WASM Genomics', icon: '⚡' },
        { path: '/wasm-gblup', label: 'WASM GBLUP', icon: '📊' },
        { path: '/wasm-popgen', label: 'Population Gen', icon: '👥' },
        { path: '/wasm-ld', label: 'LD Analysis', icon: '🔗' },
        { path: '/wasm-selection', label: 'Selection Index', icon: '🎯' },
      ],
    },
    {
      title: 'Future Tech',
      icon: '🔮',
      items: [
        { path: '/drones', label: 'Drones', icon: '🚁' },
        { path: '/iot-sensors', label: 'IoT Sensors', icon: '📡' },
        { path: '/blockchain', label: 'Blockchain', icon: '⛓️' },
        { path: '/weather-forecast', label: 'Weather', icon: '🌤️' },
        { path: '/genetic-map', label: 'Genetic Map', icon: '🧬' },
        { path: '/germplasm-search', label: 'Search', icon: '🔍' },
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
          {/* Favorites/Pinned Section */}
          {pinnedItems.length > 0 && !sidebarCollapsed && (
            <div className="mb-3 pb-2 border-b border-gray-100">
              <div className="px-2 py-1.5 text-xs font-medium text-gray-400 uppercase tracking-wider flex items-center gap-1">
                <span>⭐</span> Favorites
              </div>
              {pinnedItems.map((pinnedPath) => {
                const item = navSections.flatMap(s => s.items).find(i => i.path === pinnedPath)
                if (!item) return null
                const isItemActive = location.pathname.startsWith(item.path)
                return (
                  <Link
                    key={`pinned-${item.path}`}
                    to={item.path}
                    onClick={closeMobileMenu}
                    className={`flex items-center gap-2 px-2 py-1.5 rounded-md transition-all text-sm group
                      ${isItemActive
                        ? 'bg-green-500 text-white shadow-sm'
                        : 'text-gray-600 hover:bg-gray-100'
                      }
                    `}
                  >
                    <span className="text-base flex-shrink-0">{item.icon}</span>
                    <span className="flex-1">{item.label}</span>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        togglePin(item.path)
                      }}
                      className={`opacity-0 group-hover:opacity-100 p-0.5 rounded transition-opacity ${isItemActive ? 'text-white/70 hover:text-white' : 'text-gray-400 hover:text-gray-600'}`}
                      title="Unpin"
                    >
                      ✕
                    </button>
                  </Link>
                )
              })}
            </div>
          )}

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
                      const itemIsPinned = isPinned(item.path)
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={closeMobileMenu}
                          className={`flex items-center gap-2 px-2 py-1.5 rounded-md transition-all text-sm group
                            ${isItemActive
                              ? 'bg-green-500 text-white shadow-sm'
                              : 'text-gray-600 hover:bg-gray-100'
                            }
                          `}
                          title={sidebarCollapsed ? item.label : ''}
                        >
                          <span className="text-base flex-shrink-0">{item.icon}</span>
                          {!sidebarCollapsed && (
                            <>
                              <span className="flex-1">{item.label}</span>
                              <button
                                onClick={(e) => {
                                  e.preventDefault()
                                  e.stopPropagation()
                                  togglePin(item.path)
                                }}
                                className={`opacity-0 group-hover:opacity-100 p-0.5 rounded transition-opacity text-xs
                                  ${itemIsPinned 
                                    ? (isItemActive ? 'text-yellow-200' : 'text-yellow-500') 
                                    : (isItemActive ? 'text-white/50 hover:text-white' : 'text-gray-400 hover:text-gray-600')
                                  }
                                `}
                                title={itemIsPinned ? 'Unpin from favorites' : 'Pin to favorites'}
                              >
                                {itemIsPinned ? '⭐' : '☆'}
                              </button>
                            </>
                          )}
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
          
          {/* Context-Aware Related Items */}
          <ContextSidebar collapsed={sidebarCollapsed} />
        </nav>

        {/* Sidebar Footer - Only Collapse button */}
        <div className="flex-shrink-0 p-2 border-t border-gray-200 bg-white">
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-md hidden lg:flex"
          >
            <span>{sidebarCollapsed ? '→' : '←'}</span>
            {!sidebarCollapsed && <span>Collapse</span>}
          </button>
        </div>
      </aside>


      {/* Main Content Area */}
      <div className={`flex-1 transition-all duration-300 ${sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-60'}`}>
        {/* Top Bar */}
        <header className="h-14 bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-40 flex items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-4">
            {/* Mobile menu toggle */}
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
            
            {/* Page title */}
            <h2 className="text-base font-semibold text-gray-800 hidden sm:block">
              {navSections.flatMap(s => s.items).find(item => location.pathname.startsWith(item.path))?.label || 'Bijmantra'}
            </h2>
          </div>

          {/* Center - Command Palette Trigger */}
          <button
            onClick={() => setCommandPaletteOpen(true)}
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors border border-gray-200"
          >
            <span>🔍</span>
            <span className="hidden md:inline">Search anything...</span>
            <kbd className="hidden lg:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-xs bg-white rounded border border-gray-300 font-mono">
              ⌘K
            </kbd>
          </button>
          
          {/* Right side - Simplified */}
          <div className="flex items-center gap-2">
            {/* Role indicator when not in 'all' mode */}
            <RoleIndicator />
            
            {/* Role Switcher - hidden on mobile */}
            <div className="hidden md:block">
              <RoleSwitcher compact />
            </div>
            
            {/* Online presence indicator */}
            <div className="hidden lg:block">
              <PresenceIndicator maxVisible={3} showCount={false} />
            </div>
            
            {/* Sync status indicator */}
            <div className="hidden sm:block">
              <SyncStatusIndicator />
            </div>
            
            {/* Mobile search button */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="sm:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              aria-label="Search"
            >
              <span className="text-lg">🔍</span>
            </button>
            
            {/* Unified User Menu */}
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
    </div>
  )
}
