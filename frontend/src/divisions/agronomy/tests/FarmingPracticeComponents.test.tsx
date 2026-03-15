import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import FarmingPracticeList from '../pages/FarmingPracticeList';
import FarmingPracticeDetail from '../pages/FarmingPracticeDetail';
import FarmingPracticeForm from '../pages/FarmingPracticeForm';
import { agronomyApi } from '../api/client';

// Mock the API client
vi.mock('../api/client', () => ({
  agronomyApi: {
    getFarmingPractice: vi.fn(),
    getField: vi.fn(),
    getSeason: vi.fn(),
  }
}));

// Mock the context hook
const mockUseAgronomy = vi.fn();
vi.mock('../context/AgronomyContext', () => ({
  useAgronomy: () => mockUseAgronomy()
}));

// Mock data
const mockPractices = [
  {
    id: 1,
    name: 'Practice 1',
    practice_type: 'Irrigation',
    date: '2023-01-01',
    field_id: 101,
    description: 'First practice',
    season_id: 201,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  },
  {
    id: 2,
    name: 'Practice 2',
    practice_type: 'Fertilization',
    date: '2023-02-01',
    field_id: 102,
    description: 'Second practice',
    created_at: '2023-02-01T00:00:00Z',
    updated_at: '2023-02-01T00:00:00Z'
  }
];

const mockFields = [
  { id: 101, name: 'Field 1', area: 10, created_at: '', updated_at: '' },
  { id: 102, name: 'Field 2', area: 20, created_at: '', updated_at: '' }
];

const mockSeasons = [
  { id: 201, name: 'Season 1', start_date: '2023-01-01', end_date: '2023-06-01', field_id: 101, crop_id: 1, created_at: '', updated_at: '' }
];

