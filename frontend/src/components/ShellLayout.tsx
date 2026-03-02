/**
 * ShellLayout — Minimal layout for Web-OS shell mode.
 * 
 * When pages are rendered inside BijMantraDesktop, the shell already provides:
 *   - SystemBar (top)
 *   - Context Sidebar (left, auto-detected from route)
 *   - Dock (bottom)
 *   - STRATA launcher
 *   - Notifications, Command Palette, Context Menu
 * 
 * So pages only need:
 *   - Breadcrumbs (for wayfinding)
 *   - The content itself
 *   - Error boundaries
 * 
 * This replaces the old Layout component when isInShell === true,
 * eliminating the awkward conditional hiding of ~15 Layout features.
 */

import { Suspense, Component, ReactNode } from 'react'
import { Breadcrumbs } from '@/components/navigation/MahasarthiBreadcrumbs'

// Error boundary for safety
class ShellErrorBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: ReactNode; fallback?: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center min-h-[200px] p-8">
          <div className="text-center space-y-2">
            <p className="text-sm font-medium text-red-600 dark:text-red-400">
              Something went wrong loading this page.
            </p>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 underline"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-600 dark:border-emerald-400" />
    </div>
  )
}

interface ShellLayoutProps {
  children: ReactNode
}

export function ShellLayout({ children }: ShellLayoutProps) {
  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Breadcrumbs bar */}
      <div className="flex items-center h-10 px-4 border-b border-slate-200/60 dark:border-slate-800/60 bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm flex-shrink-0">
        <ShellErrorBoundary>
          <Breadcrumbs />
        </ShellErrorBoundary>
      </div>

      {/* Page content */}
      <main
        id="main-content"
        className="flex-1 overflow-y-auto p-4 lg:p-6"
        tabIndex={-1}
      >
        <ShellErrorBoundary>
          <Suspense fallback={<LoadingSpinner />}>
            {children}
          </Suspense>
        </ShellErrorBoundary>
      </main>
    </div>
  )
}

export default ShellLayout
