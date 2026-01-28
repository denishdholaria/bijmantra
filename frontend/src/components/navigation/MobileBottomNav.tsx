/**
 * Mobile Bottom Navigation Bar
 * 
 * PWA-friendly bottom navigation for mobile devices.
 * Shows workspace-specific modules with quick access to core features.
 * Designed for field use with large touch targets.
 */

import { Link, useLocation, useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  Home,
  Sprout,
  Warehouse,
  Globe,
  MoreHorizontal,
  Building2,
  Radio,
  Rocket,
  BookOpen,
  Settings,
  Factory,
  Microscope,
  Wheat,
  FlaskConical,
  Package,
  BarChart3,
  CloudRain,
  Droplets,
  Mountain,
  Leaf,
  type LucideIcon,
} from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { useState } from 'react'
import { useWorkspaceStore, useActiveWorkspace } from '@/store/workspaceStore'
import type { WorkspaceId } from '@/types/workspace'

interface NavItem {
  id: string
  name: string
  icon: LucideIcon
  route: string
  color: string
}

// Workspace-specific primary nav items
const workspaceNavItems: Record<WorkspaceId, NavItem[]> = {
  breeding: [
    { id: 'home', name: 'Home', icon: Home, route: '/dashboard', color: 'text-blue-500' },
    { id: 'programs', name: 'Programs', icon: Wheat, route: '/programs', color: 'text-green-500' },
    { id: 'germplasm', name: 'Germplasm', icon: Sprout, route: '/germplasm', color: 'text-emerald-500' },
    { id: 'trials', name: 'Trials', icon: FlaskConical, route: '/trials', color: 'text-amber-500' },
  ],
  'seed-ops': [
    { id: 'home', name: 'Home', icon: Home, route: '/dashboard', color: 'text-blue-500' },
    { id: 'inventory', name: 'Inventory', icon: Package, route: '/seed-operations/lots', color: 'text-indigo-500' },
    { id: 'testing', name: 'Testing', icon: FlaskConical, route: '/seed-operations/testing', color: 'text-purple-500' },
    { id: 'dispatch', name: 'Dispatch', icon: Factory, route: '/seed-operations/dispatch', color: 'text-blue-500' },
  ],
  research: [
    { id: 'home', name: 'Home', icon: Home, route: '/dashboard', color: 'text-blue-500' },
    { id: 'analytics', name: 'Analytics', icon: Microscope, route: '/apex-analytics', color: 'text-purple-500' },
    { id: 'ai-vision', name: 'AI Vision', icon: Rocket, route: '/ai-vision', color: 'text-violet-500' },
    { id: 'space', name: 'Space', icon: Rocket, route: '/space-research', color: 'text-indigo-500' },
  ],
  genebank: [
    { id: 'home', name: 'Home', icon: Home, route: '/dashboard', color: 'text-blue-500' },
    { id: 'seed-bank', name: 'Seed Bank', icon: Warehouse, route: '/seed-bank', color: 'text-amber-500' },
    { id: 'environment', name: 'Environment', icon: Globe, route: '/earth-systems', color: 'text-cyan-500' },
    { id: 'sensors', name: 'Sensors', icon: Radio, route: '/sensor-networks', color: 'text-teal-500' },
  ],
  admin: [
    { id: 'home', name: 'Home', icon: Home, route: '/dashboard', color: 'text-blue-500' },
    { id: 'users', name: 'Users', icon: Building2, route: '/users', color: 'text-slate-500' },
    { id: 'system', name: 'System', icon: Settings, route: '/system-health', color: 'text-gray-500' },
    { id: 'settings', name: 'Settings', icon: Settings, route: '/settings', color: 'text-zinc-500' },
  ],
  atmosphere: [
    { id: 'weather', name: 'Weather', icon: CloudRain, route: '/earth-systems/atmosphere', color: 'text-blue-500' }
  ],
  hydrology: [
    { id: 'water', name: 'Water', icon: Droplets, route: '/earth-systems/hydrology', color: 'text-cyan-500' }
  ],
  lithosphere: [
    { id: 'soil', name: 'Soil', icon: Mountain, route: '/earth-systems/lithosphere', color: 'text-amber-700' }
  ],
  biosphere: [
    { id: 'crop', name: 'Crop', icon: Leaf, route: '/earth-systems/biosphere', color: 'text-green-600' }
  ]
}

// Default nav items (no workspace selected)
const defaultNavItems: NavItem[] = [
  { id: 'home', name: 'Home', icon: Home, route: '/dashboard', color: 'text-blue-500' },
  { id: 'plant-sciences', name: 'Breeding', icon: Sprout, route: '/programs', color: 'text-green-500' },
  { id: 'seed-bank', name: 'Seed Bank', icon: Warehouse, route: '/seed-bank', color: 'text-amber-500' },
  { id: 'environment', name: 'Environment', icon: Globe, route: '/earth-systems', color: 'text-cyan-500' },
]

