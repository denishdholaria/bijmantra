/**
 * PhenomicUploadPanel Tests
 * Unit tests for phenomic upload component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PhenomicUploadPanel } from './PhenomicUploadPanel';
import { PhenomicUploadService } from '../services/phenomicUploadService';

// Mock the service
vi.mock('../services/phenomicUploadService', () => ({
  PhenomicUploadService: {
    uploadSpectralData: vi.fn(),
    validateFile: vi.fn(),
  },
}));

describe('PhenomicUploadPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state with drag-drop zone', () => {
    render(<PhenomicUploadPanel />);
    
    expect(screen.getByText('Phenomic Data Upload')).toBeInTheDocument();
    expect(screen.getByText('Drop your file here')).toBeInTheDocument();
    expect(screen.getByText('or click to browse')).toBeInTheDocument();
  });

  it('displays selected file information', async () => {
    vi.mocked(PhenomicUploadService.validateFile).mockReturnValue({ valid: true });
    
    render(<PhenomicUploadPanel />);
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('test.csv')).toBeInTheDocument();
    });
  });

  it('shows error state for invalid file', async () => {
    vi.mocked(PhenomicUploadService.validateFile).mockReturnValue({
      valid: false,
      error: 'Invalid file format',
    });
    
    render(<PhenomicUploadPanel />);
    
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('Invalid file format')).toBeInTheDocument();
    });
  });

  it('shows loading state during upload', async () => {
    vi.mocked(PhenomicUploadService.validateFile).mockReturnValue({ valid: true });
    vi.mocked(PhenomicUploadService.uploadSpectralData).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );
    
    render(<PhenomicUploadPanel />);
    
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('test.csv')).toBeInTheDocument();
    });
    
    const uploadButton = screen.getByRole('button', { name: /upload spectral data/i });
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      expect(screen.getByText('Uploading Spectral Data...')).toBeInTheDocument();
    });
  });

  it('shows success state with upload receipt', async () => {
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
    
    vi.mocked(PhenomicUploadService.validateFile).mockReturnValue({ valid: true });
    vi.mocked(PhenomicUploadService.uploadSpectralData).mockResolvedValue(mockReceipt);
    
    render(<PhenomicUploadPanel />);
    
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('test.csv')).toBeInTheDocument();
    });
    
    const uploadButton = screen.getByRole('button', { name: /upload spectral data/i });
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      expect(screen.getByText('Upload Successful')).toBeInTheDocument();
      expect(screen.getByText('#123')).toBeInTheDocument();
      expect(screen.getByText('Test Dataset')).toBeInTheDocument();
    });
  });

  it('allows resetting after successful upload', async () => {
    const mockReceipt = {
      success: true,
      job_id: 123,
      status: 'queued',
      filename: 'test.csv',
      size_bytes: 1024,
      dataset_name: null,
      crop: null,
      platform: 'NIRS',
      message: 'Upload successful',
    };
    
    vi.mocked(PhenomicUploadService.validateFile).mockReturnValue({ valid: true });
    vi.mocked(PhenomicUploadService.uploadSpectralData).mockResolvedValue(mockReceipt);
    
    render(<PhenomicUploadPanel />);
    
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('test.csv')).toBeInTheDocument();
    });
    
    const uploadButton = screen.getByRole('button', { name: /upload spectral data/i });
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      expect(screen.getByText('Upload Successful')).toBeInTheDocument();
    });
    
    const resetButton = screen.getByRole('button', { name: /upload another file/i });
    fireEvent.click(resetButton);
    
    await waitFor(() => {
      expect(screen.getByText('Drop your file here')).toBeInTheDocument();
    });
  });
});
