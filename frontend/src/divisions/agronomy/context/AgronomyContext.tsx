import React, { createContext, useContext, useState, ReactNode } from 'react';
import { agronomyApi } from '../api/client';
import {
  Crop, CropCreate,
  Field, FieldCreate,
  SoilProfile, SoilProfileCreate,
  Season, SeasonCreate,
  FarmingPractice, FarmingPracticeCreate,
  FertilizerRequest, FertilizerResponse
} from '../types';

interface AgronomyContextType {
  crops: Crop[];
  fields: Field[];
  soilProfiles: SoilProfile[];
  seasons: Season[];
  farmingPractices: FarmingPractice[];
  loading: boolean;
  error: string | null;

  // Actions
  fetchCrops: () => Promise<void>;
  createCrop: (data: CropCreate) => Promise<void>;
  updateCrop: (id: number, data: Partial<CropCreate>) => Promise<void>;
  deleteCrop: (id: number) => Promise<void>;

  fetchFields: () => Promise<void>;
  createField: (data: FieldCreate) => Promise<void>;
  updateField: (id: number, data: Partial<FieldCreate>) => Promise<void>;
  deleteField: (id: number) => Promise<void>;

  fetchSoilProfiles: () => Promise<void>;
  createSoilProfile: (data: SoilProfileCreate) => Promise<void>;
  updateSoilProfile: (id: number, data: Partial<SoilProfileCreate>) => Promise<void>;
  deleteSoilProfile: (id: number) => Promise<void>;

  fetchSeasons: () => Promise<void>;
  createSeason: (data: SeasonCreate) => Promise<void>;
  updateSeason: (id: number, data: Partial<SeasonCreate>) => Promise<void>;
  deleteSeason: (id: number) => Promise<void>;

  fetchFarmingPractices: () => Promise<void>;
  createFarmingPractice: (data: FarmingPracticeCreate) => Promise<void>;
  updateFarmingPractice: (id: number, data: Partial<FarmingPracticeCreate>) => Promise<void>;
  deleteFarmingPractice: (id: number) => Promise<void>;

  calculateFertilizer: (data: FertilizerRequest) => Promise<FertilizerResponse>;
}

const AgronomyContext = createContext<AgronomyContextType | undefined>(undefined);

