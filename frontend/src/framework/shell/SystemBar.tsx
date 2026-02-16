import { useEffect, useMemo, useState } from 'react'
import { Clock3, Bell, Home, Wifi, WifiOff } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { SystemSettingsMenu } from './SystemSettingsMenu'
import { useNotificationStore } from '@/store/notificationStore'
import { useVeenaSidebarStore } from '@/store/veenaSidebarStore'
import { VeenaLogo } from '@/components/ai/VeenaTrigger'
import { cn } from '@/lib/utils'

const timeFormatOptions: Intl.DateTimeFormatOptions = {
  hour: '2-digit',
  minute: '2-digit',
}

type Wallpaper = {
  id: string
  name: string
  description: string
  previewClassName?: string
  previewImageUrl?: string
}

type SystemBarProps = {
  onToggleConsole?: () => void
  isConsoleOpen?: boolean
  wallpapers: Wallpaper[]
  activeWallpaperId: string
  onWallpaperChange: (id: string) => void
  onWallpaperUpload: (file: File) => void
}

export function SystemBar({
  wallpapers,
  activeWallpaperId,
  onWallpaperChange,
  onWallpaperUpload,
}: SystemBarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const isDesktop = ['/', '/gateway', '/dashboard'].includes(location.pathname)
  
  const timeLabel = useMemo(() => {
    return new Date().toLocaleTimeString(undefined, timeFormatOptions)
  }, [])

  return (
    <header className="relative z-50 flex h-12 items-center justify-between border-b border-slate-200/60 bg-white/70 px-6 backdrop-blur dark:border-slate-800/60 dark:bg-slate-950/70 flex-shrink-0">
      <div className="flex items-center gap-3 text-sm font-semibold tracking-wide text-slate-900 dark:text-slate-100">
        <button
          onClick={() => navigate('/dashboard')}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-full transition-colors overflow-hidden",
            isDesktop
              ? "bg-amber-50/80 ring-1 ring-amber-200/60 dark:bg-amber-900/20 dark:ring-amber-700/40"
              : "hover:bg-amber-50/80 hover:ring-1 hover:ring-amber-200/60 dark:hover:bg-amber-900/20 dark:hover:ring-amber-700/40"
          )}
          title="Home"
        >
          <img src="/logo.png" alt="BijMantraGS" className="h-5 w-5 object-contain" />
        </button>
        <div className="flex flex-col justify-center">
          <span className="text-sm font-bold tracking-wide text-slate-700 dark:text-slate-200">BijMantraVW</span>
        </div>
      </div>

      <div className="flex items-center gap-6 text-xs text-slate-600 dark:text-slate-300">
        {/* Home button when in app mode */}
        {!isDesktop && (
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 rounded-full border border-slate-200/70 bg-white/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-600 transition hover:border-emerald-200 hover:text-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400 dark:border-slate-800/70 dark:bg-slate-900/70 dark:text-slate-300 dark:hover:border-emerald-700/60 dark:hover:text-emerald-200"
          >
            <Home className="h-3.5 w-3.5" />
            Desktop
          </button>
        )}

        <div className="hidden h-4 w-px bg-slate-200 dark:bg-slate-800 sm:block" />
        
        <OfflineIndicator />
        <NotificationBell />

        <SystemSettingsMenu
          wallpapers={wallpapers}
          activeWallpaperId={activeWallpaperId}
          onChange={onWallpaperChange}
          onUpload={onWallpaperUpload}
        />

        <div className="hidden h-4 w-px bg-slate-200 dark:bg-slate-800 sm:block" />

        <VeenaButton />
        <div className="flex items-center gap-2 text-[11px]">
          <Clock3 className="h-3.5 w-3.5" />
          <span className="text-slate-500 dark:text-slate-400">Local time</span>
          <span className="font-medium text-slate-700 dark:text-slate-200">{timeLabel}</span>
        </div>
      </div>
    </header>
  )
}

function VeenaButton() {
  const { isOpen, toggle } = useVeenaSidebarStore()

  return (
    <button
      onClick={toggle}
      className={cn(
        'flex items-center gap-2 rounded-lg px-2 py-1 transition-colors',
        isOpen
          ? 'bg-emerald-50 ring-1 ring-emerald-200/60 dark:bg-emerald-900/20 dark:ring-emerald-700/40'
          : 'hover:bg-slate-100 dark:hover:bg-slate-800'
      )}
      title="Toggle Veena AI Assistant (⌘/)"
      aria-label="Toggle Veena AI Assistant"
    >
      <span className="flex h-7 w-7 items-center justify-center">
        <VeenaLogo className="h-6 w-6 drop-shadow-[0_0_4px_rgba(251,191,36,0.5)]" />
      </span>
      <div className="flex flex-col text-[11px] leading-tight">
        <span className={cn(
          'font-medium',
          isOpen ? 'text-emerald-700 dark:text-emerald-200' : 'text-slate-700 dark:text-slate-200'
        )}>
          Veena
        </span>
        <span className={cn(
          isOpen ? 'text-emerald-500 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400'
        )}>
          {isOpen ? 'Active' : 'AI Assistant'}
        </span>
      </div>
    </button>
  )
}

function NotificationBell() {
  const { unreadCount, toggleCenter, isCenterOpen } = useNotificationStore()
  
  return (
    <button
      onClick={toggleCenter}
      className={cn(
        "relative flex h-7 w-7 items-center justify-center rounded-full transition-colors",
        isCenterOpen 
          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200"
          : "hover:bg-slate-100 text-slate-500 hover:text-slate-700 dark:hover:bg-slate-800 dark:text-slate-400"
      )}
      title="Notifications"
    >
      <Bell className="h-4 w-4" />
      {unreadCount > 0 && (
        <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white shadow-sm ring-2 ring-white dark:ring-slate-950">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </button>
  )
}


function OfflineIndicator() {
  const [online, setOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true)

  useEffect(() => {
    const goOnline = () => setOnline(true)
    const goOffline = () => setOnline(false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  return (
    <div
      className={cn(
        'flex items-center gap-1 rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-wide',
        online
          ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-700/40 dark:bg-emerald-900/20 dark:text-emerald-300'
          : 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-700/40 dark:bg-amber-900/20 dark:text-amber-300',
      )}
      title={online ? 'Online' : 'Offline mode active'}
    >
      {online ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
      {online ? 'Online' : 'Offline'}
    </div>
  )
}
