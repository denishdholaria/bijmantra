import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, Mock } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import CropList from '../pages/CropList';
import CropDetail from '../pages/CropDetail';
import CropForm from '../pages/CropForm';
import * as AgronomyContextModule from '../context/AgronomyContext';
import { agronomyApi } from '../api/client';

// Mock dependencies
vi.mock('../context/AgronomyContext', () => ({
  useAgronomy: vi.fn(),
}));

vi.mock('../api/client', () => ({
  agronomyApi: {
    getCrop: vi.fn(),
  },
}));

// Mock useNavigate since it's used in components
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Crop Components', () => {
  const mockCrops = [
    { id: 1, name: 'Wheat', scientific_name: 'Triticum aestivum', variety: 'VariA', description: 'Desc A', n_req: 100, p_req: 50, k_req: 40 },
    { id: 2, name: 'Corn', scientific_name: 'Zea mays', variety: 'VariB', description: 'Desc B', n_req: 120, p_req: 60, k_req: 50 },
  ];

  const mockUseAgronomy = AgronomyContextModule.useAgronomy as Mock;

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAgronomy.mockReturnValue({
      crops: [],
      fetchCrops: vi.fn(),
      deleteCrop: vi.fn(),
      createCrop: vi.fn(),
      updateCrop: vi.fn(),
      loading: false,
    });
  });

  describe('CropList', () => {
    it('renders loading state when loading and no crops', () => {
      mockUseAgronomy.mockReturnValue({
        crops: [],
        fetchCrops: vi.fn(),
        loading: true,
        deleteCrop: vi.fn(),
      });

      render(
        <MemoryRouter>
          <CropList />
        </MemoryRouter>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders empty state when no crops', () => {
      mockUseAgronomy.mockReturnValue({
        crops: [],
        fetchCrops: vi.fn(),
        loading: false,
        deleteCrop: vi.fn(),
      });

      render(
        <MemoryRouter>
          <CropList />
        </MemoryRouter>
      );

      expect(screen.getByText('No crops found.')).toBeInTheDocument();
    });

    it('renders list of crops', () => {
      mockUseAgronomy.mockReturnValue({
        crops: mockCrops,
        fetchCrops: vi.fn(),
        loading: false,
        deleteCrop: vi.fn(),
      });

      render(
        <MemoryRouter>
          <CropList />
        </MemoryRouter>
      );

      expect(screen.getByText('Wheat')).toBeInTheDocument();
      expect(screen.getByText('Corn')).toBeInTheDocument();
      expect(screen.getByText('Triticum aestivum')).toBeInTheDocument();
    });

    it('calls deleteCrop when delete button is clicked', () => {
      const deleteCropMock = vi.fn();
      mockUseAgronomy.mockReturnValue({
        crops: mockCrops,
        fetchCrops: vi.fn(),
        loading: false,
        deleteCrop: deleteCropMock,
      });

      render(
        <MemoryRouter>
          <CropList />
        </MemoryRouter>
      );

      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]);

      expect(deleteCropMock).toHaveBeenCalledWith(1);
    });
  });

  describe('CropDetail', () => {
    it('renders loading state initially', () => {
        (agronomyApi.getCrop as Mock).mockReturnValue(new Promise(() => {})); // Never resolves
        render(
            <MemoryRouter initialEntries={['/agronomy/crops/1']}>
                <Routes>
                    <Route path="/agronomy/crops/:id" element={<CropDetail />} />
                </Routes>
            </MemoryRouter>
        );
        expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders crop details after fetch', async () => {
      const cropData = mockCrops[0];
      (agronomyApi.getCrop as Mock).mockResolvedValue(cropData);

      render(
        <MemoryRouter initialEntries={['/agronomy/crops/1']}>
          <Routes>
            <Route path="/agronomy/crops/:id" element={<CropDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Wheat')).toBeInTheDocument();
        expect(screen.getByText('ID: 1')).toBeInTheDocument();
        expect(screen.getByText('Triticum aestivum')).toBeInTheDocument();
        expect(screen.getByText('100')).toBeInTheDocument(); // N req
      });
    });

    it('navigates back when back button is clicked', async () => {
        const cropData = mockCrops[0];
        (agronomyApi.getCrop as Mock).mockResolvedValue(cropData);

        render(
            <MemoryRouter initialEntries={['/agronomy/crops/1']}>
                <Routes>
                    <Route path="/agronomy/crops/:id" element={<CropDetail />} />
                </Routes>
            </MemoryRouter>
        );

        await waitFor(() => screen.getByText('Wheat'));

        fireEvent.click(screen.getByText('Back'));
        expect(mockNavigate).toHaveBeenCalledWith('/agronomy/crops');
    });
  });

  describe('CropForm', () => {
    it('renders empty form for new crop', () => {
      const { container } = render(
        <MemoryRouter>
          <CropForm />
        </MemoryRouter>
      );

      expect(screen.getByText('New Crop')).toBeInTheDocument();
      // Use querySelector because the input lacks an ID or label association
      expect((container.querySelector('input[name="name"]') as HTMLInputElement).value).toBe('');
    });

    it('submits new crop data', async () => {
      const createCropMock = vi.fn();
      mockUseAgronomy.mockReturnValue({
        createCrop: createCropMock,
        crops: [],
        fetchCrops: vi.fn(),
      });

      const { container } = render(
        <MemoryRouter>
          <CropForm />
        </MemoryRouter>
      );

      // Use querySelector because the input lacks an ID or label association
      fireEvent.change(container.querySelector('input[name="name"]')!, { target: { value: 'Rice' } });
      fireEvent.change(container.querySelector('input[name="scientific_name"]')!, { target: { value: 'Oryza sativa' } });
      fireEvent.change(container.querySelector('input[name="n_req"]')!, { target: { value: '80' } });

      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(createCropMock).toHaveBeenCalledWith(expect.objectContaining({
          name: 'Rice',
          scientific_name: 'Oryza sativa',
          n_req: 80,
        }));
      });
      expect(mockNavigate).toHaveBeenCalledWith('/agronomy/crops');
    });

    it('populates form for editing existing crop', () => {
      mockUseAgronomy.mockReturnValue({
        crops: mockCrops,
        fetchCrops: vi.fn(),
        updateCrop: vi.fn(),
      });

      const { container } = render(
        <MemoryRouter initialEntries={['/agronomy/crops/1/edit']}>
          <Routes>
            <Route path="/agronomy/crops/:id/edit" element={<CropForm />} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Edit Crop')).toBeInTheDocument();
      // Use querySelector because the input lacks an ID or label association
      expect((container.querySelector('input[name="name"]') as HTMLInputElement).value).toBe('Wheat');
      expect((container.querySelector('input[name="scientific_name"]') as HTMLInputElement).value).toBe('Triticum aestivum');
    });

    it('submits updated crop data', async () => {
      const updateCropMock = vi.fn();
      mockUseAgronomy.mockReturnValue({
        crops: mockCrops,
        fetchCrops: vi.fn(),
        updateCrop: updateCropMock,
      });

      const { container } = render(
        <MemoryRouter initialEntries={['/agronomy/crops/1/edit']}>
          <Routes>
            <Route path="/agronomy/crops/:id/edit" element={<CropForm />} />
          </Routes>
        </MemoryRouter>
      );

      // Use querySelector because the input lacks an ID or label association
      fireEvent.change(container.querySelector('input[name="name"]')!, { target: { value: 'Wheat Updated' } });
      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(updateCropMock).toHaveBeenCalledWith(1, expect.objectContaining({
          name: 'Wheat Updated',
        }));
      });
       expect(mockNavigate).toHaveBeenCalledWith('/agronomy/crops');
    });
  });
});
