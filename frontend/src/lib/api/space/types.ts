export enum MarsFailureMode {
  ATMOSPHERIC_COLLAPSE = "ATMOSPHERIC_COLLAPSE",
  RADIATION_DAMAGE = "RADIATION_DAMAGE",
  WATER_STARVATION = "WATER_STARVATION",
  NUTRIENT_LOCKOUT = "NUTRIENT_LOCKOUT",
  ENERGY_DEFICIT = "ENERGY_DEFICIT",
  PHYSIOLOGICAL_LIMIT = "PHYSIOLOGICAL_LIMIT",
  UNKNOWN = "UNKNOWN",
}

export interface MarsEnvironmentProfile {
  id: string;
  organization_id: number;
  pressure_kpa: number;
  co2_ppm: number;
  o2_ppm: number;
  radiation_msv: number;
  gravity_factor: number;
  photoperiod_hours: number;
  temperature_profile: Record<string, any>;
  humidity_profile: Record<string, any>;
  created_at: string;
}

export type MarsEnvironmentProfileCreate = Omit<MarsEnvironmentProfile, 'id' | 'organization_id' | 'created_at'>;

export interface MarsClosedLoopMetrics {
  water_recycling_pct: number;
  nutrient_loss_pct: number;
  energy_input_kwh: number;
  oxygen_output: number;
}

export interface MarsTrial {
  id: string;
  organization_id: number;
  germplasm_id: number;
  environment_profile_id: string;
  generation: number;
  survival_score: number;
  biomass_yield: number;
  failure_mode: MarsFailureMode;
  notes?: string;
  created_at: string;
  closed_loop_metrics?: MarsClosedLoopMetrics;
}

export interface MarsSimulationRequest {
  environment_profile_id: string;
  germplasm_id: number;
  generation?: number;
}

export interface MarsSimulationResponse {
  trial_id: string;
  survival_score: number;
  biomass_yield: number;
  failure_mode: MarsFailureMode;
  closed_loop_metrics: MarsClosedLoopMetrics;
}

// ==========================================
// Lunar Types
// ==========================================

export enum LunarFailureMode {
  ROOT_DISORIENTATION = "ROOT_DISORIENTATION",
  ANCHORAGE_FAILURE = "ANCHORAGE_FAILURE",
  PHOTOPERIOD_COLLAPSE = "PHOTOPERIOD_COLLAPSE",
  TRANSLOCATION_IMPAIRMENT = "TRANSLOCATION_IMPAIRMENT",
  MORPHOGENETIC_INSTABILITY = "MORPHOGENETIC_INSTABILITY",
  UNKNOWN = "UNKNOWN",
}

export interface LunarEnvironmentProfile {
  id: string;
  organization_id: number;
  gravity_factor: number;
  light_cycle_days: number;
  dark_cycle_days: number;
  habitat_pressure_kpa: number;
  o2_ppm: number;
  co2_ppm: number;
  root_support_factor: number;
  created_at: string;
}

export type LunarEnvironmentProfileCreate = Omit<LunarEnvironmentProfile, 'id' | 'organization_id' | 'created_at'>;

export interface LunarTrial {
  id: string;
  organization_id: number;
  environment_profile_id: string;
  germplasm_id: number;
  generation: number;
  anchorage_score: number;
  morphology_stability: number;
  yield_index: number;
  failure_mode: LunarFailureMode;
  notes?: string;
}

export type LunarTrialCreate = Omit<LunarTrial, 'id'>;

export interface LunarSimulationRequest {
  environment_profile_id: string;
  germplasm_id: number;
  generation: number;
}

export interface LunarSimulationResponse {
  anchorage_score: number;
  morphology_stability: number;
  yield_index: number;
  failure_mode: LunarFailureMode;
}

// ==========================================
// Research Types
// ==========================================

export interface RadiationRequest {
  mission_type: string;
  duration_days: number;
  shielding_gcm2: number;
}

export interface LifeSupportRequest {
  crew_size: number;
  mission_days: number;
  crop_area_m2: number;
}

