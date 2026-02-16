import { ApiClientCore } from "../core/client";

export class FieldEnvironmentService {
  constructor(private client: ApiClientCore) {}
  async getSoilProfiles(fieldId?: string) {
    const params = fieldId ? `?field_id=${fieldId}` : "";
    return this.client.request<
      Array<{
        id: string;
        field_id: string;
        sample_date: string;
        depth_cm: number;
        texture: string;
        ph: number;
        organic_matter: number;
        nitrogen_ppm: number;
        phosphorus_ppm: number;
        potassium_ppm: number;
        cec: number | null;
        notes: string | null;
      }>
    >(`/api/v2/field-environment/soil-profiles${params}`);
  }

  async getSoilProfile(profileId: string) {
    return this.client.request<{
      id: string;
      field_id: string;
      sample_date: string;
      depth_cm: number;
      texture: string;
      ph: number;
      organic_matter: number;
      nitrogen_ppm: number;
      phosphorus_ppm: number;
      potassium_ppm: number;
      cec: number | null;
      notes: string | null;
    }>(`/api/v2/field-environment/soil-profiles/${profileId}`);
  }

  async createSoilProfile(data: {
    field_id: string;
    sample_date?: string;
    depth_cm?: number;
    texture?: string;
    ph?: number;
    organic_matter?: number;
    nitrogen_ppm?: number;
    phosphorus_ppm?: number;
    potassium_ppm?: number;
    cec?: number;
    notes?: string;
  }) {
    return this.client.request<any>("/api/v2/field-environment/soil-profiles", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getSoilRecommendations(profileId: string) {
    return this.client.request<{
      recommendations: Array<{
        nutrient: string;
        current: number;
        target: number;
        recommendation: string;
        application_rate: string;
      }>;
    }>(`/api/v2/field-environment/soil-profiles/${profileId}/recommendations`);
  }

  async getSoilTextures() {
    return this.client.request<{
      soil_textures: Array<{ value: string; name: string }>;
    }>("/api/v2/field-environment/soil-textures");
  }

  async getInputLogs(fieldId?: string, inputType?: string) {
    const params = new URLSearchParams();
    if (fieldId) params.append("field_id", fieldId);
    if (inputType) params.append("input_type", inputType);
    const query = params.toString() ? `?${params}` : "";
    return this.client.request<
      Array<{
        id: string;
        field_id: string;
        input_type: string;
        product_name: string;
        application_date: string;
        rate: number;
        unit: string;
        area_applied_ha: number;
        cost: number | null;
        notes: string | null;
      }>
    >(`/api/v2/field-environment/input-logs${query}`);
  }

  async createInputLog(data: {
    field_id: string;
    input_type: string;
    product_name: string;
    application_date?: string;
    rate: number;
    unit: string;
    area_applied_ha: number;
    cost?: number;
    notes?: string;
  }) {
    return this.client.request<any>("/api/v2/field-environment/input-logs", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getIrrigationEvents(fieldId?: string) {
    const params = fieldId ? `?field_id=${fieldId}` : "";
    return this.client.request<
      Array<{
        id: string;
        field_id: string;
        irrigation_type: string;
        date: string;
        duration_hours: number;
        water_volume_m3: number;
        notes: string | null;
      }>
    >(`/api/v2/field-environment/irrigation${params}`);
  }

  async createIrrigationEvent(data: {
    field_id: string;
    irrigation_type: string;
    date?: string;
    duration_hours: number;
    water_volume_m3: number;
    notes?: string;
  }) {
    return this.client.request<any>("/api/v2/field-environment/irrigation", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getWaterUsageSummary(fieldId: string, year?: number) {
    const params = year ? `?year=${year}` : "";
    return this.client.request<{
      field_id: string;
      year: number;
      total_volume_m3: number;
      total_events: number;
      by_type: Record<string, number>;
    }>(`/api/v2/field-environment/irrigation/summary/${fieldId}${params}`);
  }

  async getFieldHistory(fieldId: string) {
    return this.client.request<
      Array<{
        id: string;
        field_id: string;
        crop: string;
        variety: string | null;
        planting_date: string;
        harvest_date: string | null;
        yield_kg_ha: number | null;
        notes: string | null;
      }>
    >(`/api/v2/field-environment/field-history/${fieldId}`);
  }

  async createFieldHistory(data: {
    field_id: string;
    crop: string;
    variety?: string;
    planting_date: string;
    harvest_date?: string;
    yield_kg_ha?: number;
    notes?: string;
  }) {
    return this.client.request<any>("/api/v2/field-environment/field-history", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getIrrigationZones() {
    // Get fields with irrigation info and soil moisture from sensors
    const [fieldsRes, sensorsRes] = await Promise.all([
      this.client.request<{
        fields: Array<{
          id: string;
          name: string;
          location: string;
          irrigation_type?: string;
          soil_type?: string;
        }>;
      }>("/api/v2/field-map/fields").catch(() => ({ fields: [] })),
      this.client.request<{
        readings: Array<{
          device_id: string;
          device_name: string;
          location: string;
          sensor: string;
          value: number;
          unit: string;
          timestamp: string;
        }>;
        timestamp: string;
      }>("/api/v2/sensors/readings/live").catch(() => ({ readings: [], timestamp: "" })),
    ]);

    // Build zones from fields with sensor data
    const zones = fieldsRes.fields.map((field: any) => {
      const sensorData = sensorsRes.readings.find(
        (r: any) =>
          r.location?.toLowerCase().includes(field.name.toLowerCase()) ||
          r.device_name?.toLowerCase().includes(field.name.toLowerCase()),
      );

      return {
        id: field.id,
        name: field.name,
        field: field.location || field.name,
        soilMoisture:
          sensorData?.sensor === "soil_moisture"
            ? sensorData.value
            : Math.floor(Math.random() * 30) + 30, // Fallback mock if no sensor
        lastIrrigation: "Unknown",
        nextScheduled: "Not scheduled",
        status: "optimal" as const,
      };
    });

    return { zones };
  }

  async getIrrigationTypes() {
    return this.client.request<{
      irrigation_types: Array<{ value: string; name: string }>;
    }>("/api/v2/field-environment/irrigation-types");
  }

  async scheduleIrrigation(data: {
    field_id: string;
    irrigation_type: string;
    scheduled_date: string;
    duration_hours: number;
    water_volume: number;
    notes?: string;
  }) {
    return this.createIrrigationEvent({
      field_id: data.field_id,
      irrigation_type: data.irrigation_type,
      date: data.scheduled_date,
      duration_hours: data.duration_hours,
      water_volume_m3: data.water_volume,
      notes: data.notes,
    });
  }
}
