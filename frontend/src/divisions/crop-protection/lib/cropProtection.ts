export interface PestObservationRecord {
  id: number
  field_id: number
  study_id: number | null
  observation_date: string
  observation_time: string | null
  observer_name: string | null
  pest_name: string
  pest_type: string
  pest_stage: string | null
  crop_name: string
  growth_stage: string | null
  plant_part_affected: string | null
  severity_score: number | null
  incidence_percent: number | null
  count_per_plant: number | null
  count_per_trap: number | null
  area_affected_percent: number | null
  sample_location: string | null
  lat: number | null
  lon: number | null
  weather_conditions: Record<string, unknown> | null
  image_urls: string[] | null
  notes: string | null
  organization_id: number
  created_at: string
  updated_at: string
}

export interface DiseaseRiskForecastRecord {
  id: number
  location_id: number | null
  forecast_date: string
  valid_from: string
  valid_until: string
  disease_name: string
  crop_name: string
  risk_level: string
  risk_score: number | null
  contributing_factors: Record<string, unknown> | null
  recommended_actions: string[] | null
  model_name: string
  model_version: string
  organization_id: number
  created_at: string
  updated_at: string
}

export interface SprayApplicationRecord {
  id: number
  field_id: number | null
  application_date: string
  product_name: string
  product_type: string | null
  active_ingredient: string | null
  rate_per_ha: number | null
  rate_unit: string | null
  total_area_ha: number | null
  water_volume_l_ha: number | null
  applicator_name: string | null
  equipment_used: string | null
  weather_conditions: Record<string, unknown> | null
  target_pest: string | null
  pre_harvest_interval_days: number | null
  re_entry_interval_hours: number | null
  notes: string | null
  organization_id: number
  created_at: string
  updated_at: string
}

export interface SprayComplianceReport {
  total_applications: number
  compliant_applications: number
  compliance_rate: number
}

export interface IPMStrategyRecord {
  id: number
  field_id: number | null
  strategy_name: string
  crop_name: string
  target_pest: string
  pest_type: string | null
  economic_threshold: string | null
  action_threshold: string | null
  prevention_methods: string[] | null
  monitoring_methods: string[] | null
  biological_controls: string[] | null
  physical_controls: string[] | null
  chemical_controls: string[] | null
  implementation_start: string | null
  implementation_end: string | null
  growth_stages: string[] | null
  effectiveness_rating: number | null
  cost_effectiveness: number | null
  environmental_impact_score: number | null
  notes: string | null
  organization_id: number
  created_at: string
  updated_at: string
}

export const pestTypes = [
  'insect',
  'mite',
  'nematode',
  'weed',
  'disease',
  'bird',
  'rodent',
  'other',
] as const

export const riskLevels = [
  { value: 'low', label: 'Low', color: 'bg-green-500', textColor: 'text-green-700 dark:text-green-400' },
  { value: 'medium', label: 'Medium', color: 'bg-yellow-500', textColor: 'text-yellow-700 dark:text-yellow-400' },
  { value: 'high', label: 'High', color: 'bg-orange-500', textColor: 'text-orange-700 dark:text-orange-400' },
  { value: 'critical', label: 'Critical', color: 'bg-red-500', textColor: 'text-red-700 dark:text-red-400' },
] as const

export const ipmMethodGroups = [
  { key: 'prevention', label: 'Prevention Methods' },
  { key: 'monitoring', label: 'Monitoring Methods' },
  { key: 'biological', label: 'Biological Controls' },
  { key: 'physical', label: 'Physical Controls' },
  { key: 'chemical', label: 'Chemical Controls' },
] as const

export function formatDisplayDate(value: string | null | undefined) {
  if (!value) {
    return '—'
  }

  return new Date(value).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDisplayDateTime(value: string | null | undefined) {
  if (!value) {
    return '—'
  }

  return new Date(value).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function toNumberOrNull(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === '') {
    return null
  }

  const parsed = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function parseMultilineList(value: string) {
  return value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean)
}

export function joinMultilineList(value: string[] | null | undefined) {
  return value?.join('\n') ?? ''
}

export function toDayBoundary(date: string, time: 'start' | 'end') {
  return `${date}T${time === 'start' ? '00:00:00' : '23:59:59'}`
}

export function riskRank(level: string) {
  switch (level.toLowerCase()) {
    case 'critical':
      return 4
    case 'high':
      return 3
    case 'medium':
      return 2
    default:
      return 1
  }
}

/**
 * Returns the arithmetic mean for finite numeric values in the array.
 * If the input is empty or only contains nullish/non-numeric entries, returns null.
 */
export function average(values: Array<number | null | undefined>) {
  const filtered = values.filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
  if (filtered.length === 0) {
    return null
  }

  const total = filtered.reduce((sum, value) => sum + value, 0)
  return total / filtered.length
}
