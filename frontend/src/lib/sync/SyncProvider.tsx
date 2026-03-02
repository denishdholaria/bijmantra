import React, { useEffect } from 'react';
import { syncEngine } from './engine';

export const SyncProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    // Start background sync (every 60 seconds)
    syncEngine.startBackgroundSync(60000);

    // Initial sync
    syncEngine.pullChanges();
    syncEngine.pushChanges();
  }, []);

  return <>{children}</>;
};
