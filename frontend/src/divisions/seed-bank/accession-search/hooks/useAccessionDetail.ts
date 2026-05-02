import { useQuery } from '@tanstack/react-query';
import { accessionSearchService } from '../services/accessionSearchService';

export function useAccessionDetail(accessionId: string | null) {
  return useQuery({
    queryKey: ['seed-bank', 'accession-detail', accessionId],
    queryFn: () => accessionSearchService.getAccessionDetail(accessionId as string),
    enabled: Boolean(accessionId),
  });
}
