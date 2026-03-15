import { ApiClientCore } from "../core/client";

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
    return this.client.get<{ crops: any[] }>("/api/v2/vision/crops");
  }

  async getModels() {
    return this.client.get<{ models: any[] }>("/api/v2/vision/models");
  }

  async getDatasets() {
    return this.client.get<{ datasets: any[] }>("/api/v2/vision/datasets");
  }
}
