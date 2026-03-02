import { IoTDevice, IoTDeviceCreate, IoTDeviceUpdate, IoTTelemetry, IoTTelemetryCreate } from '../types/iot';
import axios from 'axios';

const API_BASE_URL = '/api/v2/iot';

export const iotApi = {
  // Device Registry
  listDevices: async (params?: any): Promise<{ total: number; items: IoTDevice[] }> => {
    const response = await axios.get(`${API_BASE_URL}/devices`, { params });
    return response.data;
  },

  getDevice: async (id: number): Promise<IoTDevice> => {
    const response = await axios.get(`${API_BASE_URL}/devices/${id}`);
    return response.data;
  },

  createDevice: async (data: IoTDeviceCreate): Promise<IoTDevice> => {
    const response = await axios.post(`${API_BASE_URL}/devices`, data);
    return response.data;
  },

  updateDevice: async (id: number, data: IoTDeviceUpdate): Promise<IoTDevice> => {
    const response = await axios.put(`${API_BASE_URL}/devices/${id}`, data);
    return response.data;
  },

  deleteDevice: async (id: number): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/devices/${id}`);
  },

  // Telemetry
  recordReading: async (data: IoTTelemetryCreate): Promise<IoTTelemetry> => {
    const response = await axios.post(`${API_BASE_URL}/telemetry`, data);
    return response.data;
  },

  getReadings: async (params?: any): Promise<{ total: number; items: IoTTelemetry[] }> => {
    const response = await axios.get(`${API_BASE_URL}/telemetry`, { params });
    return response.data;
  }
};
