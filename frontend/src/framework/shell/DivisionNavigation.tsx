/**
 * Parashakti Framework - Division Navigation
 * 
 * Navigation component that renders divisions from the registry.
 * Supports nested subgroups for complex navigation structures.
 * Filters by active workspace when workspace is selected.
 * Supports custom workspaces (MyWorkspace) with page-level filtering.
 */

import { useState, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useDivisionRegistry } from '../registry'
import { Division, DivisionSection, DivisionStatus } from '../registry/types'
import { useWorkspaceStore, useActiveWorkspace } from '@/store/workspaceStore'
import { useCustomWorkspaceStore, useActiveCustomWorkspace } from '@/store/customWorkspaceStore'
import { useActiveWorkspacePages } from '@/hooks/useCustomWorkspace'
import { getWorkspaceModules, isRouteInWorkspace } from '@/framework/registry/workspaces'
import type { WorkspaceId } from '@/types/workspace'
import {
  // Navigation
  ChevronDown, 
  ChevronRight, 
  Sparkles,
  
  // Divisions
  Sprout,
  Wheat,
  Leaf,
  Warehouse,
  Globe,
  Sun,
  Radio,
  Building2,
  Factory,
  Rocket,
  Plug,
  BookOpen,
  Wrench,
  Settings,
  Home,
  LayoutDashboard,
  
  // Subgroups
  Dna,
  FlaskConical,
  Beaker,
  TestTube2,
  Microscope,
  Target,
  BarChart3,
  LineChart,
  Map,
  MapPin,
  CalendarDays,
  GitMerge,
  GitBranch,
  TreeDeciduous,
  Flower2,
  Package,
  Truck,
  QrCode,
  Shield,
  ShieldCheck,
  BadgeCheck,
  ClipboardCheck,
  ClipboardList,
  FileText,
  Calculator,
  Activity,
  Eye,
  Grid3X3,
  Cpu,
  Bell,
  Wifi,
  HelpCircle,
  GraduationCap,
  MessageSquare,
  Library,
  Brain,
  Lightbulb,
  Users,
  Cog,
  HardDrive,
  Layers,
  Droplets,
  Thermometer,
  CloudSun,
  Atom,
  Orbit,
  Scan,
  Tag,
  Archive,
  RefreshCw,
  SlidersHorizontal,
  Crosshair,
  TrendingUp,
  Folder,
  type LucideIcon,
} from 'lucide-react'

// Comprehensive icon mapping for divisions and sections
const divisionIcons: Record<string, LucideIcon> = {
  // Division Icons
  'Seedling': Sprout,
  'Sprout': Sprout,
  'Wheat': Wheat,
  'Leaf': Leaf,
  'Warehouse': Warehouse,
  'Globe': Globe,
  'Sun': Sun,
  'Radio': Radio,
  'Building2': Building2,
  'Factory': Factory,
  'Rocket': Rocket,
  'Plug': Plug,
  'BookOpen': BookOpen,
  'Wrench': Wrench,
  'Settings': Settings,
  'Home': Home,
  'LayoutDashboard': LayoutDashboard,
  
  // Science & Lab
  'Dna': Dna,
  'FlaskConical': FlaskConical,
  'Beaker': Beaker,
  'TestTube2': TestTube2,
  'Microscope': Microscope,
  'Atom': Atom,
  
  // Analytics & Data
  'Target': Target,
  'Crosshair': Crosshair,
  'BarChart3': BarChart3,
  'LineChart': LineChart,
  'TrendingUp': TrendingUp,
  'Activity': Activity,
  'Calculator': Calculator,
  
  // Field & Location
  'Map': Map,
  'MapPin': MapPin,
  'Grid3X3': Grid3X3,
  'CalendarDays': CalendarDays,
  'Calendar': CalendarDays,
  
  // Breeding & Genetics
  'GitMerge': GitMerge,
  'GitBranch': GitBranch,
  'TreeDeciduous': TreeDeciduous,
  'Flower2': Flower2,
  
  // Operations
  'Package': Package,
  'Truck': Truck,
  'QrCode': QrCode,
  'Scan': Scan,
  'Tag': Tag,
  'Archive': Archive,
  'Cog': Cog,
  
  // Quality & Compliance
  'Shield': Shield,
  'ShieldCheck': ShieldCheck,
  'BadgeCheck': BadgeCheck,
  'ClipboardCheck': ClipboardCheck,
  'ClipboardList': ClipboardList,
  'FileText': FileText,
  'FileCheck': BadgeCheck,
  
  // Environment
  'Layers': Layers,
  'Droplets': Droplets,
  'Thermometer': Thermometer,
  'CloudSun': CloudSun,
  
  // Technology
  'Cpu': Cpu,
  'Bell': Bell,
  'Wifi': Wifi,
  'HardDrive': HardDrive,
  'Orbit': Orbit,
  
  // Knowledge & Help
  'HelpCircle': HelpCircle,
  'GraduationCap': GraduationCap,
  'MessageSquare': MessageSquare,
  'Library': Library,
  'Book': BookOpen,
  
  // AI & Smart
  'Brain': Brain,
  'Lightbulb': Lightbulb,
  
  // Users
  'Users': Users,
  
  // Misc
  'Eye': Eye,
  'RefreshCw': RefreshCw,
  'SlidersHorizontal': SlidersHorizontal,
  'Folder': Folder,
  'ArrowLeftRight': GitMerge,
  'Clock': CalendarDays,
}

