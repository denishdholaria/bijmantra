import { useEffect, useState } from 'react'
import { Clock3, Bell, Wifi, WifiOff, LogOut, HardDrive, FileCode2 } from 'lucide-react'
import { useNotificationStore } from '@/store/notificationStore'
import { useReevuSidebarStore } from '@/store/reevuSidebarStore'
import { ReevuLogo } from '@/components/ai/ReevuTrigger'
import { UserMenu } from '@/components/UserMenu'
import { cn } from '@/lib/utils'
import { useSystemStore } from '@/store/systemStore'

const timeFormatOptions: Intl.DateTimeFormatOptions = {
  hour: '2-digit',
  minute: '2-digit',
}

function getLocalTimeLabel() {
  return new Date().toLocaleTimeString(undefined, timeFormatOptions)
}

export function SystemBarBrand({
  isDesktop,
  onGoHome,
}: {
  isDesktop: boolean
  onGoHome: () => void
}) {
  return (
    <div className="flex items-center gap-3 text-sm font-semibold tracking-wide text-shell">
      <button
        type="button"
        onClick={onGoHome}
        className={cn(
          'relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-2xl border border-[hsl(var(--app-shell-border)/0.8)] transition-all duration-200',
          isDesktop
            ? 'bg-[radial-gradient(circle_at_30%_30%,rgba(255,255,255,0.9),transparent_45%),linear-gradient(145deg,hsl(var(--app-shell-radiance)/0.82),hsl(var(--primary)/0.22))] shadow-[0_12px_28px_-16px_rgba(196,145,31,0.7)]'
            : 'bg-[hsl(var(--app-shell-panel)/0.88)] hover:border-[hsl(var(--primary)/0.24)] hover:bg-[hsl(var(--app-shell-panel))]'
        )}
        title="Home"
      >
        <img src="/logo.png" alt="BijMantra" className="h-5 w-5 object-contain" />
      </button>
      <div className="flex flex-col justify-center">
        <span className="text-sm font-bold tracking-[0.22em] text-shell">BijMantra</span>
      </div>
    </div>
  )
}

export function SystemBarControls({
  isDesktop,
  onLogout,
}: {
  isDesktop: boolean
  onLogout: () => void
}) {
  return (
    <div className="text-shell-muted flex items-center gap-3 text-xs sm:gap-5">
      {isDesktop && <DesktopToolButtons />}
      <OfflineIndicator />
      <NotificationBell />
      <LogoutButton onLogout={onLogout} />
      <UserMenu />

      <div className="border-shell hidden h-4 w-px border-l sm:block" />

      <ReevuButton />
      <LocalTimeDisplay />
    </div>
  )
}

function DesktopToolButtons() {
  const activeSurface = useSystemStore((state) => state.desktopToolSurface)
  const openDesktopTool = useSystemStore((state) => state.openDesktopTool)

  return (
    <div className="hidden items-center gap-2 lg:flex">
      <DesktopToolButton
        icon={HardDrive}
        label="File System"
        active={activeSurface === 'filesystem'}
        onClick={() => openDesktopTool('filesystem')}
      />
      <DesktopToolButton
        icon={FileCode2}
        label="Editor"
        active={activeSurface === 'editor'}
        onClick={() => openDesktopTool('editor')}
      />
    </div>
  )
}

function DesktopToolButton({
  active,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean
  icon: typeof HardDrive
  label: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'border-shell inline-flex items-center gap-2 rounded-2xl border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] transition-all duration-200',
        active
          ? 'bg-[linear-gradient(135deg,hsl(var(--primary)/0.14),hsl(var(--app-shell-radiance)/0.2))] text-shell shadow-[0_18px_32px_-22px_rgba(18,84,49,0.75)]'
          : 'bg-[hsl(var(--app-shell-panel)/0.7)] text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell'
      )}
      title={label}
      aria-label={label}
    >
      <Icon className="h-3.5 w-3.5" />
      <span>{label}</span>
    </button>
  )
}

function LogoutButton({ onLogout }: { onLogout: () => void }) {
  return (
    <button
      type="button"
      onClick={onLogout}
      className="border-shell inline-flex items-center gap-2 rounded-2xl border bg-[hsl(var(--app-shell-panel)/0.7)] px-2.5 py-1.5 text-shell-muted transition-all duration-200 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/30 dark:hover:text-red-400"
      title="Logout"
      aria-label="Logout"
    >
      <LogOut className="h-4 w-4" />
      <span className="hidden text-[11px] font-medium uppercase tracking-[0.14em] md:inline">Logout</span>
    </button>
  )
}

