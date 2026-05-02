
import { useNavigate, useLocation } from 'react-router-dom'
import { useDockStore } from '@/store/dockStore'
import { dockApps } from '../registry/moduleRegistry'
import { cn } from '@/lib/utils'

export function Dock() {
  const navigate = useNavigate()
  const location = useLocation()
  const { recordVisit } = useDockStore()

  const handleAppClick = (appId: string, title: string, route?: string) => {
    if (!route) return
    
    // Track in recent items
    recordVisit({ id: appId, label: title, path: route, icon: appId })
    
    // Navigate via React Router (single page navigation)
    navigate(route)
  }

  return (
    <div className="pointer-events-none fixed bottom-6 left-1/2 z-50 -translate-x-1/2">
      <div className="pointer-events-auto flex items-end gap-2 rounded-2xl border border-slate-200/70 bg-white/80 px-4 py-3 shadow-2xl backdrop-blur-xl dark:border-slate-800/70 dark:bg-slate-900/70">
        {dockApps.map((app) => {
          const Icon = app.icon
          // Check if current route starts with this app's route
          const isActive = app.route 
            ? location.pathname === app.route || location.pathname.startsWith(app.route + '/')
            : false

          return (
            <div key={app.id} className="group relative flex flex-col items-center gap-1">
              <button
                type="button"
                onClick={() => handleAppClick(app.id, app.title, app.route)}
                className={cn(
                  "relative flex h-12 w-12 items-center justify-center rounded-xl transition-all duration-300",
                  "hover:bg-white hover:scale-110 hover:-translate-y-2 hover:shadow-xl dark:hover:bg-slate-800",
                  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400",
                  isActive ? "bg-slate-100 dark:bg-slate-800" : "text-slate-600 dark:text-slate-400"
                )}
                aria-label={app.title}
              >
                <Icon className={cn(
                  "h-6 w-6 transition-colors",
                  isActive ? "text-slate-900 dark:text-slate-100" : "text-slate-500 dark:text-slate-400"
                )} />

                {/* Tooltip on Hover */}
                <span className="absolute -top-10 left-1/2 -translate-x-1/2 rounded-md bg-slate-900 px-2 py-1 text-[10px] font-medium text-white opacity-0 transition-opacity group-hover:opacity-100 whitespace-nowrap dark:bg-white dark:text-slate-900">
                  {app.title}
                </span>
              </button>

              {/* Active Indicator */}
              <div className={cn(
                "h-1 w-1 rounded-full bg-emerald-500 transition-all duration-300",
                isActive ? "opacity-100 scale-100" : "opacity-0 scale-0"
              )} />
            </div>
          )
        })}
      </div>
    </div>
  )
}
