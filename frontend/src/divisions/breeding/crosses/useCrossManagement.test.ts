/**
 * Tests for useCrossManagement hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useCrossManagement } from './useCrossManagement';
import { crossManagementService } from './crossManagementService';

vi.mock('./crossManagementService', () => ({
  crossManagementService: {
    fetchCrosses: vi.fn(),
    createCross: vi.fn(),
    updateCross: vi.fn(),
  },
}));

describe('useCrossManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads crosses on mount', async () => {
    const mockCrosses = [
      { 
        id: '1', 
        crossCode: 'C001', 
        maternalParent: 'P001', 
        paternalParent: 'P002', 
        crossDate: new Date(), 
        generation: 'F1', 
        status: 'completed' as const, 
        seedsProduced: 100, 
        notes: 'Test cross', 
        createdBy: 'user1' 
      },
    ];
    (crossManagementService.fetchCrosses as any).mockResolvedValue(mockCrosses);

    const { result } = renderHook(() => useCrossManagement());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.crosses).toEqual(mockCrosses);
    expect(result.current.error).toBeNull();
  });

  it('handles fetch errors', async () => {
    (crossManagementService.fetchCrosses as any).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useCrossManagement());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.crosses).toEqual([]);
  });
});
