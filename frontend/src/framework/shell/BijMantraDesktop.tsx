import type { ReactNode } from 'react'
import { useEffect, useMemo, useState } from 'react'
import { useSystemStore } from '@/store/systemStore'
import { Grid3X3, RefreshCw, Image, Settings } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { MahasarthiStrata } from '@/components/navigation/MahasarthiStrata'
// import { Dock } from './Dock'  // DISABLED — see docs/tasks/20260207.md
import { SystemBar } from './SystemBar'
import { ShellSidebar } from './ShellSidebar'
import { ContextMenu, useContextMenu } from './ContextMenu'
import { NotificationCenter } from './NotificationCenter'
import { CommandPalette } from './CommandPalette'
import { useNotificationStore } from '@/store/notificationStore'
import { lazy, Suspense } from 'react'
import { LEGACY_REEVU_ROUTE } from '@/lib/legacyReevu'

const ReevuSidebar = lazy(() =>
  import('@/components/ai/ReevuSidebar').then((m) => ({ default: m.ReevuSidebar }))
)

import { wallpaperOptions } from '@/config/wallpapers'

// ============================================================================
// Desktop Routes — routes that show the wallpaper + shortcuts instead of app content
// ============================================================================

const DESKTOP_ROUTES = new Set(['/', '/gateway', '/dashboard'])

/** Routes where the Dock + STRATA auto-hide to avoid overlapping bottom-anchored content. */
const IMMERSIVE_ROUTES = new Set(['/reevu', LEGACY_REEVU_ROUTE, '/ai-assistant'])

// ============================================================================
// BijMantraDesktop — Unified Web-OS Shell
// ============================================================================

type BijMantraDesktopProps = {
  children?: ReactNode
}

