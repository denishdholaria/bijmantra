/**
 * ShellSidebar — Context-aware sidebar for Web-OS shell mode.
 * 
 * Auto-detects the current division from the active route, then shows
 * only that division's sections in a slim collapsible sidebar.
 * 
 * When no app route is active (on desktop/home), shows all division icons
 * in collapsed mode for quick access.
 * 
 * This replaces:
 *   - Mahasarthi.tsx (old gateway sidebar)
 *   - MahasarthiNav.tsx (navigation content wrapper)
 *   - MahasarthiKshetra.tsx (workspace switcher dropdown)
 *   - The conditional sidebar hiding in Layout.tsx
 */

import { useState, useMemo, useCallback } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useDivisionRegistry } from '@/framework/registry'
import { useSystemStore } from '@/store/systemStore'
import type { Division, DivisionSection } from '@/framework/registry/types'
import {
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  PanelLeftClose,
  PanelLeftOpen,
  Sparkles,
  type LucideIcon,
  // Division icons
  Sprout, Wheat, Leaf, Warehouse, Globe, Sun, Radio, Building2,
  Factory, Rocket, Plug, BookOpen, Wrench, Settings, Home, LayoutDashboard,
  // Section icons
  Dna, FlaskConical, Beaker, TestTube2, Microscope, Target, BarChart3,
  LineChart, Map, MapPin, CalendarDays, GitMerge, GitBranch, TreeDeciduous,
  Flower2, Package, Truck, QrCode, Shield, ShieldCheck, BadgeCheck,
  ClipboardCheck, ClipboardList, FileText, Calculator, Activity, Eye,
  Grid3X3, Cpu, Bell, Wifi, HelpCircle, GraduationCap, MessageSquare,
  Library, Brain, Lightbulb, Users, Cog, HardDrive, Layers, Droplets,
  Thermometer, CloudSun, Atom, Orbit, Scan, Tag, Archive, RefreshCw,
  SlidersHorizontal, Crosshair, TrendingUp, Folder,
} from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

// ============================================================================
// Icon Mapping (same as DivisionNavigation — single source of truth)
// ============================================================================

const iconMap: Record<string, LucideIcon> = {
  'Seedling': Sprout, 'Sprout': Sprout, 'Wheat': Wheat, 'Leaf': Leaf,
  'Warehouse': Warehouse, 'Globe': Globe, 'Sun': Sun, 'Radio': Radio,
  'Building2': Building2, 'Factory': Factory, 'Rocket': Rocket, 'Plug': Plug,
  'BookOpen': BookOpen, 'Wrench': Wrench, 'Settings': Settings, 'Home': Home,
  'LayoutDashboard': LayoutDashboard, 'Dna': Dna, 'FlaskConical': FlaskConical,
  'Beaker': Beaker, 'TestTube2': TestTube2, 'Microscope': Microscope,
  'Target': Target, 'Crosshair': Crosshair, 'BarChart3': BarChart3,
  'LineChart': LineChart, 'TrendingUp': TrendingUp, 'Activity': Activity,
  'Calculator': Calculator, 'Map': Map, 'MapPin': MapPin, 'Grid3X3': Grid3X3,
  'CalendarDays': CalendarDays, 'Calendar': CalendarDays, 'GitMerge': GitMerge,
  'GitBranch': GitBranch, 'TreeDeciduous': TreeDeciduous, 'Flower2': Flower2,
  'Package': Package, 'Truck': Truck, 'QrCode': QrCode, 'Scan': Scan,
  'Tag': Tag, 'Archive': Archive, 'Cog': Cog, 'Shield': Shield,
  'ShieldCheck': ShieldCheck, 'BadgeCheck': BadgeCheck,
  'ClipboardCheck': ClipboardCheck, 'ClipboardList': ClipboardList,
  'FileText': FileText, 'FileCheck': BadgeCheck, 'Layers': Layers,
  'Droplets': Droplets, 'Thermometer': Thermometer, 'CloudSun': CloudSun,
  'Cpu': Cpu, 'Bell': Bell, 'Wifi': Wifi, 'HardDrive': HardDrive,
  'Orbit': Orbit, 'HelpCircle': HelpCircle, 'GraduationCap': GraduationCap,
  'MessageSquare': MessageSquare, 'Library': Library, 'Book': BookOpen,
  'Brain': Brain, 'Lightbulb': Lightbulb, 'Users': Users, 'Eye': Eye,
  'RefreshCw': RefreshCw, 'SlidersHorizontal': SlidersHorizontal,
  'Folder': Folder, 'ArrowLeftRight': GitMerge, 'Clock': CalendarDays,
  'Atom': Atom,
}

const getIcon = (name: string): LucideIcon => iconMap[name] || Sparkles

