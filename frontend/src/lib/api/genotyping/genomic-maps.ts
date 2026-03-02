import { ApiClientCore } from "../core/client";
import { BrAPIListResponse, BrAPIResponse } from "./genotyping-results";

export class GenomicMapService {
  constructor(private client: ApiClientCore) {}

  // ============ References ============

  async getReferences(params?: {
    referenceDbId?: string;
    referenceSetDbId?: string;
    accession?: string;
    md5checksum?: string;
    isDerived?: boolean;
    minLength?: number;
    maxLength?: number;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.referenceDbId)
      searchParams.append("referenceDbId", params.referenceDbId);
    if (params?.referenceSetDbId)
      searchParams.append("referenceSetDbId", params.referenceSetDbId);
    if (params?.accession) searchParams.append("accession", params.accession);
    if (params?.md5checksum)
      searchParams.append("md5checksum", params.md5checksum);
    if (params?.isDerived !== undefined)
      searchParams.append("isDerived", String(params.isDerived));
    if (params?.minLength !== undefined)
      searchParams.append("minLength", String(params.minLength));
    if (params?.maxLength !== undefined)
      searchParams.append("maxLength", String(params.maxLength));
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/references?${searchParams}`
    );
  }

  async getReference(referenceDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/references/${referenceDbId}`
    );
  }

  async getReferenceBases(
    referenceDbId: string,
    params?: { start?: number; end?: number }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.start !== undefined)
      searchParams.append("start", String(params.start));
    if (params?.end !== undefined)
      searchParams.append("end", String(params.end));
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/references/${referenceDbId}/bases?${searchParams}`
    );
  }

  // ============ ReferenceSets ============

  async getReferenceSets(params?: {
    referenceSetDbId?: string;
    accession?: string;
    assemblyPUI?: string;
    md5checksum?: string;
    isDerived?: boolean;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.referenceSetDbId)
      searchParams.append("referenceSetDbId", params.referenceSetDbId);
    if (params?.accession) searchParams.append("accession", params.accession);
    if (params?.assemblyPUI)
      searchParams.append("assemblyPUI", params.assemblyPUI);
    if (params?.md5checksum)
      searchParams.append("md5checksum", params.md5checksum);
    if (params?.isDerived !== undefined)
      searchParams.append("isDerived", String(params.isDerived));
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/referencesets?${searchParams}`
    );
  }

  async getReferenceSet(referenceSetDbId: string) {
    return this.client.get<BrAPIResponse<any>>(
      `/brapi/v2/referencesets/${referenceSetDbId}`
    );
  }

  // ============ Maps ============

  async getMaps(params?: {
    mapDbId?: string;
    mapPUI?: string;
    scientificName?: string;
    commonCropName?: string;
    type?: string;
    programDbId?: string;
    trialDbId?: string;
    studyDbId?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.mapDbId) searchParams.append("mapDbId", params.mapDbId);
    if (params?.mapPUI) searchParams.append("mapPUI", params.mapPUI);
    if (params?.scientificName)
      searchParams.append("scientificName", params.scientificName);
    if (params?.commonCropName)
      searchParams.append("commonCropName", params.commonCropName);
    if (params?.type) searchParams.append("type", params.type);
    if (params?.programDbId)
      searchParams.append("programDbId", params.programDbId);
    if (params?.trialDbId) searchParams.append("trialDbId", params.trialDbId);
    if (params?.studyDbId) searchParams.append("studyDbId", params.studyDbId);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/maps?${searchParams}`
    );
  }

  async getMap(mapDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/maps/${mapDbId}`);
  }

  async getMapLinkageGroups(
    mapDbId: string,
    params?: { page?: number; pageSize?: number }
  ) {
    const searchParams = new URLSearchParams();
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/maps/${mapDbId}/linkagegroups?${searchParams}`
    );
  }

  async createMap(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/maps", data);
  }

  async updateMap(mapDbId: string, data: any) {
    return this.client.put<BrAPIResponse<any>>(
      `/brapi/v2/maps/${mapDbId}`,
      data
    );
  }

  async deleteMap(mapDbId: string) {
    return this.client.delete<BrAPIResponse<any>>(`/brapi/v2/maps/${mapDbId}`);
  }

  // ============ Marker Positions ============

  async getMarkerPositions(params?: {
    mapDbId?: string;
    linkageGroupName?: string;
    variantDbId?: string;
    minPosition?: number;
    maxPosition?: number;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.mapDbId) searchParams.append("mapDbId", params.mapDbId);
    if (params?.linkageGroupName)
      searchParams.append("linkageGroupName", params.linkageGroupName);
    if (params?.variantDbId)
      searchParams.append("variantDbId", params.variantDbId);
    if (params?.minPosition !== undefined)
      searchParams.append("minPosition", String(params.minPosition));
    if (params?.maxPosition !== undefined)
      searchParams.append("maxPosition", String(params.maxPosition));
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/markerpositions?${searchParams}`
    );
  }
}
