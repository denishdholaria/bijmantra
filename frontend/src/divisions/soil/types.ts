// Common Types
export interface BaseEntity {
  id: number;
  created_at?: string;
  updated_at?: string;
}

// NutrientTest Types
export interface NutrientTest extends BaseEntity {
  field_id: number;
  sample_date: string;
  depth_cm: number;
  nitrogen_ppm: number;
  phosphorus_ppm: number;
  potassium_ppm: number;
  ph_level: number;
  organic_matter_percent: number;
  notes?: string;
  // Mapped properties for UI compatibility if backend returns different names or component expects these
  lab_name?: string;
  depth?: string;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ph?: number;
}

export interface NutrientTestCreate {
  field_id: number;
  sample_date: string;
  depth_cm: number;
  nitrogen_ppm: number;
  phosphorus_ppm: number;
  potassium_ppm: number;
  ph_level: number;
  organic_matter_percent: number;
  notes?: string;
}

export interface NutrientTestUpdate extends Partial<NutrientTestCreate> {}

// PhysicalProperties Types
export interface PhysicalProperties extends BaseEntity {
  field_id: number;
  test_date: string;
  texture_class: string;
  bulk_density_g_cm3: number;
  porosity_percent: number;
  water_holding_capacity_percent: number;
  infiltration_rate_mm_hr: number;
  notes?: string;
}

export interface PhysicalPropertiesCreate {
  field_id: number;
  test_date: string;
  texture_class: string;
  bulk_density_g_cm3: number;
  porosity_percent: number;
  water_holding_capacity_percent: number;
  infiltration_rate_mm_hr: number;
  notes?: string;
}

export interface PhysicalPropertiesUpdate extends Partial<PhysicalPropertiesCreate> {}

// MicrobialActivity Types
export interface MicrobialActivity extends BaseEntity {
  field_id: number;
  measurement_date: string;
  respiration_rate_mg_c_kg_soil_day: number;
  biomass_c_mg_kg: number;
  enzyme_activity_score: number;
  notes?: string;
}

export interface MicrobialActivityCreate {
  field_id: number;
  measurement_date: string;
  respiration_rate_mg_c_kg_soil_day: number;
  biomass_c_mg_kg: number;
  enzyme_activity_score: number;
  notes?: string;
}

export interface MicrobialActivityUpdate extends Partial<MicrobialActivityCreate> {}

// AmendmentLog Types
export interface AmendmentLog extends BaseEntity {
  field_id: number;
  application_date: string;
  amendment_type: string;
  quantity_kg_ha: number;
  method: string;
  notes?: string;
}

export interface AmendmentLogCreate {
  field_id: number;
  application_date: string;
  amendment_type: string;
  quantity_kg_ha: number;
  method: string;
  notes?: string;
}

export interface AmendmentLogUpdate extends Partial<AmendmentLogCreate> {}

// SoilMap Types
export interface SoilMap extends BaseEntity {
  field_id: number;
  map_date: string;
  map_type: string;
  file_url: string;
  resolution_meters: number;
  notes?: string;
}

export interface SoilMapCreate {
  field_id: number;
  map_date: string;
  map_type: string;
  file_url: string;
  resolution_meters: number;
  notes?: string;
}

export interface SoilMapUpdate extends Partial<SoilMapCreate> {}
