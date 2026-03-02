import { ApiClientCore } from "../core/client";

export class PhenomicSelectionService {
  constructor(private client: ApiClientCore) {}

  async getDatasets(params?: { crop?: string; platform?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.append("crop", params.crop);
    if (params?.platform) searchParams.append("platform", params.platform);
    return this.client.get<any>(
      `/api/v2/phenomic-selection/datasets?${searchParams}`
    );
  }

  async getDataset(datasetId: string) {
    return this.client.get<any>(
      `/api/v2/phenomic-selection/datasets/${datasetId}`
    );
  }

  async getModels(params?: { dataset_id?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.dataset_id)
      searchParams.append("dataset_id", params.dataset_id);
    if (params?.status) searchParams.append("status", params.status);
    return this.client.get<any>(
      `/api/v2/phenomic-selection/models?${searchParams}`
    );
  }

  async predictTraits(modelId: string, sampleIds: string[]) {
    return this.client.post<any>("/api/v2/phenomic-selection/predict", {
      model_id: modelId,
      sample_ids: sampleIds,
    });
  }

  async uploadSpectralData(
    file: File,
    datasetName?: string,
    crop?: string,
    platform: string = "NIRS"
  ) {
    const formData = new FormData();
    formData.append("file", file);
    if (datasetName) formData.append("dataset_name", datasetName);
    if (crop) formData.append("crop", crop);
    formData.append("platform", platform);

    return this.client.request<any>("/api/v2/phenomic-selection/upload", {
      method: "POST",
      body: formData,
    });
  }

  async getSpectralData(datasetId: string, sampleId?: string) {
    const searchParams = new URLSearchParams();
    if (sampleId) searchParams.append("sample_id", sampleId);
    return this.client.get<any>(
      `/api/v2/phenomic-selection/spectral/${datasetId}?${searchParams}`
    );
  }

  async getStatistics() {
    return this.client.get<any>("/api/v2/phenomic-selection/statistics");
  }
}