export const AgronomyProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [crops, setCrops] = useState<Crop[]>([]);
  const [fields, setFields] = useState<Field[]>([]);
  const [soilProfiles, setSoilProfiles] = useState<SoilProfile[]>([]);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [farmingPractices, setFarmingPractices] = useState<FarmingPractice[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleError = (err: any) => {
    console.error(err);
    setError(err.message || 'An error occurred');
    setLoading(false);
  };

  // --- Crops ---
  const fetchCrops = async () => {
    setLoading(true);
    try {
      const data = await agronomyApi.getCrops();
      setCrops(data);
      setLoading(false);
    } catch (err) { handleError(err); }
  };

  const createCrop = async (data: CropCreate) => {
    setLoading(true);
    try {
      await agronomyApi.createCrop(data);
      await fetchCrops();
    } catch (err) { handleError(err); }
  };

  const updateCrop = async (id: number, data: Partial<CropCreate>) => {
      setLoading(true);
      try {
        await agronomyApi.updateCrop(id, data);
        await fetchCrops();
      } catch (err) { handleError(err); }
  };

  const deleteCrop = async (id: number) => {
      setLoading(true);
      try {
        await agronomyApi.deleteCrop(id);
        await fetchCrops();
      } catch (err) { handleError(err); }
  };

  // --- Fields ---
  const fetchFields = async () => {
    setLoading(true);
    try {
      const data = await agronomyApi.getFields();
      setFields(data);
      setLoading(false);
    } catch (err) { handleError(err); }
  };

  const createField = async (data: FieldCreate) => {
      setLoading(true);
      try {
        await agronomyApi.createField(data);
        await fetchFields();
      } catch (err) { handleError(err); }
  };

  const updateField = async (id: number, data: Partial<FieldCreate>) => {
      setLoading(true);
      try {
        await agronomyApi.updateField(id, data);
        await fetchFields();
      } catch (err) { handleError(err); }
  };

  const deleteField = async (id: number) => {
      setLoading(true);
      try {
        await agronomyApi.deleteField(id);
        await fetchFields();
      } catch (err) { handleError(err); }
  };

  // --- Soil Profiles ---
  const fetchSoilProfiles = async () => {
    setLoading(true);
    try {
      const data = await agronomyApi.getSoilProfiles();
      setSoilProfiles(data);
      setLoading(false);
    } catch (err) { handleError(err); }
  };

  const createSoilProfile = async (data: SoilProfileCreate) => {
      setLoading(true);
      try {
        await agronomyApi.createSoilProfile(data);
        await fetchSoilProfiles();
      } catch (err) { handleError(err); }
  };

  const updateSoilProfile = async (id: number, data: Partial<SoilProfileCreate>) => {
      setLoading(true);
      try {
        await agronomyApi.updateSoilProfile(id, data);
        await fetchSoilProfiles();
      } catch (err) { handleError(err); }
  };

  const deleteSoilProfile = async (id: number) => {
      setLoading(true);
      try {
        await agronomyApi.deleteSoilProfile(id);
        await fetchSoilProfiles();
      } catch (err) { handleError(err); }
  };

  // --- Seasons ---
  const fetchSeasons = async () => {
    setLoading(true);
    try {
      const data = await agronomyApi.getSeasons();
      setSeasons(data);
      setLoading(false);
    } catch (err) { handleError(err); }
  };

  const createSeason = async (data: SeasonCreate) => {
      setLoading(true);
      try {
        await agronomyApi.createSeason(data);
        await fetchSeasons();
      } catch (err) { handleError(err); }
  };

  const updateSeason = async (id: number, data: Partial<SeasonCreate>) => {
      setLoading(true);
      try {
        await agronomyApi.updateSeason(id, data);
        await fetchSeasons();
      } catch (err) { handleError(err); }
  };

  const deleteSeason = async (id: number) => {
      setLoading(true);
      try {
        await agronomyApi.deleteSeason(id);
        await fetchSeasons();
      } catch (err) { handleError(err); }
  };

  // --- Farming Practices ---
  const fetchFarmingPractices = async () => {
    setLoading(true);
    try {
      const data = await agronomyApi.getFarmingPractices();
      setFarmingPractices(data);
      setLoading(false);
    } catch (err) { handleError(err); }
  };

  const createFarmingPractice = async (data: FarmingPracticeCreate) => {
      setLoading(true);
      try {
        await agronomyApi.createFarmingPractice(data);
        await fetchFarmingPractices();
      } catch (err) { handleError(err); }
  };

  const updateFarmingPractice = async (id: number, data: Partial<FarmingPracticeCreate>) => {
      setLoading(true);
      try {
        await agronomyApi.updateFarmingPractice(id, data);
        await fetchFarmingPractices();
      } catch (err) { handleError(err); }
  };

  const deleteFarmingPractice = async (id: number) => {
      setLoading(true);
      try {
        await agronomyApi.deleteFarmingPractice(id);
        await fetchFarmingPractices();
      } catch (err) { handleError(err); }
  };

  // --- Calculator ---
  const calculateFertilizer = async (data: FertilizerRequest) => {
      setLoading(true);
      try {
        const result = await agronomyApi.calculateFertilizer(data);
        setLoading(false);
        return result;
      } catch (err) {
        handleError(err);
        throw err;
      }
  };


  return (
    <AgronomyContext.Provider value={{
      crops, fields, soilProfiles, seasons, farmingPractices,
      loading, error,
      fetchCrops, createCrop, updateCrop, deleteCrop,
      fetchFields, createField, updateField, deleteField,
      fetchSoilProfiles, createSoilProfile, updateSoilProfile, deleteSoilProfile,
      fetchSeasons, createSeason, updateSeason, deleteSeason,
      fetchFarmingPractices, createFarmingPractice, updateFarmingPractice, deleteFarmingPractice,
      calculateFertilizer
    }}>
      {children}
    </AgronomyContext.Provider>
  );
};

export const useAgronomy = () => {
  const context = useContext(AgronomyContext);
  if (context === undefined) {
    throw new Error('useAgronomy must be used within an AgronomyProvider');
  }
  return context;
};
