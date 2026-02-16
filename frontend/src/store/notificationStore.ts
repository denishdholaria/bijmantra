import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type NotificationType = 'info' | 'success' | 'warning' | 'error'

export interface Notification {
  id: string
  title: string
  message: string
  type: NotificationType
  timestamp: number
  read: boolean
  source?: string // App ID
  action?: {
    label: string
    onClick: () => void
  }
}

interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  isCenterOpen: boolean

  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  clearNotification: (id: string) => void
  clearAll: () => void
  toggleCenter: () => void
  setCenterOpen: (open: boolean) => void
}

export const useNotificationStore = create<NotificationState>()(
  persist(
    (set, get) => ({
      notifications: [],
      unreadCount: 0,
      isCenterOpen: false,

      addNotification: (params) => {
        const id = Math.random().toString(36).substring(2, 9)
        const newNotification: Notification = {
          ...params,
          id,
          timestamp: Date.now(),
          read: false
        }

        set(state => ({
          notifications: [newNotification, ...state.notifications],
          unreadCount: state.unreadCount + 1
        }))
      },

      markAsRead: (id) => {
        set(state => ({
          notifications: state.notifications.map(n => 
            n.id === id ? { ...n, read: true } : n
          ),
          unreadCount: Math.max(0, state.unreadCount - 1)
        }))
      },

      markAllAsRead: () => {
        set(state => ({
          notifications: state.notifications.map(n => ({ ...n, read: true })),
          unreadCount: 0
        }))
      },

      clearNotification: (id) => {
        set(state => ({
          notifications: state.notifications.filter(n => n.id !== id),
          unreadCount: state.notifications.find(n => n.id === id && !n.read) 
            ? Math.max(0, state.unreadCount - 1) 
            : state.unreadCount
        }))
      },

      clearAll: () => {
        set({ notifications: [], unreadCount: 0 })
      },

      toggleCenter: () => set(state => ({ isCenterOpen: !state.isCenterOpen })),
      setCenterOpen: (open) => set({ isCenterOpen: open })
    }),
    {
      name: 'bijmantra-notifications',
      // Don't persist ephemeral state if desired, but notifications are usually good to keep
      // Exclude actions function from persistence if any
      partialize: (state) => ({ 
        notifications: state.notifications,
        unreadCount: state.unreadCount
        // Don't persist isCenterOpen
      })
    }
  )
)
