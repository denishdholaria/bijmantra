import { ApiClientCore } from "../core/client";

export interface SyncStats {
  total_items: number;
  synced_items: number;
  pending_items: number;
  conflicts: number;
  errors: number;
  last_full_sync?: string;
  sync_in_progress: boolean;
}

export interface SyncItem {
  id: string;
  entity_type: string;
  entity_id: string;
  name: string;
  status: string;
  size_bytes: number;
  created_at: string;
  last_modified: string;
  error_message?: string;
}

export interface SyncHistoryEntry {
  id: string;
  action: string;
  description: string;
  items_count: number;
  status: string;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface OfflineDataCategory {
  type: string;
  count: number;
  size_bytes: number;
  last_updated?: string;
}

export interface SyncSettings {
  auto_sync: boolean;
  sync_on_wifi_only: boolean;
  background_sync: boolean;
  sync_images: boolean;
  sync_interval_minutes: number;
  max_offline_days: number;
  conflict_resolution: string;
}

export class DataSyncService {
  constructor(private client: ApiClientCore) {}

  async getStats() {
    return this.client.get<SyncStats>("/api/v2/data-sync/stats");
  }

  async getPending() {
    return this.client.get<{ items: SyncItem[] }>("/api/v2/data-sync/pending");
  }

  async sync(action: string = "full_sync") {
    return this.client.post<{ status: string; message: string }>(
      `/api/v2/data-sync/sync?action=${action}`,
      {}
    );
  }

  async getHistory() {
    return this.client.get<{ history: SyncHistoryEntry[] }>(
      "/api/v2/data-sync/history"
    );
  }

  async getOfflineData() {
    return this.client.get<{
      categories: OfflineDataCategory[];
      total_size_bytes: number;
      storage_quota_bytes: number;
    }>("/api/v2/data-sync/offline-data");
  }

  async upload() {
    return this.client.post<{ status: string; uploaded: number }>(
      "/api/v2/data-sync/upload",
      {}
    );
  }

  async deletePending(itemId: string) {
    return this.client.delete<void>(`/api/v2/data-sync/pending/${itemId}`);
  }

  async clearOfflineData(category: string) {
    return this.client.delete<void>(
      `/api/v2/data-sync/offline-data/${category}`
    );
  }

  async getSettings() {
    return this.client.get<SyncSettings>("/api/v2/data-sync/settings");
  }

  async updateSettings(settings: Partial<SyncSettings>) {
    const params = new URLSearchParams();
    Object.entries(settings).forEach(([k, v]) => {
      if (v !== undefined) params.append(k, String(v));
    });
    return this.client.patch<SyncSettings>(
      `/api/v2/data-sync/settings?${params}`,
      {}
    );
  }
}
