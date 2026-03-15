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
import {
  findActiveShellDivision,
  findActiveShellSection,
  isDesktopShellRoute,
  isShellNavItemActive,
  isShellSectionActive,
  resolveShellNavPath,
} from './shellNavigationResolver'

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

  const sectionPath = resolveShellNavPath(divisionRoute, section.route, section.isAbsolute)
  const hasItems = section.items && section.items.length > 0

  // Check if any item is active → auto-expand
  const isActive = useMemo(() => {
    return isShellSectionActive(location.pathname, divisionRoute, section)
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
          'flex items-center gap-2 rounded-xl px-3 py-2 text-[13px] transition-all duration-200',
          isActive
            ? 'bg-[linear-gradient(135deg,hsl(var(--primary)/0.12),hsl(var(--app-shell-radiance)/0.12))] text-prakruti-patta-dark dark:text-prakruti-patta-light font-medium'
            : 'text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell'
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
          'w-full flex items-center gap-2 rounded-xl px-3 py-2 text-left text-[13px] transition-all duration-200',
          isActive
            ? 'bg-[hsl(var(--accent)/0.5)] text-prakruti-patta-dark dark:text-prakruti-patta-light font-medium'
            : 'text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell'
        )}
      >
        {isOpen ? (
          <ChevronDown className="w-3 h-3 flex-shrink-0 opacity-50" />
        ) : (
          <ChevronRight className="w-3 h-3 flex-shrink-0 opacity-50" />
        )}
        <span className="truncate flex-1">{section.name}</span>
        <span className="text-shell-muted text-[10px]">{section.items!.length}</span>
      </button>

      {isOpen && (
        <div className="border-shell mt-1 ml-4 space-y-1 border-l pl-3">
          {section.items!.map(item => {
            const itemPath = resolveShellNavPath(divisionRoute, item.route, item.isAbsolute)
            const isItemActive = isShellNavItemActive(location.pathname, divisionRoute, item)

            return (
              <Link
                key={item.id}
                to={itemPath}
                onClick={onNavigate}
                className={cn(
                  'flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs transition-all duration-200',
                  isItemActive
                    ? 'bg-[linear-gradient(135deg,hsl(var(--primary)/0.1),hsl(var(--app-shell-radiance)/0.12))] text-prakruti-patta-dark dark:text-prakruti-patta-light font-medium'
                    : 'text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell'
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
    return findActiveShellDivision(navigableDivisions, location.pathname)
  }, [location.pathname, navigableDivisions])

  const isDesktopRoute = isDesktopShellRoute(location.pathname)

  const resolvePath = useCallback((divisionRoute: string, route: string, isAbsolute?: boolean) => {
    return resolveShellNavPath(divisionRoute, route, isAbsolute)
  }, [])

  const activeSection = useMemo<DivisionSection | null>(() => {
    return findActiveShellSection(activeDivision, location.pathname)
  }, [activeDivision, location.pathname])

  const handleDivisionClick = useCallback((division: Division) => {
    navigate(division.route)
  }, [navigate])

  // ─── Collapsed Mode: Icon rail ───
  if (sidebarCollapsed) {
    return (
      <TooltipProvider delayDuration={150}>
        <aside className="bg-shell-chrome border-shell flex flex-col w-14 h-full border-r flex-shrink-0">
          {/* Toggle button */}
          <div className="border-shell flex items-center justify-center h-10 border-b">
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={toggleSidebar}
                  className="text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell rounded-md p-1.5 transition-colors"
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
                            : 'text-shell-muted hover:bg-[hsl(var(--accent))]'
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
    <aside className="bg-shell-chrome border-shell flex flex-col w-60 h-full border-r flex-shrink-0">
      {/* Header with collapse toggle */}
      <div className="border-shell flex items-center justify-between h-10 px-3 border-b flex-shrink-0">
        {activeDivision ? (
          <div className="flex items-center gap-2 min-w-0">
            {(() => {
              const Icon = getIcon(activeDivision.icon)
              return <Icon className="text-prakruti-patta dark:text-prakruti-patta-light w-4 h-4 flex-shrink-0" />
            })()}
            <span className="text-shell text-sm font-semibold truncate">
              {activeDivision.name}
            </span>
          </div>
        ) : (
          <span className="text-shell-muted text-xs font-semibold uppercase tracking-[0.2em]">
            All Modules
          </span>
        )}
        <button
          type="button"
          onClick={toggleSidebar}
          className="text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell rounded-xl p-1.5 transition-colors flex-shrink-0"
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
              <div className="bg-[hsl(var(--app-shell-panel)/0.78)] border-shell rounded-2xl border px-3 py-2 shadow-shell">
                <div className="text-shell-muted text-[11px] uppercase tracking-[0.22em]">Section</div>
                <div className="text-shell text-sm font-semibold truncate">{activeSection.name}</div>
              </div>

              {activeSection.items && activeSection.items.length > 0 ? (
                <div className="space-y-0.5">
                  {activeSection.items.map(item => {
                    const itemPath = resolvePath(activeDivision.route, item.route, item.isAbsolute)
                    const isItemActive = isShellNavItemActive(location.pathname, activeDivision.route, item)

                    return (
                      <Link
                        key={item.id}
                        to={itemPath}
                        className={cn(
                          'flex items-center gap-2 rounded-xl px-3 py-2 text-[13px] transition-all duration-200',
                          isItemActive
                            ? 'bg-[linear-gradient(135deg,hsl(var(--primary)/0.12),hsl(var(--app-shell-radiance)/0.12))] text-prakruti-patta-dark dark:text-prakruti-patta-light font-medium'
                            : 'text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell'
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
                  className="flex items-center gap-2 rounded-xl bg-[linear-gradient(135deg,hsl(var(--primary)/0.12),hsl(var(--app-shell-radiance)/0.12))] px-3 py-2 text-[13px] font-medium text-prakruti-patta-dark dark:text-prakruti-patta-light"
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
                      'w-full flex items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition-all duration-200',
                      isActive
                        ? `bg-gradient-to-r ${gradient} text-white shadow-sm`
                        : 'text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell'
                    )}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{division.name}</div>
                      <div className="text-[11px] opacity-60 truncate">{division.description}</div>
                    </div>
                    {division.status === 'beta' && (
                      <span className="ml-auto rounded-full bg-[hsl(var(--accent))] px-1.5 py-0.5 text-[9px] text-shell flex-shrink-0">
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
