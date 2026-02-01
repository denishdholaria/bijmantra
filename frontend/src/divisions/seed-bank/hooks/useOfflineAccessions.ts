/**
 * Seed Bank - Offline Accessions Hook
 *
 * Typed hook for offline-first accession management.
 */

import { useCallback } from 'react';
import { useOfflineData } from '@/framework/sync/hooks';
import { OfflineAccession } from '@/framework/sync/db';

export interface AccessionInput {
  accession_number: string;
  genus: string;
  species: string;
  subspecies?: string;
  common_name?: string;
  origin: string;
  collection_date?: string;
  collection_site?: string;
  latitude?: number;
  longitude?: number;
  altitude?: number;
  vault_id?: string;
  seed_count: number;
  viability?: number;
  status?: 'active' | 'depleted' | 'regenerating';
  acquisition_type?: string;
  donor_institution?: string;
  mls?: boolean;
  pedigree?: string;
  notes?: string;
  organization_id: string;
}

export function useOfflineAccessions() {
  const {
    data,
    isLoading,
    error,
    reload,
    create: baseCreate,
    update,
    remove,
    getById,
  } = useOfflineData<OfflineAccession>('accessions');

  const create = useCallback(
    async (input: AccessionInput) => {
      return baseCreate({
        ...input,
        viability: input.viability ?? 100,
        status: input.status ?? 'active',
        mls: input.mls ?? false,
        vaultId: input.vault_id ?? '',
        seedCount: input.seed_count,
        accessionNumber: input.accession_number,
        commonName: input.common_name,
        collectionDate: input.collection_date,
        collectionSite: input.collection_site,
        acquisitionType: input.acquisition_type,
        donorInstitution: input.donor_institution,
        organizationId: input.organization_id,
      } as any);
    },
    [baseCreate]
  );

  // Filter by status
  const filterByStatus = useCallback(
    (status: 'active' | 'depleted' | 'regenerating') => {
      return data.filter((acc) => acc.status === status);
    },
    [data]
  );

  // Filter by vault
  const filterByVault = useCallback(
    (vaultId: string) => {
      return data.filter((acc) => acc.vaultId === vaultId);
    },
    [data]
  );

  // Search accessions
  const search = useCallback(
    (query: string) => {
      const q = query.toLowerCase();
      return data.filter(
        (acc) =>
          acc.accessionNumber.toLowerCase().includes(q) ||
          acc.genus.toLowerCase().includes(q) ||
          acc.species.toLowerCase().includes(q) ||
          acc.commonName?.toLowerCase().includes(q)
      );
    },
    [data]
  );

  // Get low viability accessions
  const getLowViability = useCallback(
    (threshold = 70) => {
      return data.filter((acc) => acc.viability < threshold);
    },
    [data]
  );

  return {
    accessions: data,
    isLoading,
    error,
    reload,
    create,
    update,
    remove,
    getById,
    filterByStatus,
    filterByVault,
    search,
    getLowViability,
    stats: {
      total: data.length,
      active: data.filter((a) => a.status === 'active').length,
      regenerating: data.filter((a) => a.status === 'regenerating').length,
      lowViability: data.filter((a) => a.viability < 70).length,
    },
  };
}

export default useOfflineAccessions;
