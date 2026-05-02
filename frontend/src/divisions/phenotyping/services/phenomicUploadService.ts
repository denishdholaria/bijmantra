/**
 * Phenomic Upload Service
 * API client for phenomic data upload endpoints
 */

import { apiClient } from '@/lib/api-client';
import type { UploadReceipt } from '../upload/types';

export class PhenomicUploadService {
  /**
   * Upload spectral data file to the server
   */
  static async uploadSpectralData(
    file: File,
    datasetName: string | null,
    crop: string | null,
    platform: string
  ): Promise<UploadReceipt> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (datasetName) {
      formData.append('dataset_name', datasetName);
    }
    
    if (crop) {
      formData.append('crop', crop);
    }
    
    formData.append('platform', platform);

    const response = await apiClient.post('/api/v2/phenomic-selection/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }) as unknown as UploadReceipt;

    return response;
  }

  /**
   * Validate file before upload
   */
  static validateFile(file: File): { valid: boolean; error?: string } {
    const validExtensions = ['.csv', '.dx', '.spc'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));

    if (!hasValidExtension) {
      return {
        valid: false,
        error: `Invalid file format. Supported formats: ${validExtensions.join(', ')}`,
      };
    }

    // Check file size (max 100MB)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'File size exceeds 100MB limit',
      };
    }

    return { valid: true };
  }
}
