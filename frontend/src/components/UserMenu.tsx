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
import { useSystemStore } from '@/store/systemStore'
import { wallpaperOptions } from '@/config/wallpapers'
import {
  User, Bell, Settings, Info, HelpCircle, Keyboard, LogOut, Upload
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
  const {
    activeWallpaperId,
    setActiveWallpaperId,
    customWallpaperUrl,
    setCustomWallpaperUrl,
  } = useSystemStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleWallpaperUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
      const result = typeof reader.result === 'string' ? reader.result : null
      if (result) {
        setCustomWallpaperUrl(result)
        setActiveWallpaperId('custom')
      }
    }
    reader.readAsDataURL(file)
    event.target.value = ''
  }

  // Combine default wallpapers with custom if exists
  const allWallpapers = customWallpaperUrl
    ? [
      { id: 'custom', name: 'Custom', description: 'Uploaded wallpaper', imageUrl: customWallpaperUrl },
      ...wallpaperOptions,
    ]
    : wallpaperOptions

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

        {/* Appearance Settings */}
        <div className="px-3 py-2">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">Appearance</p>
          <div className="mb-4">
            <span className="mb-1 block text-[10px] text-gray-500 dark:text-gray-400">Theme</span>
            <ThemeToggle />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-gray-500 dark:text-gray-400">Wallpaper</span>
              <label className="flex cursor-pointer items-center gap-1 rounded px-1.5 py-0.5 text-[10px] uppercase font-medium text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/30">
                <Upload className="h-3 w-3" />
                Upload
                <input
                  type="file"
                  accept="image/*"
                  className="sr-only"
                  onChange={handleWallpaperUpload}
                />
              </label>
            </div>
            <div className="grid grid-cols-2 gap-2" role="group" aria-label="Wallpaper Options">
              {allWallpapers.map((wallpaper) => (
                <button
                  key={wallpaper.id}
                  type="button"
                  title={wallpaper.name}
                  onClick={() => setActiveWallpaperId(wallpaper.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      setActiveWallpaperId(wallpaper.id)
                    }
                  }}
                  className={`relative flex aspect-video items-center justify-center overflow-hidden rounded-lg border transition ${activeWallpaperId === wallpaper.id
                    ? 'border-green-500 ring-2 ring-green-500/20'
                    : 'border-slate-200 hover:border-green-200 dark:border-slate-700 dark:bg-slate-900'
                    }`}
                >
                  <div
                    className={`absolute inset-0 ${wallpaper.previewClassName ?? ''}`}
                    style={
                      wallpaper.imageUrl
                        ? { backgroundImage: `url(${wallpaper.imageUrl})`, backgroundSize: 'cover', backgroundPosition: 'center' }
                        : undefined
                    }
                  />
                  {activeWallpaperId === wallpaper.id && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/10">
                      <div className="h-2 w-2 rounded-full bg-white shadow-sm" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
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
