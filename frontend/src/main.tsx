import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/sonner'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { initSentry } from '@/lib/sentry'
import { initPostHog } from '@/lib/posthog'
import { initWebGPU } from '@/lib/webgpu'
import App from './App.tsx'
import './index.css'

// Initialize monitoring and analytics
initSentry()
initPostHog()

// Initialize WebGPU for genomics acceleration (async, non-blocking)
initWebGPU().then((capabilities) => {
  if (capabilities.available) {
    console.log('[Bijmantra] WebGPU available for genomics acceleration')
  }
})

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: false, // Don't retry failed requests (backend might not be running)
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <App />
        <Toaster richColors position="top-right" />
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)

// Register service worker for PWA (only in production)
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then(
      (registration) => {
        console.log('SW registered:', registration)
      },
      (error) => {
        console.log('SW registration failed:', error)
      },
    )
  })
}
