import { ApiClientCore } from "../core/client";

export interface NotificationRecord {
  id: number;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  category: string;
  action_url?: string | null;
}

export interface NotificationStats {
  total: number;
  unread: number;
  warnings: number;
  success: number;
  errors: number;
  info: number;
}

export interface NotificationPreferenceRecord {
  category: string;
  email: boolean;
  push: boolean;
  in_app: boolean;
}

export interface QuietHoursRecord {
  enabled: boolean;
  start_time: string;
  end_time: string;
}

export class NotificationService {
  constructor(private client: ApiClientCore) {}

  async getNotifications(params?: {
    filter?: 'all' | 'unread' | 'success' | 'warning' | 'error' | 'info';
    unreadOnly?: boolean;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.filter && params.filter !== 'all' && params.filter !== 'unread') {
      searchParams.append('filter', params.filter);
    }
    if (params?.unreadOnly || params?.filter === 'unread') {
      searchParams.append('unread_only', 'true');
    }
    
    const query = searchParams.toString();
    return this.client.get<NotificationRecord[]>(`/api/v2/notifications/${query ? `?${query}` : ''}`);
  }

  async getStats() {
    return this.client.get<NotificationStats>('/api/v2/notifications/stats');
  }

  async markAsRead(notificationId: number) {
    return this.client.post<{ message: string }>('/api/v2/notifications/mark-read', {
      notification_ids: [notificationId],
    });
  }

  async markAllAsRead() {
    return this.client.post<{ message: string }>('/api/v2/notifications/mark-all-read', {});
  }

  async deleteNotification(notificationId: number) {
    return this.client.delete<{ message: string }>(`/api/v2/notifications/${notificationId}`);
  }

  async createNotification(data: {
    type?: string;
    title: string;
    message: string;
    link?: string;
    category?: string;
  }) {
    return this.client.post<NotificationRecord>('/api/v2/notifications/', data);
  }

  async getPreferences() {
    return this.client.get<NotificationPreferenceRecord[]>('/api/v2/notifications/preferences');
  }

  async updatePreference(data: NotificationPreferenceRecord) {
    return this.client.put<{ message: string }>('/api/v2/notifications/preferences', data);
  }

  async getQuietHours() {
    return this.client.get<QuietHoursRecord>('/api/v2/notifications/quiet-hours');
  }

  async updateQuietHours(data: QuietHoursRecord) {
    return this.client.put<{ message: string }>('/api/v2/notifications/quiet-hours', data);
  }
}
