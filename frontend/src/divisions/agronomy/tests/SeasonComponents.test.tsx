import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import SeasonList from '../pages/SeasonList';
import SeasonDetail from '../pages/SeasonDetail';
import SeasonForm from '../pages/SeasonForm';
import { useAgronomy } from '../context/AgronomyContext';
import { agronomyApi } from '../api/client';
import { useParams, useNavigate } from 'react-router-dom';

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual as any,
    Link: ({ children, to }: { children: React.ReactNode, to: string }) => <a href={to}>{children}</a>,
    useNavigate: vi.fn(),
    useParams: vi.fn(),
  };
});

// Mock AgronomyContext
vi.mock('../context/AgronomyContext', () => ({
  useAgronomy: vi.fn(),
}));

// Mock agronomyApi
vi.mock('../api/client', () => ({
  agronomyApi: {
    getSeason: vi.fn(),
    getField: vi.fn(),
    getCrop: vi.fn(),
  },
}));

describe('Season Components', () => {
  const mockSeasons = [
    {
      id: 1,
      name: 'Summer 2024',
      start_date: '2024-06-01',
      end_date: '2024-08-31',
      field_id: 101,
      crop_id: 201,
    },
  ];

  const mockFields = [
    { id: 101, name: 'North Field', area: 50 },
  ];

  const mockCrops = [
    { id: 201, name: 'Corn' },
  ];

  const mockContextValue = {
    seasons: mockSeasons,
    fields: mockFields,
    crops: mockCrops,
    loading: false,
    fetchSeasons: vi.fn(),
    fetchFields: vi.fn(),
    fetchCrops: vi.fn(),
    createSeason: vi.fn(),
    updateSeason: vi.fn(),
    deleteSeason: vi.fn(),
  };

  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAgronomy as any).mockReturnValue(mockContextValue);
    (useParams as any).mockReturnValue({ id: '1' });
    (useNavigate as any).mockReturnValue(mockNavigate);
  });

  describe('SeasonList', () => {
    it('renders loading state', () => {
      (useAgronomy as any).mockReturnValue({
        ...mockContextValue,
        seasons: [],
        loading: true,
      });

      render(<SeasonList />);
      expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
    });

    it('renders empty state', () => {
      (useAgronomy as any).mockReturnValue({
        ...mockContextValue,
        seasons: [],
        loading: false,
      });

      render(<SeasonList />);
      expect(screen.getByText(/No seasons found/i)).toBeInTheDocument();
    });

    it('renders list of seasons', () => {
      render(<SeasonList />);
      expect(screen.getByText('Summer 2024')).toBeInTheDocument();
      expect(screen.getByText(/2024-06-01 - 2024-08-31/i)).toBeInTheDocument();
      expect(screen.getByText(/Field: 101 \/ Crop: 201/i)).toBeInTheDocument();
    });

    it('calls deleteSeason when delete button is clicked', () => {
      render(<SeasonList />);
      const deleteButton = screen.getByText('Delete');
      fireEvent.click(deleteButton);
      expect(mockContextValue.deleteSeason).toHaveBeenCalledWith(1);
    });
  });

  describe('SeasonDetail', () => {
    it('renders season details and fetches associated data', async () => {
      (agronomyApi.getSeason as any).mockResolvedValue(mockSeasons[0]);
      (agronomyApi.getField as any).mockResolvedValue(mockFields[0]);
      (agronomyApi.getCrop as any).mockResolvedValue(mockCrops[0]);

      render(<SeasonDetail />);

      expect(await screen.findByText('Summer 2024')).toBeInTheDocument();
      expect(screen.getByText('2024-06-01')).toBeInTheDocument();
      expect(screen.getByText('2024-08-31')).toBeInTheDocument();

      // Check for field and crop names
      expect(await screen.findByText('North Field')).toBeInTheDocument();
      expect(await screen.findByText('Corn')).toBeInTheDocument();

      expect(agronomyApi.getSeason).toHaveBeenCalledWith(1);
      expect(agronomyApi.getField).toHaveBeenCalledWith(101);
      expect(agronomyApi.getCrop).toHaveBeenCalledWith(201);
    });

    it('renders loading state when season is not yet loaded', () => {
      (agronomyApi.getSeason as any).mockReturnValue(new Promise(() => {})); // Never resolves
      render(<SeasonDetail />);
      expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
    });
  });

  describe('SeasonForm', () => {
    it('renders for "New Season"', () => {
      (useParams as any).mockReturnValue({ id: undefined });
      render(<SeasonForm />);

      expect(screen.getByText('New Season')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/e.g., Kharif 2026/i)).toHaveValue('');
    });

    it('renders for "Edit Season" with pre-filled data', () => {
      (useParams as any).mockReturnValue({ id: '1' });
      render(<SeasonForm />);

      expect(screen.getByText('Edit Season')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Summer 2024')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2024-06-01')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2024-08-31')).toBeInTheDocument();
    });

    it('calls createSeason on form submission for new season', async () => {
      (useParams as any).mockReturnValue({ id: undefined });
      render(<SeasonForm />);

      fireEvent.change(screen.getByLabelText(/Season Name/i), { target: { value: 'Winter 2024' } });
      fireEvent.change(screen.getByLabelText(/Start Date/i), { target: { value: '2024-11-01' } });
      fireEvent.change(screen.getByLabelText(/End Date/i), { target: { value: '2025-01-31' } });
      fireEvent.change(screen.getByLabelText(/Field/i), { target: { value: '101' } });
      fireEvent.change(screen.getByLabelText(/Crop/i), { target: { value: '201' } });

      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(mockContextValue.createSeason).toHaveBeenCalledWith({
          name: 'Winter 2024',
          start_date: '2024-11-01',
          end_date: '2025-01-31',
          field_id: 101,
          crop_id: 201,
        });
      });
      expect(mockNavigate).toHaveBeenCalledWith('/agronomy/seasons');
    });

    it('calls updateSeason on form submission for editing', async () => {
      (useParams as any).mockReturnValue({ id: '1' });
      render(<SeasonForm />);

      fireEvent.change(screen.getByLabelText(/Season Name/i), { target: { value: 'Updated Season' } });
      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(mockContextValue.updateSeason).toHaveBeenCalledWith(1, expect.objectContaining({
          name: 'Updated Season',
        }));
      });
      expect(mockNavigate).toHaveBeenCalledWith('/agronomy/seasons');
    });
  });
});
