/**
 * Parashakti Framework - Division Navigation
 * 
 * Navigation component that renders divisions from the registry.
 * Supports nested subgroups for complex navigation structures.
 * Filters by active workspace when workspace is selected.
 * Supports custom workspaces (MyWorkspace) with page-level filtering.
 */

import { useState, useMemo, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useDivisionRegistry } from '../registry'
import { Division, DivisionSection, DivisionStatus } from '../registry/types'
import { useWorkspaceStore, useActiveWorkspace } from '@/store/workspaceStore'
import { useActiveCustomWorkspace } from '@/store/customWorkspaceStore'
import { useActiveWorkspacePages } from '@/hooks/useCustomWorkspace'
import { isRouteInWorkspace } from '@/framework/registry/workspaces'
import { useNavigationStore } from '@/store/navigationStore'
import {
  ChevronDown, 
  ChevronRight, 
  Sparkles,
} from 'lucide-react'
import { navigationIcons } from './navigationIcons'
import {
  findActiveShellDivision,
  getActiveShellSubgroups,
  isShellPathActive,
  isShellSectionActive,
  resolveShellNavPath,
} from './shellNavigationResolver'
import {
  applyDivisionDomainProjection,
  projectDivisionsForCustomWorkspace,
  projectDivisionsForSystemWorkspace,
} from './divisionNavigationProjection'
import {
  CustomWorkspaceIndicator,
  DivisionNavigationEmptyState,
  DivisionNavigationLabel,
  SystemWorkspaceIndicator,
} from './DivisionNavigationParts'


// Use shared icon map
const divisionIcons = navigationIcons


// Status badge colors - Prakruti Design System
const statusColors: Record<DivisionStatus, string> = {
  active: 'bg-prakruti-patta-pale text-prakruti-patta dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light',
  preview: 'bg-prakruti-neela-pale text-prakruti-neela dark:bg-prakruti-neela/20 dark:text-prakruti-neela-light',
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
  const sectionPath = resolveShellNavPath(divisionRoute, section.route, section.isAbsolute)
  const hasItems = section.items && section.items.length > 0
  
  // Check if any item in this subgroup is active
  const isActive = isShellSectionActive(location.pathname, divisionRoute, section)

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
            const itemPath = resolveShellNavPath(divisionRoute, item.route, item.isAbsolute)
            const isItemActive = isShellPathActive(location.pathname, itemPath)
            
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

export interface DivisionNavItemProps {
  division: Division
  isExpanded: boolean
  onToggle: () => void
  onNavigate?: () => void
}

export function DivisionNavItem({ division, isExpanded, onToggle, onNavigate }: DivisionNavItemProps) {
  const location = useLocation()

  // Initialize state with active subgroups
  const [expandedSubgroups, setExpandedSubgroups] = useState<Set<string>>(() =>
    getActiveShellSubgroups(division, location.pathname)
  )

  const IconComponent = divisionIcons[division.icon] || Sparkles
  const isActive = findActiveShellDivision([division], location.pathname)?.id === division.id
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

  // Update expanded subgroups when route or division changes
  useEffect(() => {
    const active = getActiveShellSubgroups(division, location.pathname)
    if (active.size > 0) {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      setExpandedSubgroups(prev => {
        const next = new Set(prev)
        let changed = false
        active.forEach(id => {
          if (!next.has(id)) {
            next.add(id)
            changed = true
          }
        })
        return changed ? next : prev
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
  const activeDomain = useNavigationStore(state => state.activeDomain)
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
      return projectDivisionsForCustomWorkspace(navigableDivisions, customWorkspacePages)
    }
    
    // System workspace filtering
    const workspaceProjectedDivisions = projectDivisionsForSystemWorkspace(
      navigableDivisions,
      activeWorkspaceId,
      isRouteInWorkspace,
    )

    if (activeWorkspaceId || isCustomWorkspaceActive) {
      return workspaceProjectedDivisions
    }

    return applyDivisionDomainProjection(workspaceProjectedDivisions, activeDomain)
  }, [navigableDivisions, activeWorkspaceId, isCustomWorkspaceActive, customWorkspacePages, activeDomain])

  // Auto-expand current division
  useEffect(() => {
    const currentDivision = findActiveShellDivision(filteredDivisions, location.pathname)
    if (currentDivision && currentDivision.id !== expandedDivision) {
      setExpandedDivision(currentDivision.id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname, filteredDivisions])

  if (collapsed) {
    return (
      <div className="py-2 space-y-1">
        {filteredDivisions.map(division => {
          const IconComponent = divisionIcons[division.icon] || Sparkles
          const isActive = findActiveShellDivision([division], location.pathname)?.id === division.id
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
      {isCustomWorkspaceActive && activeCustomWorkspace && <CustomWorkspaceIndicator workspace={activeCustomWorkspace} />}
      
      {/* System Workspace indicator */}
      {!isCustomWorkspaceActive && activeWorkspace && <SystemWorkspaceIndicator workspace={activeWorkspace} />}
      
      <DivisionNavigationLabel
        isCustomWorkspaceActive={isCustomWorkspaceActive}
        hasActiveWorkspace={Boolean(activeWorkspace)}
      />
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
        <DivisionNavigationEmptyState
          isCustomWorkspaceActive={isCustomWorkspaceActive}
          customWorkspaceName={activeCustomWorkspace?.name}
          activeWorkspaceName={activeWorkspace?.name}
        />
      )}
    </div>
  )
}

export default DivisionNavigation
