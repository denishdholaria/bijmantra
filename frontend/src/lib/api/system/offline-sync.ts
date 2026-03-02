import { ApiClientCore } from "../core/client";

export class OfflineSyncService {
  constructor(private client: ApiClientCore) {}

  async getPendingChanges(status?: string) {
    const query = status ? `?status=${status}` : "";
    return this.client.get<
      Array<{
        id: string;
        type: string;
        name: string;
        status: string;
        last_sync: string;
        size: string;
        error_message?: string;
      }>
    >(`/api/v2/offline-sync/pending-changes${query}`);
  }

  async queueChange(data: {
    type: string;
    name: string;
    data: any;
    size_bytes: number;
  }) {
    return this.client.post<any>("/api/v2/offline-sync/queue-change", data);
  }

  async deletePendingChange(itemId: string) {
    return this.client.delete<any>(
      `/api/v2/offline-sync/pending-changes/${itemId}`
    );
  }

  async syncNow() {
    return this.client.post<{
      success: boolean;
      synced: number;
      errors: number;
      message: string;
    }>("/api/v2/offline-sync/sync-now", {});
  }

  async getCachedData() {
    return this.client.get<
      Array<{
        category: string;
        items: number;
        size: string;
        last_updated: string;
        enabled: boolean;
      }>
    >("/api/v2/offline-sync/cached-data");
  }

  async updateCache(category: string) {
    return this.client.post<any>(
      `/api/v2/offline-sync/update-cache/${category}`,
      {}
    );
  }

  async clearCache(category?: string) {
    const query = category ? `?category=${category}` : "";
    return this.client.delete<any>(`/api/v2/offline-sync/clear-cache${query}`);
  }

  async getStats() {
    return this.client.get<{
      cached_data_mb: number;
      pending_uploads: number;
      last_sync: string;
      sync_errors: number;
      total_items_cached: number;
    }>("/api/v2/offline-sync/stats");
  }

  async getSettings() {
    // Try to get from local storage first for immediate render
    const localSettings = localStorage.getItem('offline_settings');
    let settings = localSettings ? JSON.parse(localSettings) : null;

    try {
      // Try fetching from server
      const serverSettings = await this.client.get<{
        auto_sync: boolean;
        background_sync: boolean;
        wifi_only: boolean;
        cache_images: boolean;
        max_cache_size_mb: number;
      }>("/api/v2/offline-sync/settings");
      
      // Update local storage with latest server truth
      localStorage.setItem('offline_settings', JSON.stringify(serverSettings));
      return serverSettings;
    } catch (e) {
      // If network fails and we have local settings, return them
      if (settings) return settings;
      throw e; // Otherwise propagate error
    }
  }

  async updateSettings(data: {
    auto_sync?: boolean;
    background_sync?: boolean;
    wifi_only?: boolean;
    cache_images?: boolean;
    max_cache_size_mb?: number;
  }) {
    // Optimistically update local storage
    const current = JSON.parse(localStorage.getItem('offline_settings') || '{}');
    const updated = { ...current, ...data };
    localStorage.setItem('offline_settings', JSON.stringify(updated));

    // Try to sync with server
    try {
      return await this.client.patch<any>("/api/v2/offline-sync/settings", data);
    } catch (e) {
      // If offline, just return the local updated version as success (optimistic)
      // The settings are "saved" locally and effectively active for the client
      console.warn('Network failed, settings saved locally only', e);
      return updated;
    }
  }

  async getStorageQuota() {
    return this.client.get<{
      recommended_max_mb: number;
      current_usage_mb: number;
      available_mb: number;
      quota_exceeded: boolean;
    }>("/api/v2/offline-sync/storage-quota");
  }

  async resolveConflict(
    itemId: string,
    resolution: "server_wins" | "client_wins" | "merge"
  ) {
    return this.client.post<any>(
      `/api/v2/offline-sync/resolve-conflict/${itemId}?resolution=${resolution}`,
      {}
    );
  }
}
