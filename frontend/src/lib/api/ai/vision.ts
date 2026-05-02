import { ApiClientCore } from "../core/client";

export type VisionCrop = {
  code: string;
  name: string;
  icon: string;
  diseases: number;
  stages: number;
};

export type VisionModelSummary = {
  id?: string;
  name?: string;
  status?: string;
};

export type VisionDatasetSummary = {
  id?: string;
  name?: string;
  total_images?: number;
};

export class VisionService {
  constructor(private client: ApiClientCore) {}

  async analyzeImage(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return this.client.post<any>("/api/v2/vision/analyze", formData);
  }

  async getAnalysisResults(analysisId: string) {
    return this.client.get<any>(`/api/v2/vision/analyses/${analysisId}`);
  }
  async getCrops() {
    return this.client.get<{ crops: VisionCrop[] }>("/api/v2/vision/crops");
  }

  async getModels() {
    return this.client.get<{ models: VisionModelSummary[] }>("/api/v2/vision/models");
  }

  async getDatasets() {
    return this.client.get<{ datasets: VisionDatasetSummary[] }>("/api/v2/vision/datasets");
  }
}
