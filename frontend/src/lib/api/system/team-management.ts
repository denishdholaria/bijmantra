import { ApiClientCore } from "../core/client";

export class TeamManagementService {
  constructor(private client: ApiClientCore) {}

  async getMembers(params?: {
    role?: string;
    status?: string;
    team_id?: string;
    search?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.role) searchParams.append("role", params.role);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.team_id) searchParams.append("team_id", params.team_id);
    if (params?.search) searchParams.append("search", params.search);
    
    return this.client.get<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        email: string;
        role: string;
        status: string;
        joined_at: string;
        last_active: string | null;
        team_ids: string[];
      }>;
      count: number;
    }>(`/api/v2/teams/members?${searchParams}`);
  }

  async getMember(memberId: string) {
    return this.client.get<any>(`/api/v2/teams/members/${memberId}`);
  }

  async createMember(data: {
    name: string;
    email: string;
    role: string;
    team_ids?: string[];
  }) {
    return this.client.post<any>("/api/v2/teams/members", data);
  }

  async updateMember(
    memberId: string,
    data: { role?: string; status?: string; team_ids?: string[] }
  ) {
    return this.client.patch<any>(`/api/v2/teams/members/${memberId}`, data);
  }

  async deleteMember(memberId: string) {
    return this.client.delete<any>(`/api/v2/teams/members/${memberId}`);
  }

  async getTeams() {
    return this.client.get<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        description: string;
        member_count: number;
        project_count: number;
      }>;
    }>("/api/v2/teams");
  }

  async getTeam(teamId: string) {
    return this.client.get<any>(`/api/v2/teams/${teamId}`);
  }

  async createTeam(data: {
    name: string;
    description?: string;
    lead_id?: string;
  }) {
    return this.client.post<any>("/api/v2/teams", data);
  }

  async updateTeam(
    teamId: string,
    data: { name?: string; description?: string; lead_id?: string }
  ) {
    return this.client.patch<any>(`/api/v2/teams/${teamId}`, data);
  }

  async deleteTeam(teamId: string) {
    return this.client.delete<any>(`/api/v2/teams/${teamId}`);
  }

  async getRoles() {
    return this.client.get<any>("/api/v2/teams/roles");
  }

  async getInvites(status?: string) {
    const query = status ? `?status=${status}` : "";
    return this.client.get<any>(`/api/v2/teams/invites${query}`);
  }

  async createInvite(data: { email: string; role: string }) {
    return this.client.post<any>("/api/v2/teams/invites", data);
  }

  async resendInvite(inviteId: string) {
    return this.client.post<any>(`/api/v2/teams/invites/${inviteId}/resend`, {});
  }

  async deleteInvite(inviteId: string) {
    return this.client.delete<any>(`/api/v2/teams/invites/${inviteId}`);
  }

  async getStats() {
    return this.client.get<any>("/api/v2/teams/stats");
  }
}
