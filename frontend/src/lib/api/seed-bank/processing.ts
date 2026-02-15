import { ApiClientCore } from "../core/client";

export class ProcessingService {
  constructor(private client: ApiClientCore) {}

  async createProcessingBatch(data: {
    lot_id: string;
    variety_name: string;
    crop: string;
    seed_class?: string;
    input_quantity_kg: number;
    target_output_kg?: number;
    notes?: string;
  }) {
    return this.client.post<any>("/api/v2/processing/batches", data);
  }

  async getProcessingBatches(status?: string, stage?: string, lotId?: string) {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (stage) params.append("stage", stage);
    if (lotId) params.append("lot_id", lotId);
    return this.client.get<any>(`/api/v2/processing/batches?${params}`);
  }

  async getProcessingBatch(batchId: string) {
    return this.client.get<any>(`/api/v2/processing/batches/${batchId}`);
  }

  async updateBatchStatus(
    batchId: string,
    status: string,
    data?: {
      stage?: string;
      notes?: string;
      output_quantity_kg?: number;
      waste_quantity_kg?: number;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/processing/batches/${batchId}/status`,
      {
        status,
        ...data,
      }
    );
  }

  async recordProcessingAction(
    batchId: string,
    data: {
      action_type: string;
      description: string;
      operator_id?: string;
      operator_name?: string;
      duration_minutes?: number;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/processing/batches/${batchId}/actions`,
      data
    );
  }

  async startProcessingStage(
    batchId: string,
    data: {
      stage: string;
      operator: string;
      equipment?: string;
      input_quantity_kg?: number;
      parameters?: Record<string, any>;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/processing/batches/${batchId}/stages`,
      data
    );
  }

  async completeProcessingStage(
    batchId: string,
    stageId: string,
    data: {
      output_quantity_kg: number;
      notes?: string;
    }
  ) {
    return this.client.put<any>(
      `/api/v2/processing/batches/${batchId}/stages/${stageId}`,
      data
    );
  }

  async addBatchQualityCheck(
    batchId: string,
    data: {
      check_type: string;
      result_value: number;
      passed: boolean;
      checked_by: string;
      notes?: string;
    }
  ) {
    return this.client.post<any>(
      `/api/v2/processing/batches/${batchId}/quality-checks`,
      data
    );
  }

  async holdBatch(batchId: string, reason: string) {
    return this.client.post<any>(
      `/api/v2/processing/batches/${batchId}/hold?reason=${encodeURIComponent(
        reason
      )}`,
      {}
    );
  }

  async resumeBatch(batchId: string) {
    return this.client.post<any>(
      `/api/v2/processing/batches/${batchId}/resume`,
      {}
    );
  }

  async rejectBatch(batchId: string, reason: string) {
    return this.client.post<any>(
      `/api/v2/processing/batches/${batchId}/reject?reason=${encodeURIComponent(
        reason
      )}`,
      {}
    );
  }

  async getBatchSummary(batchId: string) {
    return this.client.get<any>(`/api/v2/processing/batches/${batchId}/summary`);
  }

  async getProcessingStages() {
    return this.client.get<any>("/api/v2/processing/stages");
  }

  async getProcessingStatistics() {
    return this.client.get<any>("/api/v2/processing/statistics");
  }
}
