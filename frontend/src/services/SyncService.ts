import { db, SyncQueueItem } from '../lib/db';
import { apiClient } from '../lib/api-client';

export class SyncService {
  private isSyncing = false;

  constructor() {
    // Listen for online events
    window.addEventListener('online', () => {
      console.log('🌐 Online detected. Triggering sync.');
      this.triggerSync();
    });
  }

  /**
   * Queue an action to be performed (optimistic UI update + sync later)
   */
  async queueAction(
    action: SyncQueueItem['action'],
    entity: SyncQueueItem['entity'],
    data: any
  ) {
    // 1. Save to local Sync Queue
    await db.syncQueue.add({
      action,
      entity,
      data,
      timestamp: Date.now(),
      retryCount: 0
    });

    // 2. Try to sync immediately if online
    if (navigator.onLine) {
      this.triggerSync();
    }
  }

  /**
   * Process the sync queue
   */
  async triggerSync() {
    if (this.isSyncing) return;
    if (!navigator.onLine) return;

    this.isSyncing = true;
    console.log('🔄 Starting Sync...');

    try {
      // Get all pending items
      const queue = await db.syncQueue.orderBy('timestamp').toArray();

      if (queue.length === 0) {
        console.log('✅ Sync complete (No items)');
        this.isSyncing = false;
        return;
      }

      for (const item of queue) {
        try {
          await this.processItem(item);
          // Remove from queue on success
          if (item.id) await db.syncQueue.delete(item.id);
        } catch (err) {
          console.error(`❌ Sync failed for item ${item.id}`, err);
          // Increment retry count or implement backoff strategy here
        }
      }
    } finally {
      this.isSyncing = false;
    }
  }

  private async processItem(item: SyncQueueItem) {
    const { action, entity, data } = item;
    
    // Mapping entities to API endpoints
    let endpoint = '';
    
    // We only support creating OBSERVATIONS for now in offline mode
    if (entity === 'OBSERVATION') {
      endpoint = '/api/v2/field-book/observations'; 
    } else {
      console.warn(`Sync not implemented for entity: ${entity}`);
      return; 
    }

    if (!endpoint) return;

    // Execute API call
    if (action === 'CREATE') {
      // Data should match ObservationRequest schema
      // We might need to transform it if local storage differs from API request
      await apiClient.post(endpoint, data);
    } else if (action === 'UPDATE') {
      // Not yet supported by bulk endpoint, strictly
      // await apiClient.put(`${endpoint}/${data.id}`, data);
      console.warn("Update not yet supported in offline sync");
    } else if (action === 'DELETE') {
       // await apiClient.delete(`${endpoint}/${data.id}`);
       console.warn("Delete not yet supported in offline sync");
    }
  }
}

export const syncService = new SyncService();
