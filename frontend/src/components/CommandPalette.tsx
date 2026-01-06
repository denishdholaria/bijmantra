/**
 * Command Palette Component
 * Global search and navigation with ⌘K / Ctrl+K
 */

import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Command } from 'cmdk'

interface NavItem {
  path: string
  label: string
  icon: string
  section: string
  keywords?: string[]
}

// Flattened navigation items for search
const allNavItems: NavItem[] = [
  // AI
  { path: '/ai-assistant', label: 'AI Assistant', icon: '💬', section: 'AI', keywords: ['chat', 'help', 'question'] },
  { path: '/plant-vision', label: 'Plant Vision', icon: '🌿', section: 'AI', keywords: ['camera', 'detect', 'disease'] },
  { path: '/field-scanner', label: 'Field Scanner', icon: '📱', section: 'AI', keywords: ['scan', 'qr', 'barcode'] },
  { path: '/disease-atlas', label: 'Disease Atlas', icon: '🦠', section: 'AI', keywords: ['pest', 'pathogen'] },
  { path: '/crop-health', label: 'Crop Health Dashboard', icon: '🌾', section: 'AI' },
  { path: '/yield-predictor', label: 'Yield Predictor', icon: '🎯', section: 'AI', keywords: ['forecast', 'estimate'] },
  { path: '/chrome-ai', label: 'Chrome AI', icon: '🌐', section: 'AI', keywords: ['gemini', 'local'] },
  { path: '/ai-settings', label: 'AI Settings', icon: '⚙️', section: 'AI' },
  
  // Core
  { path: '/dashboard', label: 'Dashboard', icon: '📊', section: 'Core', keywords: ['home', 'overview'] },
  { path: '/search', label: 'Search', icon: '🔍', section: 'Core', keywords: ['find', 'lookup'] },
  { path: '/programs', label: 'Programs', icon: '🌾', section: 'Core', keywords: ['breeding program'] },
  { path: '/trials', label: 'Trials', icon: '🧪', section: 'Core', keywords: ['experiment', 'test'] },
  { path: '/studies', label: 'Studies', icon: '📈', section: 'Core' },
  { path: '/locations', label: 'Locations', icon: '📍', section: 'Core', keywords: ['site', 'field', 'place'] },
  { path: '/people', label: 'People', icon: '👥', section: 'Core', keywords: ['team', 'staff', 'contact'] },
  { path: '/seasons', label: 'Seasons', icon: '📅', section: 'Core', keywords: ['year', 'cycle'] },
  
  // Germplasm
  { path: '/germplasm', label: 'Germplasm', icon: '🌱', section: 'Germplasm', keywords: ['accession', 'variety', 'line'] },
  { path: '/seedlots', label: 'Seed Lots', icon: '📦', section: 'Germplasm', keywords: ['inventory', 'stock'] },
  { path: '/crosses', label: 'Crosses', icon: '🧬', section: 'Germplasm', keywords: ['hybridization', 'mating'] },
  { path: '/crossingprojects', label: 'Crossing Projects', icon: '🔀', section: 'Germplasm' },
  { path: '/plannedcrosses', label: 'Planned Crosses', icon: '📋', section: 'Germplasm' },
  { path: '/progeny', label: 'Progeny', icon: '🌿', section: 'Germplasm', keywords: ['offspring', 'descendants'] },
  { path: '/attributevalues', label: 'Germplasm Attributes', icon: '📝', section: 'Germplasm' },
  
  // Phenotyping
  { path: '/traits', label: 'Traits', icon: '🔬', section: 'Phenotyping', keywords: ['variable', 'characteristic'] },
  { path: '/observations', label: 'Observations', icon: '📋', section: 'Phenotyping', keywords: ['data', 'measurement'] },
  { path: '/observationunits', label: 'Observation Units', icon: '🌿', section: 'Phenotyping', keywords: ['plot', 'plant'] },
  { path: '/events', label: 'Events', icon: '📆', section: 'Phenotyping', keywords: ['activity', 'treatment'] },
  { path: '/images', label: 'Images', icon: '📷', section: 'Phenotyping', keywords: ['photo', 'picture'] },
  { path: '/ontologies', label: 'Ontologies', icon: '📖', section: 'Phenotyping' },
  
  // Genotyping
  { path: '/samples', label: 'Samples', icon: '🧫', section: 'Genotyping', keywords: ['dna', 'tissue'] },
  { path: '/variants', label: 'Variants', icon: '🔀', section: 'Genotyping', keywords: ['snp', 'marker'] },
  { path: '/allelematrix', label: 'Allele Matrix', icon: '📐', section: 'Genotyping' },
  { path: '/plates', label: 'Plates', icon: '🧪', section: 'Genotyping' },
  { path: '/references', label: 'References', icon: '📚', section: 'Genotyping', keywords: ['genome'] },
  { path: '/genomemaps', label: 'Genome Maps', icon: '🗺️', section: 'Genotyping' },
  
  // Genomics
  { path: '/genetic-diversity', label: 'Genetic Diversity', icon: '🌈', section: 'Genomics', keywords: ['diversity', 'heterozygosity'] },
  { path: '/breeding-values', label: 'Breeding Values', icon: '📊', section: 'Genomics', keywords: ['blup', 'ebv'] },
  { path: '/qtl-mapping', label: 'QTL Mapping', icon: '🎯', section: 'Genomics', keywords: ['gwas', 'association'] },
  { path: '/genomic-selection', label: 'Genomic Selection', icon: '🧬', section: 'Genomics', keywords: ['gs', 'gebv'] },
  { path: '/marker-assisted-selection', label: 'Marker Assisted Selection', icon: '🔖', section: 'Genomics', keywords: ['mas', 'mabc'] },
  { path: '/haplotype-analysis', label: 'Haplotype Analysis', icon: '🔗', section: 'Genomics' },
  { path: '/linkage-disequilibrium', label: 'Linkage Disequilibrium', icon: '📈', section: 'Genomics', keywords: ['ld'] },
  { path: '/population-genetics', label: 'Population Genetics', icon: '👥', section: 'Genomics', keywords: ['structure', 'pca'] },
  { path: '/parentage-analysis', label: 'Parentage Analysis', icon: '👨‍👩‍👧', section: 'Genomics', keywords: ['pedigree', 'verification'] },
  { path: '/genetic-correlation', label: 'Genetic Correlation', icon: '🔄', section: 'Genomics' },
  { path: '/gxe-interaction', label: 'G×E Interaction', icon: '🌍', section: 'Genomics', keywords: ['ammi', 'gge'] },
  { path: '/stability-analysis', label: 'Stability Analysis', icon: '⚖️', section: 'Genomics' },
  
  // Advanced Breeding
  { path: '/molecular-breeding', label: 'Molecular Breeding', icon: '🧪', section: 'Advanced' },
  { path: '/phenomic-selection', label: 'Phenomic Selection', icon: '📷', section: 'Advanced' },
  { path: '/speed-breeding', label: 'Speed Breeding', icon: '⚡', section: 'Advanced' },
  { path: '/doubled-haploid', label: 'Doubled Haploid', icon: '🔬', section: 'Advanced', keywords: ['dh'] },
  { path: '/breeding-simulator', label: 'Breeding Simulator', icon: '🎮', section: 'Advanced' },
  { path: '/genetic-gain-calculator', label: 'Genetic Gain Calculator', icon: '📈', section: 'Advanced' },
  { path: '/cross-prediction', label: 'Cross Prediction', icon: '🔮', section: 'Advanced' },
  { path: '/parent-selection', label: 'Parent Selection', icon: '👨‍👩‍👧', section: 'Advanced' },
  { path: '/selection-decision', label: 'Selection Decision', icon: '✅', section: 'Advanced' },
  { path: '/performance-ranking', label: 'Performance Ranking', icon: '🏆', section: 'Advanced' },

  // Analytics
  { path: '/analytics', label: 'Analytics Dashboard', icon: '📊', section: 'Analytics' },
  { path: '/trial-summary', label: 'Trial Summary', icon: '📋', section: 'Analytics' },
  { path: '/trial-comparison', label: 'Trial Comparison', icon: '⚖️', section: 'Analytics' },
  { path: '/trial-network', label: 'Trial Network', icon: '🌐', section: 'Analytics' },
  { path: '/visualization', label: 'Data Visualization', icon: '📈', section: 'Analytics' },
  { path: '/advanced-reports', label: 'Advanced Reports', icon: '📑', section: 'Analytics' },
  { path: '/activity', label: 'Activity Timeline', icon: '📜', section: 'Analytics' },
  
  // Planning
  { path: '/season-planning', label: 'Season Planning', icon: '🗓️', section: 'Planning' },
  { path: '/field-planning', label: 'Field Planning', icon: '🗺️', section: 'Planning' },
  { path: '/resource-allocation', label: 'Resource Allocation', icon: '💰', section: 'Planning' },
  { path: '/breeding-history', label: 'Breeding History', icon: '📚', section: 'Planning' },
  { path: '/breeding-goals', label: 'Breeding Goals', icon: '🎯', section: 'Planning' },
  { path: '/resource-calendar', label: 'Resource Calendar', icon: '📆', section: 'Planning' },
  
  // Tools
  { path: '/fieldlayout', label: 'Field Layout', icon: '🗺️', section: 'Tools' },
  { path: '/trialdesign', label: 'Trial Design', icon: '🎲', section: 'Tools', keywords: ['rcbd', 'alpha'] },
  { path: '/selectionindex', label: 'Selection Index', icon: '📊', section: 'Tools' },
  { path: '/geneticgain', label: 'Genetic Gain', icon: '📈', section: 'Tools' },
  { path: '/pedigree', label: 'Pedigree Viewer', icon: '🌳', section: 'Tools' },
  { path: '/pipeline', label: 'Breeding Pipeline', icon: '🔀', section: 'Tools' },
  { path: '/harvest', label: 'Harvest Planner', icon: '🌾', section: 'Tools' },
  { path: '/inventory', label: 'Seed Inventory', icon: '📦', section: 'Tools' },
  { path: '/crossingplanner', label: 'Crossing Planner', icon: '💑', section: 'Tools' },
  { path: '/scanner', label: 'Barcode Scanner', icon: '📱', section: 'Tools' },
  { path: '/weather', label: 'Weather', icon: '🌤️', section: 'Tools' },
  { path: '/import-export', label: 'Import/Export', icon: '🔄', section: 'Tools' },
  { path: '/reports', label: 'Reports', icon: '📋', section: 'Tools' },
  
  // WASM
  { path: '/wasm-genomics', label: 'WASM Genomics', icon: '⚡', section: 'WASM Engine', keywords: ['rust', 'performance'] },
  { path: '/wasm-gblup', label: 'WASM GBLUP', icon: '📊', section: 'WASM Engine' },
  { path: '/wasm-popgen', label: 'WASM Population Genetics', icon: '👥', section: 'WASM Engine' },
  { path: '/wasm-ld', label: 'WASM LD Analysis', icon: '🔗', section: 'WASM Engine' },
  { path: '/wasm-selection', label: 'WASM Selection Index', icon: '🎯', section: 'WASM Engine' },
  
  // System
  { path: '/settings', label: 'Settings', icon: '⚙️', section: 'System' },
  { path: '/profile', label: 'Profile', icon: '👤', section: 'System' },
  { path: '/notifications', label: 'Notifications', icon: '🔔', section: 'System' },
  { path: '/system-health', label: 'System Health', icon: '💚', section: 'System' },
  { path: '/offline', label: 'Offline Mode', icon: '📴', section: 'System' },
  { path: '/backup', label: 'Backup & Restore', icon: '💾', section: 'System' },
  { path: '/users', label: 'User Management', icon: '👤', section: 'System' },
  { path: '/auditlog', label: 'Audit Log', icon: '📋', section: 'System' },
  { path: '/api-explorer', label: 'API Explorer', icon: '🔌', section: 'System' },
  
  // Help
  { path: '/help', label: 'Help Center', icon: '📚', section: 'Help' },
  { path: '/quick-guide', label: 'Quick Start Guide', icon: '🚀', section: 'Help' },
  { path: '/glossary', label: 'Glossary', icon: '📖', section: 'Help' },
  { path: '/faq', label: 'FAQ', icon: '❓', section: 'Help' },
  { path: '/keyboard-shortcuts', label: 'Keyboard Shortcuts', icon: '⌨️', section: 'Help' },
  { path: '/about', label: 'About', icon: 'ℹ️', section: 'Help' },
]

