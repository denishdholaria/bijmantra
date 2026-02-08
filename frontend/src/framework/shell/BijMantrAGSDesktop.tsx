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

const VeenaSidebar = lazy(() =>
  import('@/components/ai/VeenaSidebar').then((m) => ({ default: m.VeenaSidebar }))
)

// ============================================================================
// Wallpaper Configuration
// ============================================================================

type WallpaperOption = {
  id: string
  name: string
  description: string
  backgroundClassName?: string
  previewClassName?: string
  imageUrl?: string
}

const wallpaperOptions: WallpaperOption[] = [
  {
    id: 'bijmantrags',
    name: 'BijMantraGS',
    description: 'Signature system mark',
    backgroundClassName: 'bg-gradient-to-br from-[#f7efe3] via-[#f4e8d8] to-[#efe0c8]',
    previewClassName: 'bg-gradient-to-br from-[#f7efe3] via-[#f4e8d8] to-[#efe0c8]',
  },
  {
    id: 'field-dawn',
    name: 'Field Dawn',
    description: 'Soft sunrise over soil textures',
    backgroundClassName: 'bg-gradient-to-br from-[#f5efe4] via-[#f1eadf] to-[#e7dcc7]',
    previewClassName: 'bg-gradient-to-br from-[#f5efe4] via-[#f1eadf] to-[#e7dcc7]',
  },
  {
    id: 'canopy-dusk',
    name: 'Canopy Dusk',
    description: 'Cool canopy gradients for focus',
    backgroundClassName: 'bg-gradient-to-br from-[#eff4f6] via-[#e3edf1] to-[#d7e5ec]',
    previewClassName: 'bg-gradient-to-br from-[#eff4f6] via-[#e3edf1] to-[#d7e5ec]',
  },
  {
    id: 'monsoon',
    name: 'Monsoon',
    description: 'Deep greens with rainfall calm',
    backgroundClassName: 'bg-gradient-to-br from-[#edf3ee] via-[#e2ece5] to-[#d2e0d7]',
    previewClassName: 'bg-gradient-to-br from-[#edf3ee] via-[#e2ece5] to-[#d2e0d7]',
  },
]

// ============================================================================
// Desktop Routes — routes that show the wallpaper + shortcuts instead of app content
// ============================================================================

const DESKTOP_ROUTES = new Set(['/', '/gateway', '/dashboard'])

/** Routes where the Dock + STRATA auto-hide to avoid overlapping bottom-anchored content. */
const IMMERSIVE_ROUTES = new Set(['/veena', '/ai-assistant'])

// ============================================================================
// BijMantrAGSDesktop — Unified Web-OS Shell
// ============================================================================

type BijMantrAGSDesktopProps = {
  children?: ReactNode
}

export function BijMantrAGSDesktop({ children }: BijMantrAGSDesktopProps) {
  const {
    isInShell,
    setIsInShell,
    activeWallpaperId,
    setActiveWallpaperId,
    customWallpaperUrl,
    setCustomWallpaperUrl,
  } = useSystemStore()

  const location = useLocation()
  const [isStrataOpen, setIsStrataOpen] = useState(false)
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

  // ─── Handlers ───

  const handleWallpaperChange = (id: string) => {
    setActiveWallpaperId(id)
  }

  const handleWallpaperUpload = (file: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = typeof reader.result === 'string' ? reader.result : null
      if (result) {
        setCustomWallpaperUrl(result)
        setActiveWallpaperId('custom')
      }
    }
    reader.readAsDataURL(file)
  }

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
    { separator: true, label: '', action: () => {} },
    {
      label: 'Test Notification',
      icon: Image,
      action: () => {
        addNotification({
          title: 'System Alert',
          message: 'Veena has detected a new signal anomaly in Block C.',
          type: 'warning',
          action: {
            label: 'View',
            onClick: () => console.log('View clicked'),
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
      className="h-screen w-screen flex flex-col text-slate-900 dark:text-slate-100 overflow-hidden"
      onContextMenu={onContextMenu}
    >
      {/* Portals */}
      <ContextMenu />
      <NotificationCenter />
      <CommandPalette />

      {/* System Bar (top) */}
      <SystemBar
        onToggleConsole={() => {}} // No-op — console mode removed
        isConsoleOpen={!isDesktopRoute}
        wallpapers={allWallpapers}
        activeWallpaperId={activeWallpaperId}
        onWallpaperChange={handleWallpaperChange}
        onWallpaperUpload={handleWallpaperUpload}
      />

      {/* Main Area: Sidebar + Content / Desktop */}
      <div className="flex-1 flex min-h-0 relative">
        {/* Wallpaper background (always rendered, visible on desktop routes) */}
        <div
          className={`absolute inset-0 transition-opacity duration-300 ${
            isDesktopRoute ? 'opacity-100' : 'opacity-0 pointer-events-none'
          } ${activeWallpaper?.backgroundClassName ?? ''}`}
          style={
            activeWallpaper?.imageUrl
              ? {
                  backgroundImage: `url(${activeWallpaper.imageUrl})`,
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                }
              : undefined
          }
          aria-hidden="true"
        />

        {/* BijMantraGS watermark (desktop only) */}
        {isDesktopRoute && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center z-0">
            <div className="flex flex-col items-center gap-3 text-slate-600/40">
              <img src="/logo.png" alt="" className="h-20 w-20 opacity-40" />
              <div className="text-center">
                <p className="text-2xl font-semibold tracking-[0.18em]">BijMantraGS</p>
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

      {/* Veena AI Sidebar (lazy-loaded) */}
      <Suspense fallback={null}>
        <VeenaSidebar />
      </Suspense>
    </div>
  )
}
