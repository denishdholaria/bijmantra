/**
 * Type definitions for Seed Bank Inventory module
 */

export interface InventoryItem {
  id: string;
  accessionId: string;
  vaultId: string;
  quantity: number;
  unit: string;
  location: string;
  lastUpdated: Date;
  status: 'available' | 'reserved' | 'depleted';
}

export interface InventoryFilter {
  vaultId?: string;
  status?: InventoryItem['status'];
  searchTerm?: string;
}

export interface InventoryState {
  items: InventoryItem[];
  loading: boolean;
  error: string | null;
  filter: InventoryFilter;
}
