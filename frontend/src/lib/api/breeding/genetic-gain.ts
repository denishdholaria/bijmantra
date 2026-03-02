import { ApiClientCore } from "../core/client";

export interface GeneticGainCycleData {
  id: string;
  program_id: string;
  cycle: number;
  year: number;
  mean_value: number;
  best_value: number;
  n_entries: number;
  std_dev: number;
}

export interface GeneticGainReleaseData {
  id: string;
  program_id: string;
  variety_name: string;
  year: number;
  trait_value: number;
}

export interface GeneticGainResult {
  program_id: string;
  trait: string;
  gain_per_year: number;
  gain_per_cycle: number;
  r_squared: number;
  cycles: GeneticGainCycleData[];
  releases: GeneticGainReleaseData[];
}

export interface GeneticGainStats {
  total_programs: number;
  avg_gain_per_year: number;
  programs_with_positive_gain: number;
  overall_trend: string;
}

export class GeneticGainService {
  constructor(private client: ApiClientCore) {}

  async getPrograms() {
    return this.client.get<{
      data: Array<{
        id: string;
        name: string;
        crop: string;
        trait: string;
        start_year: number;
        cycles: GeneticGainCycleData[];
        releases: GeneticGainReleaseData[];
      }>;
    }>("/api/v2/genetic-gain/programs");
  }

  async createProgram(data: { name: string; crop: string; trait: string }) {
    return this.client.post<any>("/api/v2/genetic-gain/programs", data);
  }

  async getCycles(programId: string) {
    return this.client.get<{ data: GeneticGainCycleData[] }>(
      `/api/v2/genetic-gain/programs/${programId}/cycles`
    );
  }

  async getReleases(programId: string) {
    return this.client.get<{ data: GeneticGainReleaseData[] }>(
      `/api/v2/genetic-gain/programs/${programId}/releases`
    );
  }

  async recordCycle(
    programId: string,
    data: { year: number; mean: number; variance: number; n_entries: number }
  ) {
    return this.client.post<{ data: GeneticGainCycleData }>(
      `/api/v2/genetic-gain/programs/${programId}/cycles`,
      {
        cycle: 0,
        year: data.year,
        mean_value: data.mean,
        best_value: data.mean * 1.1,
        n_entries: data.n_entries,
        std_dev: Math.sqrt(data.variance),
      }
    );
  }

  async recordRelease(
    programId: string,
    data: { variety_name: string; year: number; value: number }
  ) {
    return this.client.post<{ data: GeneticGainReleaseData }>(
      `/api/v2/genetic-gain/programs/${programId}/releases`,
      {
        variety_name: data.variety_name,
        year: data.year,
        trait_value: data.value,
      }
    );
  }

  async calculateGain(programId: string, useMean: boolean = true) {
    return this.client.get<{ data: GeneticGainResult }>(
      `/api/v2/genetic-gain/programs/${programId}/gain?use_mean=${useMean}`
    );
  }

  async getProjection(programId: string, yearsAhead: number = 10) {
    return this.client.get<{ data: any }>(
      `/api/v2/genetic-gain/programs/${programId}/projection?years_ahead=${yearsAhead}`
    );
  }

  async getRealizedHeritability(programId: string) {
    return this.client.get<{ data: any }>(
      `/api/v2/genetic-gain/programs/${programId}/realized-heritability`
    );
  }

  async getStatistics() {
    return this.client.get<{ data: GeneticGainStats }>(
      "/api/v2/genetic-gain/statistics"
    );
  }
}
