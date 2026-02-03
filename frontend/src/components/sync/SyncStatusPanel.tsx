/**
 * Sync Status Panel
 * 
 * Shows sync status, pending changes, and conflict resolution UI.
 */

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import {
  AlertTriangle,
  Check,
  Cloud,
  CloudOff,
  RefreshCw,
  Trash2,
  Upload,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useSync, useSyncStatus } from '@/framework/sync/hooks';
import { db, PendingSyncOperation, SyncLogEntry } from '@/framework/sync/db';
import { ConflictResolutionDialog, ConflictData } from './ConflictResolutionDialog';

export function SyncStatusPanel() {
  const { isOnline, isSyncing, pendingCount, lastSyncResult, sync } = useSync();
  const { status, statusText, statusColor } = useSyncStatus();
  const [pendingOps, setPendingOps] = useState<PendingSyncOperation[]>([]);
  const [syncLogs, setSyncLogs] = useState<SyncLogEntry[]>([]);
  const [conflicts, setConflicts] = useState<ConflictData[]>([]);
  const [selectedConflict, setSelectedConflict] = useState<ConflictData | null>(null);
  const [conflictDialogOpen, setConflictDialogOpen] = useState(false);

  // Load pending operations and sync logs
  useEffect(() => {
    const loadData = async () => {
      const ops = await db.pendingSync.toArray();
      setPendingOps(ops);

      const logs = await db.syncLog.orderBy('timestamp').reverse().limit(10).toArray();
      setSyncLogs(logs);

      // Check for conflicts in all entity tables
      const conflictItems: ConflictData[] = [];
      const entityTypes = ['programs', 'trials', 'studies', 'germplasm', 'observations', 'traits'];
      
      for (const entityType of entityTypes) {
        const table = (db as any)[entityType];
        if (table) {
          const conflicted = await table.where('_syncStatus').equals('conflict').toArray();
          for (const item of conflicted) {
            conflictItems.push({
              id: `${entityType}-${item.id}`,
              entityType,
              entityId: item.id,
              localData: item._localChanges || item,
              serverData: item,
              localTimestamp: item._updatedAt,
              serverTimestamp: item._lastSyncAt || item._updatedAt,
              conflictFields: Object.keys(item._localChanges || {}),
            });
          }
        }
      }
      setConflicts(conflictItems);
    };

    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSync = async () => {
    await sync();
  };

  const handleClearPending = async (id: number) => {
    await db.pendingSync.delete(id);
    const ops = await db.pendingSync.toArray();
    setPendingOps(ops);
  };

  const handleResolveConflict = async (
    resolution: 'local' | 'server' | 'merge',
    mergedData?: Record<string, unknown>
  ) => {
    if (!selectedConflict) return;

    const table = (db as any)[selectedConflict.entityType];
    if (!table) return;

    if (resolution === 'local') {
      // Keep local version, mark for push
      await table.update(selectedConflict.entityId, {
        _syncStatus: 'pending',
      });
    } else if (resolution === 'server') {
      // Accept server version
      await table.update(selectedConflict.entityId, {
        ...selectedConflict.serverData,
        _syncStatus: 'synced',
        _localChanges: undefined,
      });
    } else if (resolution === 'merge' && mergedData) {
      // Apply merged data
      await table.update(selectedConflict.entityId, {
        ...mergedData,
        _syncStatus: 'pending',
        _localChanges: undefined,
      });
    }

    setConflictDialogOpen(false);
    setSelectedConflict(null);
    
    // Refresh conflicts list
    const remaining = conflicts.filter(c => c.id !== selectedConflict.id);
    setConflicts(remaining);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const getOperationBadge = (op: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive'> = {
      create: 'default',
      update: 'secondary',
      delete: 'destructive',
    };
    return <Badge variant={variants[op] || 'default'}>{op}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isOnline ? (
                <Wifi className="h-5 w-5 text-green-500" />
              ) : (
                <WifiOff className="h-5 w-5 text-gray-500" />
              )}
              <div>
                <CardTitle className="text-lg">Sync Status</CardTitle>
                <CardDescription className={statusColor}>{statusText}</CardDescription>
              </div>
            </div>
            <Button
              onClick={handleSync}
              disabled={!isOnline || isSyncing}
              size="sm"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`} />
              {isSyncing ? 'Syncing...' : 'Sync Now'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{pendingCount}</div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </div>
            <div className="p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{conflicts.length}</div>
              <div className="text-xs text-muted-foreground">Conflicts</div>
            </div>
            <div className="p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{lastSyncResult?.pushed || 0}</div>
              <div className="text-xs text-muted-foreground">Last Pushed</div>
            </div>
            <div className="p-3 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{lastSyncResult?.pulled || 0}</div>
              <div className="text-xs text-muted-foreground">Last Pulled</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Conflicts Section */}
      {conflicts.length > 0 && (
        <Card className="border-yellow-200 dark:border-yellow-800">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              <CardTitle className="text-lg">Conflicts ({conflicts.length})</CardTitle>
            </div>
            <CardDescription>
              These items have conflicting changes. Resolve them to continue syncing.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[200px]">
              <div className="space-y-2">
                {conflicts.map(conflict => (
                  <div
                    key={conflict.id}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
                    onClick={() => {
                      setSelectedConflict(conflict);
                      setConflictDialogOpen(true);
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      <div>
                        <div className="font-medium">{conflict.entityType}</div>
                        <div className="text-xs text-muted-foreground font-mono">
                          {conflict.entityId}
                        </div>
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {conflict.conflictFields.length} field(s)
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Pending Operations */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Upload className="h-5 w-5 text-blue-500" />
            <CardTitle className="text-lg">Pending Changes ({pendingOps.length})</CardTitle>
          </div>
          <CardDescription>
            Local changes waiting to be synced to the server.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {pendingOps.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Cloud className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>All changes synced</p>
            </div>
          ) : (
            <ScrollArea className="h-[200px]">
              <div className="space-y-2">
                {pendingOps.map(op => (
                  <div
                    key={op.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {getOperationBadge(op.operation)}
                      <div>
                        <div className="font-medium">{op.entityType}</div>
                        <div className="text-xs text-muted-foreground font-mono">
                          {op.entityId}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {op.retryCount > 0 && (
                        <Badge variant="outline" className="text-yellow-500">
                          Retry {op.retryCount}
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {formatDate(op.createdAt)}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => op.id && handleClearPending(op.id)}
                        aria-label="Remove pending operation"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Sync History */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Sync History</CardTitle>
          <CardDescription>Recent synchronization operations.</CardDescription>
        </CardHeader>
        <CardContent>
          {syncLogs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CloudOff className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No sync history yet</p>
            </div>
          ) : (
            <ScrollArea className="h-[150px]">
              <div className="space-y-2">
                {syncLogs.map(log => (
                  <div
                    key={log.id}
                    className="flex items-center justify-between p-2 border rounded"
                  >
                    <div className="flex items-center gap-2">
                      {log.recordsFailed === 0 ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      )}
                      <Badge variant="outline">{log.direction}</Badge>
                      <span className="text-sm">
                        {log.recordsProcessed} records
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatDate(log.timestamp)}
                    </span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Conflict Resolution Dialog */}
      <ConflictResolutionDialog
        open={conflictDialogOpen}
        onOpenChange={setConflictDialogOpen}
        conflict={selectedConflict}
        onResolve={handleResolveConflict}
      />
    </div>
  );
}
