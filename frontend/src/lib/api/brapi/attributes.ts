import { ApiClientCore } from "../core/client";

export interface GermplasmAttribute {
  attributeDbId: string;
  attributeName: string;
  attributeCategory?: string;
  attributeDescription?: string;
  dataType?: string;
  commonCropName?: string;
  values?: string[];
}

export class GermplasmAttributesService {
  constructor(private client: ApiClientCore) {}
  async getAttributes(params?: {
    attributeCategory?: string;
    pageSize?: number;
    page?: number;
  }): Promise<{ result: { data: GermplasmAttribute[] } }> {
    const searchParams = new URLSearchParams();
    if (params?.attributeCategory)
      searchParams.set("attributeCategory", params.attributeCategory);
    if (params?.pageSize)
      searchParams.set("pageSize", params.pageSize.toString());
    if (params?.page) searchParams.set("page", params.page.toString());
    const query = searchParams.toString();
    return this.client.get<{ result: { data: GermplasmAttribute[] } }>(
      `/brapi/v2/attributes${query ? `?${query}` : ""}`
    );
  }

  async getAttribute(
    attributeDbId: string,
  ): Promise<{ result: GermplasmAttribute }> {
    return this.client.get<{ result: GermplasmAttribute }>(`/brapi/v2/attributes/${attributeDbId}`);
  }

  async getCategories(): Promise<{ result: { data: string[] } }> {
    return this.client.get<{ result: { data: string[] } }>("/brapi/v2/attributes/categories");
  }

  async createAttribute(
    data: Partial<GermplasmAttribute>,
  ): Promise<{ result: { data: GermplasmAttribute[] } }> {
    return this.client.post<{ result: { data: GermplasmAttribute[] } }>(
      "/brapi/v2/attributes",
      [data]
    );
  }

  async updateAttribute(
    attributeDbId: string,
    data: Partial<GermplasmAttribute>,
  ): Promise<{ result: GermplasmAttribute }> {
    return this.client.put<{ result: GermplasmAttribute }>(
      `/brapi/v2/attributes/${attributeDbId}`,
      data
    );
  }

  async deleteAttribute(attributeDbId: string): Promise<any> {
    return this.client.delete(`/brapi/v2/attributes/${attributeDbId}`);
  }
}
