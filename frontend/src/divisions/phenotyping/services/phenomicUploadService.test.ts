/**
 * PhenomicUploadService Tests
 * Unit tests for phenomic upload API service
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PhenomicUploadService } from './phenomicUploadService';
import { apiClient } from '@/lib/api-client';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

describe('PhenomicUploadService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('uploadSpectralData', () => {
    it('uploads file with all parameters', async () => {
      const mockReceipt = {
        success: true,
        job_id: 123,
        status: 'queued',
        filename: 'test.csv',
        size_bytes: 1024,
        dataset_name: 'Test Dataset',
        crop: 'Wheat',
        platform: 'NIRS',
        message: 'Upload successful',
      };
      
      vi.mocked(apiClient.post).mockResolvedValue(mockReceipt);
      
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const result = await PhenomicUploadService.uploadSpectralData(
        file,
        'Test Dataset',
        'Wheat',
        'NIRS'
      );
      
      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v2/phenomic-selection/upload',
        expect.any(FormData),
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      
      expect(result).toEqual(mockReceipt);
    });

    it('uploads file with null optional parameters', async () => {
      const mockReceipt = {
        success: true,
        job_id: 456,
        status: 'queued',
        filename: 'data.spc',
        size_bytes: 2048,
        dataset_name: null,
        crop: null,
        platform: 'Hyperspectral',
        message: 'Upload successful',
      };
      
      vi.mocked(apiClient.post).mockResolvedValue(mockReceipt);
      
      const file = new File(['spectral data'], 'data.spc', { type: 'application/octet-stream' });
      const result = await PhenomicUploadService.uploadSpectralData(
        file,
        null,
        null,
        'Hyperspectral'
      );
      
      expect(result).toEqual(mockReceipt);
    });
  });

  describe('validateFile', () => {
    it('accepts valid CSV file', () => {
      const file = new File(['data'], 'test.csv', { type: 'text/csv' });
      const result = PhenomicUploadService.validateFile(file);
      
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('accepts valid DX file', () => {
      const file = new File(['data'], 'test.dx', { type: 'application/octet-stream' });
      const result = PhenomicUploadService.validateFile(file);
      
      expect(result.valid).toBe(true);
    });

    it('accepts valid SPC file', () => {
      const file = new File(['data'], 'test.spc', { type: 'application/octet-stream' });
      const result = PhenomicUploadService.validateFile(file);
      
      expect(result.valid).toBe(true);
    });

    it('rejects invalid file extension', () => {
      const file = new File(['data'], 'test.txt', { type: 'text/plain' });
      const result = PhenomicUploadService.validateFile(file);
      
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid file format');
    });

    it('rejects file exceeding size limit', () => {
      const largeContent = new Array(101 * 1024 * 1024).fill('x').join('');
      const file = new File([largeContent], 'large.csv', { type: 'text/csv' });
      const result = PhenomicUploadService.validateFile(file);
      
      expect(result.valid).toBe(false);
      expect(result.error).toContain('exceeds 100MB limit');
    });

    it('accepts file at size limit', () => {
      const content = new Array(100 * 1024 * 1024).fill('x').join('');
      const file = new File([content], 'max.csv', { type: 'text/csv' });
      const result = PhenomicUploadService.validateFile(file);
      
      expect(result.valid).toBe(true);
    });
  });
});
