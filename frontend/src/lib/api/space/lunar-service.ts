import { ApiClientCore } from "../core/client";
import { 
  LunarEnvironmentProfile, 
  LunarEnvironmentProfileCreate, 
  LunarSimulationRequest, 
  LunarSimulationResponse, 
  LunarTrial,
  LunarTrialCreate
} from "./types";

export class LunarService {
  constructor(private client: ApiClientCore) {}

  async createEnvironment(data: LunarEnvironmentProfileCreate) {
    return this.client.request<LunarEnvironmentProfile>("/api/v2/space/lunar/environments", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getEnvironment(id: string) {
    return this.client.request<LunarEnvironmentProfile>(`/api/v2/space/lunar/environments/${id}`);
  }

  async createTrial(data: LunarTrialCreate) {
    return this.client.request<LunarTrial>("/api/v2/space/lunar/trials", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getTrial(id: string) {
    return this.client.request<LunarTrial>(`/api/v2/space/lunar/trials/${id}`);
  }

  async simulate(data: LunarSimulationRequest) {
    return this.client.request<LunarSimulationResponse>("/api/v2/space/lunar/simulate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
}
