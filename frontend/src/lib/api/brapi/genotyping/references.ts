import { ApiClientCore } from "../../core/client";

export interface Reference {
  referenceDbId: string;
  referenceName: string;
  referenceSetDbId: string;
  length: number;
  md5checksum?: string;
}

export interface ReferenceSet {
  referenceSetDbId: string;
  referenceSetName: string;
  description?: string;
  species?: { genus: string; species: string };
}

export class ReferencesService {
  constructor(private client: ApiClientCore) {}

  async getReferences(params?: {
    referenceSetDbId?: string;
    pageSize?: number;
    page?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.referenceSetDbId)
      searchParams.append("referenceSetDbId", params.referenceSetDbId);
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    if (params?.page) searchParams.append("page", String(params.page));

    return this.client.get<{ result: { data: Reference[] } }>(
      `/brapi/v2/references?${searchParams}`
    );
  }

  async getReferenceSets(params?: { pageSize?: number; page?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    if (params?.page) searchParams.append("page", String(params.page));

    return this.client.get<{ result: { data: ReferenceSet[] } }>(
      `/brapi/v2/referencesets?${searchParams}`
    );
  }
}
