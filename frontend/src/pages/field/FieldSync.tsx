import { FieldLayout } from '@/components/layouts/FieldLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RefreshCw, CheckCircle, Wifi, WifiOff, UploadCloud } from 'lucide-react';
import { syncService } from '@/services/SyncService';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '@/lib/db';
import { useState } from 'react';

export function FieldSync() {
  const [isSyncing, setIsSyncing] = useState(false);
  const queueCount = useLiveQuery(() => db.syncQueue.count()) ?? 0;
  const isOnline = navigator.onLine;

  const handleSync = async () => {
    setIsSyncing(true);
    await syncService.triggerSync();
    setIsSyncing(false);
  };

  return (
    <FieldLayout title="Data Sync">
      <div className="space-y-4">
        {/* Status Card */}
        <Card className={isOnline ? 'bg-green-50 border-green-200' : 'bg-orange-50 border-orange-200'}>
          <CardContent className="pt-6 flex flex-col items-center">
             {isOnline ? (
               <Wifi className="w-12 h-12 text-green-600 mb-2" />
             ) : (
               <WifiOff className="w-12 h-12 text-orange-600 mb-2" />
             )}
             <h3 className="text-lg font-bold">
               {isOnline ? 'You are Online' : 'You are Offline'}
             </h3>
             <p className="text-sm text-gray-500">
               {isOnline ? 'Ready to sync data' : 'Data is saved locally'}
             </p>
          </CardContent>
        </Card>

        {/* Sync Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Sync Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b">
              <span>Pending Updates</span>
              <span className="font-bold bg-gray-100 px-3 py-1 rounded-full">{queueCount}</span>
            </div>

            <Button 
              className="w-full" 
              onClick={handleSync} 
              disabled={!isOnline || queueCount === 0 || isSyncing}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
              {isSyncing ? 'Syncing...' : 'Sync Now'}
            </Button>
            
            <p className="text-xs text-center text-gray-400">
              Last sync: Never
            </p>
          </CardContent>
        </Card>
      </div>
    </FieldLayout>
  );
}

export default FieldSync;
