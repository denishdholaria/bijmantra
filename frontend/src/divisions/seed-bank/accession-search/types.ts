export interface AccessionSearchParams {
  query: string;
  page: number;
  pageSize: number;
}

export interface AccessionSearchItem {
  id: string;
  accessionNumber: string;
  name: string;
  species: string;
  institute: string;
  origin: string;
  status: string;
  subspecies?: string;
  traits: string[];
  year?: number;
}

export interface AccessionSearchResult {
  items: AccessionSearchItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface SeedlotInventoryItem {
  lotId: string;
  accessionId: string;
  accessionUuid?: string;
  species: string;
  variety: string;
  quantityGrams: number;
  quantityKg: number;
  storageType: string;
  storageLocation: string;
  currentViabilityPercent?: number;
  lastViabilityTest?: string;
  status: string;
  notes: string;
}

export interface AccessionObservationHistoryItem {
  id: string;
  lotId: string;
  observedAt: string;
  label: string;
  value: string;
  method?: string;
  notes?: string;
}

export interface RelatedGermplasmItem {
  id: string;
  accessionNumber: string;
  name: string;
  species: string;
  institute: string;
}

export interface AccessionDetail {
  id: string;
  accessionNumber: string;
  name: string;
  species: string;
  institute: string;
  origin: string;
  status: string;
  subspecies?: string;
  traits: string[];
  year?: number;
  seedlots: SeedlotInventoryItem[];
  observationHistory: AccessionObservationHistoryItem[];
  relatedGermplasm: RelatedGermplasmItem[];
}
