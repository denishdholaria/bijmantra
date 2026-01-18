/**
 * PWA Install Prompt Component
 * 
 * Professional install prompt that:
 * - Captures beforeinstallprompt event (Chrome, Edge, Samsung)
 * - Shows iOS-specific instructions (Safari doesn't support beforeinstallprompt)
 * - Respects user dismissal (localStorage)
 * - Non-intrusive banner design
 * - Auto-hides if already installed
 */

import { useState, useEffect, useCallback } from 'react'
import { X, Download, Share, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISS_KEY = 'bijmantra-pwa-install-dismissed'
const DISMISS_DURATION = 7 * 24 * 60 * 60 * 1000 // 7 days

// Detect iOS (Safari doesn't support beforeinstallprompt)
const isIOS = () => {
  if (typeof navigator === 'undefined') return false
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as unknown as { MSStream?: unknown }).MSStream
}

// Detect if running as installed PWA
const isStandalone = () => {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(display-mode: standalone)').matches ||
         (window.navigator as unknown as { standalone?: boolean }).standalone === true
}

export function PWAInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [showBanner, setShowBanner] = useState(false)
  const [showIOSInstructions, setShowIOSInstructions] = useState(false)
  const [isInstalling, setIsInstalling] = useState(false)

  // Check if user dismissed recently
  const isDismissed = useCallback(() => {
    const dismissed = localStorage.getItem(DISMISS_KEY)
    if (!dismissed) return false
    const dismissedAt = parseInt(dismissed, 10)
    return Date.now() - dismissedAt < DISMISS_DURATION
  }, [])

  // Handle beforeinstallprompt event
  useEffect(() => {
    // Don't show if already installed or dismissed
    if (isStandalone() || isDismissed()) return

    const handleBeforeInstall = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      // Delay showing banner to not interrupt initial experience
      setTimeout(() => setShowBanner(true), 3000)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstall)

    // For iOS, show after delay if not dismissed
    if (isIOS() && !isDismissed()) {
      setTimeout(() => setShowBanner(true), 5000)
    }

    // Hide banner if app gets installed
    window.addEventListener('appinstalled', () => {
      setShowBanner(false)
      setDeferredPrompt(null)
    })

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
    }
  }, [isDismissed])

  // Handle install click
  const handleInstall = async () => {
    if (isIOS()) {
      setShowIOSInstructions(true)
      return
    }

    if (!deferredPrompt) return

    setIsInstalling(true)
    try {
      await deferredPrompt.prompt()
      const { outcome } = await deferredPrompt.userChoice
      
      if (outcome === 'accepted') {
        setShowBanner(false)
      }
      setDeferredPrompt(null)
    } catch {
      // User cancelled or error
    } finally {
      setIsInstalling(false)
    }
  }

  // Handle dismiss
  const handleDismiss = () => {
    localStorage.setItem(DISMISS_KEY, Date.now().toString())
    setShowBanner(false)
    setShowIOSInstructions(false)
  }

  // Don't render if nothing to show
  if (!showBanner || isStandalone()) return null

  return (
    <>
      {/* Install Banner */}
      <div
        className={cn(
          'fixed bottom-20 left-4 right-4 lg:bottom-6 lg:left-auto lg:right-6 lg:max-w-sm',
          'bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700',
          'p-4 z-50 animate-in slide-in-from-bottom-4 duration-300'
        )}
      >
        <button
          onClick={handleDismiss}
          className="absolute top-2 right-2 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
          aria-label="Dismiss install prompt"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-start gap-3 pr-6">
          {/* App Icon */}
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center flex-shrink-0">
            <span className="text-white text-lg font-bold">बी</span>
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
              Install Bijmantra
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {isIOS() 
                ? 'Add to Home Screen for quick access'
                : 'Install for offline field data collection'
              }
            </p>

            <div className="flex items-center gap-2 mt-3">
              <Button
                size="sm"
                onClick={handleInstall}
                disabled={isInstalling}
                className="h-8 text-xs bg-emerald-600 hover:bg-emerald-700"
              >
                {isInstalling ? (
                  <span className="animate-pulse">Installing...</span>
                ) : (
                  <>
                    <Download className="w-3.5 h-3.5 mr-1.5" />
                    Install
                  </>
                )}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDismiss}
                className="h-8 text-xs text-slate-500"
              >
                Not now
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* iOS Instructions Modal */}
      {showIOSInstructions && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-end lg:items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-800 rounded-t-2xl lg:rounded-2xl w-full max-w-md p-6 animate-in slide-in-from-bottom duration-300">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg text-slate-900 dark:text-slate-100">
                Install on iOS
              </h3>
              <button
                onClick={() => setShowIOSInstructions(false)}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg"
                aria-label="Close instructions"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
                  <Share className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100 text-sm">
                    1. Tap the Share button
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Located at the bottom of Safari
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
                  <Plus className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100 text-sm">
                    2. Tap "Add to Home Screen"
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Scroll down in the share menu if needed
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center flex-shrink-0">
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold text-sm">✓</span>
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100 text-sm">
                    3. Tap "Add"
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Bijmantra will appear on your home screen
                  </p>
                </div>
              </div>
            </div>

            <Button
              onClick={() => setShowIOSInstructions(false)}
              className="w-full mt-6 bg-emerald-600 hover:bg-emerald-700"
            >
              Got it
            </Button>
          </div>
        </div>
      )}
    </>
  )
}

/**
 * Hook to check PWA install state
 * Useful for conditionally showing install-related UI elsewhere
 */
export function usePWAInstall() {
  const [canInstall, setCanInstall] = useState(false)
  const [isInstalled, setIsInstalled] = useState(false)

  useEffect(() => {
    setIsInstalled(isStandalone())

    const handleBeforeInstall = () => setCanInstall(true)
    const handleInstalled = () => {
      setIsInstalled(true)
      setCanInstall(false)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstall)
    window.addEventListener('appinstalled', handleInstalled)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
      window.removeEventListener('appinstalled', handleInstalled)
    }
  }, [])

  return { canInstall, isInstalled, isIOS: isIOS() }
}
