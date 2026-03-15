import type { ReactNode } from 'react'
import { ErrorBoundary, type FallbackProps } from 'react-error-boundary'

type ShellSubsystemBoundaryProps = {
  name: string
  children: ReactNode
  fallback?: ReactNode
}

function DefaultFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div className="border-shell bg-shell-panel text-shell-muted m-2 rounded-2xl border px-3 py-2 text-xs shadow-sm">
      <div className="font-medium text-shell">Shell component unavailable</div>
      <div className="mt-1 break-words">{error instanceof Error ? error.message : String(error)}</div>
      <button
        type="button"
        onClick={resetErrorBoundary}
        className="mt-2 rounded-xl bg-[hsl(var(--app-shell-panel))] px-3 py-1.5 text-[11px] font-medium text-shell transition-colors hover:bg-[hsl(var(--accent))]"
      >
        Retry
      </button>
    </div>
  )
}

function createFallback(name: string, fallback?: ReactNode) {
  return function ShellSubsystemFallback(props: FallbackProps) {
    if (fallback !== undefined) {
      return <>{fallback}</>
    }

    console.error(`[ShellBoundary:${name}]`, props.error)
    return <DefaultFallback {...props} />
  }
}

export function ShellSubsystemBoundary({
  name,
  children,
  fallback,
}: ShellSubsystemBoundaryProps) {
  const FallbackComponent = createFallback(name, fallback)

  return (
    <ErrorBoundary
      FallbackComponent={FallbackComponent}
      onError={(error) => {
        console.error(`[ShellBoundary:${name}]`, error)
      }}
    >
      {children}
    </ErrorBoundary>
  )
}