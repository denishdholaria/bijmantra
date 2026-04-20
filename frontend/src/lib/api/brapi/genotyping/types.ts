export interface CallSet {
  callSetDbId: string;
  callSetName: string;
  sampleDbId: string;
  studyDbId: string;
  variantSetDbIds: string[];
  created?: string;
  updated?: string;
  additionalInfo?: Record<string, any>;
}

export interface Call {
  callSetDbId: string;
  callSetName: string;
  variantDbId: string;
  variantName: string;
  genotype: {
    values: string[];
  };
  phaseSet?: string;
  genotypeLikelihood?: number[];
}

export interface VariantSet {
  variantSetDbId: string;
  variantSetName: string;
  studyDbId: string;
  referenceSetDbId: string;
  callSetCount: number;
  variantCount: number;
  metadata?: any;
}
