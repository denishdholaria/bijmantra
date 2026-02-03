import { ApiClientCore } from "../core/client";

export class NotificationService {
  constructor(private client: ApiClientCore) {}

  async getNotifications(params?: {
    category?: string;
    type?: string;
    read?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.append("category", params.category);
    if (params?.type) searchParams.append("type", params.type);
    if (params?.read !== undefined)
      searchParams.append("read", String(params.read));
    if (params?.limit) searchParams.append("limit", String(params.limit));
    if (params?.offset) searchParams.append("offset", String(params.offset));
    
    const query = searchParams.toString();
    return this.client.get<{
      status: string;
      data: Array<{
        id: string;
        type: string;
        title: string;
        message: string;
        timestamp: string;
        read: boolean;
        link?: string;
        category: string;
      }>;
      total: number;
      unread_count: number;
    }>(`/api/v2/notifications?${query}`);
  }

  async getUnreadCount() {
    return this.client.get<{ status: string; count: number }>(
      "/api/v2/notifications/unread-count"
    );
  }

  async getSummary() {
    return this.client.get<{
      status: string;
      data: {
        total: number;
        unread: number;
        by_category: Record<string, number>;
        by_type: Record<string, number>;
      };
    }>("/api/v2/notifications/summary");
  }

  async markAsRead(notificationId: string) {
    return this.client.patch<{ status: string; data: any; message: string }>(
      `/api/v2/notifications/${notificationId}/read`,
      {}
    );
  }

  async markAllAsRead() {
    return this.client.post<{
      status: string;
      message: string;
      count: number;
    }>("/api/v2/notifications/mark-all-read", {});
  }

  async deleteNotification(notificationId: string) {
    return this.client.delete<{ status: string; message: string }>(
      `/api/v2/notifications/${notificationId}`
    );
  }

  async createNotification(data: {
    type?: string;
    title: string;
    message: string;
    link?: string;
    category?: string;
  }) {
    return this.client.post<{ status: string; data: any }>(
      "/api/v2/notifications",
      data
    );
  }
}
