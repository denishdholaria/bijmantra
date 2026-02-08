import { ApiClientCore } from "../core/client";

export class SystemSettingsService {
  constructor(private client: ApiClientCore) {}

  async getAllSettings() {
    return this.client.get<{
      general: {
        site_name: string;
        site_description: string;
        default_language: string;
        timezone: string;
        date_format: string;
      };
      security: {
        enable_registration: boolean;
        require_email_verification: boolean;
        session_timeout: number;
      };
      api: {
        brapi_version: string;
        api_rate_limit: number;
        max_upload_size: number;
      };
      features: {
        enable_offline_mode: boolean;
        enable_notifications: boolean;
        enable_audit_log: boolean;
      };
    }>("/api/v2/system-settings/all");
  }

  async getGeneralSettings() {
    return this.client.get<any>("/api/v2/system-settings/general");
  }

  async updateGeneralSettings(data: {
    site_name?: string;
    site_description?: string;
    default_language?: string;
    timezone?: string;
    date_format?: string;
  }) {
    return this.client.patch<any>("/api/v2/system-settings/general", data);
  }

  async getSecuritySettings() {
    return this.client.get<any>("/api/v2/system-settings/security");
  }

  async updateSecuritySettings(data: {
    enable_registration?: boolean;
    require_email_verification?: boolean;
    session_timeout?: number;
  }) {
    return this.client.patch<any>("/api/v2/system-settings/security", data);
  }

  async getAPISettings() {
    return this.client.get<any>("/api/v2/system-settings/api");
  }

  async updateAPISettings(data: {
    brapi_version?: string;
    api_rate_limit?: number;
    max_upload_size?: number;
  }) {
    return this.client.patch<any>("/api/v2/system-settings/api", data);
  }

  async getFeatureToggles() {
    return this.client.get<any>("/api/v2/system-settings/features");
  }

  async updateFeatureToggles(data: {
    enable_offline_mode?: boolean;
    enable_notifications?: boolean;
    enable_audit_log?: boolean;
  }) {
    return this.client.patch<any>("/api/v2/system-settings/features", data);
  }

  async getSystemStatus() {
    return this.client.get<{
      task_queue: {
        pending: number;
        running: number;
        completed: number;
        failed: number;
        max_concurrent: number;
      };
      event_bus: {
        subscriptions: Record<string, string[]>;
        total_events: number;
      };
      service_health: Record<string, string>;
    }>("/api/v2/system-settings/status");
  }

  async resetToDefaults() {
    return this.client.post<any>("/api/v2/system-settings/reset-defaults", {});
  }

  async exportSettings() {
    return this.client.get<any>("/api/v2/system-settings/export");
  }

  async importSettings(settings: any) {
    return this.client.post<any>("/api/v2/system-settings/import", settings);
  }
}
