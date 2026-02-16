import { ApiClientCore } from "../core/client";
import { 
  RadiationRequest, 
  LifeSupportRequest 
} from "./types";

export class ResearchService {
  constructor(private client: ApiClientCore) {}

  async getCrops() {
    return this.client.request<{ data: any[] }>("/api/v2/space/research/crops");
  }

  async getCrop(id: string) {
    return this.client.request<{ data: any }>(`/api/v2/space/research/crops/${id}`);
  }

  async getCropEnvironment(id: string) {
    return this.client.request<{ data: any }>(`/api/v2/space/research/crops/${id}/environment`);
  }

  async getExperiments(status?: string) {
    const query = status ? `?status=${status}` : "";
    return this.client.request<{ data: any[] }>(`/api/v2/space/research/experiments${query}`);
  }

  async calculateRadiation(data: RadiationRequest) {
    return this.client.request<{ data: any }>("/api/v2/space/research/radiation", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async calculateLifeSupport(data: LifeSupportRequest) {
    return this.client.request<{ data: any }>("/api/v2/space/research/life-support", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getMissions() {
    return this.client.request<{ data: any[] }>("/api/v2/space/research/missions");
  }

  async getAgencies() {
    return this.client.request<{ data: any[] }>("/api/v2/space/research/agencies");
  }
}
