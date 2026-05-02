import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BreedingValueCalculator } from './BreedingValueCalculator';
import { apiClient } from '@/lib/api-client';

// Mock apiClient
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    studyService: { getStudies: vi.fn().mockResolvedValue({ result: { data: [] } }) },
    observationService: { getObservationVariables: vi.fn().mockResolvedValue({ result: { data: [] } }) },
    breedingValueService: {
      getIndividuals: vi.fn(),
      runBLUP: vi.fn(),
      estimateFromDb: vi.fn(),
      runGBLUP: vi.fn(),
      predictCross: vi.fn()
    }
  }
}));

describe('BreedingValueCalculator Performance', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    vi.clearAllMocks();

    // Mock ResizeObserver
    global.ResizeObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    }));

    // Mock Pointer Capture methods (needed for Radix UI)
    Element.prototype.setPointerCapture = vi.fn();
    Element.prototype.releasePointerCapture = vi.fn();
    Element.prototype.hasPointerCapture = vi.fn();

    // Mock PointerEvent
    if (!global.PointerEvent) {
      class MockPointerEvent extends MouseEvent {
        constructor(type: string, props: PointerEventInit = {}) {
          super(type, props);
        }
      }
      global.PointerEvent = MockPointerEvent as any;
    }
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should not re-sort individuals when selection intensity changes', async () => {
    // Setup mock data
    const mockIndividuals = Array.from({ length: 100 }, (_, i) => ({
      id: `ind-${i}`,
      name: `Individual ${i}`,
      ebv: Math.random(),
      accuracy: 0.8,
      rank: i + 1
    }));

    (apiClient.breedingValueService.getIndividuals as any).mockResolvedValue({
      data: mockIndividuals
    });

    // Spy on Array.prototype.sort
    const sortSpy = vi.spyOn(Array.prototype, 'sort');

    render(
      <QueryClientProvider client={queryClient}>
        <BreedingValueCalculator initialTab="select" />
      </QueryClientProvider>
    );

    // Wait for input to appear (since we start on select tab)
    const input = await screen.findByDisplayValue('20', {}, { timeout: 3000 });
    expect(input).toBeInTheDocument();

    // Count initial sort calls relevant to our data
    // We check if the array sorted contains our mock individuals
    const getRelevantSortCount = () => {
        return sortSpy.mock.instances.filter(arr =>
            Array.isArray(arr) && arr.length > 0 && (arr[0] as any).id && (arr[0] as any).id.startsWith('ind-')
        ).length;
    };

    const initialSortCount = getRelevantSortCount();

    // Change selection intensity
    fireEvent.change(input, { target: { value: '30' } });

    // Wait for update (checking the summary text)
    await waitFor(() => {
       expect(screen.getByText(/Top 30 of 100/)).toBeInTheDocument();
    });

    const finalSortCount = getRelevantSortCount();

    // Expect no additional sort calls
    expect(finalSortCount).toBe(initialSortCount);
  });
});
