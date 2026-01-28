import { ApiClientCore } from "../core/client";

export interface PedigreeRecord {
  id: string;
  sire_id: string | null;
  dam_id: string | null;
}

export interface PedigreeIndividual {
  id: string;
  sire_id: string | null;
  dam_id: string | null;
  generation: number;
  inbreeding: number;
}

export interface PedigreeStats {
  n_individuals: number;
  n_founders: number;
  n_generations: number;
  avg_inbreeding: number;
  max_inbreeding: number;
  completeness_index: number;
}

export interface CoancestryResult {
  coancestry: number;
  relationship: string;
  individual_1: string;
  individual_2: string;
}

export interface AncestorResult {
  individual_id: string;
  sire_id: string | null;
  dam_id: string | null;
  n_ancestors: number;
  ancestors?: string[];
  tree?: PedigreeNode;
}

export interface DescendantResult {
  individual_id: string;
  n_descendants: number;
  descendants?: string[];
}

// Helper inteface
export interface PedigreeNode {
  id: string;
  name?: string;
  type?: string;
  generation?: number;
  sire?: PedigreeNode;
  dam?: PedigreeNode;
}

export class PedigreeAnalysisService {
  constructor(private client: ApiClientCore) {}

  async loadPedigree(pedigree: PedigreeRecord[]) {
    return this.client.post<{ success: boolean; message: string } & PedigreeStats>(
      "/api/v2/pedigree/load",
      { pedigree }
    );
  }

  async getIndividual(individualId: string) {
    return this.client.get<{ success: boolean } & PedigreeIndividual>(
      `/api/v2/pedigree/individual/${individualId}`
    );
  }

  async getIndividuals(generation?: number) {
    const params = generation !== undefined ? `?generation=${generation}` : "";
    return this.client.get<{
      success: boolean;
      count: number;
      individuals: PedigreeIndividual[];
    }>(`/api/v2/pedigree/individuals${params}`);
  }

  async getStats() {
    return this.client.get<{ success: boolean } & PedigreeStats>(
      "/api/v2/pedigree/stats"
    );
  }

  async getRelationshipMatrix(individualIds?: string[]) {
    return this.client.post<{
      success: boolean;
      individuals: string[];
      matrix: number[][];
    }>("/api/v2/pedigree/relationship-matrix", { individual_ids: individualIds });
  }

  async getAncestors(individualId: string, maxGenerations: number = 5) {
    return this.client.get<{ success: boolean } & AncestorResult>(
      `/api/v2/pedigree/ancestors/${individualId}?max_generations=${maxGenerations}`
    );
  }

  async getDescendants(individualId: string, maxGenerations: number = 3) {
    return this.client.get<{ success: boolean } & DescendantResult>(
      `/api/v2/pedigree/descendants/${individualId}?max_generations=${maxGenerations}`
    );
  }

  async calculateCoancestry(individual1: string, individual2: string) {
    return this.client.post<{ success: boolean } & CoancestryResult>(
      "/api/v2/pedigree/coancestry",
      { individual_1: individual1, individual_2: individual2 }
    );
  }
}
