/**
 * Offline Indicator Component
 * Shows network status and offline capabilities
 */
import { useState, useEffect } from 'react'
import { toast } from 'sonner'

export function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [showBanner, setShowBanner] = useState(false)

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      toast.success('Back online! Syncing data...')
      setShowBanner(false)
    }

    const handleOffline = () => {
      setIsOnline(false)
      toast.warning('You are offline. Changes will sync when connected.')
      setShowBanner(true)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (isOnline && !showBanner) return null

  return (
    <div className={`fixed bottom-4 left-4 z-50 transition-all ${showBanner ? 'translate-y-0' : 'translate-y-20'}`}>
      <div className={`flex items-center gap-2 px-4 py-2 rounded-lg shadow-lg ${
        isOnline ? 'bg-green-500 text-white' : 'bg-yellow-500 text-yellow-900'
      }`}>
        <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-200' : 'bg-yellow-200'} animate-pulse`} />
        <span className="text-sm font-medium">
          {isOnline ? 'Online' : 'Offline Mode'}
        </span>
        {!isOnline && (
          <button 
            onClick={() => setShowBanner(false)}
            className="ml-2 text-yellow-900/70 hover:text-yellow-900"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  )
}

export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return isOnline
}
