import { ApiClientCore } from "../core/client";

export interface SeedRequest {
  id: string;
  requester: string;
  organization: string;
  germplasm: string;
  quantity: number;
  unit: string;
  purpose: string;
  status: "pending" | "approved" | "shipped" | "delivered" | "rejected";
  requestDate: string;
}

export class SeedRequestService {
  constructor(private client: ApiClientCore) {}
  async getRequests(params?: {
    status?: string;
    requester?: string;
  }): Promise<{ data: SeedRequest[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.requester) searchParams.set("requester", params.requester);
    const query = searchParams.toString();
    return this.client.get<{ data: SeedRequest[]; total: number }>(
      `/api/v2/seed-requests${query ? `?${query}` : ""}`
    );
  }

  async getRequest(requestId: string): Promise<{ data: SeedRequest }> {
    return this.client.get<{ data: SeedRequest }>(`/api/v2/seed-requests/${requestId}`);
  }

  async createRequest(
    data: Partial<SeedRequest>,
  ): Promise<{ data: SeedRequest }> {
    return this.client.post<{ data: SeedRequest }>("/api/v2/seed-requests", data);
  }

  async updateStatus(
    requestId: string,
    status: SeedRequest["status"],
  ): Promise<{ data: SeedRequest }> {
    return this.client.patch<{ data: SeedRequest }>(
      `/api/v2/seed-requests/${requestId}/status`,
      { status }
    );
  }

  async getStats(): Promise<{
    total: number;
    pending: number;
    approved: number;
    shipped: number;
    delivered: number;
    rejected: number;
  }> {
    // Explicit return type inferred from usage or API def, added 'rejected' for completeness or if it was missing in original type but needed
    return this.client.get("/api/v2/seed-requests/stats");
  }
}
