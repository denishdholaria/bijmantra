/**
 * Custom hook for seed bank inventory management
 */

import { useState, useEffect } from 'react';
import { inventoryService } from './inventoryService';
import type { InventoryState, InventoryFilter } from './types';

export function useInventory(initialFilter: InventoryFilter = {}) {
  const [state, setState] = useState<InventoryState>({
    items: [],
    loading: false,
    error: null,
    filter: initialFilter,
  });

  const loadInventory = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const items = await inventoryService.fetchInventory(state.filter);
      setState(prev => ({ ...prev, items, loading: false }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load inventory',
      }));
    }
  };

  const updateFilter = (filter: Partial<InventoryFilter>) => {
    setState(prev => ({ ...prev, filter: { ...prev.filter, ...filter } }));
  };

  useEffect(() => {
    loadInventory();
  }, [state.filter]);

  return {
    ...state,
    updateFilter,
    reload: loadInventory,
  };
}
