import { ApiClientCore } from "../core/client";

export class CollaborationService {
  constructor(private client: ApiClientCore) {}

  async getTeamMembers() {
    return this.client.get<
      Array<{
        id: string;
        name: string;
        email: string;
        role: string;
        avatar?: string;
        status: "online" | "away" | "offline";
        last_active?: string;
      }>
    >("/api/v2/collaboration/team-members");
  }

  async getSharedItems(itemType?: string) {
    const query = itemType ? `?item_type=${itemType}` : "";
    return this.client.get<
      Array<{
        id: string;
        type: string;
        name: string;
        shared_by: string;
        shared_at: string;
        permission: string;
      }>
    >(`/api/v2/collaboration/shared-items${query}`);
  }

  async shareItem(data: {
    item_type: string;
    item_id: string;
    user_ids: string[];
    permission?: string;
  }) {
    return this.client.post<any>("/api/v2/collaboration/share-item", data);
  }

  async getActivityFeed(limit?: number, offset?: number) {
    const params = new URLSearchParams();
    if (limit) params.append("limit", limit.toString());
    if (offset) params.append("offset", offset.toString());
    return this.client.get<
      Array<{
        id: string;
        user: string;
        action: string;
        target: string;
        timestamp: string;
        type: string;
      }>
    >(`/api/v2/collaboration/activity?${params}`);
  }

  async getConversations() {
    return this.client.get<
      Array<{
        id: string;
        name: string;
        type: string;
        participants: string[];
        last_message?: string;
        unread_count: number;
      }>
    >("/api/v2/collaboration/conversations");
  }

  async getMessages(conversationId: string, limit?: number, offset?: number) {
    const params = new URLSearchParams();
    if (limit) params.append("limit", limit.toString());
    if (offset) params.append("offset", offset.toString());
    return this.client.get<
      Array<{
        id: string;
        sender: string;
        content: string;
        timestamp: string;
        is_own: boolean;
        conversation_id: string;
      }>
    >(`/api/v2/collaboration/messages/${conversationId}?${params}`);
  }

  async sendMessage(data: { conversation_id: string; content: string }) {
    return this.client.post<any>("/api/v2/collaboration/messages", data);
  }

  async updatePresence(status: "online" | "away" | "offline") {
    return this.client.post<any>("/api/v2/collaboration/presence", { status });
  }

  async getStats() {
    return this.client.get<{
      team_members: number;
      online_now: number;
      shared_items: number;
      today_activity: number;
      unread_messages: number;
    }>("/api/v2/collaboration/stats");
  }
}
