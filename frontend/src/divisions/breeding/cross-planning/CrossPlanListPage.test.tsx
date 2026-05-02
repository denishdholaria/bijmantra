import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CrossPlanListPage } from './CrossPlanListPage';
import * as crossPlansHookModule from './hooks/useCrossPlans';

vi.mock('./hooks/useCrossPlans');

describe('CrossPlanListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders cross plans and opens the create flow', () => {
    const onCreateRequested = vi.fn();
    const refetch = vi.fn();

    vi.mocked(crossPlansHookModule.useCrossPlans).mockReturnValue({
      isLoading: false,
      isError: false,
      isFetching: false,
      data: {
        items: [
          {
            crossId: 'cross-1',
            crossName: '2026 drought resilience',
            femaleParentId: 'female-1',
            femaleParentName: 'IR64',
            maleParentId: 'male-1',
            maleParentName: 'Swarna',
            objective: 'Improve drought resilience while preserving yield',
            priority: 'high',
            targetDate: '2026-06-15',
            status: 'scheduled',
            expectedProgeny: 150,
            actualProgeny: 0,
            crossType: 'planned',
            season: 'Kharif',
            location: 'Main station',
            breeder: 'Dr. Rao',
            notes: '',
            created: '2026-04-22T00:00:00Z',
          },
        ],
        total: 1,
        page: 0,
        pageSize: 20,
        totalPages: 1,
      },
      error: null,
      refetch,
    } as unknown as ReturnType<typeof crossPlansHookModule.useCrossPlans>);

    render(<CrossPlanListPage onCreateRequested={onCreateRequested} />);

    expect(screen.getByText('2026 drought resilience')).toBeInTheDocument();
    expect(screen.getByText('IR64 × Swarna')).toBeInTheDocument();
    expect(screen.getByText('Planned date: 2026-06-15')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /create new plan/i }));
    expect(onCreateRequested).toHaveBeenCalledTimes(1);
  });
});
