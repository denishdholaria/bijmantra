/**
 * usePhenomicUpload Hook
 * State management and orchestration for phenomic upload workflows
 */

import { useState, useCallback } from 'react';
import { PhenomicUploadService } from '../services/phenomicUploadService';
import type { PhenomicUploadState, UploadValidationError } from './types';

export function usePhenomicUpload() {
  const [state, setState] = useState<PhenomicUploadState>({
    isUploading: false,
    uploadProgress: 0,
    uploadMessage: null,
    uploadReceipt: null,
    selectedFile: null,
    datasetName: '',
    crop: '',
    platform: 'NIRS',
  });

  const update = useCallback((partial: Partial<PhenomicUploadState>) => {
    setState((prev) => ({ ...prev, ...partial }));
  }, []);

  const selectFile = useCallback((file: File | null) => {
    if (!file) {
      update({ selectedFile: null, uploadMessage: null });
      return;
    }

    const validation = PhenomicUploadService.validateFile(file);
    if (!validation.valid) {
      update({
        selectedFile: null,
        uploadMessage: validation.error || 'Invalid file',
      });
      return;
    }

    update({
      selectedFile: file,
      uploadMessage: null,
      uploadReceipt: null,
    });
  }, [update]);

  const validateForm = useCallback((): UploadValidationError[] => {
    const errors: UploadValidationError[] = [];

    if (!state.selectedFile) {
      errors.push({
        field: 'file',
        message: 'Please select a file to upload',
      });
    }

    if (!state.platform) {
      errors.push({
        field: 'platform',
        message: 'Please select a platform',
      });
    }

    return errors;
  }, [state.selectedFile, state.platform]);

  const uploadFile = useCallback(async () => {
    const errors = validateForm();
    if (errors.length > 0) {
      update({
        uploadMessage: errors.map(e => e.message).join('; '),
      });
      return;
    }

    if (!state.selectedFile) {
      return;
    }

    update({
      isUploading: true,
      uploadProgress: 0,
      uploadMessage: null,
      uploadReceipt: null,
    });

    try {
      // Simulate progress for better UX
      update({ uploadProgress: 30 });

      const receipt = await PhenomicUploadService.uploadSpectralData(
        state.selectedFile,
        state.datasetName || null,
        state.crop || null,
        state.platform
      );

      update({
        uploadProgress: 100,
        uploadReceipt: receipt,
        uploadMessage: receipt.message,
      });
    } catch (error) {
      update({
        uploadProgress: 0,
        uploadMessage: error instanceof Error ? error.message : 'Upload failed. Please try again.',
      });
    } finally {
      update({ isUploading: false });
    }
  }, [state.selectedFile, state.datasetName, state.crop, state.platform, validateForm, update]);

  const reset = useCallback(() => {
    setState({
      isUploading: false,
      uploadProgress: 0,
      uploadMessage: null,
      uploadReceipt: null,
      selectedFile: null,
      datasetName: '',
      crop: '',
      platform: 'NIRS',
    });
  }, []);

  return {
    ...state,
    update,
    selectFile,
    uploadFile,
    reset,
  };
}
