export interface SeedLot {
  lot_id: string;
  accession_id: string;
  species: string;
  variety: string;
  harvest_date: string;
  quantity: number;
  storage_type: string;
  storage_location: string;
  current_viability: number;
  status: string;
  last_test_date?: string;
  notes: string;
}

export interface ViabilityTest {
  test_id: string;
  lot_id: string;
  test_date: string;
  seeds_tested: number;
  seeds_germinated: number;
  germination_percent: number;
  test_method: string;
  tester: string;
  notes: string;
  id?: string;
}

export interface SeedInventorySummary {
  success: boolean;
  total_lots: number;
  total_quantity: number;
  by_status: Record<string, number>;
  by_storage_type: Record<string, number>;
  by_species: Record<string, number>;
  lots_needing_test: number;
}

export interface CreateSeedRequest {
  lot_id: string;
  requester: string;
  institution: string;
  quantity: number;
  purpose?: string;
}
