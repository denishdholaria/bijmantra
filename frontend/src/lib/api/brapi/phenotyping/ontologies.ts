import { ApiClientCore } from "../../core/client";
import { BrAPIListResponse, BrAPIResponse } from "../../core/types";

export class OntologiesService {
  constructor(private client: ApiClientCore) {}

  async getOntologies(params?: {
    ontologyDbId?: string;
    ontologyName?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.ontologyDbId)
      searchParams.append("ontologyDbId", params.ontologyDbId);
    if (params?.ontologyName)
      searchParams.append("ontologyName", params.ontologyName);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));

    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/ontologies?${searchParams}`
    );
  }

  async getOntology(ontologyDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/ontologies/${ontologyDbId}`
    );
  }
}
