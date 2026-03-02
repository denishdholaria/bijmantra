import {
  NutrientTest, NutrientTestCreate, NutrientTestUpdate,
  PhysicalProperties, PhysicalPropertiesCreate, PhysicalPropertiesUpdate,
  MicrobialActivity, MicrobialActivityCreate, MicrobialActivityUpdate,
  AmendmentLog, AmendmentLogCreate, AmendmentLogUpdate,
  SoilMap, SoilMapCreate, SoilMapUpdate
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_URL = `${API_BASE_URL}/api/v2/soil`;

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token'); // Assuming token is stored in localStorage
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const SoilService = {
  // NutrientTest
  getNutrientTests: (fieldId?: number) =>
    request<NutrientTest[]>(`/nutrient-tests${fieldId ? `?field_id=${fieldId}` : ''}`),

  createNutrientTest: (data: NutrientTestCreate) =>
    request<NutrientTest>('/nutrient-tests', { method: 'POST', body: JSON.stringify(data) }),

  getNutrientTest: (id: number) =>
    request<NutrientTest>(`/nutrient-tests/${id}`),

  updateNutrientTest: (id: number, data: NutrientTestUpdate) =>
    request<NutrientTest>(`/nutrient-tests/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteNutrientTest: (id: number) =>
    request<void>(`/nutrient-tests/${id}`, { method: 'DELETE' }),

  // PhysicalProperties
  getPhysicalProperties: (fieldId?: number) =>
    request<PhysicalProperties[]>(`/physical-properties${fieldId ? `?field_id=${fieldId}` : ''}`),

  createPhysicalProperties: (data: PhysicalPropertiesCreate) =>
    request<PhysicalProperties>('/physical-properties', { method: 'POST', body: JSON.stringify(data) }),

  getPhysicalProperty: (id: number) =>
    request<PhysicalProperties>(`/physical-properties/${id}`),

  updatePhysicalProperties: (id: number, data: PhysicalPropertiesUpdate) =>
    request<PhysicalProperties>(`/physical-properties/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deletePhysicalProperties: (id: number) =>
    request<void>(`/physical-properties/${id}`, { method: 'DELETE' }),

  // MicrobialActivity
  getMicrobialActivities: (fieldId?: number) =>
    request<MicrobialActivity[]>(`/microbial-activity${fieldId ? `?field_id=${fieldId}` : ''}`),

  createMicrobialActivity: (data: MicrobialActivityCreate) =>
    request<MicrobialActivity>('/microbial-activity', { method: 'POST', body: JSON.stringify(data) }),

  getMicrobialActivity: (id: number) =>
    request<MicrobialActivity>(`/microbial-activity/${id}`),

  updateMicrobialActivity: (id: number, data: MicrobialActivityUpdate) =>
    request<MicrobialActivity>(`/microbial-activity/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteMicrobialActivity: (id: number) =>
    request<void>(`/microbial-activity/${id}`, { method: 'DELETE' }),

  // AmendmentLog
  getAmendmentLogs: (fieldId?: number) =>
    request<AmendmentLog[]>(`/amendment-logs${fieldId ? `?field_id=${fieldId}` : ''}`),

  createAmendmentLog: (data: AmendmentLogCreate) =>
    request<AmendmentLog>('/amendment-logs', { method: 'POST', body: JSON.stringify(data) }),

  getAmendmentLog: (id: number) =>
    request<AmendmentLog>(`/amendment-logs/${id}`),

  updateAmendmentLog: (id: number, data: AmendmentLogUpdate) =>
    request<AmendmentLog>(`/amendment-logs/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteAmendmentLog: (id: number) =>
    request<void>(`/amendment-logs/${id}`, { method: 'DELETE' }),

  // SoilMap
  getSoilMaps: (fieldId?: number) =>
    request<SoilMap[]>(`/maps${fieldId ? `?field_id=${fieldId}` : ''}`),

  createSoilMap: (data: SoilMapCreate) =>
    request<SoilMap>('/maps', { method: 'POST', body: JSON.stringify(data) }),

  getSoilMap: (id: number) =>
    request<SoilMap>(`/maps/${id}`),

  updateSoilMap: (id: number, data: SoilMapUpdate) =>
    request<SoilMap>(`/maps/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteSoilMap: (id: number) =>
    request<void>(`/maps/${id}`, { method: 'DELETE' }),
};
