import React from 'react';
import { useSync } from '../hooks';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export function SyncIndicator() {
  const { isOnline, isSyncing, pendingUploads, lastSyncTime, forceSync } = useSync();

  const formatLastSync = (timestamp: number | null) => {
    if (!timestamp) return 'Never';
    const diff = Date.now() - timestamp;
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return new Date(timestamp).toLocaleDateString();
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors border ${
            !isOnline
              ? 'bg-amber-100 text-amber-800 border-amber-200'
              : isSyncing
              ? 'bg-blue-100 text-blue-800 border-blue-200'
              : pendingUploads > 0
              ? 'bg-orange-100 text-orange-800 border-orange-200'
              : 'bg-green-100 text-green-800 border-green-200'
          }`}
        >
          {/* Status icon */}
          {!isOnline ? (
            <span role="img" aria-label="offline">📴</span>
          ) : isSyncing ? (
            <span className="animate-spin" role="img" aria-label="syncing">🔄</span>
          ) : pendingUploads > 0 ? (
            <span role="img" aria-label="pending">⏳</span>
          ) : (
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
          )}

          {/* Status text */}
          <span className="hidden sm:inline">
            {!isOnline
              ? 'Offline'
              : isSyncing
              ? 'Syncing...'
              : pendingUploads > 0
              ? `${pendingUploads} Unsynced`
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
              <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
              Offline Mode
            </>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {/* Sync status details */}
        <div className="px-2 py-2 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Unsynced changes</span>
            <span className={pendingUploads > 0 ? 'text-orange-600 font-medium' : 'text-gray-700'}>
              {pendingUploads}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Last sync</span>
            <span className="text-gray-700">{formatLastSync(lastSyncTime)}</span>
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
          {isSyncing ? 'Syncing...' : 'Force Sync'}
        </DropdownMenuItem>

        {!isOnline && (
          <div className="px-2 py-2 text-xs text-amber-700 bg-amber-50 rounded-md mx-2 mb-2">
            Your changes are saved to the queue and will upload automatically when online.
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
