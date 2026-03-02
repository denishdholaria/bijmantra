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

import { useState, useMemo, useCallback, useEffect } from 'react'
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
} from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { getNavIcon } from './navigationIcons'

// ============================================================================
// Icon helper (delegates to shared navigationIcons)
// ============================================================================

const getIcon = getNavIcon

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

  const [isOpen, setIsOpen] = useState(!!(isActive && hasItems))

  // Auto-expand when active
  useEffect(() => {
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
  const { sidebarCollapsed, toggleSidebar, isStrataOpen } = useSystemStore()

  // Determine which division matches the current route
  const activeDivision = useMemo<Division | null>(() => {
    // Sort by route length descending so more specific routes match first.
    const sorted = [...navigableDivisions].sort((a, b) => b.route.length - a.route.length)

    // 1) Direct division route prefix match.
    const prefixMatch = sorted.find((d) => location.pathname.startsWith(d.route))
    if (prefixMatch) {
      return prefixMatch
    }

    // 2) Absolute section/item route match (for routes like /plannedcrosses).
    for (const division of sorted) {
      if (!division.sections?.length) continue

      for (const section of division.sections) {
        const sectionPath = section.isAbsolute ? section.route : `${division.route}${section.route}`
        if (location.pathname === sectionPath || location.pathname.startsWith(sectionPath + '/')) {
          return division
        }

        if (section.items?.length) {
          for (const item of section.items) {
            const itemPath = item.isAbsolute ? item.route : `${division.route}${item.route}`
            if (location.pathname === itemPath || location.pathname.startsWith(itemPath + '/')) {
              return division
            }
          }
        }
      }
    }

    return null
  }, [location.pathname, navigableDivisions])

  const isDesktopRoute = ['/', '/gateway', '/dashboard'].includes(location.pathname)

  const resolvePath = useCallback((divisionRoute: string, route: string, isAbsolute?: boolean) => {
    return isAbsolute ? route : `${divisionRoute}${route}`
  }, [])

  const activeSection = useMemo<DivisionSection | null>(() => {
    if (!activeDivision?.sections?.length) return null

    const matchesPath = (path: string) =>
      location.pathname === path || location.pathname.startsWith(path + '/')

    for (const section of activeDivision.sections) {
      const sectionPath = resolvePath(activeDivision.route, section.route, section.isAbsolute)

      if (matchesPath(sectionPath)) {
        return section
      }

      if (section.items?.length) {
        for (const item of section.items) {
          const itemPath = resolvePath(activeDivision.route, item.route, item.isAbsolute)
          if (matchesPath(itemPath)) {
            return section
          }
        }
      }
    }

    return null
  }, [activeDivision, location.pathname, resolvePath])

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
          activeSection ? (
            // App route: keep sidebar focused to only the active section's sub-pages.
            <div className="space-y-2">
              <div className="px-3 py-1.5 rounded-lg bg-slate-100/80 dark:bg-slate-800/50">
                <div className="text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400">Section</div>
                <div className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate">{activeSection.name}</div>
              </div>

              {activeSection.items && activeSection.items.length > 0 ? (
                <div className="space-y-0.5">
                  {activeSection.items.map(item => {
                    const itemPath = resolvePath(activeDivision.route, item.route, item.isAbsolute)
                    const isItemActive =
                      location.pathname === itemPath || location.pathname.startsWith(itemPath + '/')

                    return (
                      <Link
                        key={item.id}
                        to={itemPath}
                        className={cn(
                          'flex items-center gap-2 px-3 py-1.5 text-[13px] rounded-lg transition-colors',
                          isItemActive
                            ? 'bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300 font-medium'
                            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800/50'
                        )}
                      >
                        <span className="truncate">{item.name}</span>
                      </Link>
                    )
                  })}
                </div>
              ) : (
                <Link
                  to={resolvePath(activeDivision.route, activeSection.route, activeSection.isAbsolute)}
                  className="flex items-center gap-2 px-3 py-1.5 text-[13px] rounded-lg bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300 font-medium"
                >
                  <span className="truncate">{activeSection.name}</span>
                </Link>
              )}
            </div>
          ) : (
            // Division route or unmatched child route: show all sections for discovery.
            <div className="space-y-0.5">
              {activeDivision.sections.map(section => (
                <SidebarSection
                  key={section.id}
                  section={section}
                  divisionRoute={activeDivision.route}
                />
              ))}
            </div>
          )
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
    </aside>
  )
}

export default ShellSidebar
