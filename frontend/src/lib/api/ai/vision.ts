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

export type VisionImageMetadata = {
  filename: string;
  content_type: string;
  format: string;
  width: number;
  height: number;
  size_bytes: number;
  quality_warnings: string[];
};

export type VisionPrediction = {
  type?: string;
  label?: string;
  confidence?: number;
  description?: string;
  severity?: string;
  recommendations?: string[];
};

export type VisionAnalyzeResponse = {
  success: boolean;
  status: string;
  image: VisionImageMetadata;
  predictions: VisionPrediction[];
  explainability?: {
    message?: string;
    crop?: string;
  };
  model?: unknown;
};

export class VisionService {
  constructor(private client: ApiClientCore) {}

  async analyzeImage(file: File, crop?: string, modelId?: string) {
    const formData = new FormData();
    formData.append("file", file);
    if (crop) {
      formData.append("crop", crop);
    }
    if (modelId) {
      formData.append("model_id", modelId);
    }
    return this.client.request<VisionAnalyzeResponse>("/api/v2/vision/analyze", {
      method: "POST",
      body: formData,
    });
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
