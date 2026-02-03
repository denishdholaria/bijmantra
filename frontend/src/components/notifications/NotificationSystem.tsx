/**
 * Notification System
 * Real-time alerts and notifications for breeding activities
 * 
 * Features:
 * - Push notifications
 * - In-app alerts
 * - Notification preferences
 * - Veena AI alerts
 * 
 * Production-ready: Fetches from /api/v2/notifications
 */

import { useState, useEffect, createContext, useContext, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/auth'

// ============================================
// TYPES
// ============================================

type NotificationType = 
  | 'info' 
  | 'success' 
  | 'warning' 
  | 'error' 
  | 'veena'  // AI insights
  | 'collaboration'  // Team activity
  | 'data'  // Data quality
  | 'weather'  // Weather alerts

interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  timestamp: Date
  read: boolean
  actionUrl?: string
  actionLabel?: string
  source?: string
  metadata?: Record<string, any>
}

interface NotificationPreferences {
  pushEnabled: boolean
  emailEnabled: boolean
  soundEnabled: boolean
  categories: {
    veena: boolean
    collaboration: boolean
    data: boolean
    weather: boolean
    system: boolean
  }
}

// ============================================
// CONTEXT
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
// PROVIDER
// ============================================

interface NotificationProviderProps {
  children: React.ReactNode
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { token, user } = useAuthStore()

  const [preferences, setPreferences] = useState<NotificationPreferences>({
    pushEnabled: true,
    emailEnabled: false,
    soundEnabled: true,
    categories: {
      veena: true,
      collaboration: true,
      data: true,
      weather: true,
      system: true
    }
  })

  // Fetch notifications from API
  const fetchNotifications = useCallback(async () => {
    if (!token) {
      setNotifications([])
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch(`/api/v2/notifications/?user_id=${user?.id || 1}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        // Map API response to frontend format
        const mapped: Notification[] = data.map((n: any) => ({
          id: String(n.id),
          type: mapNotificationType(n.type),
          title: n.title,
          message: n.message,
          timestamp: new Date(n.timestamp),
          read: n.read,
          actionUrl: n.action_url,
          source: n.category
        }))
        setNotifications(mapped)
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      setIsLoading(false)
    }
  }, [token, user?.id])

  // Map backend notification types to frontend types
  function mapNotificationType(type: string): NotificationType {
    const typeMap: Record<string, NotificationType> = {
      'success': 'success',
      'warning': 'warning',
      'error': 'error',
      'info': 'info'
    }
    return typeMap[type] || 'info'
  }

  // Fetch on mount and when token changes
  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  // Poll for new notifications every 30 seconds
  useEffect(() => {
    if (!token) return
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [token, fetchNotifications])

  const unreadCount = notifications.filter(n => !n.read).length

  const addNotification = useCallback(async (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    // Optimistically add to local state
    const tempId = Date.now().toString()
    const newNotification: Notification = {
      ...notification,
      id: tempId,
      timestamp: new Date(),
      read: false
    }

    setNotifications(prev => [newNotification, ...prev])

    // POST to API if authenticated
    if (token) {
      try {
        const response = await fetch(`/api/v2/notifications/?user_id=${user?.id || 1}&organization_id=${user?.organization_id || 1}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            type: notification.type === 'veena' || notification.type === 'collaboration' || notification.type === 'data' || notification.type === 'weather' 
              ? 'info' 
              : notification.type,
            title: notification.title,
            message: notification.message,
            category: notification.source || 'system',
            action_url: notification.actionUrl
          })
        })

        if (response.ok) {
          const data = await response.json()
          // Update with real ID from server
          setNotifications(prev => 
            prev.map(n => n.id === tempId ? { ...n, id: String(data.id) } : n)
          )
        }
      } catch (error) {
        console.error('Failed to create notification:', error)
      }
    }

    // Play sound if enabled
    if (preferences.soundEnabled) {
      // Could play a notification sound here
    }

    // Show browser notification if enabled
    if (preferences.pushEnabled && 'Notification' in window && Notification.permission === 'granted') {
      new window.Notification(notification.title, {
        body: notification.message,
        icon: '/icons/icon-192.png'
      })
    }
  }, [preferences, token, user?.id, user?.organization_id])

  const markAsRead = useCallback(async (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )

    // Call API
    if (token) {
      try {
        await fetch(`/api/v2/notifications/mark-read?user_id=${user?.id || 1}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ notification_ids: [parseInt(id)] })
        })
      } catch (error) {
        console.error('Failed to mark notification as read:', error)
      }
    }
  }, [token, user?.id])

  const markAllAsRead = useCallback(async () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))

    // Call API
    if (token) {
      try {
        await fetch(`/api/v2/notifications/mark-all-read?user_id=${user?.id || 1}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
      } catch (error) {
        console.error('Failed to mark all as read:', error)
      }
    }
  }, [token, user?.id])

  const clearNotification = useCallback(async (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))

    // Call API
    if (token) {
      try {
        await fetch(`/api/v2/notifications/${id}?user_id=${user?.id || 1}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      } catch (error) {
        console.error('Failed to delete notification:', error)
      }
    }
  }, [token, user?.id])

  const clearAll = useCallback(() => {
    setNotifications([])
  }, [])

  const updatePreferences = useCallback((prefs: Partial<NotificationPreferences>) => {
    setPreferences(prev => ({ ...prev, ...prefs }))
  }, [])

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  return (
    <NotificationContext.Provider value={{
      notifications,
      unreadCount,
      preferences,
      addNotification,
      markAsRead,
      markAllAsRead,
      clearNotification,
      clearAll,
      updatePreferences
    }}>
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
    veena: { icon: '🪷', color: 'amber' },
    collaboration: { icon: '👥', color: 'purple' },
    data: { icon: '📊', color: 'blue' },
    weather: { icon: '🌤️', color: 'cyan' }
  }

  return (
    <div className="absolute right-0 top-full mt-2 w-96 bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900 dark:text-white">Notifications</h3>
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
    veena: { icon: '🪷', bgColor: 'bg-gradient-to-r from-amber-500 to-orange-500' },
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
