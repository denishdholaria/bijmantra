import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AccessionDetailView } from './AccessionDetailView';
import * as detailHookModule from './hooks/useAccessionDetail';

vi.mock('./hooks/useAccessionDetail');

describe('AccessionDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders mapped accession inventory data', () => {
    vi.mocked(detailHookModule.useAccessionDetail).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        id: '1',
        accessionNumber: 'ACC-001',
        name: 'IR64',
        species: 'Oryza sativa',
        institute: 'IRRI',
        origin: 'IND',
        status: 'Active',
        traits: ['yield'],
        seedlots: [
          {
            lotId: 'LOT-1',
            accessionId: 'ACC-001',
            species: 'Oryza sativa',
            variety: 'IR64',
            quantityGrams: 2500,
            quantityKg: 2.5,
            storageType: 'medium_term',
            storageLocation: 'A-01',
            currentViabilityPercent: 94,
            status: 'active',
            notes: '',
          },
        ],
        observationHistory: [],
        relatedGermplasm: [],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof detailHookModule.useAccessionDetail>);

    render(<AccessionDetailView accessionId="1" />);

    expect(screen.getByText('ACC-001')).toBeInTheDocument();
    expect(
      screen.getByText((_, element) => element?.textContent === 'IR64 · Oryza sativa · IRRI')
    ).toBeInTheDocument();
    expect(screen.getByText('LOT-1')).toBeInTheDocument();
    expect(screen.getByText('2,500 g')).toBeInTheDocument();
    expect(screen.getByText('Viability: 94%')).toBeInTheDocument();
  });

  it('switches between inventory, history, and related tabs', async () => {
    vi.mocked(detailHookModule.useAccessionDetail).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        id: '1',
        accessionNumber: 'ACC-001',
        name: 'IR64',
        species: 'Oryza sativa',
        institute: 'IRRI',
        origin: 'IND',
        status: 'Active',
        traits: ['yield'],
        seedlots: [],
        observationHistory: [
          {
            id: 'OBS-1',
            lotId: 'LOT-1',
            observedAt: '2026-04-01',
            label: 'Germination',
            value: '93%',
            method: 'Paper towel',
          },
        ],
        relatedGermplasm: [
          {
            id: '2',
            accessionNumber: 'ACC-002',
            name: 'Swarna',
            species: 'Oryza sativa',
            institute: 'NBPGR',
          },
        ],
      },
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof detailHookModule.useAccessionDetail>);

    render(<AccessionDetailView accessionId="1" />);

    const historyTab = screen.getByRole('tab', { name: /observation history/i });
    fireEvent.mouseDown(historyTab);
    fireEvent.click(historyTab);
    await waitFor(() => expect(screen.getByText('Paper towel')).toBeInTheDocument());
    expect(screen.getByText('93%')).toBeInTheDocument();

    const relatedTab = screen.getByRole('tab', { name: /related germplasm/i });
    fireEvent.mouseDown(relatedTab);
    fireEvent.click(relatedTab);
    await waitFor(() => expect(screen.getByText('Swarna')).toBeInTheDocument());
    expect(screen.getByText(/ACC-002/)).toBeInTheDocument();
  });
});
