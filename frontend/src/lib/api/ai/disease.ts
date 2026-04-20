import { ApiClientCore } from "../core/client";

export type DiseaseRecord = {
  id?: string;
  name: string;
  pathogen: string;
  severity?: string;
  crop?: string;
};

export type DiseaseListResponse = {
  diseases: DiseaseRecord[];
  total: number;
};

export class DiseaseService {
  constructor(private client: ApiClientCore) {}

  async detectDisease(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return this.client.post<any>("/api/v2/disease/detect", formData);
  }

  async getDetectionHistory(
    page = 0,
    pageSize = 20,
    locationId?: string,
    crop?: string
  ) {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (locationId) params.append("location_id", locationId);
    if (crop) params.append("crop", crop);
    return this.client.get<any>(`/api/v2/disease/history?${params}`);
  }
  async getDiseases(params?: { crop?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.append("crop", params.crop);
    return this.client.get<DiseaseListResponse>(
      `/api/v2/disease/diseases?${searchParams}`
    );
  }
}