describe('FarmingPractice Components', () => {
  const defaultContext = {
    farmingPractices: mockPractices,
    fetchFarmingPractices: vi.fn(),
    loading: false,
    deleteFarmingPractice: vi.fn(),
    createFarmingPractice: vi.fn(),
    updateFarmingPractice: vi.fn(),
    fetchFields: vi.fn(),
    fields: mockFields,
    fetchSeasons: vi.fn(),
    seasons: mockSeasons,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAgronomy.mockReturnValue(defaultContext);
  });

  describe('FarmingPracticeList', () => {
    it('renders list of practices', () => {
      render(
        <MemoryRouter>
          <FarmingPracticeList />
        </MemoryRouter>
      );

      expect(screen.getByText('Farming Practices')).toBeInTheDocument();
      expect(screen.getByText('Practice 1')).toBeInTheDocument();
      expect(screen.getByText('Irrigation')).toBeInTheDocument();
      expect(screen.getByText('Practice 2')).toBeInTheDocument();
      expect(screen.getByText('Fertilization')).toBeInTheDocument();
    });

    it('renders loading state', () => {
      mockUseAgronomy.mockReturnValue({
        ...defaultContext,
        loading: true,
        farmingPractices: []
      });

      render(
        <MemoryRouter>
          <FarmingPracticeList />
        </MemoryRouter>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders empty state', () => {
      mockUseAgronomy.mockReturnValue({
        ...defaultContext,
        farmingPractices: []
      });

      render(
        <MemoryRouter>
          <FarmingPracticeList />
        </MemoryRouter>
      );

      expect(screen.getByText('No farming practices found.')).toBeInTheDocument();
    });

    it('calls deleteFarmingPractice when delete button is clicked', () => {
      render(
        <MemoryRouter>
          <FarmingPracticeList />
        </MemoryRouter>
      );

      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]);

      expect(defaultContext.deleteFarmingPractice).toHaveBeenCalledWith(1);
    });
  });

  describe('FarmingPracticeDetail', () => {
    it('renders practice details', async () => {
      vi.mocked(agronomyApi.getFarmingPractice).mockResolvedValue(mockPractices[0]);
      vi.mocked(agronomyApi.getField).mockResolvedValue(mockFields[0]);
      vi.mocked(agronomyApi.getSeason).mockResolvedValue(mockSeasons[0]);

      render(
        <MemoryRouter initialEntries={['/agronomy/practices/1']}>
          <Routes>
            <Route path="/agronomy/practices/:id" element={<FarmingPracticeDetail />} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Practice 1')).toBeInTheDocument();
      });

      expect(screen.getByText('Irrigation')).toBeInTheDocument();
      expect(screen.getByText('First practice')).toBeInTheDocument();
      expect(screen.getByText('Field 1')).toBeInTheDocument();
      expect(screen.getByText('Season 1')).toBeInTheDocument();
    });
  });

  describe('FarmingPracticeForm', () => {
    it('renders create form', () => {
      render(
        <MemoryRouter>
          <FarmingPracticeForm />
        </MemoryRouter>
      );

      expect(screen.getByText('Record Farming Practice')).toBeInTheDocument();
      // Using getByText for labels since input association is not explicit in the original component
      expect(screen.getByText('Practice Name')).toBeInTheDocument();
      expect(screen.getByText('Practice Type')).toBeInTheDocument();
    });

    it('submits new practice', async () => {
      render(
        <MemoryRouter>
          <FarmingPracticeForm />
        </MemoryRouter>
      );

      // Using getByPlaceholderText or other strategies since label association is missing
      fireEvent.change(screen.getByPlaceholderText('e.g., Pre-sowing irrigation'), { target: { value: 'New Practice' } });

      // For select/inputs without unique placeholders, we can find by role or test ID if available,
      // or traverse from the label. Here we'll try locating by name attribute if testing-library supports it (it doesn't directly).
      // Instead, we can select by index or other attributes, or use container.querySelector.
      // Given the DOM structure, inputs are siblings of labels.

      const typeSelect = screen.getAllByRole('combobox')[0]; // Practice Type
      fireEvent.change(typeSelect, { target: { value: 'Sowing' } });

      // Date input (type="date") might not have a placeholder.
      // We can use container.querySelector to be precise.
      const dateInput = screen.getAllByDisplayValue('')[0]; // This is risky if there are multiple empty inputs
      // Better approach: find label then find next input
      // However, for this fix, let's use the container querySelector which is robust for this structure
      // But we don't have container easily available without destructuring render.
      // Let's rely on the order of inputs/selects in the form.

      // Re-rendering to get container
    });
  });

  // Re-implementing tests with container access for robust selection without ID/htmlFor
  describe('FarmingPracticeForm Interactions', () => {
     it('submits new practice', async () => {
      const { container } = render(
        <MemoryRouter>
          <FarmingPracticeForm />
        </MemoryRouter>
      );

      // Select inputs by name attribute using querySelector
      const nameInput = container.querySelector('input[name="name"]');
      const typeSelect = container.querySelector('select[name="practice_type"]');
      const dateInput = container.querySelector('input[name="date"]');
      const fieldSelect = container.querySelector('select[name="field_id"]');

      if (!nameInput || !typeSelect || !dateInput || !fieldSelect) {
          throw new Error('Form elements not found');
      }

      fireEvent.change(nameInput, { target: { value: 'New Practice' } });
      fireEvent.change(typeSelect, { target: { value: 'Sowing' } });
      fireEvent.change(dateInput, { target: { value: '2023-03-01' } });
      fireEvent.change(fieldSelect, { target: { value: '101' } });

      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(defaultContext.createFarmingPractice).toHaveBeenCalledWith(expect.objectContaining({
            name: 'New Practice',
            practice_type: 'Sowing',
            date: '2023-03-01',
            field_id: 101
        }));
      });
    });

    it('renders edit form and submits update', async () => {
      const { container } = render(
        <MemoryRouter initialEntries={['/agronomy/practices/1/edit']}>
          <Routes>
            <Route path="/agronomy/practices/:id/edit" element={<FarmingPracticeForm />} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Edit Farming Practice')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Practice 1')).toBeInTheDocument();
      });

      const nameInput = container.querySelector('input[name="name"]');
       if (!nameInput) {
          throw new Error('Name input not found');
      }

      fireEvent.change(nameInput, { target: { value: 'Updated Practice' } });

      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(defaultContext.updateFarmingPractice).toHaveBeenCalledWith(1, expect.objectContaining({
            name: 'Updated Practice'
        }));
      });
    });
  });
});
