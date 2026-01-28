/**
 * Quick Action Floating Action Button (FAB)
 * 
 * Mobile-friendly FAB for quick access to common field actions.
 * Expands to show quick actions when tapped.
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  Plus,
  X,
  Camera,
  ClipboardList,
  QrCode,
  Mic,
  MapPin,
  type LucideIcon,
} from 'lucide-react'

interface QuickAction {
  id: string
  name: string
  icon: LucideIcon
  route: string
  color: string
}

const quickActions: QuickAction[] = [
  { id: 'scan', name: 'Scan', icon: QrCode, route: '/barcode', color: 'bg-blue-500' },
  { id: 'photo', name: 'Photo', icon: Camera, route: '/plant-vision', color: 'bg-purple-500' },
  { id: 'collect', name: 'Collect', icon: ClipboardList, route: '/observations/collect', color: 'bg-green-500' },
  { id: 'location', name: 'Location', icon: MapPin, route: '/locations', color: 'bg-amber-500' },
  { id: 'voice', name: 'Voice', icon: Mic, route: '/ai-assistant', color: 'bg-pink-500' },
]

export function QuickActionFAB() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="fixed bottom-20 right-4 z-40 lg:hidden">
      {/* Action buttons */}
      <div className={cn(
        'flex flex-col-reverse gap-3 mb-3 transition-all duration-300',
        isOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'
      )}>
        {quickActions.map((action, index) => {
          const Icon = action.icon
          return (
            <Link
              key={action.id}
              to={action.route}
              onClick={() => setIsOpen(false)}
              className={cn(
                'flex items-center gap-2 pl-3 pr-4 py-2 rounded-full shadow-lg transition-all',
                action.color, 'text-white',
                'hover:scale-105 active:scale-95'
              )}
              style={{
                transitionDelay: isOpen ? `${index * 50}ms` : '0ms',
              }}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium whitespace-nowrap">{action.name}</span>
            </Link>
          )
        })}
      </div>

      {/* Main FAB button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all',
          'hover:scale-105 active:scale-95',
          isOpen
            ? 'bg-gray-800 dark:bg-gray-200 rotate-45'
            : 'bg-green-600 hover:bg-green-700'
        )}
        aria-label={isOpen ? 'Close quick actions' : 'Open quick actions'}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white dark:text-gray-800" />
        ) : (
          <Plus className="w-6 h-6 text-white" />
        )}
      </button>
    </div>
  )
}

export default QuickActionFAB
