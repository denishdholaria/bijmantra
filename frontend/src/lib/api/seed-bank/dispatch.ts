import { ApiClientCore } from "../core/client";

export class DispatchService {
  constructor(private client: ApiClientCore) {}

  async createDispatch(data: {
    recipient_id: string;
    recipient_name: string;
    recipient_address: string;
    recipient_contact?: string;
    recipient_phone?: string;
    transfer_type: string;
    items: Array<{
      lot_id: string;
      variety_name?: string;
      crop?: string;
      seed_class?: string;
      quantity_kg: number;
      unit_price?: number;
    }>;
    notes?: string;
  }) {
    return this.client.post<any>("/api/v2/dispatch/orders", data);
  }

  async getDispatches(
    status?: string,
    recipientId?: string,
    transferType?: string
  ) {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (recipientId) params.append("recipient_id", recipientId);
    if (transferType) params.append("transfer_type", transferType);
    return this.client.get<any>(`/api/v2/dispatch/orders?${params}`);
  }

  async getDispatch(dispatchId: string) {
    return this.client.get<any>(`/api/v2/dispatch/orders/${dispatchId}`);
  }

  async submitDispatch(dispatchId: string) {
    return this.client.post<any>(
      `/api/v2/dispatch/orders/${dispatchId}/submit`,
      {}
    );
  }

  async approveDispatch(dispatchId: string, approvedBy: string = "Manager") {
    return this.client.post<any>(
      `/api/v2/dispatch/orders/${dispatchId}/approve?approved_by=${approvedBy}`,
      {}
    );
  }

  async shipDispatch(
    dispatchId: string,
    data: {
      tracking_number?: string;
      carrier?: string;
      invoice_number?: string;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/dispatch/orders/${dispatchId}/ship`,
      data
    );
  }

  async markDispatchDelivered(dispatchId: string, notes: string = "") {
    return this.client.post<any>(
      `/api/v2/dispatch/orders/${dispatchId}/deliver?notes=${encodeURIComponent(
        notes
      )}`,
      {}
    );
  }

  async cancelDispatch(dispatchId: string, reason: string) {
    return this.client.post<any>(
      `/api/v2/dispatch/orders/${dispatchId}/cancel?reason=${encodeURIComponent(
        reason
      )}`,
      {}
    );
  }

  async getDispatchStatistics() {
    return this.client.get<any>("/api/v2/dispatch/statistics");
  }

  async getDispatchStatuses() {
    return this.client.get<any>("/api/v2/dispatch/statuses");
  }

  // Firms/Dealers
  async createFirm(data: {
    name: string;
    firm_type: string;
    address: string;
    city: string;
    state: string;
    country?: string;
    postal_code: string;
    contact_person: string;
    phone: string;
    email: string;
    gst_number?: string;
    credit_limit?: number;
    notes?: string;
  }) {
    return this.client.post<any>("/api/v2/dispatch/firms", data);
  }

  async getFirms(
    firmType?: string,
    status?: string,
    city?: string,
    state?: string
  ) {
    const params = new URLSearchParams();
    if (firmType) params.append("firm_type", firmType);
    if (status) params.append("status", status);
    if (city) params.append("city", city);
    if (state) params.append("state", state);
    return this.client.get<any>(`/api/v2/dispatch/firms?${params}`);
  }

  async getFirm(firmId: string) {
    return this.client.get<any>(`/api/v2/dispatch/firms/${firmId}`);
  }

  async updateFirm(firmId: string, data: Record<string, any>) {
    return this.client.put<any>(`/api/v2/dispatch/firms/${firmId}`, data);
  }

  async deactivateFirm(firmId: string) {
    return this.client.delete<any>(`/api/v2/dispatch/firms/${firmId}`);
  }

  async getFirmTypes() {
    return this.client.get<any>("/api/v2/dispatch/firm-types");
  }
}
