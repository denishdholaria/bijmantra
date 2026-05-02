/**
 * Notification System
 * Real-time alerts and notifications for breeding activities
 *
 * Architecture note: All notification state is owned by `useNotificationStore`
 * (Zustand, persisted). This provider is a thin shell that:
 *   1. Polls the backend API and syncs results into the store.
 *   2. Handles browser push-notification permission.
 *   3. Re-exports the store's interface via context so legacy consumers of
 *      `useNotifications()` continue to work without changes.
 *
 * Do NOT add local `useState` for notification lists here — use the store.
 */

import { useEffect, createContext, useContext, useCallback } from 'react'
import { LEGACY_REEVU_NOTIFICATION_TYPE } from '@/lib/legacyReevu'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/auth'
import { useNotificationStore, type Notification, type NotificationType } from '@/store/notificationStore'

// ============================================
// TYPES (re-exported from store for backward compat)
// ============================================

export type { Notification, NotificationType }

interface NotificationPreferences {
  pushEnabled: boolean
  emailEnabled: boolean
  soundEnabled: boolean
  categories: {
    [LEGACY_REEVU_NOTIFICATION_TYPE]: boolean
    collaboration: boolean
    data: boolean
    weather: boolean
    system: boolean
  }
}

// ============================================
// CONTEXT — delegates to notificationStore
// ============================================

interface NotificationContextValue {
  notifications: Notification[]
  unreadCount: number
  preferences: NotificationPreferences
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  clearNotification: (id: string) => void
  clearAll: () => void
  updatePreferences: (prefs: Partial<NotificationPreferences>) => void
}

const NotificationContext = createContext<NotificationContextValue | null>(null)

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return context
}

// ============================================
// PROVIDER — syncs API → store, no local state
// ============================================

interface NotificationProviderProps {
  children: React.ReactNode
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const { token, user } = useAuthStore()
  // All notification state lives in the Zustand store — no local useState here.
  const store = useNotificationStore()

  const defaultPreferences: NotificationPreferences = {
    pushEnabled: true,
    emailEnabled: false,
    soundEnabled: true,
    categories: {
      [LEGACY_REEVU_NOTIFICATION_TYPE]: true,
      collaboration: true,
      data: true,
      weather: true,
      system: true,
    },
  }

  // Map backend notification types to store types
  function mapNotificationType(type: string): NotificationType {
    const typeMap: Record<string, NotificationType> = {
      success: 'success',
      warning: 'warning',
      error: 'error',
      info: 'info',
    }
    return (typeMap[type] as NotificationType) || 'info'
  }

  // Fetch notifications from API and sync into the store
  const fetchNotifications = useCallback(async () => {
    if (!token) return
    try {
      const response = await fetch(`/api/v2/notifications/?user_id=${user?.id || 1}`, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      })
      if (response.ok) {
        const data = await response.json()
        // Replace store contents with server state
        store.clearAll()
        for (const n of data) {
          store.addNotification({
            title: n.title,
            message: n.message,
            type: mapNotificationType(n.type),
            source: n.category,
          })
        }
      }
    } catch {
      // Non-fatal — store retains its persisted state
    }
  }, [token, user?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetchNotifications() }, [fetchNotifications])

  useEffect(() => {
    if (!token) return
    const interval = setInterval(fetchNotifications, 30_000)
    return () => clearInterval(interval)
  }, [token, fetchNotifications])

  // Request browser notification permission once
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  // Wrap store.addNotification to also POST to API and trigger browser push
  const addNotification = useCallback(
    async (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
      store.addNotification(notification)

      if (token) {
        try {
          await fetch(
            `/api/v2/notifications/?user_id=${user?.id || 1}&organization_id=${user?.organization_id || 1}`,
            {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
              body: JSON.stringify({
                type: ['collaboration', 'data', 'weather', LEGACY_REEVU_NOTIFICATION_TYPE].includes(
                  notification.type,
                )
                  ? 'info'
                  : notification.type,
                title: notification.title,
                message: notification.message,
                category: notification.source || 'system',
              }),
            },
          )
        } catch {
          // Non-fatal
        }
      }

      if (
        defaultPreferences.pushEnabled &&
        'Notification' in window &&
        Notification.permission === 'granted'
      ) {
        new window.Notification(notification.title, {
          body: notification.message,
          icon: '/icons/icon-192.png',
        })
      }
    },
    [token, user?.id, user?.organization_id, store], // eslint-disable-line react-hooks/exhaustive-deps
  )

  const contextValue: NotificationContextValue = {
    notifications: store.notifications as unknown as Notification[],
    unreadCount: store.unreadCount,
    preferences: defaultPreferences,
    addNotification,
    markAsRead: store.markAsRead,
    markAllAsRead: store.markAllAsRead,
    clearNotification: store.clearNotification,
    clearAll: store.clearAll,
    updatePreferences: () => {}, // preferences are local-only for now
  }

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
    </NotificationContext.Provider>
  )
}