// Status badge colors - Prakruti Design System
const statusColors: Record<DivisionStatus, string> = {
  active: 'bg-prakruti-patta-pale text-prakruti-patta dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light',
  beta: 'bg-prakruti-neela-pale text-prakruti-neela dark:bg-prakruti-neela/20 dark:text-prakruti-neela-light',
  planned: 'bg-prakruti-dhool-200 text-prakruti-dhool-600 dark:bg-prakruti-dhool-800 dark:text-prakruti-dhool-400',
  visionary: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
}

// Division gradient colors - Prakruti Design System
const divisionColors: Record<string, string> = {
  'plant-sciences': 'from-prakruti-patta to-prakruti-patta-dark',
  'seed-bank': 'from-prakruti-sona to-prakruti-sona-dark',
  'earth-systems': 'from-prakruti-neela to-prakruti-neela-dark',
  'environment': 'from-prakruti-neela to-prakruti-neela-dark',
  'sun-earth-systems': 'from-prakruti-sona to-prakruti-narangi',
  'sensor-networks': 'from-teal-500 to-prakruti-patta',
  'seed-operations': 'from-prakruti-neela to-indigo-600',
  'seed-commerce': 'from-indigo-500 to-purple-500',
  'commercial': 'from-indigo-500 to-purple-500',
  'space-research': 'from-violet-500 to-purple-500',
  'integrations': 'from-prakruti-dhool-500 to-prakruti-dhool-600',
  'knowledge': 'from-pink-500 to-rose-500',
  'tools': 'from-prakruti-dhool-500 to-prakruti-dhool-600',
  'settings': 'from-prakruti-mitti to-prakruti-mitti-dark',
  'home': 'from-prakruti-neela to-cyan-500',
}


// Subgroup component for nested navigation
interface SubgroupProps {
  section: DivisionSection
  divisionRoute: string
  isExpanded: boolean
  onToggle: () => void
  onNavigate?: () => void
}

