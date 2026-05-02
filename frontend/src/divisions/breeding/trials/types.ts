/**
 * Trial Creation Types
 * Type definitions for trial creation workflow
 */

export interface TrialFormData {
  trialName: string;
  trialDescription?: string;
  trialType?: string;
  programDbId?: string;
  startDate?: string;
  endDate?: string;
  active?: boolean;
  commonCropName?: string;
}

export interface TrialCreationState {
  isLoading: boolean;
  isEmpty: boolean;
  error: string | null;
  success: boolean;
  createdTrialId?: string;
}

export interface TrialResponse {
  trialDbId: string;
  trialName: string;
  trialDescription?: string;
  trialType?: string;
  programDbId?: string;
  startDate?: string;
  endDate?: string;
  active?: boolean;
  commonCropName?: string;
}
