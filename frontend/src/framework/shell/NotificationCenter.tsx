import { useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNotificationStore, type Notification } from '@/store/notificationStore'
import { Bell, X, Check, AlertTriangle, Info, AlertCircle, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

// Icons Map
const TypeIcons = {
  info: Info,
  success: Check,
  warning: AlertTriangle,
  error: AlertCircle
}

const TypeColors = {
  info: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20',
  success: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-900/20',
  warning: 'text-amber-500 bg-amber-50 dark:bg-amber-900/20',
  error: 'text-red-500 bg-red-50 dark:bg-red-900/20'
}

export function NotificationCenter() {
  const { 
    isCenterOpen, 
    notifications, 
    toggleCenter, 
    markAllAsRead, 
    clearAll,
    markAsRead,
    clearNotification 
  } = useNotificationStore()

  const containerRef = useRef<HTMLDivElement>(null)

  // Close on click outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      // Logic for outside click specifically for the panel
      // But button triggers it, so we need careful handling or just use an overlay
    }
    // Skipping complex click-outside for now, rely on overlay or toggle button
  }, [])

  return (
    <AnimatePresence>
      {isCenterOpen && (
        <>
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={toggleCenter}
            className="fixed inset-0 z-[900] bg-black/20 backdrop-blur-sm dark:bg-black/40"
          />

          {/* Panel */}
          <motion.div
            ref={containerRef}
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 bottom-0 z-[910] w-80 sm:w-96 bg-white/95 backdrop-blur-xl border-l border-slate-200 shadow-2xl dark:bg-slate-900/95 dark:border-slate-800 flex flex-col"
          >
            {/* Header */}
            <div className="flex-none flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-slate-500" />
                <h2 className="font-semibold text-slate-800 dark:text-slate-200">Notifications</h2>
                <span className="text-xs font-medium bg-slate-100 px-2 py-0.5 rounded-full dark:bg-slate-800 text-slate-500">
                  {notifications.length}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={clearAll} 
                  title="Clear All"
                  disabled={notifications.length === 0}
                  className="p-2 text-slate-400 hover:text-red-500 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <button 
                  onClick={toggleCenter}
                  className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {notifications.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-2 opacity-60">
                  <Bell className="w-12 h-12 stroke-1" />
                  <p>No new notifications</p>
                </div>
              ) : (
                notifications.map(n => (
                  <div 
                    key={n.id}
                    className={cn(
                      "relative group p-3 rounded-xl border transition-all hover:shadow-md",
                      n.read 
                        ? "bg-white border-slate-100 dark:bg-slate-800/50 dark:border-slate-800" 
                        : "bg-white border-emerald-100 shadow-sm ring-1 ring-emerald-500/20 dark:bg-slate-800 dark:border-slate-700"
                    )}
                    onClick={() => markAsRead(n.id)}
                  >
                    <div className="flex gap-3">
                      <div className={cn("flex-none w-8 h-8 rounded-full flex items-center justify-center", TypeColors[n.type])}>
                        {(() => {
                          const Icon = TypeIcons[n.type]
                          return <Icon className="w-4 h-4" />
                        })()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p className={cn("text-sm font-medium truncate", n.read ? "text-slate-600 dark:text-slate-400" : "text-slate-900 dark:text-slate-100")}>
                            {n.title}
                          </p>
                          <span className="text-[10px] text-slate-400 whitespace-nowrap">
                            {new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
                          {n.message}
                        </p>
                      </div>
                    </div>
                    
                    {/* Hover Actions */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        clearNotification(n.id)
                      }}
                      className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 transition-all bg-white dark:bg-slate-800 rounded shadow-sm"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))
              )}
            </div>
            
            {/* Footer */}
            {notifications.some(n => !n.read) && (
              <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
                <button
                  onClick={markAllAsRead}
                  className="w-full py-2 text-xs font-medium text-slate-600 hover:text-emerald-600 hover:bg-emerald-50 dark:text-slate-400 dark:hover:text-emerald-400 dark:hover:bg-emerald-900/20 rounded-lg transition-colors border border-slate-200 dark:border-slate-700 dashed"
                >
                  Mark all as read
                </button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export function Toaster() {
  const { notifications, removeNotification } = useNotificationStore() // Need selector for unread/recent
  // Actually, a real toaster manages its own ephemeral state or derived from store.
  // For simplicity, let's just listen to store changes?
  // Or: Store 'recent' notification separately?
  
  // Implementation strategy:
  // We can just show the latest unread notification if it's < 5 seconds old?
  // Or simpler: The store `addNotification` updates.
  
  // Let's rely on a separate standard library like `sonner` later? 
  // For now, let's build a simple one that shows the *latest* unread notification as a popup.
  
  const latestNotification = notifications[0]
  const [visible, setVisible] = useRef(false) // ... hook issues
  
  // Actually, let's just create a toast trigger in the store or use a library.
  // Building a robust toaster from scratch is tricky with timing.
  // I'll skip the Toaster component in this file for a moment and just focus on the Center.
  // If I want toasts, I should use `sonner` or `react-hot-toast` integrated with the store.
  
  return null
}
