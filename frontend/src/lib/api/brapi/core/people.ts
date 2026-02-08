import { ApiClientCore } from "../../core/client";
import { BrAPIResponse, BrAPIListResponse } from "../../core/types";

export class PeopleService {
  constructor(private client: ApiClientCore) {}

  async getPeople(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/people?page=${page}&pageSize=${pageSize}`
    );
  }

  async getPerson(personDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/people/${personDbId}`);
  }

  async createPerson(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/people", data);
  }

  async updatePerson(personDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/people/${personDbId}`,
      data
    );
  }

  async deletePerson(personDbId: string) {
    return this.client.delete(`/brapi/v2/people/${personDbId}`);
  }
}