// ============================================
// NOTIFICATION BELL
// ============================================

interface NotificationBellProps {
  className?: string
}

export function NotificationBell({ className }: NotificationBellProps) {
  const { unreadCount } = useNotifications()
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className={cn('relative', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          <NotificationDropdown onClose={() => setIsOpen(false)} />
        </>
      )}
    </div>
  )
}

// ============================================
// NOTIFICATION DROPDOWN
// ============================================

interface NotificationDropdownProps {
  onClose: () => void
}

function NotificationDropdown({ onClose }: NotificationDropdownProps) {
  const { notifications, markAsRead, markAllAsRead, clearNotification } = useNotifications()

  const typeConfig: Record<NotificationType, { icon: string; color: string }> = {
    info: { icon: 'ℹ️', color: 'blue' },
    success: { icon: '✅', color: 'green' },
    warning: { icon: '⚠️', color: 'amber' },
    error: { icon: '❌', color: 'red' },
    [LEGACY_REEVU_NOTIFICATION_TYPE]: { icon: '🪷', color: 'amber' },
    collaboration: { icon: '👥', color: 'purple' },
    data: { icon: '📊', color: 'blue' },
    weather: { icon: '🌤️', color: 'cyan' }
  }

  return (
    <div className="absolute right-0 top-full mt-2 w-96 bg-popover text-popover-foreground rounded-xl shadow-2xl border border-border z-50 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h3 className="font-semibold">Notifications</h3>
        <button
          onClick={markAllAsRead}
          className="text-xs text-amber-600 dark:text-amber-400 hover:underline"
        >
          Mark all as read
        </button>
      </div>

      {/* Notifications List */}
      <div className="max-h-96 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <span className="text-4xl mb-2 block">🔔</span>
            <p>No notifications</p>
          </div>
        ) : (
          notifications.map(notification => {
            const config = typeConfig[notification.type]
            
            return (
              <div
                key={notification.id}
                className={cn(
                  'px-4 py-3 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer',
                  !notification.read && 'bg-amber-50/50 dark:bg-amber-900/10'
                )}
                onClick={() => markAsRead(notification.id)}
              >
                <div className="flex gap-3">
                  <span className="text-xl flex-shrink-0">{config.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className={cn(
                        'text-sm font-medium text-gray-900 dark:text-white',
                        !notification.read && 'font-semibold'
                      )}>
                        {notification.title}
                      </h4>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          clearNotification(notification.id)
                        }}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      >
                        ×
                      </button>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5 line-clamp-2">
                      {notification.message}
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-[10px] text-gray-400">
                        {formatTimeAgo(notification.timestamp)}
                        {notification.source && ` • ${notification.source}`}
                      </span>
                      {notification.actionUrl && (
                        <a
                          href={notification.actionUrl}
                          onClick={onClose}
                          className="text-xs text-amber-600 dark:text-amber-400 hover:underline"
                        >
                          {notification.actionLabel || 'View'}
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
        <a
          href="/notification-center"
          onClick={onClose}
          className="text-xs text-amber-600 dark:text-amber-400 hover:underline"
        >
          View all notifications →
        </a>
      </div>
    </div>
  )
}

// ============================================
// TOAST NOTIFICATION
// ============================================

interface ToastProps {
  notification: Notification
  onClose: () => void
}

export function Toast({ notification, onClose }: ToastProps) {
  const typeConfig: Record<NotificationType, { icon: string; bgColor: string }> = {
    info: { icon: 'ℹ️', bgColor: 'bg-blue-500' },
    success: { icon: '✅', bgColor: 'bg-green-500' },
    warning: { icon: '⚠️', bgColor: 'bg-amber-500' },
    error: { icon: '❌', bgColor: 'bg-red-500' },
    [LEGACY_REEVU_NOTIFICATION_TYPE]: { icon: '🪷', bgColor: 'bg-gradient-to-r from-amber-500 to-orange-500' },
    collaboration: { icon: '👥', bgColor: 'bg-purple-500' },
    data: { icon: '📊', bgColor: 'bg-blue-500' },
    weather: { icon: '🌤️', bgColor: 'bg-cyan-500' }
  }

  const config = typeConfig[notification.type]

  useEffect(() => {
    const timer = setTimeout(onClose, 5000)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div className={cn(
      'flex items-start gap-3 p-4 rounded-xl shadow-lg text-white max-w-sm animate-slide-in',
      config.bgColor
    )}>
      <span className="text-xl">{config.icon}</span>
      <div className="flex-1">
        <h4 className="font-medium">{notification.title}</h4>
        <p className="text-sm opacity-90 mt-0.5">{notification.message}</p>
      </div>
      <button onClick={onClose} className="opacity-70 hover:opacity-100">×</button>
    </div>
  )
}

// ============================================
// HELPERS
// ============================================

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export type { Notification, NotificationType, NotificationPreferences }
