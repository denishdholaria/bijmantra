/**
 * Toast Container Component
 * Renders all active toast notifications
 */

import { useToastStore, Toast, ToastType } from '@/hooks/useToast'

const TOAST_ICONS: Record<ToastType, string> = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️',
  loading: '⏳',
}

const TOAST_COLORS: Record<ToastType, string> = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  loading: 'bg-gray-50 border-gray-200 text-gray-800',
}

function ToastItem({ toast }: { toast: Toast }) {
  const { removeToast } = useToastStore()

  return (
    <div
      className={`
        flex items-start gap-3 p-4 rounded-lg border shadow-lg
        animate-slide-in max-w-sm w-full
        ${TOAST_COLORS[toast.type]}
      `}
      role="alert"
    >
      {/* Icon */}
      <span className="text-lg flex-shrink-0">
        {toast.type === 'loading' ? (
          <span className="inline-block animate-spin">⏳</span>
        ) : (
          TOAST_ICONS[toast.type]
        )}
      </span>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{toast.title}</p>
        {toast.description && (
          <p className="text-sm opacity-80 mt-0.5">{toast.description}</p>
        )}
        {toast.action && (
          <button
            onClick={toast.action.onClick}
            className="text-sm font-medium underline mt-1 hover:no-underline"
          >
            {toast.action.label}
          </button>
        )}
      </div>

      {/* Dismiss button */}
      {toast.dismissible && toast.type !== 'loading' && (
        <button
          onClick={() => removeToast(toast.id)}
          className="flex-shrink-0 p-1 rounded hover:bg-black/5 transition-colors"
          aria-label="Dismiss"
        >
          <span className="text-sm">✕</span>
        </button>
      )}
    </div>
  )
}

export function ToastContainer() {
  const { toasts } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div
      className="fixed bottom-4 right-4 z-[200] flex flex-col gap-2"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  )
}
