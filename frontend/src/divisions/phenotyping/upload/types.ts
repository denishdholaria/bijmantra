/**
 * Phenomic Upload Types
 * Shared interfaces for phenomic data upload workflows
 */

export interface UploadReceipt {
  success: boolean;
  job_id: number;
  status: string;
  filename: string;
  size_bytes: number;
  dataset_name: string | null;
  crop: string | null;
  platform: string;
  message: string;
}

export interface PhenomicUploadState {
  isUploading: boolean;
  uploadProgress: number;
  uploadMessage: string | null;
  uploadReceipt: UploadReceipt | null;
  selectedFile: File | null;
  datasetName: string;
  crop: string;
  platform: string;
}

export interface UploadValidationError {
  field: string;
  message: string;
}
