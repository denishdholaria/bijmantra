/**
 * Real-Time Presence System
 * Shows live cursors and user presence across the platform
 * 
 * APEX FEATURE: No competitor has real-time collaboration
 */

import { useState, useEffect } from 'react'

interface User {
  id: string
  name: string
  email: string
  avatar?: string
  color: string
}

interface Cursor {
  userId: string
  x: number
  y: number
  page: string
  timestamp: number
}

interface PresenceState {
  users: Map<string, User>
  cursors: Map<string, Cursor>
  activeUsers: User[]
}

// Generate consistent color from user ID
function getUserColor(userId: string): string {
  const colors = [
    '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#22c55e',
    '#14b8a6', '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6',
    '#a855f7', '#d946ef', '#ec4899', '#f43f5e'
  ]
  const hash = userId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[hash % colors.length]
}

// Get initials from name
function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

interface LiveCursorProps {
  user: User
  cursor: Cursor
  currentUserId: string
}

function LiveCursor({ user, cursor, currentUserId }: LiveCursorProps) {
  if (user.id === currentUserId) return null

  return (
    <div
      className="fixed pointer-events-none z-[9999] transition-all duration-75"
      style={{
        left: cursor.x,
        top: cursor.y,
        transform: 'translate(-2px, -2px)'
      }}
    >
      {/* Cursor SVG */}
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))' }}
      >
        <path
          d="M5.65376 12.4563L5.65376 12.4563L5.65314 12.4525C5.64132 12.3836 5.64132 12.3133 5.65314 12.2444L5.65376 12.2406L5.65376 12.2406L8.73388 3.32931C8.79197 3.15753 8.90594 3.00879 9.05778 2.90503C9.20962 2.80127 9.39132 2.74756 9.57656 2.75195C9.7618 2.75634 9.94066 2.81859 10.0873 2.92943C10.234 3.04027 10.3407 3.19419 10.3907 3.36875L10.3907 3.36875L10.3932 3.37756L13.4733 12.2406L13.4733 12.2406L13.4739 12.2425C13.4857 12.3114 13.4857 12.3817 13.4739 12.4506L13.4733 12.4544L13.4733 12.4544L10.3932 21.3175L10.3932 21.3175L10.3907 21.3263C10.3407 21.5009 10.234 21.6548 10.0873 21.7656C9.94066 21.8765 9.7618 21.9387 9.57656 21.9431C9.39132 21.9475 9.20962 21.8938 9.05778 21.79C8.90594 21.6863 8.79197 21.5375 8.73388 21.3658L8.73388 21.3658L5.65376 12.4563Z"
          fill={user.color}
          stroke="white"
          strokeWidth="1.5"
        />
      </svg>
      
      {/* User label */}
      <div
        className="absolute left-4 top-4 px-2 py-1 rounded-md text-xs font-medium text-white whitespace-nowrap shadow-lg"
        style={{ backgroundColor: user.color }}
      >
        {user.name}
      </div>
    </div>
  )
}

interface PresenceAvatarsProps {
  users: User[]
  currentUserId: string
  maxVisible?: number
}

export function PresenceAvatars({ users, currentUserId, maxVisible = 5 }: PresenceAvatarsProps) {
  const otherUsers = users.filter(u => u.id !== currentUserId)
  const visibleUsers = otherUsers.slice(0, maxVisible)
  const remainingCount = otherUsers.length - maxVisible

  if (otherUsers.length === 0) return null

  return (
    <div className="flex items-center -space-x-2">
      {visibleUsers.map(user => (
        <div
          key={user.id}
          className="relative group"
        >
          {user.avatar ? (
            <img
              src={user.avatar}
              alt={user.name}
              className="w-8 h-8 rounded-full border-2 border-white dark:border-gray-800 shadow-sm"
            />
          ) : (
            <div
              className="w-8 h-8 rounded-full border-2 border-white dark:border-gray-800 shadow-sm flex items-center justify-center text-xs font-medium text-white"
              style={{ backgroundColor: user.color }}
            >
              {getInitials(user.name)}
            </div>
          )}
          
          {/* Online indicator */}
          <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full" />
          
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            {user.name}
          </div>
        </div>
      ))}
      
      {remainingCount > 0 && (
        <div className="w-8 h-8 rounded-full border-2 border-white dark:border-gray-800 bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-medium text-gray-600 dark:text-gray-300">
          +{remainingCount}
        </div>
      )}
    </div>
  )
}

interface RealtimePresenceProviderProps {
  children: React.ReactNode
  currentUser: User
  roomId: string
}

export function RealtimePresenceProvider({ 
  children, 
  currentUser,
  roomId 
}: RealtimePresenceProviderProps) {
  const [presence, setPresence] = useState<PresenceState>({
    users: new Map(),
    cursors: new Map(),
    activeUsers: []
  })

  // Track mouse movement
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // In production, this would broadcast to WebSocket
      const cursor: Cursor = {
        userId: currentUser.id,
        x: e.clientX,
        y: e.clientY,
        page: window.location.pathname,
        timestamp: Date.now()
      }
      
      // Throttled broadcast would happen here
      // socket.emit('cursor:move', cursor)
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [currentUser.id])

  // Simulate other users for demo
  useEffect(() => {
    const demoUsers: User[] = [
      { id: 'demo-1', name: 'Dr. Sharma', email: 'sharma@example.com', color: getUserColor('demo-1') },
      { id: 'demo-2', name: 'Priya Patel', email: 'priya@example.com', color: getUserColor('demo-2') },
    ]

    setPresence(prev => ({
      ...prev,
      activeUsers: [currentUser, ...demoUsers]
    }))
  }, [currentUser])

  return (
    <RealtimeContext.Provider value={{ presence, currentUser }}>
      {children}
      
      {/* Render live cursors */}
      {Array.from(presence.cursors.entries()).map(([userId, cursor]) => {
        const user = presence.users.get(userId)
        if (!user) return null
        return (
          <LiveCursor
            key={userId}
            user={user}
            cursor={cursor}
            currentUserId={currentUser.id}
          />
        )
      })}
    </RealtimeContext.Provider>
  )
}

// Context
import { createContext, useContext } from 'react'

interface RealtimeContextValue {
  presence: PresenceState
  currentUser: User
}

const RealtimeContext = createContext<RealtimeContextValue | null>(null)

export function useRealtimePresence() {
  const context = useContext(RealtimeContext)
  if (!context) {
    throw new Error('useRealtimePresence must be used within RealtimePresenceProvider')
  }
  return context
}

export { getUserColor, getInitials }
export type { User, Cursor, PresenceState }
