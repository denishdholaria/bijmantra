import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAccessionSearch } from './hooks/useAccessionSearch';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: mockGet,
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

describe('useAccessionSearch', () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it('requests search results with the expected query parameters', async () => {
    mockGet.mockResolvedValue({
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

    const { result } = renderHook(
      () =>
        useAccessionSearch({
          query: 'rice',
          page: 0,
          pageSize: 10,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining('/api/v2/germplasm-search/search?')
    );
    expect(mockGet).toHaveBeenCalledWith(expect.stringContaining('query=rice'));
    expect(result.current.data?.items[0]).toMatchObject({
      accessionNumber: 'ACC-001',
      name: 'IR64',
      institute: 'IRRI',
    });
  });

  it('paginates the returned search results client-side', async () => {
    mockGet.mockResolvedValue({
      success: true,
      count: 3,
      results: [
        { id: '1', accession: 'ACC-001', name: 'IR64', species: 'Oryza sativa', origin: 'IND', status: 'Active', collection: 'IRRI', traits: [] },
        { id: '2', accession: 'ACC-002', name: 'Swarna', species: 'Oryza sativa', origin: 'IND', status: 'Active', collection: 'NBPGR', traits: [] },
        { id: '3', accession: 'ACC-003', name: 'Pusa', species: 'Oryza sativa', origin: 'IND', status: 'Active', collection: 'NBPGR', traits: [] },
      ],
    });

    const { result } = renderHook(
      () =>
        useAccessionSearch({
          query: '',
          page: 1,
          pageSize: 1,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0].accessionNumber).toBe('ACC-002');
    expect(result.current.data?.totalPages).toBe(3);
  });

  it('surfaces API errors', async () => {
    mockGet.mockRejectedValue(new Error('Search failed'));

    const { result } = renderHook(
      () =>
        useAccessionSearch({
          query: 'broken',
          page: 0,
          pageSize: 10,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe('Search failed');
  });
});
