/**
 * Parashakti Framework - Division Navigation
 * 
 * Navigation component that renders divisions from the registry.
 * Supports nested subgroups for complex navigation structures.
 */

import { useState, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useDivisionRegistry } from '../registry'
import { Division, DivisionSection, DivisionStatus } from '../registry/types'
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

// Status badge colors
const statusColors: Record<DivisionStatus, string> = {
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  beta: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  planned: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  visionary: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
}

// Division gradient colors
const divisionColors: Record<string, string> = {
  'plant-sciences': 'from-green-500 to-emerald-500',
  'seed-bank': 'from-amber-500 to-yellow-500',
  'earth-systems': 'from-blue-500 to-cyan-500',
  'sun-earth-systems': 'from-orange-500 to-red-500',
  'sensor-networks': 'from-teal-500 to-green-500',
  'seed-operations': 'from-blue-600 to-indigo-600',
  'commercial': 'from-indigo-500 to-purple-500',
  'space-research': 'from-violet-500 to-purple-500',
  'integrations': 'from-gray-500 to-slate-500',
  'knowledge': 'from-pink-500 to-rose-500',
  'tools': 'from-slate-500 to-gray-600',
  'settings': 'from-zinc-500 to-neutral-600',
  'home': 'from-blue-500 to-cyan-500',
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
            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 font-medium'
            : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
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
            ? 'text-green-700 dark:text-green-400 font-medium'
            : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
        )}
      >
        {isExpanded ? (
          <ChevronDown className="w-3 h-3 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-3 h-3 flex-shrink-0" />
        )}
        <span className="truncate">{section.name}</span>
        <span className="ml-auto text-xs text-gray-400">{section.items!.length}</span>
      </button>
      
      {isExpanded && (
        <div className="ml-4 pl-2 border-l border-gray-200 dark:border-gray-700 space-y-0.5 mt-0.5">
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
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 font-medium'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'
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
  const gradientColor = divisionColors[division.id] || 'from-gray-500 to-slate-500'

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
            : 'hover:bg-gray-100 dark:hover:bg-gray-800'
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
        <div className="mt-1 ml-3 pl-3 border-l-2 border-gray-200 dark:border-gray-700 space-y-0.5">
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
        <div className="mt-1 ml-3 pl-3 border-l-2 border-gray-200 dark:border-gray-700">
          <Link
            to={division.route}
            onClick={onNavigate}
            className={cn(
              'flex items-center gap-2 px-2 py-1.5 text-sm rounded-md transition-colors',
              isActive
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 font-medium'
                : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
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

  // Auto-expand current division
  useMemo(() => {
    const currentDivision = navigableDivisions.find(d => 
      location.pathname.startsWith(d.route)
    )
    if (currentDivision) {
      setExpandedDivision(currentDivision.id)
    }
  }, [location.pathname, navigableDivisions])

  if (collapsed) {
    return (
      <div className="py-2 space-y-1">
        {navigableDivisions.map(division => {
          const IconComponent = divisionIcons[division.icon] || Sparkles
          const isActive = location.pathname.startsWith(division.route)
          const gradientColor = divisionColors[division.id] || 'from-gray-500 to-slate-500'

          return (
            <Link
              key={division.id}
              to={division.route}
              onClick={onNavigate}
              className={cn(
                'flex items-center justify-center p-3 rounded-lg transition-all',
                isActive
                  ? `bg-gradient-to-r ${gradientColor} text-white`
                  : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'
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
      <div className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        Modules
      </div>
      {navigableDivisions.map(division => (
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
    </div>
  )
}

export default DivisionNavigation
