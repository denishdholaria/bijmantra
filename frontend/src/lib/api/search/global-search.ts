import { ApiClientCore } from "../core/client";
import { BrAPIListResponse } from "../core/types";

export class GlobalSearchService {
  constructor(private client: ApiClientCore) {}

  async searchGermplasm(searchRequest: any) {
    return this.client.post<BrAPIListResponse<any>>("/brapi/v2/search/germplasm", searchRequest);
  }

  async searchObservations(searchRequest: any) {
    return this.client.post<BrAPIListResponse<any>>("/brapi/v2/search/observations", searchRequest);
  }

  async searchStudies(searchRequest: any) {
    return this.client.post<BrAPIListResponse<any>>("/brapi/v2/search/studies", searchRequest);
  }
}
