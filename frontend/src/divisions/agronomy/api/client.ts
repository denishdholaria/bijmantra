import axios from 'axios';
import {
  Crop, CropCreate,
  Field, FieldCreate,
  SoilProfile, SoilProfileCreate,
  Season, SeasonCreate,
  FarmingPractice, FarmingPracticeCreate,
  FertilizerRequest, FertilizerResponse
} from '../types';

const API_BASE_URL = '/api/v2/agronomy'; // Proxy should handle the base URL

export const agronomyApi = {
  // Crops
  getCrops: async () => {
    const response = await axios.get<Crop[]>(`${API_BASE_URL}/crops`);
    return response.data;
  },
  getCrop: async (id: number) => {
    const response = await axios.get<Crop>(`${API_BASE_URL}/crops/${id}`);
    return response.data;
  },
  createCrop: async (data: CropCreate) => {
    const response = await axios.post<Crop>(`${API_BASE_URL}/crops`, data);
    return response.data;
  },
  updateCrop: async (id: number, data: Partial<CropCreate>) => {
    const response = await axios.put<Crop>(`${API_BASE_URL}/crops/${id}`, data);
    return response.data;
  },
  deleteCrop: async (id: number) => {
    await axios.delete(`${API_BASE_URL}/crops/${id}`);
  },

  // Fields
  getFields: async () => {
    const response = await axios.get<Field[]>(`${API_BASE_URL}/fields`);
    return response.data;
  },
  getField: async (id: number) => {
    const response = await axios.get<Field>(`${API_BASE_URL}/fields/${id}`);
    return response.data;
  },
  createField: async (data: FieldCreate) => {
    const response = await axios.post<Field>(`${API_BASE_URL}/fields`, data);
    return response.data;
  },
  updateField: async (id: number, data: Partial<FieldCreate>) => {
    const response = await axios.put<Field>(`${API_BASE_URL}/fields/${id}`, data);
    return response.data;
  },
  deleteField: async (id: number) => {
    await axios.delete(`${API_BASE_URL}/fields/${id}`);
  },

  // Soil Profiles
  getSoilProfiles: async () => {
    const response = await axios.get<SoilProfile[]>(`${API_BASE_URL}/soil-profiles`);
    return response.data;
  },
  getSoilProfile: async (id: number) => {
    const response = await axios.get<SoilProfile>(`${API_BASE_URL}/soil-profiles/${id}`);
    return response.data;
  },
  createSoilProfile: async (data: SoilProfileCreate) => {
    const response = await axios.post<SoilProfile>(`${API_BASE_URL}/soil-profiles`, data);
    return response.data;
  },
  updateSoilProfile: async (id: number, data: Partial<SoilProfileCreate>) => {
    const response = await axios.put<SoilProfile>(`${API_BASE_URL}/soil-profiles/${id}`, data);
    return response.data;
  },
  deleteSoilProfile: async (id: number) => {
    await axios.delete(`${API_BASE_URL}/soil-profiles/${id}`);
  },

  // Seasons
  getSeasons: async () => {
    const response = await axios.get<Season[]>(`${API_BASE_URL}/seasons`);
    return response.data;
  },
  getSeason: async (id: number) => {
    const response = await axios.get<Season>(`${API_BASE_URL}/seasons/${id}`);
    return response.data;
  },
  createSeason: async (data: SeasonCreate) => {
    const response = await axios.post<Season>(`${API_BASE_URL}/seasons`, data);
    return response.data;
  },
  updateSeason: async (id: number, data: Partial<SeasonCreate>) => {
    const response = await axios.put<Season>(`${API_BASE_URL}/seasons/${id}`, data);
    return response.data;
  },
  deleteSeason: async (id: number) => {
    await axios.delete(`${API_BASE_URL}/seasons/${id}`);
  },

  // Farming Practices
  getFarmingPractices: async () => {
    const response = await axios.get<FarmingPractice[]>(`${API_BASE_URL}/farming-practices`);
    return response.data;
  },
  getFarmingPractice: async (id: number) => {
    const response = await axios.get<FarmingPractice>(`${API_BASE_URL}/farming-practices/${id}`);
    return response.data;
  },
  createFarmingPractice: async (data: FarmingPracticeCreate) => {
    const response = await axios.post<FarmingPractice>(`${API_BASE_URL}/farming-practices`, data);
    return response.data;
  },
  updateFarmingPractice: async (id: number, data: Partial<FarmingPracticeCreate>) => {
    const response = await axios.put<FarmingPractice>(`${API_BASE_URL}/farming-practices/${id}`, data);
    return response.data;
  },
  deleteFarmingPractice: async (id: number) => {
    await axios.delete(`${API_BASE_URL}/farming-practices/${id}`);
  },

  // Fertilizer
  calculateFertilizer: async (data: FertilizerRequest) => {
    const response = await axios.post<FertilizerResponse>(`${API_BASE_URL}/fertilizer/calculate`, data);
    return response.data;
  }
};
