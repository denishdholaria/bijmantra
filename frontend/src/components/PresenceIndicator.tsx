/**
 * Presence Indicator Component
 * Shows online users and their activity
 */

import { usePresence, OnlineUser } from '@/lib/socket'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function UserAvatar({ user, size = 'sm' }: { user: OnlineUser; size?: 'sm' | 'md' }) {
  const sizeClasses = size === 'sm' ? 'h-6 w-6 text-xs' : 'h-8 w-8 text-sm'

  return (
    <Avatar className={`${sizeClasses} ring-2 ring-white`}>
      <AvatarFallback
        style={{ backgroundColor: user.color }}
        className="text-white font-medium"
      >
        {getInitials(user.name)}
      </AvatarFallback>
    </Avatar>
  )
}

interface PresenceIndicatorProps {
  maxVisible?: number
  showCount?: boolean
}

export function PresenceIndicator({ maxVisible = 3, showCount = true }: PresenceIndicatorProps) {
  const { onlineUsers } = usePresence()

  if (onlineUsers.length === 0) {
    return null
  }

  const visibleUsers = onlineUsers.slice(0, maxVisible)
  const remainingCount = onlineUsers.length - maxVisible

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-1 px-2 py-1 rounded-full hover:bg-gray-100 transition-colors">
          {/* Stacked avatars */}
          <div className="flex -space-x-2">
            {visibleUsers.map((user) => (
              <UserAvatar key={user.id} user={user} />
            ))}
            {remainingCount > 0 && (
              <div className="h-6 w-6 rounded-full bg-gray-200 ring-2 ring-white flex items-center justify-center text-xs font-medium text-gray-600">
                +{remainingCount}
              </div>
            )}
          </div>

          {/* Online count */}
          {showCount && (
            <span className="text-xs text-gray-500 ml-1">
              {onlineUsers.length} online
            </span>
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          {onlineUsers.length} {onlineUsers.length === 1 ? 'person' : 'people'} online
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        <div className="max-h-64 overflow-y-auto">
          {onlineUsers.map((user) => (
            <div
              key={user.id}
              className="flex items-center gap-3 px-2 py-2 hover:bg-gray-50 rounded-md"
            >
              <UserAvatar user={user} size="md" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user.name}</p>
                {user.cursor?.page && (
                  <p className="text-xs text-gray-500 truncate">
                    Viewing: {user.cursor.page}
                  </p>
                )}
              </div>
              <span className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0"></span>
            </div>
          ))}
        </div>

        {onlineUsers.length === 0 && (
          <div className="px-2 py-4 text-center text-sm text-gray-500">
            No one else is online
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/**
 * Compact presence dots for tight spaces
 */
export function PresenceDots({ maxDots = 5 }: { maxDots?: number }) {
  const { onlineUsers } = usePresence()

  if (onlineUsers.length === 0) return null

  const visibleUsers = onlineUsers.slice(0, maxDots)

  return (
    <div className="flex items-center gap-0.5" title={`${onlineUsers.length} online`}>
      {visibleUsers.map((user) => (
        <span
          key={user.id}
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: user.color }}
          title={user.name}
        />
      ))}
      {onlineUsers.length > maxDots && (
        <span className="text-xs text-gray-400 ml-0.5">
          +{onlineUsers.length - maxDots}
        </span>
      )}
    </div>
  )
}

/**
 * Cursor presence overlay for collaborative editing
 */
export function CursorPresence() {
  const { onlineUsers } = usePresence()

  return (
    <>
      {onlineUsers
        .filter((user) => user.cursor)
        .map((user) => (
          <div
            key={user.id}
            className="fixed pointer-events-none z-50 transition-all duration-100"
            style={{
              left: user.cursor!.x,
              top: user.cursor!.y,
              transform: 'translate(-2px, -2px)',
            }}
          >
            {/* Cursor */}
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              style={{ color: user.color }}
            >
              <path
                d="M5.65376 12.4563L5.65376 12.4563L5.65314 12.4525C5.64132 12.3836 5.64132 12.3133 5.65314 12.2444L5.65376 12.2406L5.65376 12.2406L8.97939 3.32869C9.03424 3.19352 9.13232 3.08026 9.25808 3.00628C9.38384 2.9323 9.53024 2.90137 9.67539 2.91814C9.82054 2.93491 9.95631 2.99848 10.0627 3.09918C10.1691 3.19988 10.2405 3.33236 10.2661 3.47669L10.2667 3.48L10.2667 3.48L12.0001 12L10.2667 20.52L10.2667 20.52L10.2661 20.5233C10.2405 20.6676 10.1691 20.8001 10.0627 20.9008C9.95631 21.0015 9.82054 21.0651 9.67539 21.0819C9.53024 21.0986 9.38384 21.0677 9.25808 20.9937C9.13232 20.9197 9.03424 20.8065 8.97939 20.6713L5.65376 12.4563Z"
                fill="currentColor"
              />
            </svg>
            {/* Name label */}
            <div
              className="absolute left-4 top-4 px-2 py-0.5 rounded text-xs text-white whitespace-nowrap"
              style={{ backgroundColor: user.color }}
            >
              {user.name}
            </div>
          </div>
        ))}
    </>
  )
}
