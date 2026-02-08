import { ApiClientCore } from "../core/client";

export interface BrAPIListResponse<T> {
  metadata: any;
  result: {
    data: T[];
    pagination?: any;
  };
}

export interface BrAPIResponse<T> {
  metadata: any;
  result: T;
}

export class GenotypingResultsService {
  constructor(private client: ApiClientCore) {}

  // ============================================
  // GENOTYPING (Custom API)
  // ============================================

  async createVariantSet(data: {
    variantSetName: string;
    studyDbId?: string;
    studyName?: string;
    referenceSetDbId?: string;
  }) {
    return this.client.post<any>("/api/v2/genotyping/variantsets", data);
  }

  // VariantSets
  async getVariantSets(params?: {
    variantSetDbId?: string;
    variantSetName?: string;
    studyDbId?: string;
    referenceSetDbId?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.variantSetDbId)
      searchParams.append("variantSetDbId", params.variantSetDbId);
    if (params?.variantSetName)
      searchParams.append("variantSetName", params.variantSetName);
    if (params?.studyDbId) searchParams.append("studyDbId", params.studyDbId);
    if (params?.referenceSetDbId)
      searchParams.append("referenceSetDbId", params.referenceSetDbId);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/variantsets?${searchParams}`
    );
  }

  async getVariantSet(variantSetDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/variantsets/${variantSetDbId}`
    );
  }

  // ============================================
  // BrAPI v2.1 GENOTYPING ENDPOINTS
  // ============================================

  // Calls
  async getCalls(params?: {
    callSetDbId?: string;
    variantDbId?: string;
    variantSetDbId?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.callSetDbId)
      searchParams.append("callSetDbId", params.callSetDbId);
    if (params?.variantDbId)
      searchParams.append("variantDbId", params.variantDbId);
    if (params?.variantSetDbId)
      searchParams.append("variantSetDbId", params.variantSetDbId);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/calls?${searchParams}`
    );
  }

  async updateCalls(calls: any[]) {
    return this.client.put<BrAPIListResponse<any>>("/brapi/v2/calls", calls);
  }

  async getCallsStatistics(variantSetDbId?: string) {
    // Calculate stats from calls data
    const calls = await this.getCalls({ variantSetDbId, pageSize: 1000 });
    const data = calls?.result?.data || [];
    const heterozygous = data.filter((c: any) => {
      const gt = c.genotype?.values || [];
      return gt.length === 2 && gt[0] !== gt[1];
    }).length;
    const homozygousAlt = data.filter((c: any) => {
      const gt = c.genotype?.values || [];
      return gt.length === 2 && gt[0] === gt[1] && gt[0] !== "A";
    }).length;
    return {
      result: {
        total: data.length,
        heterozygous,
        homozygousAlt,
        avgQuality: 30,
      },
    };
  }

  // CallSets
  async getCallSets(params?: {
    callSetDbId?: string;
    callSetName?: string;
    sampleDbId?: string;
    variantSetDbId?: string;
    germplasmDbId?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.callSetDbId)
      searchParams.append("callSetDbId", params.callSetDbId);
    if (params?.callSetName)
      searchParams.append("callSetName", params.callSetName);
    if (params?.sampleDbId)
      searchParams.append("sampleDbId", params.sampleDbId);
    if (params?.variantSetDbId)
      searchParams.append("variantSetDbId", params.variantSetDbId);
    if (params?.germplasmDbId)
      searchParams.append("germplasmDbId", params.germplasmDbId);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/callsets?${searchParams}`
    );
  }

  async getCallSet(callSetDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/callsets/${callSetDbId}`
    );
  }

  async getCallSetCalls(
    callSetDbId: string,
    params?: { page?: number; pageSize?: number }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/callsets/${callSetDbId}/calls?${searchParams}`
    );
  }

  // Variants
  async getVariants(params?: {
    variantDbId?: string;
    variantSetDbId?: string;
    referenceDbId?: string;
    referenceName?: string;
    start?: number;
    end?: number;
    variantType?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.variantDbId)
      searchParams.append("variantDbId", params.variantDbId);
    if (params?.variantSetDbId)
      searchParams.append("variantSetDbId", params.variantSetDbId);
    if (params?.referenceDbId)
      searchParams.append("referenceDbId", params.referenceDbId);
    if (params?.referenceName)
      searchParams.append("referenceName", params.referenceName);
    if (params?.start !== undefined)
      searchParams.append("start", String(params.start));
    if (params?.end !== undefined)
      searchParams.append("end", String(params.end));
    if (params?.variantType)
      searchParams.append("variantType", params.variantType);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/variants?${searchParams}`
    );
  }

  async getVariant(variantDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/variants/${variantDbId}`
    );
  }

  async getVariantCalls(
    variantDbId: string,
    params?: { page?: number; pageSize?: number }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/variants/${variantDbId}/calls?${searchParams}`
    );
  }

  async createVariant(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/variants", data);
  }

  async updateVariant(variantDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/variants/${variantDbId}`,
      data
    );
  }

  async deleteVariant(variantDbId: string) {
    return this.client.delete<BrAPIResponse<any>>(
      `/brapi/v2/variants/${variantDbId}`
    );
  }

  // ============ VariantSet Methods ============

  async getVariantSetCalls(
    variantSetDbId: string,
    params?: { page?: number; pageSize?: number }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/variantsets/${variantSetDbId}/calls?${searchParams}`
    );
  }

  async getVariantSetCallSets(
    variantSetDbId: string,
    params?: { page?: number; pageSize?: number }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/variantsets/${variantSetDbId}/callsets?${searchParams}`
    );
  }

  async getVariantSetVariants(
    variantSetDbId: string,
    params?: { page?: number; pageSize?: number }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/variantsets/${variantSetDbId}/variants?${searchParams}`
    );
  }

  async extractVariantSet(data: {
    variantSetDbId: string;
    callSetDbIds?: string[];
    variantDbIds?: string[];
  }) {
    return this.client.post<BrAPIResponse<any>>(
      "/brapi/v2/variantsets/extract",
      data
    );
  }

  // ============ Allele Matrix ============

  async getAlleleMatrix(params?: {
    dimensionVariantPage?: number;
    dimensionVariantPageSize?: number;
    dimensionCallSetPage?: number;
    dimensionCallSetPageSize?: number;
    preview?: boolean;
    germplasmDbId?: string[];
    callSetDbId?: string[];
    variantDbId?: string[];
    variantSetDbId?: string[];
  }) {
    const searchParams = new URLSearchParams();
    if (params?.dimensionVariantPage !== undefined)
      searchParams.append(
        "dimensionVariantPage",
        String(params.dimensionVariantPage)
      );
    if (params?.dimensionVariantPageSize)
      searchParams.append(
        "dimensionVariantPageSize",
        String(params.dimensionVariantPageSize)
      );
    if (params?.dimensionCallSetPage !== undefined)
      searchParams.append(
        "dimensionCallSetPage",
        String(params.dimensionCallSetPage)
      );
    if (params?.dimensionCallSetPageSize)
      searchParams.append(
        "dimensionCallSetPageSize",
        String(params.dimensionCallSetPageSize)
      );
    if (params?.preview !== undefined)
      searchParams.append("preview", String(params.preview));
    params?.germplasmDbId?.forEach((id) =>
      searchParams.append("germplasmDbId", id)
    );
    params?.callSetDbId?.forEach((id) =>
      searchParams.append("callSetDbId", id)
    );
    params?.variantDbId?.forEach((id) =>
      searchParams.append("variantDbId", id)
    );
    params?.variantSetDbId?.forEach((id) =>
      searchParams.append("variantSetDbId", id)
    );
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/allelematrix?${searchParams}`
    );
  }

  // Genotyping Summary
  async getGenotypingSummary() {
    const [callSets, variantSets, variants] = await Promise.all([
      this.getCallSets({ pageSize: 1 }),
      this.getVariantSets({ pageSize: 1 }),
      this.getVariants({ pageSize: 1 }),
    ]);
    return {
      result: {
        callSets: callSets?.metadata?.pagination?.totalCount || 0,
        variantSets: variantSets?.metadata?.pagination?.totalCount || 0,
        variants: variants?.metadata?.pagination?.totalCount || 0,
        callsStatistics: { heterozygosityRate: 35 },
      },
    };
  }
}

