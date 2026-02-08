import { ApiClientCore } from "../core/client";

export interface CollaborationStats {
  total_members: number;
  online_members: number;
  active_workspaces: number;
  pending_tasks: number;
  comments_today: number;
  activities_today: number;
}

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  status: "online" | "away" | "busy" | "offline";
  last_active: string;
  current_workspace?: string;
}

export interface Workspace {
  id: string;
  name: string;
  type: string;
  description?: string;
  owner_id: string;
  members: string[];
  member_details?: TeamMember[];
  created_at: string;
  updated_at: string;
}

export interface ActivityEntry {
  id: string;
  user_id: string;
  user_name: string;
  activity_type: string;
  entity_type: string;
  entity_id: string;
  entity_name: string;
  description: string;
  timestamp: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  assignee_id?: string;
  assignee_name?: string;
  workspace_id?: string;
  status: string;
  priority: string;
  due_date?: string;
  created_at: string;
}

export class CollaborationHubService {
  constructor(private client: ApiClientCore) {}

  async getStats() {
    return this.client.get<CollaborationStats>("/api/v2/collaboration-hub/stats");
  }

  async getMembers() {
    return this.client.get<{ members: TeamMember[] }>(
      "/api/v2/collaboration-hub/members"
    );
  }

  async getWorkspaces() {
    return this.client.get<{ workspaces: Workspace[] }>(
      "/api/v2/collaboration-hub/workspaces"
    );
  }

  async createWorkspace(
    name: string,
    type: string,
    description?: string
  ) {
    const params = new URLSearchParams({ name, type });
    if (description) params.append("description", description);
    return this.client.post<Workspace>(
      `/api/v2/collaboration-hub/workspaces?${params}`,
      {}
    );
  }

  async getActivities(limit: number = 20) {
    return this.client.get<{ activities: ActivityEntry[] }>(
      `/api/v2/collaboration-hub/activities?limit=${limit}`
    );
  }

  async getTasks() {
    return this.client.get<{ tasks: Task[] }>("/api/v2/collaboration-hub/tasks");
  }

  async createTask(
    title: string,
    description?: string,
    priority?: string
  ) {
    const params = new URLSearchParams({ title });
    if (description) params.append("description", description);
    if (priority) params.append("priority", priority);
    return this.client.post<Task>(
      `/api/v2/collaboration-hub/tasks?${params}`,
      {}
    );
  }

  async updateTask(
    taskId: string,
    updates: { status?: string; title?: string; priority?: string }
  ) {
    const params = new URLSearchParams();
    if (updates.status) params.append("status", updates.status);
    if (updates.title) params.append("title", updates.title);
    if (updates.priority) params.append("priority", updates.priority);
    return this.client.patch<Task>(
      `/api/v2/collaboration-hub/tasks/${taskId}?${params}`,
      {}
    );
  }

  async getPresence() {
    return this.client.get<{
      users: Array<{ user_id: string; status: string; current_page?: string }>;
    }>("/api/v2/collaboration-hub/presence");
  }
}
