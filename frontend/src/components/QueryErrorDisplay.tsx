/**
 * QueryErrorDisplay
 *
 * Drop-in replacement for inline error states in React Query pages.
 * Detects preview-environment 404s and renders PreviewUnavailable instead
 * of a raw error message.
 *
 * Usage:
 *   {error && <QueryErrorDisplay error={error} feature="Programs" onRetry={refetch} />}
 */

import { Button } from '@/components/ui/button'
import { PreviewUnavailable } from './PreviewUnavailable'
import { RefreshCw } from 'lucide-react'

interface QueryErrorDisplayProps {
  error: unknown
  /** Optional feature name shown in the preview message */
  feature?: string
  /** Optional retry callback */
  onRetry?: () => void
  className?: string
}

function isPreviewScopeError(error: unknown): boolean {
  if (!error) return false
  const msg = error instanceof Error ? error.message : String(error)
  return (
    msg.includes('not available in the current preview environment') ||
    msg.includes('full BijMantra platform') ||
    (error instanceof Error && 'statusCode' in error && (error as { statusCode?: number }).statusCode === 404)
  )
}

export function QueryErrorDisplay({ error, feature, onRetry, className = '' }: QueryErrorDisplayProps) {
  if (isPreviewScopeError(error)) {
    return <PreviewUnavailable feature={feature} className={className} />
  }

  const message = error instanceof Error ? error.message : 'An unexpected error occurred.'

  return (
    <div className={`flex min-h-[240px] flex-col items-center justify-center px-6 py-12 text-center ${className}`}>
      <div className="text-4xl mb-4">⚠️</div>
      <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100 mb-2">
        {feature ? `Error loading ${feature}` : 'Something went wrong'}
      </h3>
      <p className="max-w-sm text-sm text-slate-600 dark:text-slate-300 mb-6">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      )}
    </div>
  )
}

export default QueryErrorDisplay