// Quick actions
const quickActions = [
  { id: 'new-observation', label: 'Add Observation', icon: '➕', action: 'navigate', path: '/observations/collect' },
  { id: 'new-germplasm', label: 'Add Germplasm', icon: '🌱', action: 'navigate', path: '/germplasm/new' },
  { id: 'new-cross', label: 'Create Cross', icon: '🧬', action: 'navigate', path: '/crosses/new' },
  { id: 'scan', label: 'Scan Barcode', icon: '📱', action: 'navigate', path: '/scanner' },
  { id: 'ai-chat', label: 'Ask AI Assistant', icon: '💬', action: 'navigate', path: '/ai-assistant' },
]

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [recentItems, setRecentItems] = useState<string[]>([])

  // Load recent items from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('bijmantra-recent-nav')
    if (stored) {
      setRecentItems(JSON.parse(stored))
    }
  }, [open])

  const handleSelect = useCallback((path: string) => {
    // Update recent items
    const updated = [path, ...recentItems.filter(p => p !== path)].slice(0, 5)
    localStorage.setItem('bijmantra-recent-nav', JSON.stringify(updated))
    setRecentItems(updated)
    
    onOpenChange(false)
    setSearch('')
    navigate(path)
  }, [navigate, onOpenChange, recentItems])

  // Get recent nav items
  const recentNavItems = recentItems
    .map(path => allNavItems.find(item => item.path === path))
    .filter(Boolean) as NavItem[]

  // Group items by section
  const groupedItems = allNavItems.reduce((acc, item) => {
    if (!acc[item.section]) acc[item.section] = []
    acc[item.section].push(item)
    return acc
  }, {} as Record<string, NavItem[]>)

  return (
    <Command.Dialog
      open={open}
      onOpenChange={onOpenChange}
      label="Global Command Menu"
      className="fixed inset-0 z-[100]"
    >
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      
      {/* Dialog */}
      <div className="fixed left-1/2 top-[20%] -translate-x-1/2 w-full max-w-2xl">
        <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
          {/* Search Input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
            <span className="text-gray-400">🔍</span>
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Search pages, tools, or type a command..."
              className="flex-1 bg-transparent outline-none text-gray-900 placeholder:text-gray-400"
              autoFocus
            />
            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 bg-gray-100 rounded">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <Command.List className="max-h-[60vh] overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-gray-500">
              No results found. Try a different search term.
            </Command.Empty>

            {/* Quick Actions */}
            {!search && (
              <Command.Group heading="Quick Actions" className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quick Actions
                </div>
                {quickActions.map((action) => (
                  <Command.Item
                    key={action.id}
                    value={action.label}
                    onSelect={() => handleSelect(action.path)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 hover:bg-green-50 hover:text-green-700 data-[selected=true]:bg-green-50 data-[selected=true]:text-green-700"
                  >
                    <span className="text-lg">{action.icon}</span>
                    <span className="font-medium">{action.label}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Recent */}
            {!search && recentNavItems.length > 0 && (
              <Command.Group heading="Recent" className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Recent
                </div>
                {recentNavItems.map((item) => (
                  <Command.Item
                    key={`recent-${item.path}`}
                    value={`recent ${item.label}`}
                    onSelect={() => handleSelect(item.path)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 hover:bg-gray-50 data-[selected=true]:bg-gray-100"
                  >
                    <span className="text-lg">{item.icon}</span>
                    <span>{item.label}</span>
                    <span className="ml-auto text-xs text-gray-400">{item.section}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* All Sections */}
            {Object.entries(groupedItems).map(([section, items]) => (
              <Command.Group key={section} heading={section} className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {section}
                </div>
                {items.map((item) => (
                  <Command.Item
                    key={item.path}
                    value={`${item.label} ${item.section} ${item.keywords?.join(' ') || ''}`}
                    onSelect={() => handleSelect(item.path)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 hover:bg-gray-50 data-[selected=true]:bg-gray-100"
                  >
                    <span className="text-lg">{item.icon}</span>
                    <span>{item.label}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            ))}
          </Command.List>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 bg-gray-50 text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white rounded border">↑↓</kbd> Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white rounded border">↵</kbd> Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white rounded border">ESC</kbd> Close
              </span>
            </div>
            <span>🌱 Bijmantra</span>
          </div>
        </div>
      </div>
    </Command.Dialog>
  )
}
