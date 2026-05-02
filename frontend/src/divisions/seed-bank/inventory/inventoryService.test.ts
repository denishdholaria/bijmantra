/**
 * Tests for inventoryService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { inventoryService } from './inventoryService';

global.fetch = vi.fn();

describe('inventoryService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches inventory with filters', async () => {
    const mockItems = [
      { id: '1', accessionId: 'ACC001', vaultId: 'V1', quantity: 100, unit: 'g', location: 'A1', lastUpdated: new Date(), status: 'available' },
    ];
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockItems,
    });

    const result = await inventoryService.fetchInventory({ vaultId: 'V1', status: 'available' });

    expect(result).toEqual(mockItems);
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('vault_id=V1'));
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('status=available'));
  });

  it('throws error on failed fetch', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: false,
    });

    await expect(inventoryService.fetchInventory({})).rejects.toThrow('Failed to fetch inventory');
  });
});
