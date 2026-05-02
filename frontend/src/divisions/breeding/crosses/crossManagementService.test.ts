/**
 * Tests for crossManagementService
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { crossManagementService } from './crossManagementService';

global.fetch = vi.fn();

describe('crossManagementService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches crosses with filters', async () => {
    const mockCrosses = [
      { 
        id: '1', 
        crossCode: 'C001', 
        maternalParent: 'P001', 
        paternalParent: 'P002', 
        crossDate: new Date(), 
        generation: 'F1', 
        status: 'completed', 
        seedsProduced: 100, 
        notes: 'Test cross', 
        createdBy: 'user1' 
      },
    ];
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockCrosses,
    });

    const result = await crossManagementService.fetchCrosses({ status: 'completed', generation: 'F1' });

    expect(result).toEqual(mockCrosses);
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('status=completed'));
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('generation=F1'));
  });

  it('throws error on failed fetch', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: false,
    });

    await expect(crossManagementService.fetchCrosses({})).rejects.toThrow('Failed to fetch crosses');
  });

  it('creates a new cross', async () => {
    const newCross = { 
      crossCode: 'C002', 
      maternalParent: 'P003', 
      paternalParent: 'P004', 
      crossDate: new Date(), 
      generation: 'F1', 
      status: 'planned' as const, 
      seedsProduced: 0, 
      notes: '', 
      createdBy: 'user1' 
    };
    const createdCross = { ...newCross, id: '2' };
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => createdCross,
    });

    const result = await crossManagementService.createCross(newCross);

    expect(result).toEqual(createdCross);
    expect(global.fetch).toHaveBeenCalledWith('/api/v2/breeding/crosses', expect.objectContaining({
      method: 'POST',
    }));
  });
});
