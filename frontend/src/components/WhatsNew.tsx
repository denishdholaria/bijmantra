/**
 * What's New Component
 * 
 * Shows recent updates and new features to users.
 * Displayed as a modal/sheet that can be triggered from various places.
 */

import { useState, useEffect } from 'react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Sparkles,
  Smartphone,
  Navigation,
  Bug,
  Zap,
  Box,
  type LucideIcon,
} from 'lucide-react'

interface Update {
  id: string
  version: string
  date: string
  title: string
  description: string
  type: 'feature' | 'improvement' | 'fix'
  icon: LucideIcon
}

const updates: Update[] = [
  {
    id: 'mobile-nav',
    version: '1.5.0',
    date: 'Dec 17, 2025',
    title: 'Mobile Bottom Navigation',
    description: 'New PWA-friendly bottom navigation bar with quick access to core modules. Includes a floating action button for field operations like scanning, photos, and data collection.',
    type: 'feature',
    icon: Smartphone,
  },
  {
    id: 'nav-consolidation',
    version: '1.5.0',
    date: 'Dec 17, 2025',
    title: 'Simplified Navigation',
    description: 'Merged related modules for cleaner navigation: Earth Systems + Sun-Earth → Environment, Seed Operations + Commercial → Seed Commerce. Now 8 modules instead of 11.',
    type: 'improvement',
    icon: Navigation,
  },
  {
    id: 'white-screen-fix',
    version: '1.4.1',
    date: 'Dec 17, 2025',
    title: 'App Stability Fix',
    description: 'Fixed white screen issue caused by Three.js initialization. 3D visualizations now load on-demand for better performance.',
    type: 'fix',
    icon: Bug,
  },
  {
    id: 'three-js-viz',
    version: '1.4.0',
    date: 'Dec 17, 2025',
    title: '3D Pedigree Visualization',
    description: 'Interactive 3D pedigree tree and breeding simulator. Visualize genetic relationships and simulate selection in 3D space.',
    type: 'feature',
    icon: Box,
  },
  {
    id: 'layout-features',
    version: '1.4.0',
    date: 'Dec 17, 2025',
    title: 'Enhanced Layout',
    description: 'Restored Command Palette (⌘K), notification bell, sync status indicator, and user menu with error boundaries for stability.',
    type: 'improvement',
    icon: Zap,
  },
]

const typeColors = {
  feature: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  improvement: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  fix: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
}

const typeLabels = {
  feature: 'New Feature',
  improvement: 'Improvement',
  fix: 'Bug Fix',
}

interface WhatsNewProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function WhatsNew({ open, onOpenChange }: WhatsNewProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader className="pb-4">
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-yellow-500" />
            What's New
          </SheetTitle>
          <SheetDescription>
            Recent updates and improvements to Bijmantra
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6">
          {updates.map((update) => {
            const Icon = update.icon
            return (
              <div
                key={update.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">
                        {update.title}
                      </h3>
                      <Badge variant="outline" className={typeColors[update.type]}>
                        {typeLabels[update.type]}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      {update.description}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span>v{update.version}</span>
                      <span>•</span>
                      <span>{update.date}</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            variant="outline"
            className="w-full"
            onClick={() => onOpenChange(false)}
          >
            Got it!
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

// Hook to manage "What's New" visibility
// NOTE: Auto-show disabled - users can access via Help menu or /whats-new route
const WHATS_NEW_VERSION_KEY = 'bijmantra_whats_new_version'
const CURRENT_VERSION = '1.5.0'

export function useWhatsNew() {
  const [showWhatsNew, setShowWhatsNew] = useState(false)

  // Auto-show disabled to reduce interruptions on login
  // useEffect(() => {
  //   const lastSeenVersion = localStorage.getItem(WHATS_NEW_VERSION_KEY)
  //   if (lastSeenVersion !== CURRENT_VERSION) {
  //     const timer = setTimeout(() => {
  //       setShowWhatsNew(true)
  //     }, 2000)
  //     return () => clearTimeout(timer)
  //   }
  // }, [])

  const dismissWhatsNew = () => {
    localStorage.setItem(WHATS_NEW_VERSION_KEY, CURRENT_VERSION)
    setShowWhatsNew(false)
  }

  return {
    showWhatsNew,
    setShowWhatsNew,
    dismissWhatsNew,
  }
}

export default WhatsNew
