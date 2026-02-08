import { ApiClientCore } from "../core/client";

export interface StorageLocation {
  id: string;
  code: string;
  name: string;
  storage_type: "cold" | "ambient" | "controlled" | "cryo";
  capacity_kg: number;
  used_kg: number;
  current_temperature: number | null;
  current_humidity: number | null;
  target_temperature: number | null;
  target_humidity: number | null;
  lot_count: number;
  status: "normal" | "warning" | "critical" | "maintenance";
  utilization_percent: number;
  created_at: string;
  updated_at: string;
}

export interface WarehouseSummary {
  total_locations: number;
  total_capacity_kg: number;
  total_used_kg: number;
  utilization_percent: number;
  total_lots: number;
  locations_by_type: Record<
    string,
    { count: number; capacity_kg: number; used_kg: number }
  >;
  alerts_count: number;
}

export interface WarehouseAlert {
  id: string;
  location_id: string;
  location_name: string;
  alert_type: "capacity" | "temperature" | "humidity";
  severity: "warning" | "critical";
  message: string;
  current_value: number;
  threshold_value: number;
  created_at: string;
}

export class WarehouseService {
  constructor(private client: ApiClientCore) {}

  private baseUrl = "/api/v2/warehouse";

  /**
   * List all storage locations
   */
  async getLocations(params?: {
    storage_type?: string;
    status?: string;
  }): Promise<StorageLocation[]> {
    const searchParams = new URLSearchParams();
    if (params?.storage_type)
      searchParams.append("storage_type", params.storage_type);
    if (params?.status) searchParams.append("status", params.status);
    const query = searchParams.toString();
    return this.client.get<StorageLocation[]>(
      `${this.baseUrl}/locations${query ? `?${query}` : ""}`
    );
  }

  /**
   * Get a specific storage location
   */
  async getLocation(locationId: string): Promise<StorageLocation> {
    return this.client.get<StorageLocation>(
      `${this.baseUrl}/locations/${locationId}`
    );
  }

  /**
   * Create a new storage location
   */
  async createLocation(data: {
    name: string;
    code: string;
    storage_type: "cold" | "ambient" | "controlled" | "cryo";
    capacity_kg: number;
    target_temperature?: number;
    target_humidity?: number;
    description?: string;
  }): Promise<StorageLocation> {
    return this.client.post<StorageLocation>(`${this.baseUrl}/locations`, data);
  }

  /**
   * Update a storage location
   */
  async updateLocation(
    locationId: string,
    data: {
      name?: string;
      storage_type?: string;
      capacity_kg?: number;
      used_kg?: number;
      current_temperature?: number;
      current_humidity?: number;
      target_temperature?: number;
      target_humidity?: number;
      status?: string;
      description?: string;
    }
  ): Promise<StorageLocation> {
    return this.client.patch<StorageLocation>(
      `${this.baseUrl}/locations/${locationId}`,
      data
    );
  }

  /**
   * Delete a storage location
   */
  async deleteLocation(
    locationId: string
  ): Promise<{ message: string; id: string }> {
    return this.client.delete<{ message: string; id: string }>(
      `${this.baseUrl}/locations/${locationId}`
    );
  }

  /**
   * Get warehouse summary statistics
   */
  async getSummary(): Promise<WarehouseSummary> {
    return this.client.get<WarehouseSummary>(`${this.baseUrl}/summary`);
  }

  /**
   * Get warehouse alerts
   */
  async getAlerts(
    severity?: "warning" | "critical"
  ): Promise<WarehouseAlert[]> {
    const query = severity ? `?severity=${severity}` : "";
    return this.client.get<WarehouseAlert[]>(`${this.baseUrl}/alerts${query}`);
  }
}
