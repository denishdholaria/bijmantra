import { useEffect, useState } from 'react'

export function useWorkbenchRuntime() {
  const [runtimeSnapshot, setRuntimeSnapshot] = useState(() => ({
    online: typeof navigator !== 'undefined' ? navigator.onLine : true,
    language: typeof navigator !== 'undefined' ? navigator.language : 'en-US',
    platform: typeof navigator !== 'undefined' ? navigator.platform : 'unknown',
    viewport: {
      width: typeof window !== 'undefined' ? window.innerWidth : 0,
      height: typeof window !== 'undefined' ? window.innerHeight : 0,
    },
  }))

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const handleResize = () => {
      setRuntimeSnapshot((prev) => ({
        ...prev,
        viewport: { width: window.innerWidth, height: window.innerHeight },
      }))
    }
    const handleOnline = () => {
      setRuntimeSnapshot((prev) => ({ ...prev, online: true }))
    }
    const handleOffline = () => {
      setRuntimeSnapshot((prev) => ({ ...prev, online: false }))
    }

    window.addEventListener('resize', handleResize)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return runtimeSnapshot
}
