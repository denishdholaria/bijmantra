/**
 * usePhenomicUpload Hook Tests
 * Unit tests for phenomic upload state management hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { usePhenomicUpload } from './usePhenomicUpload';
import * as PhenomicUploadServiceModule from '../services/phenomicUploadService';

// Mock the service
vi.mock('../services/phenomicUploadService', () => ({
  PhenomicUploadService: {
    uploadSpectralData: vi.fn(),
    validateFile: vi.fn(),
  },
}));

const { PhenomicUploadService } = PhenomicUploadServiceModule;

describe('usePhenomicUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => usePhenomicUpload());
    
    expect(result.current.isUploading).toBe(false);
    expect(result.current.uploadProgress).toBe(0);
    expect(result.current.uploadMessage).toBeNull();
    expect(result.current.uploadReceipt).toBeNull();
    expect(result.current.selectedFile).toBeNull();
    expect(result.current.platform).toBe('NIRS');
  });

  it('updates state with partial updates', () => {
    const { result } = renderHook(() => usePhenomicUpload());
    
    act(() => {
      result.current.update({ datasetName: 'Test Dataset', crop: 'Wheat' });
    });
    
    expect(result.current.datasetName).toBe('Test Dataset');
    expect(result.current.crop).toBe('Wheat');
    expect(result.current.platform).toBe('NIRS'); // unchanged
  });

  it('validates and selects valid file', () => {
    (PhenomicUploadService.validateFile as any).mockReturnValue({ valid: true });
    
    const { result } = renderHook(() => usePhenomicUpload());
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    act(() => {
      result.current.selectFile(file);
    });
    
    expect(result.current.selectedFile).toBe(file);
    expect(result.current.uploadMessage).toBeNull();
  });

  it('rejects invalid file with error message', () => {
    (PhenomicUploadService.validateFile as any).mockReturnValue({
      valid: false,
      error: 'Invalid file format',
    });
    
    const { result } = renderHook(() => usePhenomicUpload());
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    
    act(() => {
      result.current.selectFile(file);
    });
    
    expect(result.current.selectedFile).toBeNull();
    expect(result.current.uploadMessage).toBe('Invalid file format');
  });

  it('uploads file successfully', async () => {
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
    
    (PhenomicUploadService.validateFile as any).mockReturnValue({ valid: true });
    (PhenomicUploadService.uploadSpectralData as any).mockResolvedValue(mockReceipt);
    
    const { result } = renderHook(() => usePhenomicUpload());
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    act(() => {
      result.current.selectFile(file);
      result.current.update({ datasetName: 'Test Dataset', crop: 'Wheat' });
    });
    
    await act(async () => {
      await result.current.uploadFile();
    });
    
    await waitFor(() => {
      expect(result.current.uploadReceipt).toEqual(mockReceipt);
      expect(result.current.isUploading).toBe(false);
      expect(result.current.uploadProgress).toBe(100);
    });
  });

  it('handles upload error', async () => {
    (PhenomicUploadService.validateFile as any).mockReturnValue({ valid: true });
    (PhenomicUploadService.uploadSpectralData as any).mockRejectedValue(
      new Error('Network error')
    );
    
    const { result } = renderHook(() => usePhenomicUpload());
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    act(() => {
      result.current.selectFile(file);
    });
    
    await act(async () => {
      await result.current.uploadFile();
    });
    
    await waitFor(() => {
      expect(result.current.uploadMessage).toBe('Network error');
      expect(result.current.isUploading).toBe(false);
      expect(result.current.uploadReceipt).toBeNull();
    });
  });

  it('prevents upload without file', async () => {
    const { result } = renderHook(() => usePhenomicUpload());
    
    await act(async () => {
      await result.current.uploadFile();
    });
    
    expect(result.current.uploadMessage).toContain('Please select a file');
    expect(PhenomicUploadService.uploadSpectralData).not.toHaveBeenCalled();
  });

  it('resets state to initial values', () => {
    (PhenomicUploadService.validateFile as any).mockReturnValue({ valid: true });
    
    const { result } = renderHook(() => usePhenomicUpload());
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    act(() => {
      result.current.selectFile(file);
      result.current.update({ datasetName: 'Test', crop: 'Wheat', platform: 'Hyperspectral' });
    });
    
    expect(result.current.selectedFile).toBe(file);
    expect(result.current.datasetName).toBe('Test');
    
    act(() => {
      result.current.reset();
    });
    
    expect(result.current.selectedFile).toBeNull();
    expect(result.current.datasetName).toBe('');
    expect(result.current.crop).toBe('');
    expect(result.current.platform).toBe('NIRS');
    expect(result.current.uploadReceipt).toBeNull();
  });
});