// Secondary nav items (in "More" sheet)
const secondaryNavItems: NavItem[] = [
  { id: 'seed-commerce', name: 'Seed Commerce', icon: Building2, route: '/seed-operations', color: 'text-indigo-500' },
  { id: 'sensor-networks', name: 'Sensors', icon: Radio, route: '/sensor-networks', color: 'text-teal-500' },
  { id: 'space-research', name: 'Space', icon: Rocket, route: '/space-research', color: 'text-violet-500' },
  { id: 'knowledge', name: 'Knowledge', icon: BookOpen, route: '/help', color: 'text-pink-500' },
  { id: 'settings', name: 'Settings', icon: Settings, route: '/settings', color: 'text-zinc-500' },
]

export function MobileBottomNav() {
  const location = useLocation()
  const navigate = useNavigate()
  const [moreOpen, setMoreOpen] = useState(false)
  
  // Workspace state
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId)
  const activeWorkspace = useActiveWorkspace()
  
  // Get primary nav items based on workspace
  const primaryNavItems = activeWorkspaceId 
    ? workspaceNavItems[activeWorkspaceId] 
    : defaultNavItems

  const isActive = (route: string) => {
    if (route === '/dashboard') {
      return location.pathname === '/' || location.pathname === '/dashboard'
    }
    return location.pathname.startsWith(route)
  }

  const isMoreActive = secondaryNavItems.some(item => isActive(item.route))

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-800 lg:hidden safe-area-bottom">
      <div className="flex items-center justify-around h-16 px-2">
        {primaryNavItems.map(item => {
          const Icon = item.icon
          const active = isActive(item.route)
          
          return (
            <Link
              key={item.id}
              to={item.route}
              className={cn(
                'flex flex-col items-center justify-center flex-1 h-full min-w-0 px-1 transition-colors',
                active ? item.color : 'text-gray-500 dark:text-gray-400'
              )}
            >
              <Icon className={cn(
                'w-6 h-6 mb-0.5 transition-transform',
                active && 'scale-110'
              )} />
              <span className={cn(
                'text-[10px] font-medium truncate max-w-full',
                active && 'font-semibold'
              )}>
                {item.name}
              </span>
              {active && (
                <div className={cn(
                  'absolute bottom-1 w-1 h-1 rounded-full',
                  item.color.replace('text-', 'bg-')
                )} />
              )}
            </Link>
          )
        })}

        {/* More Button */}
        <Sheet open={moreOpen} onOpenChange={setMoreOpen}>
          <SheetTrigger asChild>
            <button
              className={cn(
                'flex flex-col items-center justify-center flex-1 h-full min-w-0 px-1 transition-colors',
                isMoreActive ? 'text-green-500' : 'text-gray-500 dark:text-gray-400'
              )}
            >
              <MoreHorizontal className={cn(
                'w-6 h-6 mb-0.5',
                isMoreActive && 'scale-110'
              )} />
              <span className={cn(
                'text-[10px] font-medium',
                isMoreActive && 'font-semibold'
              )}>
                More
              </span>
            </button>
          </SheetTrigger>
          <SheetContent side="bottom" className="h-auto max-h-[70vh] rounded-t-2xl">
            <SheetHeader className="pb-4">
              <SheetTitle>
                {activeWorkspace ? `${activeWorkspace.name} - More` : 'More Modules'}
              </SheetTitle>
            </SheetHeader>
            
            {/* Workspace switcher button */}
            <button
              onClick={() => {
                setMoreOpen(false)
                navigate('/gateway')
              }}
              className="w-full mb-4 p-3 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium text-sm flex items-center justify-center gap-2"
            >
              <Globe className="w-5 h-5" />
              {activeWorkspace ? 'Switch Workspace' : 'Choose Workspace'}
            </button>
            
            <div className="grid grid-cols-3 gap-4 pb-8">
              {secondaryNavItems.map(item => {
                const Icon = item.icon
                const active = isActive(item.route)
                
                return (
                  <Link
                    key={item.id}
                    to={item.route}
                    onClick={() => setMoreOpen(false)}
                    className={cn(
                      'flex flex-col items-center justify-center p-4 rounded-xl transition-all',
                      active
                        ? 'bg-green-100 dark:bg-green-900/30'
                        : 'bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700'
                    )}
                  >
                    <Icon className={cn(
                      'w-8 h-8 mb-2',
                      active ? item.color : 'text-gray-600 dark:text-gray-400'
                    )} />
                    <span className={cn(
                      'text-xs font-medium text-center',
                      active ? 'text-green-700 dark:text-green-400' : 'text-gray-700 dark:text-gray-300'
                    )}>
                      {item.name}
                    </span>
                  </Link>
                )
              })}
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </nav>
  )
}

export default MobileBottomNav
