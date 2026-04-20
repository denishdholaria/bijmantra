import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { VisionRegistry } from '../VisionRegistry';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

describe('VisionRegistry', () => {
  beforeEach(() => {
    // Mock global fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ models: [] }),
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('debounces search input', async () => {
    render(
      <BrowserRouter>
        <VisionRegistry />
      </BrowserRouter>
    );

    // Initial fetch calls (fetchData calls 2, searchModels calls 1)
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(3));

    // Clear mock to reset count
    vi.mocked(global.fetch).mockClear();

    // Use fake timers for the debounce test
    vi.useFakeTimers();

    const searchInput = screen.getByPlaceholderText('Search models...');

    // Type "test" rapidly
    fireEvent.change(searchInput, { target: { value: 't' } });
    fireEvent.change(searchInput, { target: { value: 'te' } });
    fireEvent.change(searchInput, { target: { value: 'tes' } });
    fireEvent.change(searchInput, { target: { value: 'test' } });

    // Should not have been called yet (debounce pending)
    expect(global.fetch).not.toHaveBeenCalled();

    // Fast-forward time
    await act(async () => {
        vi.advanceTimersByTime(300);
    });

    // Should have been called once with 'test'
    expect(global.fetch).toHaveBeenCalledTimes(1);
    const url = vi.mocked(global.fetch).mock.calls[0][0] as string;
    expect(url).toContain('query=test');
  });
});
