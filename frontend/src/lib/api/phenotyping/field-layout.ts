import { ApiClientCore } from "../core/client";

export interface FieldStudy {
  studyDbId: string;
  studyName: string;
  rows: number;
  cols: number;
  programDbId?: string;
  locationDbId?: string;
  startDate?: string;
  endDate?: string;
}

export interface FieldPlot {
  plotNumber: string;
  row: number;
  col: number;
  germplasmName?: string;
  germplasmDbId?: string;
  blockNumber?: number;
  replicate?: number;
  entryType?: string;
  observationUnitDbId?: string;
}

export interface FieldLayoutSummary {
  total_plots: number;
  check_plots: number;
  test_plots: number;
  unique_germplasm: number;
  blocks: number;
  replicates: number;
}

export class FieldLayoutService {
  constructor(private client: ApiClientCore) {}

  async getStudies(params?: { program_id?: string; search?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.program_id) searchParams.set("program_id", params.program_id);
    if (params?.search) searchParams.set("search", params.search);
    const query = searchParams.toString();
    return this.client.get<{ data: FieldStudy[]; total: number }>(
      `/api/v2/field-layout/studies${query ? `?${query}` : ""}`
    );
  }

  async getStudy(studyId: string) {
    return this.client.get<{ data: FieldStudy }>(
      `/api/v2/field-layout/studies/${studyId}`
    );
  }

  async getLayout(studyId: string) {
    return this.client.get<{
      study: FieldStudy;
      plots: FieldPlot[];
      summary: FieldLayoutSummary;
    }>(`/api/v2/field-layout/studies/${studyId}/layout`);
  }

  async getPlots(
    studyId: string,
    params?: { block?: number; replicate?: number; entry_type?: string }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.block) searchParams.set("block", params.block.toString());
    if (params?.replicate)
      searchParams.set("replicate", params.replicate.toString());
    if (params?.entry_type) searchParams.set("entry_type", params.entry_type);
    const query = searchParams.toString();
    return this.client.get<{ data: FieldPlot[]; total: number }>(
      `/api/v2/field-layout/studies/${studyId}/plots${query ? `?${query}` : ""}`
    );
  }

  async getPlot(studyId: string, plotNumber: string) {
    return this.client.get<{ data: FieldPlot }>(
      `/api/v2/field-layout/studies/${studyId}/plots/${plotNumber}`
    );
  }

  async updatePlot(
    studyId: string,
    plotNumber: string,
    data: Partial<FieldPlot>
  ) {
    return this.client.put<any>(
      `/api/v2/field-layout/studies/${studyId}/plots/${plotNumber}`,
      data
    );
  }

  async getGermplasm() {
    return this.client.get<{
      data: Array<{ germplasmDbId: string; germplasmName: string }>;
    }>("/api/v2/field-layout/germplasm");
  }

  async generateLayout(
    studyId: string,
    params: { design?: string; blocks?: number; replicates?: number }
  ) {
    const searchParams = new URLSearchParams();
    if (params.design) searchParams.set("design", params.design);
    if (params.blocks) searchParams.set("blocks", params.blocks.toString());
    if (params.replicates)
      searchParams.set("replicates", params.replicates.toString());
    return this.client.post<any>(
      `/api/v2/field-layout/studies/${studyId}/generate?${searchParams}`,
      {}
    );
  }

  async exportLayout(studyId: string, format: string = "csv") {
    return this.client.get<any>(
      `/api/v2/field-layout/export/${studyId}?format=${format}`
    );
  }
}
