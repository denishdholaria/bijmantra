import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CrossPlanForm } from './CrossPlanForm';
import { crossPlanningService } from './services/crossPlanningService';
import * as createCrossPlanHookModule from './hooks/useCreateCrossPlan';

vi.mock('./hooks/useCreateCrossPlan');
vi.mock('./services/crossPlanningService', () => ({
  crossPlanningService: {
    searchParentCandidates: vi.fn(),
  },
}));
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('CrossPlanForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('submits a valid cross plan with the selected parents', async () => {
    const mutateAsync = vi.fn().mockResolvedValue({
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
      notes: 'Advance to crossing block',
      created: '2026-04-22T00:00:00Z',
    });
    const onCreated = vi.fn();

    vi.mocked(createCrossPlanHookModule.useCreateCrossPlan).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof createCrossPlanHookModule.useCreateCrossPlan>);
    vi.mocked(crossPlanningService.searchParentCandidates).mockResolvedValue([
      {
        id: 'female-1',
        name: 'IR64',
        accessionNumber: 'ACC-001',
      },
      {
        id: 'male-1',
        name: 'Swarna',
        accessionNumber: 'ACC-002',
      },
    ]);

    render(<CrossPlanForm onCreated={onCreated} />, {
      wrapper: createWrapper(),
    });

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
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: 'Advance to crossing block' },
    });

    fireEvent.click(screen.getByRole('button', { name: /save cross plan/i }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        femaleParentId: 'female-1',
        maleParentId: 'male-1',
        name: '2026 drought resilience',
        description: 'Advance to crossing block',
        plannedDate: '2026-06-01',
        objective: 'Improve drought resilience while preserving yield',
      })
    );

    expect(onCreated).toHaveBeenCalledWith(
      expect.objectContaining({
        crossId: 'cross-100',
        femaleParentId: 'female-1',
      })
    );
  });
});
