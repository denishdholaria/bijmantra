import { useQuery } from '@tanstack/react-query';
import { accessionSearchService } from '../services/accessionSearchService';
import type { AccessionSearchParams } from '../types';

export function useAccessionSearch(params: AccessionSearchParams) {
  const trimmedQuery = params.query.trim();

  return useQuery({
    queryKey: ['seed-bank', 'accession-search', trimmedQuery, params.page, params.pageSize],
    queryFn: () => accessionSearchService.searchAccessions(params),
    placeholderData: (previousData) => previousData,
  });
}
