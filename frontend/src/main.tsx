import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/sonner'
import { SyncProvider } from '@/lib/sync/SyncProvider'
import App from './App.tsx'
// import App from './AppDebug.tsx'
import './index.css'

// Simplified initialization for debugging
console.log('[Bijmantra] Starting app...')

// Global error handler for uncaught errors
window.onerror = (message, source, lineno, colno, error) => {
  console.error('[Bijmantra] Global error:', { message, source, lineno, colno, error })
  const root = document.getElementById('root')
  if (root) {
    root.innerHTML = `
      <div style="padding: 20px; font-family: system-ui;">
        <h1 style="color: red;">JavaScript Error</h1>
        <p><strong>Message:</strong> ${message}</p>
        <p><strong>Source:</strong> ${source}</p>
        <p><strong>Line:</strong> ${lineno}, Column: ${colno}</p>
        <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">${error?.stack || 'No stack trace'}</pre>
        <button onclick="window.location.reload()">Reload</button>
      </div>
    `
  }
  return true
}

// Handle unhandled promise rejections
window.onunhandledrejection = (event) => {
  console.error('[Bijmantra] Unhandled promise rejection:', event.reason)
}

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
})

// Simple error boundary
class SimpleErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[Bijmantra] React Error:', error)
    console.error('[Bijmantra] Component Stack:', info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', fontFamily: 'system-ui' }}>
          <h1 style={{ color: 'red' }}>Something went wrong</h1>
          <pre style={{ background: '#f5f5f5', padding: '10px', overflow: 'auto' }}>
            {this.state.error?.message}
          </pre>
          <pre style={{ background: '#f5f5f5', padding: '10px', overflow: 'auto', fontSize: '12px' }}>
            {this.state.error?.stack}
          </pre>
          <button onClick={() => window.location.reload()}>Reload</button>
        </div>
      )
    }
    return this.props.children
  }
}

console.log('[Bijmantra] About to render...')
const rootElement = document.getElementById('root')
console.log('[Bijmantra] Root element:', rootElement)

if (!rootElement) {
  console.error('[Bijmantra] Root element not found!')
} else {
  try {
    const root = ReactDOM.createRoot(rootElement)
    console.log('[Bijmantra] Root created, rendering...')
    root.render(
      <React.StrictMode>
        <SimpleErrorBoundary>
          <QueryClientProvider client={queryClient}>
            <SyncProvider>
              <App />
            </SyncProvider>
            <Toaster richColors position="top-right" />
          </QueryClientProvider>
        </SimpleErrorBoundary>
      </React.StrictMode>,
    )
    console.log('[Bijmantra] Render called successfully')
  } catch (error) {
    console.error('[Bijmantra] Error during render:', error)
    rootElement.innerHTML = `
      <div style="padding: 20px; font-family: system-ui;">
        <h1 style="color: red;">Render Error</h1>
        <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">${error instanceof Error ? error.stack : String(error)}</pre>
        <button onclick="window.location.reload()">Reload</button>
      </div>
    `
  }
}

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