// Division gradient colors
const divisionGradients: Record<string, string> = {
  'plant-sciences': 'from-emerald-600 to-emerald-700',
  'seed-bank': 'from-amber-500 to-amber-600',
  'earth-systems': 'from-blue-500 to-blue-600',
  'environment': 'from-blue-500 to-blue-600',
  'sun-earth-systems': 'from-amber-500 to-orange-500',
  'sensor-networks': 'from-teal-500 to-emerald-600',
  'seed-operations': 'from-blue-500 to-indigo-600',
  'seed-commerce': 'from-indigo-500 to-purple-500',
  'commercial': 'from-indigo-500 to-purple-500',
  'space-research': 'from-violet-500 to-purple-500',
  'integrations': 'from-slate-500 to-slate-600',
  'knowledge': 'from-pink-500 to-rose-500',
  'tools': 'from-slate-500 to-slate-600',
  'settings': 'from-stone-500 to-stone-600',
  'home': 'from-blue-500 to-cyan-500',
}

// ============================================================================
// Sidebar Subgroup (Section with items)
// ============================================================================

function SidebarSection({
  section,
  divisionRoute,
  onNavigate,
}: {
  section: DivisionSection
  divisionRoute: string
  onNavigate?: () => void
}) {
  const location = useLocation()
  const [isOpen, setIsOpen] = useState(false)
  const sectionPath = section.isAbsolute ? section.route : `${divisionRoute}${section.route}`
  const hasItems = section.items && section.items.length > 0

  // Check if any item is active → auto-expand
  const isActive = useMemo(() => {
    if (hasItems) {
      return section.items!.some(item => {
        const itemPath = item.isAbsolute ? item.route : `${divisionRoute}${item.route}`
        return location.pathname === itemPath || location.pathname.startsWith(itemPath + '/')
      })
    }
    return location.pathname === sectionPath || location.pathname.startsWith(sectionPath + '/')
  }, [location.pathname, section, divisionRoute, hasItems, sectionPath])

  // Auto-expand when active
  useMemo(() => {
    if (isActive && hasItems) setIsOpen(true)
  }, [isActive, hasItems])

  if (!hasItems) {
    return (
      <Link
        to={sectionPath}
        onClick={onNavigate}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 text-[13px] rounded-lg transition-colors',
          isActive
            ? 'bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300 font-medium'
            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800/50'
        )}
      >
        <span className="truncate">{section.name}</span>
      </Link>
    )
  }

  return (
    <div>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-full flex items-center gap-2 px-3 py-1.5 text-[13px] rounded-lg transition-colors text-left',
          isActive
            ? 'text-emerald-700 dark:text-emerald-300 font-medium'
            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800/50'
        )}
      >
        {isOpen ? (
          <ChevronDown className="w-3 h-3 flex-shrink-0 opacity-50" />
        ) : (
          <ChevronRight className="w-3 h-3 flex-shrink-0 opacity-50" />
        )}
        <span className="truncate flex-1">{section.name}</span>
        <span className="text-[10px] text-slate-400 dark:text-slate-500">{section.items!.length}</span>
      </button>

      {isOpen && (
        <div className="ml-4 pl-2 border-l border-slate-200 dark:border-slate-700/50 space-y-0.5 mt-0.5">
          {section.items!.map(item => {
            const itemPath = item.isAbsolute ? item.route : `${divisionRoute}${item.route}`
            const isItemActive =
              location.pathname === itemPath || location.pathname.startsWith(itemPath + '/')

            return (
              <Link
                key={item.id}
                to={itemPath}
                onClick={onNavigate}
                className={cn(
                  'flex items-center gap-2 px-2 py-1 text-xs rounded-md transition-colors',
                  isItemActive
                    ? 'bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300 font-medium'
                    : 'text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800/50'
                )}
              >
                <span className="truncate">{item.name}</span>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Main Shell Sidebar
// ============================================================================

export function ShellSidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { navigableDivisions } = useDivisionRegistry()
  const { sidebarCollapsed, toggleSidebar } = useSystemStore()

  // Determine which division matches the current route
  const activeDivision = useMemo<Division | null>(() => {
    // Sort by route length descending so more specific routes match first
    const sorted = [...navigableDivisions].sort(
      (a, b) => b.route.length - a.route.length
    )
    return sorted.find(d => location.pathname.startsWith(d.route)) || null
  }, [location.pathname, navigableDivisions])

  const isDesktopRoute = ['/', '/gateway', '/dashboard'].includes(location.pathname)

  const handleDivisionClick = useCallback((division: Division) => {
    navigate(division.route)
  }, [navigate])

  // ─── Collapsed Mode: Icon rail ───
  if (sidebarCollapsed) {
    return (
      <TooltipProvider delayDuration={150}>
        <aside className="flex flex-col w-14 h-full border-r border-slate-200/60 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/60 backdrop-blur-sm flex-shrink-0">
          {/* Toggle button */}
          <div className="flex items-center justify-center h-10 border-b border-slate-200/60 dark:border-slate-800/60">
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={toggleSidebar}
                  className="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                  aria-label="Expand sidebar"
                >
                  <PanelLeftOpen className="w-4 h-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" className="text-xs">Expand sidebar</TooltipContent>
            </Tooltip>
          </div>

          {/* Division icons */}
          <div className="flex-1 overflow-y-auto py-2 px-1.5 space-y-1">
            {navigableDivisions
              .filter(d => d.status === 'active' || d.status === 'beta')
              .map(division => {
                const Icon = getIcon(division.icon)
                const isActive = activeDivision?.id === division.id
                const gradient = divisionGradients[division.id] || 'from-slate-500 to-slate-600'

                return (
                  <Tooltip key={division.id}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => handleDivisionClick(division)}
                        className={cn(
                          'w-full flex items-center justify-center p-2.5 rounded-lg transition-all duration-200',
                          isActive
                            ? `bg-gradient-to-br ${gradient} text-white shadow-sm`
                            : 'text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
                        )}
                        aria-label={division.name}
                      >
                        <Icon className="w-4.5 h-4.5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="right" className="text-xs">
                      <span className="font-medium">{division.name}</span>
                      {division.status === 'beta' && (
                        <span className="ml-1 text-blue-400">(beta)</span>
                      )}
                    </TooltipContent>
                  </Tooltip>
                )
              })}
          </div>
        </aside>
      </TooltipProvider>
    )
  }

  // ─── Expanded Mode: Full sidebar ───
  return (
    <aside className="flex flex-col w-60 h-full border-r border-slate-200/60 dark:border-slate-800/60 bg-white/60 dark:bg-slate-950/60 backdrop-blur-sm flex-shrink-0">
      {/* Header with collapse toggle */}
      <div className="flex items-center justify-between h-10 px-3 border-b border-slate-200/60 dark:border-slate-800/60 flex-shrink-0">
        {activeDivision ? (
          <div className="flex items-center gap-2 min-w-0">
            {(() => {
              const Icon = getIcon(activeDivision.icon)
              return <Icon className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
            })()}
            <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate">
              {activeDivision.name}
            </span>
          </div>
        ) : (
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            All Modules
          </span>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors flex-shrink-0"
          aria-label="Collapse sidebar"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      {/* Navigation content */}
      <div className="flex-1 overflow-y-auto py-2 px-2">
        {activeDivision && activeDivision.sections && activeDivision.sections.length > 0 ? (
          // Show active division's sections
          <div className="space-y-0.5">
            {activeDivision.sections.map(section => (
              <SidebarSection
                key={section.id}
                section={section}
                divisionRoute={activeDivision.route}
              />
            ))}
          </div>
        ) : isDesktopRoute || !activeDivision ? (
          // On desktop/home or unmatched route: show all divisions as compact list
          <div className="space-y-0.5">
            {navigableDivisions
              .filter(d => d.status === 'active' || d.status === 'beta')
              .map(division => {
                const Icon = getIcon(division.icon)
                const isActive = activeDivision?.id === division.id
                const gradient = divisionGradients[division.id] || 'from-slate-500 to-slate-600'

                return (
                  <button
                    key={division.id}
                    onClick={() => handleDivisionClick(division)}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-left',
                      isActive
                        ? `bg-gradient-to-r ${gradient} text-white shadow-sm`
                        : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800/50'
                    )}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{division.name}</div>
                      <div className="text-[11px] opacity-60 truncate">{division.description}</div>
                    </div>
                    {division.status === 'beta' && (
                      <span className="ml-auto text-[9px] px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400 flex-shrink-0">
                        β
                      </span>
                    )}
                  </button>
                )
              })}
          </div>
        ) : (
          // Division with no sections — just show a link to the division overview
          <Link
            to={activeDivision.route}
            className="flex items-center gap-2 px-3 py-2 text-sm text-emerald-700 dark:text-emerald-300 font-medium rounded-lg bg-emerald-500/10 dark:bg-emerald-500/15"
          >
            Overview
          </Link>
        )}
      </div>

      {/* Back to all divisions button when viewing a specific division */}
      {activeDivision && !isDesktopRoute && (
        <div className="px-2 py-2 border-t border-slate-200/60 dark:border-slate-800/60 flex-shrink-0">
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-3 h-3" />
            <span>All Modules</span>
          </button>
        </div>
      )}
    </aside>
  )
}

export default ShellSidebar
