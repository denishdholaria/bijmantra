/**
 * Contextual Tabs Navigation Component
 * 
 * Horizontal tabs below header showing sections within current division.
 * Features:
 * - Scrollable if many tabs
 * - Active tab indicator
 * - "More" dropdown for overflow items
 */

import { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { divisions } from '@/framework/registry/divisions'
import type { Division, DivisionSection } from '@/framework/registry/types'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  Sprout,
  Wheat,
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
  Dna,
  FlaskConical,
  Beaker,
  TestTube2,
  Microscope,
  Target,
  BarChart3,
  Map,
  Cpu,
  type LucideIcon,
} from 'lucide-react'

// Icon mapping
const sectionIcons: Record<string, LucideIcon> = {
  'Wheat': Wheat,
  'GitMerge': Sprout,
  'Target': Target,
  'Microscope': Microscope,
  'TestTube2': TestTube2,
  'Dna': Dna,
  'Map': Map,
  'BarChart3': BarChart3,
  'Cpu': Cpu,
  'Beaker': Beaker,
  'FlaskConical': FlaskConical,
  'LayoutDashboard': LayoutDashboard,
  'Sprout': Sprout,
  'Shield': Warehouse,
  'ArrowLeftRight': Sprout,
  'CloudSun': Globe,
  'Leaf': Sprout,
  'Package': Factory,
  'Truck': Factory,
  'QrCode': Factory,
  'FileCheck': Building2,
}

// Division colors for tab underline
const divisionColors: Record<string, string> = {
  'plant-sciences': 'border-green-500 text-green-600',
  'seed-bank': 'border-amber-500 text-amber-600',
  'earth-systems': 'border-cyan-500 text-cyan-600',
  'sun-earth-systems': 'border-orange-500 text-orange-600',
  'sensor-networks': 'border-teal-500 text-teal-600',
  'seed-operations': 'border-indigo-500 text-indigo-600',
  'commercial': 'border-purple-500 text-purple-600',
  'space-research': 'border-violet-500 text-violet-600',
  'integrations': 'border-slate-500 text-slate-600',
  'knowledge': 'border-pink-500 text-pink-600',
  'tools': 'border-gray-500 text-gray-600',
  'settings': 'border-zinc-500 text-zinc-600',
  'home': 'border-blue-500 text-blue-600',
}

interface ContextualTabsProps {
  className?: string
  maxVisibleTabs?: number
}