function Subgroup({ section, divisionRoute, isExpanded, onToggle, onNavigate }: SubgroupProps) {
  const location = useLocation()
  const sectionPath = section.isAbsolute ? section.route : `${divisionRoute}${section.route}`
  const hasItems = section.items && section.items.length > 0
  
  // Check if any item in this subgroup is active
  const isActive = hasItems 
    ? section.items!.some(item => {
        const itemPath = item.isAbsolute ? item.route : `${divisionRoute}${item.route}`
        return location.pathname === itemPath || location.pathname.startsWith(itemPath + '/')
      })
    : location.pathname === sectionPath || location.pathname.startsWith(sectionPath + '/')

  if (!hasItems) {
    // Simple link without nested items
    return (
      <Link
        to={sectionPath}
        onClick={onNavigate}
        className={cn(
          'flex items-center gap-2 px-2 py-1.5 text-sm rounded-md transition-colors',
          isActive
            ? 'bg-prakruti-patta-pale text-prakruti-patta dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light font-medium'
            : 'hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 text-prakruti-dhool-700 dark:text-prakruti-dhool-300'
        )}
      >
        <span className="truncate">{section.name}</span>
      </Link>
    )
  }

  return (
    <div>
      <button
        onClick={onToggle}
        className={cn(
          'w-full flex items-center gap-2 px-2 py-1.5 text-sm rounded-md transition-colors text-left',
          isActive
            ? 'text-prakruti-patta dark:text-prakruti-patta-light font-medium'
            : 'hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 text-prakruti-dhool-700 dark:text-prakruti-dhool-300'
        )}
      >
        {isExpanded ? (
          <ChevronDown className="w-3 h-3 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-3 h-3 flex-shrink-0" />
        )}
        <span className="truncate">{section.name}</span>
        <span className="ml-auto text-xs text-prakruti-dhool-400">{section.items!.length}</span>
      </button>
      
      {isExpanded && (
        <div className="ml-4 pl-2 border-l border-prakruti-dhool-200 dark:border-prakruti-dhool-700 space-y-0.5 mt-0.5">
          {section.items!.map(item => {
            const itemPath = item.isAbsolute ? item.route : `${divisionRoute}${item.route}`
            const isItemActive = location.pathname === itemPath || 
                                 location.pathname.startsWith(itemPath + '/')
            
            return (
              <Link
                key={item.id}
                to={itemPath}
                onClick={onNavigate}
                className={cn(
                  'flex items-center gap-2 px-2 py-1 text-xs rounded-md transition-colors',
                  isItemActive
                    ? 'bg-prakruti-patta-pale text-prakruti-patta dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light font-medium'
                    : 'hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 text-prakruti-dhool-600 dark:text-prakruti-dhool-400'
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

interface DivisionNavItemProps {
  division: Division
  isExpanded: boolean
  onToggle: () => void
  onNavigate?: () => void
}

function DivisionNavItem({ division, isExpanded, onToggle, onNavigate }: DivisionNavItemProps) {
  const location = useLocation()
  const [expandedSubgroups, setExpandedSubgroups] = useState<Set<string>>(new Set())
  const IconComponent = divisionIcons[division.icon] || Sparkles
  const isActive = location.pathname.startsWith(division.route)
  const gradientColor = divisionColors[division.id] || 'from-prakruti-dhool-500 to-prakruti-dhool-600'

  const toggleSubgroup = (sectionId: string) => {
    setExpandedSubgroups(prev => {
      const next = new Set(prev)
      if (next.has(sectionId)) {
        next.delete(sectionId)
      } else {
        next.add(sectionId)
      }
      return next
    })
  }

  // Auto-expand subgroup containing current route
  useMemo(() => {
    if (division.sections) {
      division.sections.forEach(section => {
        if (section.items) {
          const hasActiveItem = section.items.some(item => {
            const itemPath = item.isAbsolute ? item.route : `${division.route}${item.route}`
            return location.pathname === itemPath || location.pathname.startsWith(itemPath + '/')
          })
          if (hasActiveItem) {
            setExpandedSubgroups(prev => new Set([...prev, section.id]))
          }
        }
      })
    }
  }, [location.pathname, division])

  return (
    <div className="mb-1">
      {/* Division Header */}
      <button
        onClick={onToggle}
        className={cn(
          'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-left',
          isActive
            ? `bg-gradient-to-r ${gradientColor} text-white shadow-md`
            : 'hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 text-prakruti-dhool-700 dark:text-prakruti-dhool-300'
        )}
      >
        <IconComponent className="w-5 h-5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{division.name}</span>
            {division.status !== 'active' && (
              <span className={cn(
                'px-1.5 py-0.5 text-[10px] font-medium rounded-full uppercase',
                statusColors[division.status]
              )}>
                {division.status}
              </span>
            )}
          </div>
          {!isExpanded && (
            <div className="text-xs opacity-70 truncate">{division.description}</div>
          )}
        </div>
        {division.sections && division.sections.length > 0 && (
          isExpanded ? (
            <ChevronDown className="w-4 h-4 flex-shrink-0" />
          ) : (
            <ChevronRight className="w-4 h-4 flex-shrink-0" />
          )
        )}
      </button>

      {/* Division Sections */}
      {isExpanded && division.sections && division.sections.length > 0 && (
        <div className="mt-1 ml-3 pl-3 border-l-2 border-prakruti-dhool-200 dark:border-prakruti-dhool-700 space-y-0.5">
          {division.sections.map(section => (
            <Subgroup
              key={section.id}
              section={section}
              divisionRoute={division.route}
              isExpanded={expandedSubgroups.has(section.id)}
              onToggle={() => toggleSubgroup(section.id)}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}

      {/* Direct link if no sections */}
      {isExpanded && (!division.sections || division.sections.length === 0) && (
        <div className="mt-1 ml-3 pl-3 border-l-2 border-prakruti-dhool-200 dark:border-prakruti-dhool-700">
          <Link
            to={division.route}
            onClick={onNavigate}
            className={cn(
              'flex items-center gap-2 px-2 py-1.5 text-sm rounded-md transition-colors',
              isActive
                ? 'bg-prakruti-patta-pale text-prakruti-patta dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light font-medium'
                : 'hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 text-prakruti-dhool-700 dark:text-prakruti-dhool-300'
            )}
          >
            <span>Overview</span>
          </Link>
        </div>
      )}
    </div>
  )
}

interface DivisionNavigationProps {
  collapsed?: boolean
  onNavigate?: () => void
}

export function DivisionNavigation({ collapsed = false, onNavigate }: DivisionNavigationProps) {
  const location = useLocation()
  const { navigableDivisions } = useDivisionRegistry()
  const [expandedDivision, setExpandedDivision] = useState<string | null>('plant-sciences')
  
  // System workspace filtering
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  const activeWorkspace = useActiveWorkspace()
  
  // Custom workspace filtering
  const activeCustomWorkspace = useActiveCustomWorkspace()
  const customWorkspacePages = useActiveWorkspacePages()
  
  // Determine if we're in custom workspace mode
  const isCustomWorkspaceActive = activeCustomWorkspace !== null
  
  // Filter divisions based on active workspace (system or custom)
  const filteredDivisions = useMemo(() => {
    // Custom workspace takes precedence
    if (isCustomWorkspaceActive && customWorkspacePages.length > 0) {
      // Get all routes from custom workspace pages
      const customRoutes = new Set<string>()
      customWorkspacePages.forEach(module => {
        module.pages.forEach(page => {
          customRoutes.add(page.route)
          // Also add base route for nested routes
          const baseRoute = page.route.split('/')[1]
          if (baseRoute) customRoutes.add(`/${baseRoute}`)
        })
      })
      
      // Filter divisions that have routes in the custom workspace
      return navigableDivisions.filter(division => {
        // Check if division route is in custom workspace
        if (customRoutes.has(division.route)) {
          return true
        }
        
        // Check if any section route is in custom workspace
        if (division.sections) {
          return division.sections.some(section => {
            const sectionRoute = section.isAbsolute ? section.route : `${division.route}${section.route}`
            if (customRoutes.has(sectionRoute)) {
              return true
            }
            // Check items
            if (section.items) {
              return section.items.some(item => {
                const itemRoute = item.isAbsolute ? item.route : `${division.route}${item.route}`
                return customRoutes.has(itemRoute)
              })
            }
            return false
          })
        }
        
        return false
      }).map(division => {
        // Filter sections to only include those with pages in custom workspace
        if (!division.sections) return division
        
        const filteredSections = division.sections.map(section => {
          if (!section.items) {
            const sectionRoute = section.isAbsolute ? section.route : `${division.route}${section.route}`
            if (customRoutes.has(sectionRoute)) {
              return section
            }
            return null
          }
          
          const filteredItems = section.items.filter(item => {
            const itemRoute = item.isAbsolute ? item.route : `${division.route}${item.route}`
            return customRoutes.has(itemRoute)
          })
          
          if (filteredItems.length === 0) return null
          
          return {
            ...section,
            items: filteredItems
          }
        }).filter(Boolean) as DivisionSection[]
        
        return {
          ...division,
          sections: filteredSections
        }
      })
    }
    
    // System workspace filtering
    if (!activeWorkspaceId) {
      // No workspace selected - show all divisions
      return navigableDivisions
    }
    
    // Get modules for the active workspace
    const workspaceModules = getWorkspaceModules(activeWorkspaceId)
    const workspaceRoutes = new Set<string>()
    
    // Collect all routes from workspace modules
    workspaceModules.forEach(module => {
      module.pages.forEach(page => {
        workspaceRoutes.add(page.route)
        // Also add base route for nested routes
        const baseRoute = page.route.split('/')[1]
        if (baseRoute) workspaceRoutes.add(`/${baseRoute}`)
      })
    })
    
    // Filter divisions that have routes in the workspace
    return navigableDivisions.filter(division => {
      // Check if division route is in workspace
      if (isRouteInWorkspace(division.route, activeWorkspaceId)) {
        return true
      }
      
      // Check if any section route is in workspace
      if (division.sections) {
        return division.sections.some(section => {
          const sectionRoute = section.isAbsolute ? section.route : `${division.route}${section.route}`
          if (isRouteInWorkspace(sectionRoute, activeWorkspaceId)) {
            return true
          }
          // Check items
          if (section.items) {
            return section.items.some(item => {
              const itemRoute = item.isAbsolute ? item.route : `${division.route}${item.route}`
              return isRouteInWorkspace(itemRoute, activeWorkspaceId)
            })
          }
          return false
        })
      }
      
      return false
    })
  }, [navigableDivisions, activeWorkspaceId, isCustomWorkspaceActive, customWorkspacePages])

  // Auto-expand current division
  useMemo(() => {
    const currentDivision = filteredDivisions.find(d => 
      location.pathname.startsWith(d.route)
    )
    if (currentDivision) {
      setExpandedDivision(currentDivision.id)
    }
  }, [location.pathname, filteredDivisions])

  if (collapsed) {
    return (
      <div className="py-2 space-y-1">
        {filteredDivisions.map(division => {
          const IconComponent = divisionIcons[division.icon] || Sparkles
          const isActive = location.pathname.startsWith(division.route)
          const gradientColor = divisionColors[division.id] || 'from-prakruti-dhool-500 to-prakruti-dhool-600'

          return (
            <Link
              key={division.id}
              to={division.route}
              onClick={onNavigate}
              className={cn(
                'flex items-center justify-center p-3 rounded-lg transition-all',
                isActive
                  ? `bg-gradient-to-r ${gradientColor} text-white`
                  : 'hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800 text-prakruti-dhool-600 dark:text-prakruti-dhool-400'
              )}
              title={division.name}
            >
              <IconComponent className="w-5 h-5" />
            </Link>
          )
        })}
      </div>
    )
  }

  return (
    <div className="p-2 space-y-1">
      {/* Custom Workspace indicator */}
      {isCustomWorkspaceActive && activeCustomWorkspace && (
        <div className="px-3 py-2 mb-2 rounded-lg text-white text-xs font-medium"
             style={{ 
               background: `linear-gradient(to right, var(--tw-gradient-stops))`,
               ['--tw-gradient-from' as string]: activeCustomWorkspace.color === 'green' ? '#22c55e' :
                                                  activeCustomWorkspace.color === 'blue' ? '#3b82f6' :
                                                  activeCustomWorkspace.color === 'purple' ? '#a855f7' :
                                                  activeCustomWorkspace.color === 'amber' ? '#f59e0b' :
                                                  '#64748b',
               ['--tw-gradient-to' as string]: activeCustomWorkspace.color === 'green' ? '#059669' :
                                                activeCustomWorkspace.color === 'blue' ? '#4f46e5' :
                                                activeCustomWorkspace.color === 'purple' ? '#7c3aed' :
                                                activeCustomWorkspace.color === 'amber' ? '#ea580c' :
                                                '#475569',
             }}>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wider opacity-80">Custom</span>
            <span>•</span>
            <span>{activeCustomWorkspace.name}</span>
          </div>
        </div>
      )}
      
      {/* System Workspace indicator */}
      {!isCustomWorkspaceActive && activeWorkspace && (
        <div className="px-3 py-2 mb-2 rounded-lg bg-gradient-to-r opacity-90 text-white text-xs font-medium"
             style={{ 
               background: `linear-gradient(to right, var(--tw-gradient-stops))`,
               ['--tw-gradient-from' as string]: activeWorkspace.color.includes('green') ? '#22c55e' :
                                                  activeWorkspace.color.includes('blue') ? '#3b82f6' :
                                                  activeWorkspace.color.includes('purple') ? '#a855f7' :
                                                  activeWorkspace.color.includes('amber') ? '#f59e0b' :
                                                  '#64748b',
               ['--tw-gradient-to' as string]: activeWorkspace.color.includes('green') ? '#059669' :
                                                activeWorkspace.color.includes('blue') ? '#4f46e5' :
                                                activeWorkspace.color.includes('purple') ? '#7c3aed' :
                                                activeWorkspace.color.includes('amber') ? '#ea580c' :
                                                '#475569',
             }}>
          {activeWorkspace.name}
        </div>
      )}
      
      <div className="px-3 py-2 text-xs font-semibold text-prakruti-dhool-500 dark:text-prakruti-dhool-400 uppercase tracking-wider">
        {isCustomWorkspaceActive ? 'Selected Pages' : activeWorkspace ? 'Modules' : 'All Modules'}
      </div>
      {filteredDivisions.map(division => (
        <DivisionNavItem
          key={division.id}
          division={division}
          isExpanded={expandedDivision === division.id}
          onToggle={() => setExpandedDivision(
            expandedDivision === division.id ? null : division.id
          )}
          onNavigate={onNavigate}
        />
      ))}
      
      {/* Show message if no divisions match workspace */}
      {filteredDivisions.length === 0 && (isCustomWorkspaceActive || activeWorkspace) && (
        <div className="px-3 py-4 text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-400 text-center">
          {isCustomWorkspaceActive 
            ? `No pages in ${activeCustomWorkspace?.name || 'custom workspace'}`
            : `No modules available for ${activeWorkspace?.name}`
          }
        </div>
      )}
    </div>
  )
}

export default DivisionNavigation
