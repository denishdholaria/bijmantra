export interface Germplasm {
  germplasmDbId: string;
  germplasmName: string;
  accessionNumber?: string;
  commonCropName: string;
  genus?: string;
  species?: string;
  subtaxa?: string;
  pedigree?: string;
  seedSource?: string;
  biologicalStatusOfAccessionCode?: string | number;
  countryOfOriginCode?: string;
  synonyms?: string[];
  typeOfGermplasmStorageCode?: string[];
  acquisitionDate?: string;
  defaultDisplayName?: string;
  germplasmType?: string;
  germplasmPUI?: string;
  instituteCode?: string;
  instituteName?: string;
  documentationURL?: string;
}

export interface Cross {
  crossDbId: string;
  crossName: string;
  crossType: string;
  parent1DbId?: string;
  parent1?: {
    germplasmDbId: string;
    germplasmName: string;
  };
  parent2DbId?: string;
  parent2?: {
    germplasmDbId: string;
    germplasmName: string;
  };
  crossingProjectDbId?: string;
  pollinationTimeStamp?: string;
  status?: 'planned' | 'successful' | 'failed' | 'pending';
  crossingDate?: string;
  crossAttributes?: Record<string, any>;
  plannedCrossDbId?: string;
}
