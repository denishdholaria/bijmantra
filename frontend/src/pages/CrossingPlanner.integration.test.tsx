import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CrossingPlanner } from './CrossingPlanner';

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: mockGet,
    post: mockPost,
  },
}));

function renderWorkflow() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <CrossingPlanner />
    </QueryClientProvider>
  );
}

describe('CrossingPlanner integration', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPost.mockReset();

    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint.startsWith('/api/v2/crossing-planner?page=0&pageSize=20')) {
        return Promise.resolve({
          metadata: {
            pagination: {
              totalCount: 0,
              currentPage: 0,
              pageSize: 20,
              totalPages: 1,
            },
          },
          result: {
            data: [],
          },
        });
      }

      if (endpoint.startsWith('/api/v2/crossing-planner/germplasm')) {
        return Promise.resolve({
          result: {
            data: [
              {
                id: 'female-1',
                accessionNumber: 'ACC-001',
                name: 'IR64',
              },
              {
                id: 'male-1',
                accessionNumber: 'ACC-002',
                name: 'Swarna',
              },
            ],
          },
        });
      }

      if (endpoint === '/api/v2/pedigree/ancestors/female-1?max_generations=5') {
        return Promise.resolve({
          success: true,
          tree: {
            id: 'female-1',
            name: 'IR64',
            generation: 0,
            type: 'progeny',
            sire: {
              id: 'sire-1',
              name: 'IR64 Female Sire',
              generation: 1,
              type: 'ancestor',
              sire: null,
              dam: null,
            },
            dam: null,
          },
        });
      }

      throw new Error(`Unhandled endpoint: ${endpoint}`);
    });

    mockPost.mockResolvedValue({
      metadata: {},
      result: {
        crossId: 'cross-100',
        crossName: '2026 drought resilience',
        femaleParentId: 'female-1',
        femaleParentName: 'IR64',
        maleParentId: 'male-1',
        maleParentName: 'Swarna',
        objective: 'Improve drought resilience while preserving yield',
        priority: 'medium',
        targetDate: '2026-06-01',
        status: 'planned',
        expectedProgeny: 0,
        actualProgeny: 0,
        crossType: 'planned',
        season: '',
        location: '',
        breeder: '',
        notes: '',
        created: '2026-04-22T00:00:00Z',
      },
    });
  });

  it('creates a cross plan and loads pedigree detail for the selected parent', async () => {
    renderWorkflow();

    fireEvent.click(await screen.findByRole('button', { name: /create new plan/i }));

    fireEvent.click(await screen.findByRole('button', { name: 'Female Parent candidate IR64' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Male Parent candidate Swarna' }));

    fireEvent.change(screen.getByLabelText(/plan name/i), {
      target: { value: '2026 drought resilience' },
    });
    fireEvent.change(screen.getByLabelText(/planned date/i), {
      target: { value: '2026-06-01' },
    });
    fireEvent.change(screen.getByLabelText(/objective/i), {
      target: { value: 'Improve drought resilience while preserving yield' },
    });

    fireEvent.click(screen.getByRole('button', { name: /save cross plan/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/api/v2/crossing-planner', {
        femaleParentId: 'female-1',
        maleParentId: 'male-1',
        crossName: '2026 drought resilience',
        objective: 'Improve drought resilience while preserving yield',
        targetDate: '2026-06-01',
        notes: '',
      })
    );

    expect(await screen.findByText('Pedigree for IR64')).toBeInTheDocument();
    expect(await screen.findByText('IR64 Female Sire')).toBeInTheDocument();
  });
});
