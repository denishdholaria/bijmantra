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
  User, Bell, Settings, Info, HelpCircle, Keyboard, LogOut,
  Mail, ExternalLink, ChevronRight
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
          className="relative flex items-center gap-2 p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900"
        >
          <Avatar className="h-8 w-8 border-2 border-green-500/20" aria-hidden="true">
            <AvatarFallback className="bg-gradient-to-br from-green-500 to-emerald-600 text-white text-sm font-medium">
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

      <DropdownMenuContent align="end" className="w-72 bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700" sideOffset={8}>
        {/* User Info Header */}
        <div className="px-3 py-3 border-b border-gray-100 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarFallback className="bg-gradient-to-br from-green-500 to-emerald-600 text-white">
                {getInitials(userName)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{userName}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{userEmail}</p>
            </div>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Online
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">BrAPI v2.1</span>
          </div>
        </div>

        {/* Notifications Section */}
        {unreadCount > 0 && (
          <>
            <DropdownMenuLabel className="flex items-center justify-between px-3 py-2">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Notifications</span>
              <span className="text-xs text-green-600 dark:text-green-400 hover:underline cursor-pointer" onClick={() => navigate('/notifications')}>
                View all
              </span>
            </DropdownMenuLabel>
            <div className="max-h-32 overflow-y-auto">
              {notifications.filter(n => !n.read).slice(0, 3).map((notification) => (
                <DropdownMenuItem
                  key={notification.id}
                  className="px-3 py-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700"
                  onClick={() => navigate('/notifications')}
                >
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 w-2 h-2 rounded-full bg-blue-500 flex-shrink-0"></span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 dark:text-gray-200 truncate">{notification.title}</p>
                      <p className="text-xs text-gray-400 dark:text-gray-500">{formatTimeAgo(notification.timestamp)}</p>
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
          <DropdownMenuItem onClick={() => navigate('/profile')} className="cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700">
            <User className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Profile</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/notifications')} className="cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700">
            <Bell className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Notifications</span>
            {unreadCount > 0 && (
              <span className="ml-auto text-xs bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 px-1.5 py-0.5 rounded-full">
                {unreadCount}
              </span>
            )}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/settings')} className="cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700">
            <Settings className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Settings</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/about')} className="cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700">
            <Info className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>About Bijmantra</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator className="bg-gray-200 dark:bg-slate-700" />

        {/* Theme Toggle */}
        <div className="px-3 py-2">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">Theme</p>
          <ThemeToggle />
        </div>

        <DropdownMenuSeparator className="bg-gray-200 dark:bg-slate-700" />

        {/* Help & Support */}
        <DropdownMenuGroup>
          <DropdownMenuItem onClick={() => navigate('/help')} className="cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700">
            <HelpCircle className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Help Center</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/keyboard-shortcuts')} className="cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700">
            <Keyboard className="mr-2 h-4 w-4" strokeWidth={1.75} />
            <span>Keyboard Shortcuts</span>
            <kbd className="ml-auto text-xs bg-gray-100 dark:bg-slate-600 text-gray-600 dark:text-gray-300 px-1.5 py-0.5 rounded">⌘K</kbd>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator className="bg-gray-200 dark:bg-slate-700" />

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
