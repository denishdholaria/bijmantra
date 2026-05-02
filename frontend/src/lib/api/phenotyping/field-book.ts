import { ApiClientCore } from "../core/client";

export interface FieldBookStudy {
  id: string;
  name: string;
  location: string;
  season: string;
  design: string;
  reps: number;
  entries: number;
  traits: number;
}

export interface FieldBookEntry {
  plot_id: string;
  germplasm: string;
  rep: string;
  row: number;
  col: number;
  traits: Record<string, number | string | null>;
}

export interface FieldBookTrait {
  id: string;
  name: string;
  unit: string;
  min: number;
  max: number;
  step: number;
}

export class FieldBookService {
  constructor(private client: ApiClientCore) {}

  async getStudies() {
    return this.client.get<{
      success: boolean;
      count: number;
      studies: FieldBookStudy[];
    }>("/api/v2/field-book/studies");
  }

  async getStudyEntries(studyId: string) {
    return this.client.get<{
      success: boolean;
      study_id: string;
      study_name: string;
      count: number;
      entries: FieldBookEntry[];
    }>(`/api/v2/field-book/studies/${studyId}/entries`);
  }

  async getStudyTraits(studyId: string) {
    return this.client.get<{
      success: boolean;
      study_id: string;
      traits: FieldBookTrait[];
    }>(`/api/v2/field-book/studies/${studyId}/traits`);
  }

  async recordObservation(data: {
    study_id: string;
    plot_id: string;
    trait_id: string;
    value: any;
    notes?: string;
  }) {
    return this.client.post<{
      success: boolean;
      message: string;
      study_id: string;
      plot_id: string;
      trait_id: string;
      value: any;
      timestamp: string;
    }>("/api/v2/field-book/observations", data);
  }

  async recordBulkObservations(data: {
    study_id: string;
    observations: Array<{ plot_id: string; trait_id: string; value: any }>;
  }) {
    return this.client.post<{
      success: boolean;
      message: string;
      study_id: string;
      observations_recorded: number;
    }>("/api/v2/field-book/observations/bulk", data);
  }

  async getProgress(studyId: string, traitId?: string) {
    const query = traitId ? `?trait_id=${traitId}` : "";
    return this.client.get<{
      success: boolean;
      study_id: string;
      overall: { collected: number; total: number; percentage: number };
      by_trait: Record<
        string,
        {
          trait_name: string;
          collected: number;
          total: number;
          percentage: number;
        }
      >;
    }>(`/api/v2/field-book/studies/${studyId}/progress${query}`);
  }

  async getSummary(studyId: string) {
    return this.client.get<{
      success: boolean;
      study_id: string;
      study_name: string;
      total_entries: number;
      total_traits: number;
      summaries: Record<
        string,
        {
          trait_name: string;
          unit: string;
          count: number;
          mean: number | null;
          min: number | null;
          max: number | null;
          range: number | null;
        }
      >;
    }>(`/api/v2/field-book/studies/${studyId}/summary`);
  }

  async deleteObservation(studyId: string, plotId: string, traitId: string) {
    return this.client.delete<{ success: boolean; message: string }>(
      `/api/v2/field-book/observations/${studyId}/${plotId}/${traitId}`
    );
  }
}