export function BijMantraDesktop({ children }: BijMantraDesktopProps) {
  const {
    setIsInShell,
    activeWallpaperId,
    setActiveWallpaperId,
    customWallpaperUrl,
  } = useSystemStore()

  const location = useLocation()
  const [isStrataOpenState, setIsStrataOpenState] = useState(false)
  const isStrataOpen = useSystemStore((state) => state.isStrataOpen)
  const setStrataOpen = useSystemStore((state) => state.setStrataOpen)

  // Keep local state in sync with global state if we want to programmatically open it
  const setIsStrataOpen = (open: boolean) => {
    setIsStrataOpenState(open)
    setStrataOpen(open)
  }

  const { addNotification } = useNotificationStore()

  // Mark shell as active
  useEffect(() => {
    setIsInShell(true)
    return () => setIsInShell(false)
  }, [setIsInShell])

  // ─── Derived State ───

  const isDesktopRoute = DESKTOP_ROUTES.has(location.pathname)
  const isImmersiveRoute = IMMERSIVE_ROUTES.has(location.pathname)

  const allWallpapers = useMemo(() => {
    if (!customWallpaperUrl) return wallpaperOptions
    return [
      { id: 'custom', name: 'Custom', description: 'Uploaded wallpaper', imageUrl: customWallpaperUrl },
      ...wallpaperOptions,
    ]
  }, [customWallpaperUrl])

  const activeWallpaper = useMemo(
    () => allWallpapers.find((w) => w.id === activeWallpaperId) || allWallpapers[0],
    [activeWallpaperId, allWallpapers]
  )

  // ─── Context Menu ───

  const { onContextMenu } = useContextMenu([
    {
      label: 'Change Wallpaper',
      icon: Image,
      action: () => {
        const nextIdx = (wallpaperOptions.findIndex((w) => w.id === activeWallpaperId) + 1) % wallpaperOptions.length
        setActiveWallpaperId(wallpaperOptions[nextIdx].id)
      },
    },
    {
      label: 'Refresh Desktop',
      icon: RefreshCw,
      action: () => window.location.reload(),
      shortcut: '⌘R',
    },
    { separator: true, label: '', action: () => { } },
    {
      label: 'Test Notification',
      icon: Image,
      action: () => {
        addNotification({
          title: 'System Alert',
          message: 'REEVU has detected a new signal anomaly in Block C.',
          type: 'warning',
          action: {
            label: 'View',
            onClick: () => { },
          },
        })
      },
    },
    {
      label: 'System Settings',
      icon: Settings,
      action: () => setIsStrataOpen(true),
    },
  ])

  // ─── Render ───

  return (
    <div
      className={cn(
        "h-screen w-screen flex flex-col text-slate-900 dark:text-slate-100 overflow-hidden transition-all duration-700 ease-in-out bg-cover bg-center",
        // Use the wallpaper's class if provided, otherwise default to a robust neutral
        activeWallpaper?.backgroundClassName || "bg-[#FEFCE8] dark:bg-slate-950"
      )}
      style={
        activeWallpaper?.imageUrl
          ? { backgroundImage: `url(${activeWallpaper.imageUrl})` }
          : undefined
      }
      onContextMenu={onContextMenu}
    >
      {/* Portals */}
      <ContextMenu />
      <NotificationCenter />
      <CommandPalette />

      {/* System Bar (top) */}
      <SystemBar
        onToggleConsole={() => { }} // No-op — console mode removed
        isConsoleOpen={!isDesktopRoute}
      />

      {/* Main Area: Sidebar + Content / Desktop */}
      <div className="flex-1 flex min-h-0 relative">





        {/* BijMantraVW watermark (desktop only) */}
        {isDesktopRoute && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center z-0">
            <div className="flex flex-col items-center gap-3 text-slate-600/40">
              <img src="/logo.png" alt="" className="h-20 w-20 opacity-40" />
              <div className="text-center">
                <p className="text-2xl font-semibold tracking-[0.18em]">BijMantraVW</p>
                <p className="text-xs uppercase tracking-[0.4em]">Agricultural Intelligence System</p>
              </div>
            </div>
          </div>
        )}

        {isDesktopRoute ? (
          // ─── Desktop Mode: Clean desktop with Dock + STRATA ───
          <div className="relative z-10 flex-1" />
        ) : (
          // ─── App Mode: Sidebar + Content ───
          <div className="relative z-10 flex flex-1 min-h-0">
            {/* Context sidebar */}
            <ShellSidebar />

            {/* Page content (rendered by React Router via children) */}
            <div className="flex-1 min-h-0 overflow-y-auto bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm">
              {children}
            </div>
          </div>
        )}
      </div>

      {/* STRATA Button — hidden on immersive routes to avoid overlap */}
      <button
        type="button"
        onClick={() => setIsStrataOpen(true)}
        className={cn(
          'fixed bottom-6 left-6 z-30 flex items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-700 shadow-lg backdrop-blur transition-all duration-200 hover:border-emerald-200 hover:text-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400 dark:border-slate-800/70 dark:bg-slate-900/70 dark:text-slate-200 dark:hover:border-emerald-700/60 dark:hover:text-emerald-200',
          isImmersiveRoute && 'pointer-events-none translate-y-20 opacity-0'
        )}
        aria-label="Open STRATA application launcher"
      >
        <Grid3X3 className="h-4 w-4" />
        STRATA
      </button>

      {/* Dock (bottom center) — DISABLED: blocks end-of-page content.
         Re-enable when we have a smarter auto-hide or edge-peek strategy.
         See docs/tasks/20260207.md Phase 0. */}
      {/* {!isImmersiveRoute && <Dock />} */}

      {/* STRATA Launcher Overlay */}
      <MahasarthiStrata isOpen={isStrataOpen} onClose={() => setIsStrataOpen(false)} />

      {/* REEVU AI Sidebar (lazy-loaded) */}
      <Suspense fallback={null}>
        <ReevuSidebar />
      </Suspense>
    </div>
  )
}