export function ContextualTabs({ className, maxVisibleTabs = 6 }: ContextualTabsProps) {
  const location = useLocation()
  const scrollRef = useRef<HTMLDivElement>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  // Find current division based on path
  const getCurrentDivision = (): Division | null => {
    const path = location.pathname
    
    // Special case for root/dashboard
    if (path === '/' || path === '/dashboard') {
      return divisions.find(d => d.id === 'home') || null
    }
    
    // Find matching division
    for (const div of divisions) {
      if (path.startsWith(div.route)) {
        return div
      }
    }
    
    return null
  }

  const currentDivision = getCurrentDivision()
  const sections = currentDivision?.sections || []
  const activeColor = currentDivision ? divisionColors[currentDivision.id] : 'border-gray-500 text-gray-600'

  // Check scroll state
  const checkScroll = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current
      setCanScrollLeft(scrollLeft > 0)
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1)
    }
  }

  useEffect(() => {
    checkScroll()
    window.addEventListener('resize', checkScroll)
    return () => window.removeEventListener('resize', checkScroll)
  }, [sections])

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const scrollAmount = 200
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      })
      setTimeout(checkScroll, 300)
    }
  }

  // Get visible and overflow sections
  const visibleSections = sections.slice(0, maxVisibleTabs)
  const overflowSections = sections.slice(maxVisibleTabs)

  // Check if a section or its items are active
  const isSectionActive = (section: DivisionSection): boolean => {
    const sectionPath = section.isAbsolute ? section.route : `${currentDivision?.route}${section.route}`
    
    if (location.pathname === sectionPath) return true
    if (location.pathname.startsWith(sectionPath + '/')) return true
    
    if (section.items) {
      return section.items.some(item => {
        const itemPath = item.isAbsolute ? item.route : `${currentDivision?.route}${item.route}`
        return location.pathname === itemPath || location.pathname.startsWith(itemPath + '/')
      })
    }
    
    return false
  }

  if (!currentDivision || sections.length === 0) {
    return null
  }

  return (
    <div className={cn(
      'bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800',
      className
    )}>
      <div className="flex items-center px-4">
        {/* Division Name */}
        <div className="flex items-center gap-2 pr-4 border-r border-gray-200 dark:border-slate-700 mr-4">
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            {currentDivision.name}
          </span>
        </div>

        {/* Scroll Left Button */}
        {canScrollLeft && (
          <button
            onClick={() => scroll('left')}
            className="p-1 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-md mr-1"
          >
            <ChevronLeft className="h-4 w-4 text-gray-500" />
          </button>
        )}

        {/* Tabs Container */}
        <div
          ref={scrollRef}
          className="flex-1 flex items-center gap-1 overflow-x-auto scrollbar-hide"
          onScroll={checkScroll}
        >
          {visibleSections.map(section => {
            const isActive = isSectionActive(section)
            const sectionPath = section.isAbsolute ? section.route : `${currentDivision.route}${section.route}`
            const hasItems = section.items && section.items.length > 0

            if (hasItems) {
              return (
                <DropdownMenu key={section.id}>
                  <DropdownMenuTrigger asChild>
                    <button
                      className={cn(
                        'flex items-center gap-1.5 px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px',
                        isActive
                          ? activeColor
                          : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:border-gray-300'
                      )}
                    >
                      {section.name}
                      <ChevronDown className="h-3 w-3" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-48">
                    <DropdownMenuLabel>{section.name}</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {section.items!.map(item => {
                      const itemPath = item.isAbsolute ? item.route : `${currentDivision.route}${item.route}`
                      const isItemActive = location.pathname === itemPath || location.pathname.startsWith(itemPath + '/')
                      return (
                        <DropdownMenuItem key={item.id} asChild>
                          <Link
                            to={itemPath}
                            className={cn(
                              'w-full cursor-pointer',
                              isItemActive && 'bg-accent'
                            )}
                          >
                            {item.name}
                          </Link>
                        </DropdownMenuItem>
                      )
                    })}
                  </DropdownMenuContent>
                </DropdownMenu>
              )
            }

            return (
              <Link
                key={section.id}
                to={sectionPath}
                className={cn(
                  'px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px',
                  isActive
                    ? activeColor
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:border-gray-300'
                )}
              >
                {section.name}
              </Link>
            )
          })}
        </div>

        {/* Scroll Right Button */}
        {canScrollRight && (
          <button
            onClick={() => scroll('right')}
            className="p-1 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-md ml-1"
          >
            <ChevronRight className="h-4 w-4 text-gray-500" />
          </button>
        )}

        {/* More Dropdown */}
        {overflowSections.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 ml-1">
                <MoreHorizontal className="h-4 w-4" />
                <span>More</span>
                <ChevronDown className="h-3 w-3" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>More Sections</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {overflowSections.map(section => {
                const sectionPath = section.isAbsolute ? section.route : `${currentDivision.route}${section.route}`
                const isActive = isSectionActive(section)
                const hasItems = section.items && section.items.length > 0

                if (hasItems) {
                  return (
                    <DropdownMenu key={section.id}>
                      <DropdownMenuTrigger asChild>
                        <button className={cn(
                          'w-full flex items-center justify-between px-2 py-1.5 text-sm rounded-sm hover:bg-accent cursor-pointer',
                          isActive && 'bg-accent'
                        )}>
                          {section.name}
                          <ChevronRight className="h-3 w-3" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent side="right" className="w-48">
                        {section.items!.map(item => {
                          const itemPath = item.isAbsolute ? item.route : `${currentDivision.route}${item.route}`
                          return (
                            <DropdownMenuItem key={item.id} asChild>
                              <Link to={itemPath} className="w-full cursor-pointer">
                                {item.name}
                              </Link>
                            </DropdownMenuItem>
                          )
                        })}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )
                }

                return (
                  <DropdownMenuItem key={section.id} asChild>
                    <Link
                      to={sectionPath}
                      className={cn('w-full cursor-pointer', isActive && 'bg-accent')}
                    >
                      {section.name}
                    </Link>
                  </DropdownMenuItem>
                )
              })}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </div>
  )
}

export default ContextualTabs
