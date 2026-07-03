import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useDashboardService } from './dashboardService';

function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', {
    value,
    writable: true,
  });
}

describe('useDashboardService', () => {
  afterEach(() => {
    setOnline(true);
    vi.restoreAllMocks();
  });

  it('loads real data even when the browser reports offline', async () => {
    setOnline(false);
    const fetchData = vi.fn().mockResolvedValue({ activePlots: 12 });

    const { result } = renderHook(() => useDashboardService(fetchData));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(fetchData).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual({ activePlots: 12 });
    expect(result.current.error).toBeNull();
  });

  it('surfaces real data fetch errors without substituting fallback data', async () => {
    const apiError = new Error('Dashboard API unavailable');
    const fetchData = vi.fn().mockRejectedValue(apiError);

    const { result } = renderHook(() => useDashboardService(fetchData));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(fetchData).toHaveBeenCalledTimes(1);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe(apiError);
  });
});
