import { apiClient } from "@/lib/api-client";

export interface BrAPIResponse<T> {
  metadata: {
    pagination: {
      currentPage: number;
      pageSize: number;
      totalCount: number;
      totalPages: number;
    };
    status: any[];
    datafiles: any[];
  };
  result: {
    data: T[];
  };
}

export interface Marker {
  markerDbId: string;
  defaultDisplayName: string;
  markerName: string;
  markerType: string;
  synonyms: string[];
  refAlt: string[];
  analysisMethods: string[];
}

export interface Variant {
  variantDbId: string;
  variantName: string;
  variantSetDbId: string[];
  referenceName: string;
  start: number;
  end: number;
  alternateBases: string[];
  referenceBases: string;
}

export interface VariantSet {
  variantSetDbId: string;
  variantSetName: string;
  studyDbId: string;
  referenceSetDbId: string;
  callSetCount: number;
  variantCount: number;
  dataFormat: string;
}

export interface CallSet {
  callSetDbId: string;
  callSetName: string;
  variantSetDbId: string[];
  sampleDbId: string;
  germplasmDbId: string;
}

export interface Call {
  callSetDbId: string;
  callSetName: string;
  variantDbId: string;
  variantName: string;
  genotype: {
    values: string[];
  };
  genotype_likelihood: number[];
  phaseSet: string;
}

export interface Reference {
  referenceDbId: string;
  referenceName: string;
  referenceSetDbId: string;
  length: number;
  md5checksum: string;
  sourceUri: string;
}

export interface ReferenceSet {
  referenceSetDbId: string;
  referenceSetName: string;
  description: string;
  assemblyPUI: string;
  sourceUri: string;
  species: {
    commonName: string;
  };
}

export interface GenomicMap {
  mapDbId: string;
  mapName: string;
  markerCount: number;
  linkageGroupCount: number;
  type: string;
  publishedDate: string;
}

export interface MarkerProfile {
  markerProfileDbId: string;
  germplasmDbId: string;
  uniqueDisplayName: string;
  extractDbId: string;
  analysisMethod: string;
  resultCount: number;
}

export interface AlleleMatrix {
  data: string[][];
  callSetDbIds: string[];
  variantDbIds: string[];
}

export interface Sample {
  sampleDbId: string;
  sampleName: string;
  sampleType: string;
  plateDbId: string;
  plateName: string;
  row: string;
  column: string;
  germplasmDbId: string;
  observationUnitDbId: string;
}

export interface Plate {
  plateDbId: string;
  plateName: string;
  plateBarcode: string;
  plateFormat: string;
  sampleType: string;
  status: string;
}

export const GenotypingService = {
  // 1. Markers
  getMarkers: async (params: { page?: number; pageSize?: number; markerDbId?: string; name?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<Marker>>("/brapi/v2/markers", { params });
    return data;
  },

  // 2. Variants
  getVariants: async (params: { page?: number; pageSize?: number; variantDbId?: string; variantSetDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<Variant>>("/brapi/v2/variants", { params });
    return data;
  },

  // 3. Variant Sets
  getVariantSets: async (params: { page?: number; pageSize?: number; variantSetDbId?: string; studyDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<VariantSet>>("/brapi/v2/variantsets", { params });
    return data;
  },

  // 4. Call Sets
  getCallSets: async (params: { page?: number; pageSize?: number; callSetDbId?: string; variantSetDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<CallSet>>("/brapi/v2/callsets", { params });
    return data;
  },

  // 5. Calls
  getCalls: async (params: { page?: number; pageSize?: number; callSetDbId?: string; variantDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<Call>>("/brapi/v2/calls", { params });
    return data;
  },

  // 6. References
  getReferences: async (params: { page?: number; pageSize?: number; referenceDbId?: string; referenceSetDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<Reference>>("/brapi/v2/references", { params });
    return data;
  },

  // 7. Reference Sets
  getReferenceSets: async (params: { page?: number; pageSize?: number; referenceSetDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<ReferenceSet>>("/brapi/v2/referencesets", { params });
    return data;
  },

  // 8. Maps
  getMaps: async (params: { page?: number; pageSize?: number; mapDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<GenomicMap>>("/brapi/v2/maps", { params });
    return data;
  },

  // 9. Marker Profiles
  getMarkerProfiles: async (params: { page?: number; pageSize?: number; germplasmDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<MarkerProfile>>("/brapi/v1/markerprofiles", { params });
    return data;
  },

  // 10. Allele Matrix
  getAlleleMatrix: async (params: { page?: number; pageSize?: number; dimension?: string } = {}) => {
    // Note: Allele Matrix usually has a different structure, simplified here
    const { data } = await apiClient.get<BrAPIResponse<AlleleMatrix>>("/brapi/v2/allelematrix", { params });
    return data;
  },

  // 11. Samples
  getSamples: async (params: { page?: number; pageSize?: number; sampleDbId?: string; plateDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<Sample>>("/brapi/v2/samples", { params });
    return data;
  },

  // 12. Plates
  getPlates: async (params: { page?: number; pageSize?: number; plateDbId?: string } = {}) => {
    const { data } = await apiClient.get<BrAPIResponse<Plate>>("/brapi/v2/plates", { params });
    return data;
  },
};
