/**
 * Smart Navigation System with Lucide Icons
 * Professional navigation for 210+ pages
 * 
 * Integrated with Parashakti Framework Division Registry
 */

import { useState, useEffect, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { DivisionNavigation } from '@/framework/shell'
import {
  Home, Search, BarChart3, Bell, FileText, Brain, Sprout, Wheat,
  FlaskConical, ClipboardList, MapPin, Calendar, Package, GitMerge,
  GitBranch, Leaf, Target, Award, Calculator, Microscope, Eye,
  TestTube2, Dna, Camera, Grid3X3, Map as MapIcon, Activity,
  LineChart, SlidersHorizontal, CheckCircle2, Users, Layers, Zap,
  Cpu, Globe, Sun, Sparkles, RefreshCw, Wrench, Upload, Archive,
  Database, Book, MessageSquare, Settings, WifiOff,
  HelpCircle, Printer, ScanLine, Star, ChevronDown,
  TreeDeciduous, Thermometer, Shield,
  type LucideIcon,
} from 'lucide-react'

// ============================================
// TYPES
// ============================================

interface NavItem {
  path: string
  label: string
  icon: LucideIcon
  keywords?: string[]
}

interface NavCategory {
  id: string
  title: string
  icon: LucideIcon
  description: string
  color: string
  items: NavItem[]
}

// ============================================
// NAVIGATION DATA
// ============================================

export const smartNavCategories: NavCategory[] = [
  {
    id: 'home',
    title: 'Home',
    icon: Home,
    description: 'Dashboard & Overview',
    color: 'from-blue-500 to-cyan-500',
    items: [
      { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
      { path: '/insights', label: 'AI Insights', icon: Brain },
      { path: '/apex-analytics', label: 'Analytics', icon: LineChart },
      { path: '/search', label: 'Search', icon: Search },
      { path: '/notifications', label: 'Notifications', icon: Bell },
      { path: '/activity', label: 'Activity', icon: Activity },
    ],
  },
  {
    id: 'breeding',
    title: 'Breeding',
    icon: Sprout,
    description: 'Programs, Trials & Germplasm',
    color: 'from-green-500 to-emerald-500',
    items: [
      { path: '/programs', label: 'Programs', icon: Wheat },
      { path: '/trials', label: 'Trials', icon: FlaskConical },
      { path: '/studies', label: 'Studies', icon: ClipboardList },
      { path: '/locations', label: 'Locations', icon: MapPin },
      { path: '/seasons', label: 'Seasons', icon: Calendar },
      { path: '/germplasm', label: 'Germplasm', icon: Sprout },
      { path: '/seedlots', label: 'Seed Lots', icon: Package },
      { path: '/crosses', label: 'Crosses', icon: GitMerge },
      { path: '/crossingprojects', label: 'Crossing Projects', icon: GitBranch },
      { path: '/plannedcrosses', label: 'Planned Crosses', icon: ClipboardList },
      { path: '/progeny', label: 'Progeny', icon: Leaf },
      { path: '/pedigree', label: 'Pedigree', icon: TreeDeciduous },
      { path: '/pipeline', label: 'Pipeline', icon: Layers },
      { path: '/selectionindex', label: 'Selection Index', icon: Target },
      { path: '/selection-decision', label: 'Selection', icon: CheckCircle2 },
      { path: '/parent-selection', label: 'Parents', icon: Users },
      { path: '/cross-prediction', label: 'Prediction', icon: Sparkles },
      { path: '/performance-ranking', label: 'Rankings', icon: Award },
      { path: '/geneticgain', label: 'Genetic Gain', icon: LineChart },
      { path: '/genetic-gain-calculator', label: 'Calculator', icon: Calculator },
    ],
  },
  {
    id: 'data',
    title: 'Data',
    icon: Database,
    description: 'Phenotyping & Genotyping',
    color: 'from-purple-500 to-violet-500',
    items: [
      { path: '/traits', label: 'Traits', icon: Microscope },
      { path: '/observations', label: 'Observations', icon: Eye },
      { path: '/observations/collect', label: 'Collect Data', icon: ClipboardList },
      { path: '/observationunits', label: 'Units', icon: Leaf },
      { path: '/events', label: 'Events', icon: Calendar },
      { path: '/images', label: 'Images', icon: Camera },
      { path: '/samples', label: 'Samples', icon: TestTube2 },
      { path: '/variants', label: 'Variants', icon: Dna },
      { path: '/allelematrix', label: 'Allele Matrix', icon: Grid3X3 },
      { path: '/plates', label: 'Plates', icon: FlaskConical },
      { path: '/genomemaps', label: 'Genome Maps', icon: MapIcon },
      { path: '/statistics', label: 'Statistics', icon: BarChart3 },
      { path: '/visualization', label: 'Visualization', icon: LineChart },
      { path: '/trial-comparison', label: 'Compare Trials', icon: SlidersHorizontal },
      { path: '/trial-summary', label: 'Summary', icon: FileText },
      { path: '/dataquality', label: 'Data Quality', icon: CheckCircle2 },
    ],
  },
  {
    id: 'genomics',
    title: 'Genomics',
    icon: Dna,
    description: 'Molecular Analysis',
    color: 'from-amber-500 to-orange-500',
    items: [
      { path: '/genetic-diversity', label: 'Diversity', icon: Sparkles },
      { path: '/population-genetics', label: 'Population', icon: Users },
      { path: '/linkage-disequilibrium', label: 'LD Analysis', icon: GitBranch },
      { path: '/haplotype-analysis', label: 'Haplotypes', icon: Layers },
      { path: '/breeding-values', label: 'Breeding Values', icon: BarChart3 },
      { path: '/genomic-selection', label: 'Genomic Selection', icon: Dna },
      { path: '/genetic-correlation', label: 'Correlations', icon: RefreshCw },
      { path: '/qtl-mapping', label: 'QTL Mapping', icon: Target },
      { path: '/marker-assisted-selection', label: 'MAS', icon: Layers },
      { path: '/parentage-analysis', label: 'Parentage', icon: Users },
      { path: '/gxe-interaction', label: 'G×E', icon: Globe },
      { path: '/stability-analysis', label: 'Stability', icon: SlidersHorizontal },
      { path: '/trial-network', label: 'Trial Network', icon: Globe },
      { path: '/molecular-breeding', label: 'Molecular', icon: FlaskConical },
      { path: '/phenomic-selection', label: 'Phenomics', icon: Camera },
      { path: '/speed-breeding', label: 'Speed Breeding', icon: Zap },
      { path: '/doubled-haploid', label: 'Doubled Haploid', icon: Microscope },
      { path: '/breeding-simulator', label: 'Simulator', icon: Cpu },
      { path: '/wasm-genomics', label: 'WASM Engine', icon: Zap },
      { path: '/wasm-gblup', label: 'WASM GBLUP', icon: BarChart3 },
      { path: '/wasm-popgen', label: 'WASM PopGen', icon: Users },
    ],
  },
  {
    id: 'field',
    title: 'Field',
    icon: Wheat,
    description: 'Field Operations',
    color: 'from-teal-500 to-green-500',
    items: [
      { path: '/fieldlayout', label: 'Field Layout', icon: MapIcon },
      { path: '/fieldbook', label: 'Field Book', icon: Book },
      { path: '/field-map', label: 'Field Map', icon: MapIcon },
      { path: '/field-planning', label: 'Planning', icon: ClipboardList },
      { path: '/field-scanner', label: 'Scanner', icon: ScanLine },
      { path: '/trialdesign', label: 'Trial Design', icon: Grid3X3 },
      { path: '/trialplanning', label: 'Trial Planning', icon: Calendar },
      { path: '/season-planning', label: 'Season', icon: Calendar },
      { path: '/resource-allocation', label: 'Resources', icon: Database },
      { path: '/resource-calendar', label: 'Calendar', icon: Calendar },
      { path: '/harvest', label: 'Harvest', icon: Wheat },
      { path: '/nursery', label: 'Nursery', icon: Sprout },
      { path: '/inventory', label: 'Inventory', icon: Package },
      { path: '/weather', label: 'Weather', icon: Sun },
      { path: '/weather-forecast', label: 'Forecast', icon: Thermometer },
      { path: '/plant-vision', label: 'Plant Vision', icon: Eye },
      { path: '/disease-atlas', label: 'Disease Atlas', icon: Microscope },
      { path: '/crop-health', label: 'Crop Health', icon: Leaf },
      { path: '/yield-predictor', label: 'Yield Predict', icon: Target },
      { path: '/yieldmap', label: 'Yield Map', icon: MapIcon },
    ],
  },
  {
    id: 'tools',
    title: 'Tools',
    icon: Wrench,
    description: 'Utilities & Settings',
    color: 'from-gray-500 to-slate-600',
    items: [
      { path: '/quick-entry', label: 'Quick Entry', icon: Zap },
      { path: '/scanner', label: 'Barcode', icon: ScanLine },
      { path: '/labels', label: 'Labels', icon: Printer },
      { path: '/calculator', label: 'Calculator', icon: Calculator },
      { path: '/import-export', label: 'Import/Export', icon: Upload },
      { path: '/batch-operations', label: 'Batch Ops', icon: Layers },
      { path: '/reports', label: 'Reports', icon: FileText },
      { path: '/advanced-reports', label: 'Advanced', icon: FileText },
      { path: '/collaboration', label: 'Collaboration', icon: Users },
      { path: '/team-management', label: 'Team', icon: Users },
      { path: '/people', label: 'People', icon: Users },
      { path: '/workflows', label: 'Workflows', icon: RefreshCw },
      { path: '/ai-assistant', label: 'AI Assistant', icon: MessageSquare },
      { path: '/ai-settings', label: 'AI Settings', icon: Settings },
      { path: '/system-health', label: 'System', icon: Activity },
      { path: '/offline', label: 'Offline', icon: WifiOff },
      { path: '/data-sync', label: 'Sync', icon: RefreshCw },
      { path: '/backup', label: 'Backup', icon: Archive },
      { path: '/auditlog', label: 'Audit Log', icon: Shield },
      { path: '/users', label: 'Users', icon: Users },
      { path: '/settings', label: 'Settings', icon: Settings },
      { path: '/help', label: 'Help', icon: HelpCircle },
      { path: '/about', label: 'About', icon: HelpCircle },
    ],
  },
]

// All items flattened for search
export const allNavItems: NavItem[] = smartNavCategories.flatMap(cat => cat.items)

// ============================================
// HOOKS
// ============================================

export function useSmartNav() {
  const location = useLocation()
  const [recentPages, setRecentPages] = useState<string[]>([])
  const [favorites, setFavorites] = useState<string[]>([])

  useEffect(() => {
    const saved = localStorage.getItem('bijmantra-recent-pages')
    if (saved) setRecentPages(JSON.parse(saved))
    const savedFav = localStorage.getItem('bijmantra-favorites')
    if (savedFav) setFavorites(JSON.parse(savedFav))
  }, [])

  useEffect(() => {
    const path = location.pathname
    if (path === '/login') return
    setRecentPages(prev => {
      const updated = [path, ...prev.filter(p => p !== path)].slice(0, 10)
      localStorage.setItem('bijmantra-recent-pages', JSON.stringify(updated))
      return updated
    })
  }, [location.pathname])

  const toggleFavorite = (path: string) => {
    setFavorites(prev => {
      const updated = prev.includes(path)
        ? prev.filter(p => p !== path)
        : [...prev, path].slice(0, 12)
      localStorage.setItem('bijmantra-favorites', JSON.stringify(updated))
      return updated
    })
  }

  const isFavorite = (path: string) => favorites.includes(path)

  return { recentPages, favorites, toggleFavorite, isFavorite }
}

// ============================================
// COMPONENTS
// ============================================

interface SmartNavProps {
  collapsed?: boolean
  onNavigate?: () => void
}

export function SmartNavigation({ collapsed = false, onNavigate }: SmartNavProps) {
  const location = useLocation()
  const { favorites } = useSmartNav()
  const [searchQuery, setSearchQuery] = useState('')

  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return []
    const q = searchQuery.toLowerCase()
    return allNavItems.filter(item =>
      item.label.toLowerCase().includes(q) ||
      item.path.toLowerCase().includes(q) ||
      item.keywords?.some(k => k.toLowerCase().includes(q))
    ).slice(0, 8)
  }, [searchQuery])

  const favoriteItems = useMemo(() => {
    return favorites
      .map(path => allNavItems.find(item => item.path === path))
      .filter(Boolean) as NavItem[]
  }, [favorites])



  if (collapsed) {
    return (
      <div className="py-2 space-y-1">
        {smartNavCategories.map(cat => {
          const IconComponent = cat.icon
          return (
            <Link
              key={cat.id}
              to={cat.items[0].path}
              onClick={onNavigate}
              className={cn(
                'flex items-center justify-center p-3 rounded-lg transition-all',
                location.pathname.startsWith(cat.items[0].path)
                  ? 'bg-gradient-to-r ' + cat.color + ' text-white'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600'
              )}
              title={cat.title}
            >
              <IconComponent className="w-5 h-5" />
            </Link>
          )
        })}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="relative">
          <input
            type="text"
            placeholder="Search pages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 rounded-lg border-0 focus:ring-2 focus:ring-green-500"
          />
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
        </div>
        
        {searchResults.length > 0 && (
          <div className="mt-2 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 shadow-lg max-h-64 overflow-y-auto">
            {searchResults.map(item => {
              const IconComponent = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => { setSearchQuery(''); onNavigate?.() }}
                  className="flex items-center gap-3 px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <IconComponent className="w-4 h-4 text-gray-500" />
                  <span className="text-sm">{item.label}</span>
                </Link>
              )
            })}
          </div>
        )}
      </div>

      {/* Favorites */}
      {favoriteItems.length > 0 && (
        <div className="p-3 border-b border-gray-200 dark:border-gray-700">
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-1">
            <Star className="w-3 h-3" /> Favorites
          </div>
          <div className="flex flex-wrap gap-1">
            {favoriteItems.map(item => {
              const IconComponent = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={onNavigate}
                  className={cn(
                    'px-2 py-1 text-xs rounded-md transition-colors flex items-center gap-1.5',
                    location.pathname === item.path
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
                  )}
                >
                  <IconComponent className="w-3 h-3" />
                  <span className="truncate max-w-[70px]">{item.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      )}

      {/* Main Navigation Area */}
      <div className="flex-1 overflow-y-auto">
        {/* Parashakti Labs */}
        <DivisionNavigation collapsed={false} onNavigate={onNavigate} />
      </div>
    </div>
  )
}

export default SmartNavigation
