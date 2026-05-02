/**
 * Service layer for seed bank inventory operations
 */

import type { InventoryItem, InventoryFilter } from './types';

class InventoryService {
  async fetchInventory(filter: InventoryFilter): Promise<InventoryItem[]> {
    // TODO: Replace with actual API call
    const params = new URLSearchParams();
    if (filter.vaultId) params.append('vault_id', filter.vaultId);
    if (filter.status) params.append('status', filter.status);
    if (filter.searchTerm) params.append('search', filter.searchTerm);

    const response = await fetch(`/api/v2/seed-bank/inventory?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch inventory');
    }
    return response.json();
  }

  async updateInventoryItem(id: string, updates: Partial<InventoryItem>): Promise<InventoryItem> {
    const response = await fetch(`/api/v2/seed-bank/inventory/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      throw new Error('Failed to update inventory item');
    }
    return response.json();
  }
}

export const inventoryService = new InventoryService();
