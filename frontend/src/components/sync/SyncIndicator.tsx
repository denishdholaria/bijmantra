/**
 * Sync Indicator
 * 
 * Compact sync status indicator for the navbar/header.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  AlertTriangle,
  Check,
  Cloud,
  CloudOff,
  RefreshCw,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useSync, useSyncStatus } from '@/framework/sync/hooks';

interface SyncIndicatorProps {
  onOpenSyncPanel?: () => void;
}

export function SyncIndicator({ onOpenSyncPanel }: SyncIndicatorProps) {
  const { isOnline, isSyncing, pendingCount, sync } = useSync();
  const { status } = useSyncStatus();
  const [open, setOpen] = useState(false);

  const handleSync = async () => {
    await sync();
  };

  const getStatusIcon = () => {
    if (isSyncing) {
      return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />;
    }
    if (!isOnline) {
      return <WifiOff className="h-4 w-4 text-gray-500" />;
    }
    if (pendingCount > 0) {
      return <Cloud className="h-4 w-4 text-yellow-500" />;
    }
    return <Check className="h-4 w-4 text-green-500" />;
  };

  const getStatusText = () => {
    if (isSyncing) return 'Syncing...';
    if (!isOnline) return 'Offline';
    if (pendingCount > 0) return `${pendingCount} pending`;
    return 'Synced';
  };

  const getStatusColor = () => {
    if (isSyncing) return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
    if (!isOnline) return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
    if (pendingCount > 0) return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300';
    return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={`h-8 px-2 gap-1.5 ${getStatusColor()}`}
        >
          {getStatusIcon()}
          <span className="text-xs hidden sm:inline">{getStatusText()}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-3" align="end">
        <div className="space-y-3">
          {/* Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isOnline ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-gray-500" />
              )}
              <span className="font-medium">
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSync}
              disabled={!isOnline || isSyncing}
            >
              <RefreshCw className={`h-3 w-3 mr-1 ${isSyncing ? 'animate-spin' : ''}`} />
              Sync
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="p-2 bg-muted rounded">
              <div className="text-lg font-bold">{pendingCount}</div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </div>
            <div className="p-2 bg-muted rounded">
              <div className="text-lg font-bold flex items-center justify-center">
                {status === 'synced' ? (
                  <Check className="h-5 w-5 text-green-500" />
                ) : status === 'offline' ? (
                  <CloudOff className="h-5 w-5 text-gray-500" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                )}
              </div>
              <div className="text-xs text-muted-foreground">Status</div>
            </div>
          </div>

          {/* Actions */}
          {onOpenSyncPanel && (
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => {
                setOpen(false);
                onOpenSyncPanel();
              }}
            >
              View Sync Details
            </Button>
          )}

          {/* Offline Notice */}
          {!isOnline && (
            <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
              Changes will sync automatically when you're back online.
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
