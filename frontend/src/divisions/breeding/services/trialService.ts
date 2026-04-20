/**
 * Trial Service
 * API client for trial creation and management
 */

import { apiClient } from '@/lib/api-client';
import type { TrialFormData, TrialResponse } from '../trials/types';

export class TrialService {
  /**
   * Create a new trial
   */
  async createTrial(data: TrialFormData): Promise<TrialResponse> {
    const response = await apiClient.trialService.createTrial(data);
    return response.result as TrialResponse;
  }

  /**
   * Get trial by ID
   */
  async getTrial(trialDbId: string): Promise<TrialResponse> {
    const response = await apiClient.trialService.getTrial(trialDbId);
    return response.result as TrialResponse;
  }

  /**
   * Get list of trials
   */
  async getTrials(page = 0, pageSize = 20) {
    return apiClient.trialService.getTrials(page, pageSize);
  }
}

export const trialService = new TrialService();
