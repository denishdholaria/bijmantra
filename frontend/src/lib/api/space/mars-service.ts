import { ApiClientCore } from "../core/client";
import { 
  MarsEnvironmentProfile, 
  MarsEnvironmentProfileCreate, 
  MarsSimulationRequest, 
  MarsSimulationResponse, 
  MarsTrial 
} from "./types";

export class MarsService {
  constructor(private client: ApiClientCore) {}

  async createEnvironment(data: MarsEnvironmentProfileCreate) {
    return this.client.request<MarsEnvironmentProfile>("/api/v2/space/mars/environments", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getEnvironment(id: string) {
    return this.client.request<MarsEnvironmentProfile>(`/api/v2/space/mars/environments/${id}`);
  }

  async simulateTrial(data: MarsSimulationRequest) {
    return this.client.request<MarsSimulationResponse>("/api/v2/space/mars/simulate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getTrial(id: string) {
    return this.client.request<MarsTrial>(`/api/v2/space/mars/trials/${id}`);
  }
}
