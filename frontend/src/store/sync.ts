import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SyncItem {
  id: string;
  type: string;
  action: 'create' | 'update' | 'delete';
  data: any;
  timestamp: number;
  status: 'pending' | 'syncing' | 'synced' | 'error';
  error?: string;
}

interface SyncState {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime: number | null;
  pendingItems: SyncItem[];

  // Actions
  setOnlineStatus: (status: boolean) => void;
  setSyncing: (status: boolean) => void;
  addToSyncQueue: (item: Omit<SyncItem, 'timestamp' | 'status'>) => void;
  removeFromQueue: (id: string) => void;
  updateItemStatus: (id: string, status: SyncItem['status'], error?: string) => void;
  clearSyncedItems: () => void;
  getPendingCount: () => number;
}

export const useSyncStore = create<SyncState>()(
  persist(
    (set, get) => ({
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
      isSyncing: false,
      lastSyncTime: null,
      pendingItems: [],

      setOnlineStatus: (status) => set({ isOnline: status }),

      setSyncing: (status) => set({
        isSyncing: status,
        lastSyncTime: status ? get().lastSyncTime : Date.now()
      }),

      addToSyncQueue: (item) => set((state) => ({
        pendingItems: [
          ...state.pendingItems,
          {
            ...item,
            timestamp: Date.now(),
            status: 'pending'
          }
        ]
      })),

      removeFromQueue: (id) => set((state) => ({
        pendingItems: state.pendingItems.filter((i) => i.id !== id)
      })),

      updateItemStatus: (id, status, error) => set((state) => ({
        pendingItems: state.pendingItems.map((item) =>
          item.id === id ? { ...item, status, error } : item
        )
      })),

      clearSyncedItems: () => set((state) => ({
        pendingItems: state.pendingItems.filter((i) => i.status !== 'synced')
      })),

      getPendingCount: () => get().pendingItems.filter(i => i.status === 'pending').length,
    }),
    {
      name: 'bijmantra-sync-storage',
      partialize: (state) => ({
        pendingItems: state.pendingItems,
        lastSyncTime: state.lastSyncTime
      }),
    }
  )
);

// Initialize online listener
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => useSyncStore.getState().setOnlineStatus(true));
  window.addEventListener('offline', () => useSyncStore.getState().setOnlineStatus(false));
}
