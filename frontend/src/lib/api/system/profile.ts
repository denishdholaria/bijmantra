import { ApiClientCore } from "../core/client";

export class ProfileService {
  constructor(private client: ApiClientCore) {}

  async getProfile() {
    return this.client.get<{
      status: string;
      data: {
        id: string;
        full_name: string;
        email: string;
        organization_id: number;
        organization_name: string;
        role: string;
        status: string;
        avatar_url: string | null;
        phone: string | null;
        bio: string | null;
        location: string | null;
        timezone: string;
        created_at: string;
        last_login: string;
      };
    }>("/api/v2/profile");
  }

  async updateProfile(data: {
    full_name?: string;
    phone?: string;
    bio?: string;
    location?: string;
    timezone?: string;
  }) {
    return this.client.patch<any>("/api/v2/profile", data);
  }

  async getPreferences() {
    return this.client.get<{
      status: string;
      data: {
        theme: string;
        language: string;
        density: string;
        color_scheme: string;
        field_mode: boolean;
        email_notifications: boolean;
        push_notifications: boolean;
        sound_enabled: boolean;
      };
    }>("/api/v2/profile/preferences");
  }

  async updatePreferences(data: Record<string, any>) {
    return this.client.patch<any>("/api/v2/profile/preferences", data);
  }

  async changePassword(data: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }) {
    return this.client.post<any>("/api/v2/profile/change-password", data);
  }

  async getSessions() {
    return this.client.get<any>("/api/v2/profile/sessions");
  }

  async revokeSession(sessionId: string) {
    return this.client.delete<any>(`/api/v2/profile/sessions/${sessionId}`);
  }

  async getActivity(limit?: number) {
    const query = limit ? `?limit=${limit}` : "";
    return this.client.get<any>(`/api/v2/profile/activity${query}`);
  }
}