function LocalTimeDisplay() {
  const [timeLabel, setTimeLabel] = useState(() => getLocalTimeLabel())

  useEffect(() => {
    let intervalId: number | undefined

    const refreshLabel = () => {
      setTimeLabel(getLocalTimeLabel())
    }

    const now = new Date()
    const millisecondsUntilNextMinute = (60 - now.getSeconds()) * 1000 - now.getMilliseconds()
    const initialDelay = millisecondsUntilNextMinute > 0 ? millisecondsUntilNextMinute : 60_000

    const timeoutId = window.setTimeout(() => {
      refreshLabel()
      intervalId = window.setInterval(refreshLabel, 60_000)
    }, initialDelay)

    return () => {
      window.clearTimeout(timeoutId)
      if (intervalId !== undefined) {
        window.clearInterval(intervalId)
      }
    }
  }, [])

  return (
    <div className="flex items-center gap-2 text-[11px]">
      <Clock3 className="h-3.5 w-3.5" />
      <span className="text-shell-muted">Local time</span>
      <span className="text-shell font-medium">{timeLabel}</span>
    </div>
  )
}

function ReevuButton() {
  const { isOpen, toggle } = useReevuSidebarStore()

  return (
    <button
      type="button"
      onClick={toggle}
      className={cn(
        'border-shell flex items-center gap-2 rounded-2xl border px-2.5 py-1.5 transition-all duration-200',
        isOpen
          ? 'bg-[linear-gradient(135deg,hsl(var(--primary)/0.14),hsl(var(--app-shell-radiance)/0.22))] text-shell shadow-[0_18px_32px_-22px_rgba(18,84,49,0.75)]'
          : 'bg-[hsl(var(--app-shell-panel)/0.7)] hover:bg-[hsl(var(--accent))]'
      )}
      title="Toggle REEVU (⌘/ or Ctrl+/)"
      aria-label="Toggle REEVU"
    >
      <span className="flex h-7 w-7 items-center justify-center">
        <ReevuLogo className="h-6 w-6 drop-shadow-[0_0_4px_rgba(251,191,36,0.5)]" />
      </span>
      <div className="flex flex-col text-[11px] leading-tight">
        <span className={cn(
          'font-medium',
          isOpen ? 'text-prakruti-patta-dark dark:text-prakruti-patta-light' : 'text-shell'
        )}>
          REEVU
        </span>
        <span className={cn(
          isOpen ? 'text-prakruti-patta dark:text-prakruti-patta-light' : 'text-shell-muted'
        )}>
          {isOpen ? 'Active' : 'Ready'}
        </span>
      </div>
    </button>
  )
}

function NotificationBell() {
  const { unreadCount, toggleCenter, isCenterOpen } = useNotificationStore()

  return (
    <button
      type="button"
      onClick={toggleCenter}
      className={cn(
        'border-shell relative flex h-8 w-8 items-center justify-center rounded-2xl border transition-all duration-200',
        isCenterOpen
          ? 'bg-[linear-gradient(135deg,hsl(var(--primary)/0.14),hsl(var(--app-shell-radiance)/0.2))] text-prakruti-patta-dark dark:text-prakruti-patta-light'
          : 'bg-[hsl(var(--app-shell-panel)/0.7)] text-shell-muted hover:bg-[hsl(var(--accent))] hover:text-shell'
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
        'flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]',
        online
          ? 'border-prakruti-patta/20 bg-[linear-gradient(135deg,hsl(var(--primary)/0.12),hsl(var(--app-shell-radiance)/0.16))] text-prakruti-patta-dark dark:border-prakruti-patta/30 dark:text-prakruti-patta-light'
          : 'border-prakruti-sona/25 bg-[linear-gradient(135deg,hsl(var(--chart-4)/0.16),hsl(var(--app-shell-radiance)/0.2))] text-prakruti-sona-dark dark:border-prakruti-sona/35 dark:text-prakruti-sona-light',
      )}
      title={online ? 'Online' : 'Offline mode active'}
    >
      {online ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
      {online ? 'Online' : 'Offline'}
    </div>
  )
}