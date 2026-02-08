import { ApiClientCore } from "../core/client";

export class SensorService {
  constructor(private client: ApiClientCore) {}
  async getSensorDevices(options?: {
    deviceType?: string;
    status?: string;
    fieldId?: string;
  }) {
    const params = new URLSearchParams();
    if (options?.deviceType) params.append("device_type", options.deviceType);
    if (options?.status) params.append("status", options.status);
    if (options?.fieldId) params.append("field_id", options.fieldId);
    const query = params.toString() ? `?${params}` : "";
    return this.client.request<{
      devices: Array<{
        device_id: string;
        name: string;
        device_type: string;
        location: string;
        sensors: string[];
        status: string;
        battery: number;
        signal: number;
        last_seen: string;
        field_id?: string;
      }>;
      total: number;
    }>(`/api/v2/sensors/devices${query}`);
  }

  async getSensorDevice(deviceId: string) {
    return this.client.request<{
      device_id: string;
      name: string;
      device_type: string;
      location: string;
      sensors: string[];
      status: string;
      battery: number;
      signal: number;
      last_seen: string;
      field_id?: string;
    }>(`/api/v2/sensors/devices/${deviceId}`);
  }

  async registerSensorDevice(data: {
    device_id: string;
    name: string;
    device_type: string;
    location: string;
    sensors: string[];
    field_id?: string;
  }) {
    return this.client.request<any>("/api/v2/sensors/devices", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateDeviceStatus(
    deviceId: string,
    data: {
      status: string;
      battery?: number;
      signal?: number;
    },
  ) {
    return this.client.request<any>(`/api/v2/sensors/devices/${deviceId}/status`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteSensorDevice(deviceId: string) {
    return this.client.request<any>(`/api/v2/sensors/devices/${deviceId}`, {
      method: "DELETE",
    });
  }

  async getSensorReadings(options?: {
    deviceId?: string;
    sensor?: string;
    since?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (options?.deviceId) params.append("device_id", options.deviceId);
    if (options?.sensor) params.append("sensor", options.sensor);
    if (options?.since) params.append("since", options.since);
    if (options?.limit) params.append("limit", options.limit.toString());
    const query = params.toString() ? `?${params}` : "";
    return this.client.request<{
      readings: Array<{
        id: string;
        device_id: string;
        sensor: string;
        value: number;
        unit: string;
        timestamp: string;
      }>;
      total: number;
    }>(`/api/v2/sensors/readings${query}`);
  }

  async getLiveSensorReadings() {
    return this.client.request<{
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
    }>("/api/v2/sensors/readings/live");
  }

  async getLatestDeviceReadings(deviceId: string) {
    return this.client.request<{
      device_id: string;
      readings: Record<
        string,
        {
          value: number;
          unit: string;
          timestamp: string;
        }
      >;
    }>(`/api/v2/sensors/readings/${deviceId}/latest`);
  }

  async recordSensorReading(data: {
    device_id: string;
    sensor: string;
    value: number;
    unit: string;
    timestamp?: string;
  }) {
    return this.client.request<any>("/api/v2/sensors/readings", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getSensorAlertRules(enabledOnly: boolean = false) {
    const params = enabledOnly ? "?enabled_only=true" : "";
    return this.client.request<{
      rules: Array<{
        id: string;
        name: string;
        sensor: string;
        condition: string;
        threshold: number;
        unit: string;
        severity: string;
        enabled: boolean;
        notify_email: boolean;
        notify_sms: boolean;
        notify_push: boolean;
      }>;
      total: number;
    }>(`/api/v2/sensors/alerts/rules${params}`);
  }

  async createSensorAlertRule(data: {
    name: string;
    sensor: string;
    condition: string;
    threshold: number;
    unit: string;
    severity?: string;
    notify_email?: boolean;
    notify_sms?: boolean;
    notify_push?: boolean;
  }) {
    return this.client.request<any>("/api/v2/sensors/alerts/rules", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateSensorAlertRule(
    ruleId: string,
    data: {
      name?: string;
      enabled?: boolean;
      threshold?: number;
      severity?: string;
      notify_email?: boolean;
      notify_sms?: boolean;
      notify_push?: boolean;
    },
  ) {
    return this.client.request<any>(`/api/v2/sensors/alerts/rules/${ruleId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteSensorAlertRule(ruleId: string) {
    return this.client.request<any>(`/api/v2/sensors/alerts/rules/${ruleId}`, {
      method: "DELETE",
    });
  }

  async getSensorAlertEvents(options?: {
    acknowledged?: boolean;
    severity?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (options?.acknowledged !== undefined)
      params.append("acknowledged", options.acknowledged.toString());
    if (options?.severity) params.append("severity", options.severity);
    if (options?.limit) params.append("limit", options.limit.toString());
    const query = params.toString() ? `?${params}` : "";
    return this.client.request<{
      events: Array<{
        id: string;
        rule_id: string;
        rule_name: string;
        device_id: string;
        sensor: string;
        value: number;
        threshold: number;
        severity: string;
        message: string;
        timestamp: string;
        acknowledged: boolean;
        acknowledged_by?: string;
        acknowledged_at?: string;
      }>;
      total: number;
    }>(`/api/v2/sensors/alerts/events${query}`);
  }

  async acknowledgeSensorAlert(eventId: string, user: string) {
    return this.client.request<any>(
      `/api/v2/sensors/alerts/events/${eventId}/acknowledge?user=${encodeURIComponent(user)}`,
      {
        method: "POST",
      },
    );
  }

  async getSensorNetworkStats() {
    return this.client.request<{
      total_devices: number;
      online_devices: number;
      offline_devices: number;
      warning_devices: number;
      total_readings_today: number;
      active_alerts: number;
      avg_battery: number;
      avg_signal: number;
    }>("/api/v2/sensors/stats");
  }

  async getSensorDeviceTypes() {
    return this.client.request<{ types: string[] }>("/api/v2/sensors/device-types");
  }

  async getSensorTypes() {
    return this.client.request<{ types: string[] }>("/api/v2/sensors/sensor-types");
  }
}
