/**
 * Unified User Menu Component
 * Consolidates profile, notifications, settings, and logout into one dropdown
 */

import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuGroup,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ThemeToggle } from '@/components/ThemeToggle'
import { useNotifications } from '@/components/notifications'
import {
  User, Bell, Settings, Info, HelpCircle, Keyboard, LogOut
} from 'lucide-react'

// Helper to format time ago
function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export function UserMenu() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { notifications, unreadCount } = useNotifications()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userName = user?.full_name || 'User'
  const userEmail = user?.email || 'user@example.com'

  const getInitials = (name?: string) => {
    if (!name) return 'U'
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          aria-label={`User menu${unreadCount > 0 ? `, ${unreadCount} unread notifications` : ''}`}
          className="relative flex items-center gap-2 rounded-full p-1.5 transition-colors hover:bg-[hsl(var(--accent))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))] focus:ring-offset-2 focus:ring-offset-[hsl(var(--background))]"
        >
          <Avatar className="h-8 w-8 border-2 border-prakruti-patta/20" aria-hidden="true">
            <AvatarFallback className="bg-gradient-to-br from-prakruti-patta to-prakruti-sona-dark text-white text-sm font-medium">
              {getInitials(userName)}
            </AvatarFallback>
          </Avatar>
          {/* Notification badge */}
          {unreadCount > 0 && (
            <span
              className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white ring-2 ring-white dark:ring-slate-900"
              aria-hidden="true"
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="bg-shell-panel border-shell shadow-shell w-72" sideOffset={8}>
        {/* User Info Header */}
        <div className="border-shell px-3 py-3 border-b">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarFallback className="bg-gradient-to-br from-prakruti-patta to-prakruti-sona-dark text-white">
                {getInitials(userName)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-shell font-medium truncate">{userName}</p>
              <p className="text-shell-muted text-sm truncate">{userEmail}</p>
            </div>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-prakruti-patta-pale px-2 py-0.5 text-xs font-medium text-prakruti-patta-dark dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light">
              <span className="bg-prakruti-patta h-1.5 w-1.5 rounded-full"></span>
              Online
            </span>
            <span className="text-shell-muted text-xs">BrAPI v2.1</span>
          </div>
        </div>

        {/* Notifications Section */}
        {unreadCount > 0 && (
          <>
            <DropdownMenuLabel className="flex items-center justify-between px-3 py-2">
              <span className="text-shell-muted text-xs font-medium uppercase">Notifications</span>
              <span className="text-prakruti-patta dark:text-prakruti-patta-light cursor-pointer text-xs hover:underline" onClick={() => navigate('/notifications')}>
                View all
              </span>
            </DropdownMenuLabel>
            <div className="max-h-32 overflow-y-auto">
              {notifications.filter(n => !n.read).slice(0, 3).map((notification) => (
                <DropdownMenuItem
                  key={notification.id}
                  className="cursor-pointer px-3 py-2 hover:bg-[hsl(var(--accent))]"
                  onClick={() => navigate('/notifications')}
                >
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 w-2 h-2 rounded-full bg-blue-500 flex-shrink-0"></span>
                    <div className="flex-1 min-w-0">
                      <p className="text-shell text-sm truncate">{notification.title}</p>
                      <p className="text-shell-muted text-xs">{formatTimeAgo(notification.timestamp)}</p>
                    </div>
                  </div>
                </DropdownMenuItem>
              ))}
            </div>
            <DropdownMenuSeparator />
          </>
        )}

        {/* Quick Links */}
        <DropdownMenuGroup>
          <DropdownMenuItem onClick={() => navigate('/profile')} className="text-shell cursor-pointer hover:bg-[hsl(var(--accent))]">
            <User className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Profile</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/notifications')} className="text-shell cursor-pointer hover:bg-[hsl(var(--accent))]">
            <Bell className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Notifications</span>
            {unreadCount > 0 && (
              <span className="ml-auto rounded-full bg-prakruti-laal-pale px-1.5 py-0.5 text-xs text-prakruti-laal dark:bg-prakruti-laal/20 dark:text-prakruti-laal-light">
                {unreadCount}
              </span>
            )}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/settings')} className="text-shell cursor-pointer hover:bg-[hsl(var(--accent))]">
            <Settings className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Settings</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/about')} className="text-shell cursor-pointer hover:bg-[hsl(var(--accent))]">
            <Info className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>About Bijmantra</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator className="bg-[hsl(var(--border))]" />

        {/* Appearance Settings */}
        <div className="px-3 py-2">
          <p className="text-shell-muted mb-2 text-xs font-medium uppercase">Appearance</p>
          <div>
            <span className="text-shell-muted mb-1 block text-[10px]">Theme</span>
            <ThemeToggle />
          </div>
        </div>

        <DropdownMenuSeparator className="bg-[hsl(var(--border))]" />

        {/* Help & Support */}
        <DropdownMenuGroup>
          <DropdownMenuItem onClick={() => navigate('/help')} className="text-shell cursor-pointer hover:bg-[hsl(var(--accent))]">
            <HelpCircle className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Help Center</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/keyboard-shortcuts')} className="text-shell cursor-pointer hover:bg-[hsl(var(--accent))]">
            <Keyboard className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Keyboard Shortcuts</span>
            <kbd className="bg-shell-muted text-shell-muted ml-auto rounded px-1.5 py-0.5 text-xs">⌘K</kbd>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator className="bg-[hsl(var(--border))]" />

        {/* Logout */}
        <DropdownMenuItem
          onClick={handleLogout}
          className="cursor-pointer text-red-600 dark:text-red-400 focus:text-red-600 dark:focus:text-red-400 focus:bg-red-50 dark:focus:bg-red-900/30 hover:bg-red-50 dark:hover:bg-red-900/30"
        >
          <LogOut className="mr-2 h-4 w-4" strokeWidth={1.75} />
          <span>Sign out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
