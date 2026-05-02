import { apiClient } from '@/lib/api-client';
import type {
  AccessionDetail,
  AccessionObservationHistoryItem,
  AccessionSearchItem,
  AccessionSearchParams,
  AccessionSearchResult,
  RelatedGermplasmItem,
  SeedlotInventoryItem,
} from '../types';

interface GermplasmSearchPayload {
  success: boolean;
  count: number;
  results: Array<{
    id: string;
    name: string;
    accession: string;
    species: string;
    subspecies?: string;
    origin: string;
    traits?: string[];
    status: string;
    collection: string;
    year?: number;
  }>;
}

interface GermplasmDetailPayload {
  success: boolean;
  data: {
    id: string;
    name: string;
    accession: string;
    species: string;
    subspecies?: string;
    origin: string;
    traits?: string[];
    status: string;
    collection: string;
    year?: number;
  };
}

interface SeedLotPayload {
  success: boolean;
  count: number;
  lots: Array<{
    lot_id: string;
    accession_id: string;
    accession_uuid?: string | null;
    species: string;
    variety: string;
    current_quantity_g?: number;
    quantity_kg?: number;
    storage_type: string;
    storage_location: string;
    current_viability_percent?: number | null;
    last_viability_test?: string | null;
    status: string;
    notes?: string;
  }>;
}

interface ViabilityHistoryPayload {
  success: boolean;
  lot_id: string;
  tests: Array<{
    test_id: string;
    test_date: string;
    germination_percent: number;
    test_method: string;
    notes?: string;
  }>;
}

function mapSearchItem(item: GermplasmSearchPayload['results'][number]): AccessionSearchItem {
  return {
    id: item.id,
    accessionNumber: item.accession,
    name: item.name,
    species: item.species,
    institute: item.collection || 'Unassigned collection',
    origin: item.origin,
    status: item.status,
    subspecies: item.subspecies,
    traits: item.traits ?? [],
    year: item.year,
  };
}

function paginate<T>(items: T[], page: number, pageSize: number) {
  const start = page * pageSize;
  const end = start + pageSize;
  return items.slice(start, end);
}

class AccessionSearchService {
  async searchAccessions(params: AccessionSearchParams): Promise<AccessionSearchResult> {
    const trimmedQuery = params.query.trim();
    const searchParams = new URLSearchParams();
    if (trimmedQuery) {
      searchParams.set('query', trimmedQuery);
    }
    // The current backend does not provide offset pagination, so fetch a bounded
    // working set and paginate client-side.
    searchParams.set('limit', String(Math.max((params.page + 1) * params.pageSize, 100)));

    const payload = await apiClient.get<GermplasmSearchPayload>(
      `/api/v2/germplasm-search/search?${searchParams.toString()}`
    );

    const mappedItems = (payload.results ?? []).map(mapSearchItem);

    return {
      items: paginate(mappedItems, params.page, params.pageSize),
      total: mappedItems.length,
      page: params.page,
      pageSize: params.pageSize,
      totalPages: Math.max(1, Math.ceil(mappedItems.length / params.pageSize)),
    };
  }

  async getAccessionDetail(id: string): Promise<AccessionDetail> {
    const detailPayload = await apiClient.get<GermplasmDetailPayload>(
      `/api/v2/germplasm-search/${id}`
    );

    const base = mapSearchItem(detailPayload.data);
    const lotsPayload = await apiClient.get<SeedLotPayload>('/api/v2/seed-inventory/lots');
    const matchingLots = (lotsPayload.lots ?? [])
      .filter((lot) => lot.accession_id === base.accessionNumber)
      .map<SeedlotInventoryItem>((lot) => ({
        lotId: lot.lot_id,
        accessionId: lot.accession_id,
        accessionUuid: lot.accession_uuid ?? undefined,
        species: lot.species,
        variety: lot.variety,
        quantityGrams: lot.current_quantity_g ?? 0,
        quantityKg: lot.quantity_kg ?? 0,
        storageType: lot.storage_type,
        storageLocation: lot.storage_location,
        currentViabilityPercent: lot.current_viability_percent ?? undefined,
        lastViabilityTest: lot.last_viability_test ?? undefined,
        status: lot.status,
        notes: lot.notes ?? '',
      }));

    const viabilityPayloads = await Promise.all(
      matchingLots.map(async (lot) => {
        try {
          return await apiClient.get<ViabilityHistoryPayload>(
            `/api/v2/seed-inventory/viability/${lot.lotId}`
          );
        } catch {
          return null;
        }
      })
    );

    const observationHistory = viabilityPayloads.flatMap<AccessionObservationHistoryItem>((payload) => {
      if (!payload) {
        return [];
      }

      return payload.tests.map((test) => ({
        id: test.test_id,
        lotId: payload.lot_id,
        observedAt: test.test_date,
        label: 'Germination',
        value: `${test.germination_percent}%`,
        method: test.test_method,
        notes: test.notes,
      }));
    });

    const relatedSearchParams = new URLSearchParams();
    if (base.species && base.species !== 'Unknown') {
      relatedSearchParams.set('species', base.species);
    } else {
      relatedSearchParams.set('query', base.name);
    }
    relatedSearchParams.set('limit', '6');

    const relatedPayload = await apiClient.get<GermplasmSearchPayload>(
      `/api/v2/germplasm-search/search?${relatedSearchParams.toString()}`
    );

    const relatedGermplasm = (relatedPayload.results ?? [])
      .filter((item) => item.id !== id)
      .slice(0, 5)
      .map<RelatedGermplasmItem>((item) => ({
        id: item.id,
        accessionNumber: item.accession,
        name: item.name,
        species: item.species,
        institute: item.collection || 'Unassigned collection',
      }));

    return {
      ...base,
      seedlots: matchingLots,
      observationHistory,
      relatedGermplasm,
    };
  }
}

export const accessionSearchService = new AccessionSearchService();
