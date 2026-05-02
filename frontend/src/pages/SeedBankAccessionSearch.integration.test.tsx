import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SeedBankAccessionSearch } from './SeedBankAccessionSearch';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: mockGet,
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
      <MemoryRouter initialEntries={['/seed-bank/accessions']}>
        <Routes>
          <Route path="/seed-bank/accessions" element={<SeedBankAccessionSearch />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('SeedBankAccessionSearch integration', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint.startsWith('/api/v2/germplasm-search/search') && endpoint.includes('species=Oryza+sativa')) {
        return Promise.resolve({
          success: true,
          count: 2,
          results: [
            {
              id: '1',
              accession: 'ACC-001',
              name: 'IR64',
              species: 'Oryza sativa',
              origin: 'IND',
              status: 'Active',
              collection: 'IRRI',
              traits: ['yield'],
            },
            {
              id: '2',
              accession: 'ACC-002',
              name: 'Swarna',
              species: 'Oryza sativa',
              origin: 'IND',
              status: 'Active',
              collection: 'NBPGR',
              traits: ['resilience'],
            },
          ],
        });
      }

      if (endpoint.startsWith('/api/v2/germplasm-search/search')) {
        return Promise.resolve({
          success: true,
          count: 1,
          results: [
            {
              id: '1',
              accession: 'ACC-001',
              name: 'IR64',
              species: 'Oryza sativa',
              origin: 'IND',
              status: 'Active',
              collection: 'IRRI',
              traits: ['yield'],
            },
          ],
        });
      }

      if (endpoint === '/api/v2/germplasm-search/1') {
        return Promise.resolve({
          success: true,
          data: {
            id: '1',
            accession: 'ACC-001',
            name: 'IR64',
            species: 'Oryza sativa',
            origin: 'IND',
            status: 'Active',
            collection: 'IRRI',
            traits: ['yield'],
          },
        });
      }

      if (endpoint === '/api/v2/seed-inventory/lots') {
        return Promise.resolve({
          success: true,
          count: 1,
          lots: [
            {
              lot_id: 'LOT-1',
              accession_id: 'ACC-001',
              species: 'Oryza sativa',
              variety: 'IR64',
              current_quantity_g: 2500,
              quantity_kg: 2.5,
              storage_type: 'medium_term',
              storage_location: 'A-01',
              current_viability_percent: 94,
              status: 'active',
              notes: '',
            },
          ],
        });
      }

      if (endpoint === '/api/v2/seed-inventory/viability/LOT-1') {
        return Promise.resolve({
          success: true,
          lot_id: 'LOT-1',
          tests: [
            {
              test_id: 'OBS-1',
              test_date: '2026-04-01',
              germination_percent: 94,
              test_method: 'Paper towel',
            },
          ],
        });
      }

      throw new Error(`Unhandled endpoint: ${endpoint}`);
    });
  });

  it('renders the search workflow and shows detail after selecting a result', async () => {
    renderWorkflow();

    expect(await screen.findByRole('button', { name: 'ACC-001' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'ACC-001' }));

    await waitFor(() => expect(screen.getAllByText('ACC-001').length).toBeGreaterThan(1));
    expect(screen.getByText('LOT-1')).toBeInTheDocument();

    const historyTab = await screen.findByRole('tab', { name: /observation history/i });
    fireEvent.mouseDown(historyTab);
    fireEvent.click(historyTab);

    expect(await screen.findByText('Paper towel')).toBeInTheDocument();
  });
});
