export interface Crop {
  id: number;
  name: string;
  scientific_name?: string;
  variety?: string;
  description?: string;
  n_req?: number;
  p_req?: number;
  k_req?: number;
  created_at: string;
  updated_at: string;
}

export interface CropCreate {
  name: string;
  scientific_name?: string;
  variety?: string;
  description?: string;
  n_req?: number;
  p_req?: number;
  k_req?: number;
}

export interface Field {
  id: number;
  name: string;
  area: number;
  location_description?: string;
  coordinates?: any; // GeoJSON or similar
  created_at: string;
  updated_at: string;
}

export interface FieldCreate {
  name: string;
  area: number;
  location_description?: string;
  coordinates?: any;
}

export interface SoilProfile {
  id: number;
  name: string;
  description?: string;
  field_id: number;
  sample_date?: string;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ph?: number;
  organic_matter?: number;
  created_at: string;
  updated_at: string;
}

export interface SoilProfileCreate {
  name: string;
  description?: string;
  field_id: number;
  sample_date?: string;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  ph?: number;
  organic_matter?: number;
}

export interface Season {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  field_id: number;
  crop_id: number;
  created_at: string;
  updated_at: string;
}

export interface SeasonCreate {
  name: string;
  start_date: string;
  end_date: string;
  field_id: number;
  crop_id: number;
}

export interface FarmingPractice {
  id: number;
  name: string;
  description?: string;
  practice_type: string;
  date: string;
  field_id: number;
  season_id?: number;
  created_at: string;
  updated_at: string;
}

export interface FarmingPracticeCreate {
  name: string;
  description?: string;
  practice_type: string;
  date: string;
  field_id: number;
  season_id?: number;
}

export interface FertilizerRequest {
  crop_id?: number;
  crop_name?: string;
  target_yield: number;
  field_id?: number;
  soil_n?: number;
  soil_p?: number;
  soil_k?: number;
  area?: number;
}

export interface FertilizerResponse {
  urea: number;
  dap: number;
  mop: number;
  nitrogen_needed: number;
  phosphorus_needed: number;
  potassium_needed: number;
  total_cost: number;
}
