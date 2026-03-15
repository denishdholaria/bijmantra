/**
 * Sync Status Indicator Component
 * Shows offline/online status and pending sync changes
 */

import { useSync } from '@/lib/sync/hooks'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function SyncStatusIndicator() {
  const { isOnline, isSyncing, pendingUploads: pendingChanges, lastSyncTime, forceSync } = useSync()

  const formatLastSync = (timestamp: number | null) => {
    if (!timestamp) return 'Never'
    const diff = Date.now() - timestamp
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return new Date(timestamp).toLocaleDateString()
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium transition-colors ${
            !isOnline
              ? 'bg-prakruti-sona-pale text-prakruti-sona-dark dark:bg-prakruti-sona/15 dark:text-prakruti-sona-light'
              : isSyncing
              ? 'bg-prakruti-neela-pale text-prakruti-neela-dark dark:bg-prakruti-neela/15 dark:text-prakruti-neela-light'
              : pendingChanges > 0
              ? 'bg-prakruti-narangi-pale text-prakruti-narangi-dark dark:bg-prakruti-narangi/15 dark:text-prakruti-narangi-light'
              : 'bg-prakruti-patta-pale text-prakruti-patta-dark dark:bg-prakruti-patta/15 dark:text-prakruti-patta-light'
          }`}
        >
          {/* Status icon */}
          {!isOnline ? (
            <span>📴</span>
          ) : isSyncing ? (
            <span className="animate-spin">🔄</span>
          ) : pendingChanges > 0 ? (
            <span>⏳</span>
          ) : (
            <span className="bg-prakruti-patta h-2 w-2 rounded-full"></span>
          )}

          {/* Status text */}
          <span className="hidden sm:inline">
            {!isOnline
              ? 'Offline'
              : isSyncing
              ? 'Syncing...'
              : pendingChanges > 0
              ? `${pendingChanges} pending`
              : 'Synced'}
          </span>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="flex items-center gap-2">
          {isOnline ? (
            <>
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              Online
            </>
          ) : (
            <>
              <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
              Offline Mode
            </>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {/* Sync status details */}
        <div className="px-2 py-2 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-safe">Pending changes</span>
            <span className={pendingChanges > 0 ? 'text-prakruti-narangi dark:text-prakruti-narangi-light font-medium' : 'text-body'}>
              {pendingChanges}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-safe">Last sync</span>
            <span className="text-body">{formatLastSync(lastSyncTime)}</span>
          </div>
        </div>

        <DropdownMenuSeparator />

        {/* Actions */}
        <DropdownMenuItem
          onClick={() => forceSync()}
          disabled={!isOnline || isSyncing}
          className="cursor-pointer"
        >
          <span className="mr-2">🔄</span>
          {isSyncing ? 'Syncing...' : 'Sync Now'}
        </DropdownMenuItem>

        {!isOnline && (
          <div className="bg-prakruti-sona-pale text-prakruti-sona-dark dark:bg-prakruti-sona/15 dark:text-prakruti-sona-light mx-2 mb-2 rounded-md px-2 py-2 text-xs">
            💡 Your changes are saved locally and will sync when you're back online.
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/**
 * Compact sync indicator for tight spaces
 */
export function SyncDot() {
  const { isOnline, isSyncing, pendingUploads: pendingChanges } = useSync()

  return (
    <span
      className={`w-2 h-2 rounded-full ${
        !isOnline
          ? 'bg-yellow-500'
          : isSyncing
          ? 'bg-blue-500 animate-pulse'
          : pendingChanges > 0
          ? 'bg-orange-500'
          : 'bg-green-500'
      }`}
      title={
        !isOnline
          ? 'Offline'
          : isSyncing
          ? 'Syncing...'
          : pendingChanges > 0
          ? `${pendingChanges} pending changes`
          : 'Synced'
      }
    />
  )
}

/**
 * Offline banner for prominent display
 */
export function OfflineBanner() {
  const { isOnline, pendingUploads: pendingChanges } = useSync()

  if (isOnline) return null

  return (
    <div className="bg-prakruti-sona-pale text-prakruti-sona-dark dark:bg-prakruti-sona/15 dark:text-prakruti-sona-light border-b border-prakruti-sona/20 px-4 py-2 flex items-center justify-center gap-2 text-sm">
      <span>📴</span>
      <span>
        You're offline. {pendingChanges > 0 && `${pendingChanges} changes will sync when you reconnect.`}
      </span>
    </div>
  )
}
