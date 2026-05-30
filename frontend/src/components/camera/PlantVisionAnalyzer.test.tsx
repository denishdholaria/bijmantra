import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { PlantVisionAnalyzer } from './PlantVisionAnalyzer';

const apiMocks = vi.hoisted(() => ({
  analyzeImage: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    visionService: {
      analyzeImage: apiMocks.analyzeImage,
    },
  },
}));

describe('PlantVisionAnalyzer', () => {
  beforeEach(() => {
    apiMocks.analyzeImage.mockReset();
  });

  it('calls backend analysis and renders runtime unavailable without fake findings', async () => {
    apiMocks.analyzeImage.mockResolvedValue({
      success: true,
      status: 'runtime_unavailable',
      image: {
        filename: 'leaf.jpg',
        content_type: 'image/jpeg',
        format: 'JPEG',
        width: 320,
        height: 240,
        size_bytes: 128,
        quality_warnings: [],
      },
      predictions: [],
      explainability: {
        message: 'Image validated, but no production Plant Vision runtime is deployed for this organization.',
      },
      model: null,
    });

    const { container } = render(<PlantVisionAnalyzer cropType="rice" />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['leaf-image'], 'leaf.jpg', { type: 'image/jpeg' });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(apiMocks.analyzeImage).toHaveBeenCalledWith(file, 'rice'));
    expect(await screen.findByText(/no production Plant Vision runtime/i)).toBeInTheDocument();
    expect(screen.queryByText(/Bacterial Leaf Blight/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Rice Blast/i)).not.toBeInTheDocument();
  });

  it('rejects unsupported local file types before calling backend', async () => {
    const { container } = render(<PlantVisionAnalyzer cropType="rice" />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['not an image'], 'leaf.txt', { type: 'text/plain' });

    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText(/unsupported file type/i)).toBeInTheDocument();
    expect(apiMocks.analyzeImage).not.toHaveBeenCalled();
  });
});
