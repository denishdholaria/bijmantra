import type { ReactNode } from 'react'
import { useCallback, useContext, useEffect, useState } from 'react'
import { useSystemStore } from '@/store/systemStore'
import { Grid3X3, RefreshCw, Sparkles, Settings } from 'lucide-react'
import { UNSAFE_NavigationContext, useBeforeUnload, useLocation } from 'react-router-dom'
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
import { ShellSubsystemBoundary } from './ShellSubsystemBoundary'
import { DesktopWorkbench } from './DesktopWorkbench'

const ReevuSidebar = lazy(() =>
  import('@/components/ai/ReevuSidebar').then((m) => ({ default: m.ReevuSidebar }))
)

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

type BlockableNavigator = {
  block?: (blocker: (transition: { retry: () => void }) => void) => () => void
}

export function BijMantraDesktop({ children }: BijMantraDesktopProps) {
  const setIsInShell = useSystemStore((state) => state.setIsInShell)
  const navigationContext = useContext(UNSAFE_NavigationContext)

  const location = useLocation()
  const isStrataOpen = useSystemStore((state) => state.isStrataOpen)
  const setStrataOpen = useSystemStore((state) => state.setStrataOpen)
  const desktopToolSurface = useSystemStore((state) => state.desktopToolSurface)
  const lastDesktopToolSurface = useSystemStore((state) => state.lastDesktopToolSurface)
  const openDesktopTool = useSystemStore((state) => state.openDesktopTool)
  const closeDesktopTool = useSystemStore((state) => state.closeDesktopTool)
  const [hasUnsavedWorkbenchChanges, setHasUnsavedWorkbenchChanges] = useState(false)
  const [hasRestoredDesktopTool, setHasRestoredDesktopTool] = useState(false)

  const setIsStrataOpen = (open: boolean) => {
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

  useEffect(() => {
    if (!hasUnsavedWorkbenchChanges) {
      return
    }

    const navigator = navigationContext?.navigator as BlockableNavigator | undefined
    const blocker = navigator?.block?.((transition: { retry: () => void }) => {
      const shouldProceed = window.confirm('Leaving the desktop will discard unsaved changes. Continue?')
      if (!shouldProceed) {
        return
      }

      blocker?.()
      transition.retry()
    })

    return () => {
      blocker?.()
    }
  }, [hasUnsavedWorkbenchChanges, navigationContext])

  useBeforeUnload(
    useCallback(
      (event) => {
        if (!hasUnsavedWorkbenchChanges) {
          return
        }

        event.preventDefault()
        event.returnValue = ''
      },
      [hasUnsavedWorkbenchChanges]
    )
  )

  useEffect(() => {
    if (!isDesktopRoute) {
      setHasRestoredDesktopTool(false)
      return
    }

    if (hasRestoredDesktopTool || desktopToolSurface || !lastDesktopToolSurface) {
      return
    }

    openDesktopTool(lastDesktopToolSurface)
    setHasRestoredDesktopTool(true)
  }, [desktopToolSurface, hasRestoredDesktopTool, isDesktopRoute, lastDesktopToolSurface, openDesktopTool])

  useEffect(() => {
    if (!isDesktopRoute && desktopToolSurface) {
      closeDesktopTool()
    }
  }, [closeDesktopTool, desktopToolSurface, isDesktopRoute])

  // ─── Context Menu ───

  const { onContextMenu } = useContextMenu([
    {
      label: 'Refresh Desktop',
      icon: RefreshCw,
      action: () => window.location.reload(),
      shortcut: '⌘R',
    },
    { separator: true, label: '', action: () => { } },
    {
      label: 'Test Notification',
      icon: Sparkles,
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
        'app-theme-bridge desktop-stage h-screen w-screen flex flex-col overflow-hidden text-shell transition-all duration-700 ease-in-out'
      )}
      onContextMenu={onContextMenu}
    >
      {/* Portals */}
      <ShellSubsystemBoundary name="ContextMenu" fallback={null}>
        <ContextMenu />
      </ShellSubsystemBoundary>
      <ShellSubsystemBoundary name="NotificationCenter" fallback={null}>
        <NotificationCenter />
      </ShellSubsystemBoundary>
      <ShellSubsystemBoundary name="CommandPalette" fallback={null}>
        <CommandPalette />
      </ShellSubsystemBoundary>

      {/* System Bar (top) */}
      <ShellSubsystemBoundary
        name="SystemBar"
        fallback={(
          <div className="bg-shell-chrome border-shell relative z-50 flex h-14 items-center justify-center border-b px-4 text-xs text-shell-muted backdrop-blur-xl sm:px-6 flex-shrink-0">
            System bar unavailable
          </div>
        )}
      >
        <SystemBar
          onToggleConsole={() => { }} // No-op — console mode removed
          isConsoleOpen={!isDesktopRoute}
        />
      </ShellSubsystemBoundary>

      {/* Main Area: Sidebar + Content / Desktop */}
      <div className="flex-1 flex min-h-0 relative">





        {/* BijMantra watermark (desktop only) */}
        {isDesktopRoute && (
          <div className="pointer-events-none absolute inset-0 z-0 flex items-center justify-center overflow-hidden">
            <div className="desktop-brand-halo" aria-hidden="true" />
            <div className="desktop-brand-orbit" aria-hidden="true" />
            <div className="desktop-brand-grid" aria-hidden="true" />
            <div className="desktop-brand-focus-frame" aria-hidden="true" />
            <div className="desktop-brand-lockup flex flex-col items-center gap-4">
              <div className="desktop-brand-mark">
                <img src="/logo.png" alt="" className="h-24 w-24 opacity-95 drop-shadow-[0_14px_30px_rgba(0,0,0,0.18)]" />
              </div>
              <div className="text-center">
                <p className="desktop-brand-title text-3xl font-semibold tracking-[0.24em]">BijMantra</p>
                <div className="desktop-brand-divider" aria-hidden="true" />
                <p className="desktop-brand-subtitle mt-2 text-xs uppercase tracking-[0.48em]">Agricultural Intelligence System</p>
              </div>
            </div>
          </div>
        )}

        {isDesktopRoute ? (
          // ─── Desktop Mode: Calm default stage with on-demand tools ───
          <div className="relative z-10 flex flex-1 min-h-0">
            <DesktopWorkbench
              surface={desktopToolSurface}
              onClose={closeDesktopTool}
              onOpenSurface={openDesktopTool}
              onDirtyStateChange={setHasUnsavedWorkbenchChanges}
            />
          </div>
        ) : (
          // ─── App Mode: Sidebar + Content ───
          <div className="relative z-10 flex flex-1 min-h-0">
            {/* Context sidebar */}
            <ShellSubsystemBoundary
              name="ShellSidebar"
              fallback={<aside className="bg-shell-chrome border-shell w-14 h-full border-r flex-shrink-0" aria-hidden="true" />}
            >
              <ShellSidebar />
            </ShellSubsystemBoundary>

            {/* Page content (rendered by React Router via children) */}
            <div className="bg-shell-panel border-shell shadow-shell flex-1 min-h-0 overflow-y-auto border-l">
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
          'bg-shell-chrome border-shell shadow-shell fixed bottom-6 left-6 z-30 flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-shell transition-all duration-200 hover:text-prakruti-patta dark:hover:text-prakruti-patta-light focus-visible:outline focus-visible:outline-2 focus-visible:outline-[hsl(var(--ring))]',
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
      <ShellSubsystemBoundary name="MahasarthiStrata" fallback={null}>
        <MahasarthiStrata isOpen={isStrataOpen} onClose={() => setIsStrataOpen(false)} />
      </ShellSubsystemBoundary>

      {/* REEVU AI Sidebar (lazy-loaded) */}
      <ShellSubsystemBoundary name="ReevuSidebar" fallback={null}>
        <Suspense fallback={null}>
          <ReevuSidebar />
        </Suspense>
      </ShellSubsystemBoundary>
    </div>
  )
}
