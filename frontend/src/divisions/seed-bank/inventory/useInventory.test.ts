/**
 * Tests for useInventory hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useInventory } from './useInventory';
import { inventoryService } from './inventoryService';

vi.mock('./inventoryService', () => ({
  inventoryService: {
    fetchInventory: vi.fn(),
    updateInventoryItem: vi.fn(),
  },
}));

describe('useInventory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads inventory on mount', async () => {
    const mockItems = [
      { id: '1', accessionId: 'ACC001', vaultId: 'V1', quantity: 100, unit: 'g', location: 'A1', lastUpdated: new Date(), status: 'available' as const },
    ];
    (inventoryService.fetchInventory as any).mockResolvedValue(mockItems);

    const { result } = renderHook(() => useInventory());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.items).toEqual(mockItems);
    expect(result.current.error).toBeNull();
  });

  it('handles fetch errors', async () => {
    (inventoryService.fetchInventory as any).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useInventory());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.items).toEqual([]);
  });
});
