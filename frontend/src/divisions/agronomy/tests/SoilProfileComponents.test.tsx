import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import SoilProfileList from '../pages/SoilProfileList';
import SoilProfileDetail from '../pages/SoilProfileDetail';
import SoilProfileForm from '../pages/SoilProfileForm';
import { SoilProfile, Field } from '../types';

// Hoist mocks to ensure they are available before imports
const { mockUseAgronomy, mockAgronomyApi, mockNavigate } = vi.hoisted(() => {
  return {
    mockUseAgronomy: {
      soilProfiles: [] as SoilProfile[],
      fields: [] as Field[],
      loading: false,
      fetchSoilProfiles: vi.fn(),
      deleteSoilProfile: vi.fn(),
      createSoilProfile: vi.fn(),
      updateSoilProfile: vi.fn(),
      fetchFields: vi.fn(),
    },
    mockAgronomyApi: {
      getSoilProfile: vi.fn(),
      getField: vi.fn(),
    },
    mockNavigate: vi.fn(),
  };
});

// Mock dependencies
vi.mock('../context/AgronomyContext', () => ({
  useAgronomy: () => mockUseAgronomy,
}));

vi.mock('../api/client', () => ({
  agronomyApi: mockAgronomyApi,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('SoilProfile Components', () => {
  // Clear mocks before each test to ensure isolation
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mutable state in mocks
    mockUseAgronomy.soilProfiles = [];
    mockUseAgronomy.fields = [];
    mockUseAgronomy.loading = false;
  });

  describe('SoilProfileList', () => {
    it('renders loading state', () => {
      mockUseAgronomy.loading = true;
      render(
        <MemoryRouter>
          <SoilProfileList />
        </MemoryRouter>
      );
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders empty state', () => {
      render(
        <MemoryRouter>
          <SoilProfileList />
        </MemoryRouter>
      );
      expect(screen.getByText('No soil profiles found.')).toBeInTheDocument();
      expect(mockUseAgronomy.fetchSoilProfiles).toHaveBeenCalled();
    });

    it('renders list of soil profiles', () => {
      const mockProfiles: SoilProfile[] = [
        {
          id: 1,
          name: 'Profile 1',
          field_id: 101,
          sample_date: '2023-01-01',
          created_at: '',
          updated_at: ''
        },
        {
          id: 2,
          name: 'Profile 2',
          field_id: 102,
          sample_date: '2023-02-01',
          created_at: '',
          updated_at: ''
        },
      ];
      mockUseAgronomy.soilProfiles = mockProfiles;

      render(
        <MemoryRouter>
          <SoilProfileList />
        </MemoryRouter>
      );

      expect(screen.getByText('Profile 1')).toBeInTheDocument();
      expect(screen.getByText('2023-01-01')).toBeInTheDocument();
      expect(screen.getByText('101')).toBeInTheDocument();
      expect(screen.getByText('Profile 2')).toBeInTheDocument();
      expect(screen.getByText('2023-02-01')).toBeInTheDocument();
      expect(screen.getByText('102')).toBeInTheDocument();
    });

    it('calls deleteSoilProfile when delete button is clicked', () => {
      const mockProfiles: SoilProfile[] = [
        {
          id: 1,
          name: 'Profile 1',
          field_id: 101,
          sample_date: '2023-01-01',
          created_at: '',
          updated_at: ''
        },
      ];
      mockUseAgronomy.soilProfiles = mockProfiles;

      render(
        <MemoryRouter>
          <SoilProfileList />
        </MemoryRouter>
      );

      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]);

      expect(mockUseAgronomy.deleteSoilProfile).toHaveBeenCalledWith(1);
    });
  });

  describe('SoilProfileDetail', () => {
    it('renders loading state initially', async () => {
      mockAgronomyApi.getSoilProfile.mockReturnValue(new Promise(() => {}));

      render(
        <MemoryRouter initialEntries={['/agronomy/soil-profiles/1']}>
          <Routes>
            <Route path="/agronomy/soil-profiles/:id" element={<SoilProfileDetail />} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders soil profile details', async () => {
      const mockProfile: SoilProfile = {
        id: 1,
        name: 'Detailed Profile',
        field_id: 101,
        sample_date: '2023-03-01',
        description: 'Test Description',
        nitrogen: 10,
        phosphorus: 20,
        potassium: 30,
        ph: 6.5,
        organic_matter: 2.5,
        created_at: '',
        updated_at: ''
      };

      const mockField: Field = {
          id: 101,
          name: 'Test Field',
          area: 50,
          created_at: '',
          updated_at: ''
      };

      mockAgronomyApi.getSoilProfile.mockResolvedValue(mockProfile);
      mockAgronomyApi.getField.mockResolvedValue(mockField);

      render(
        <MemoryRouter initialEntries={['/agronomy/soil-profiles/1']}>
          <Routes>
            <Route path="/agronomy/soil-profiles/:id" element={<SoilProfileDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Detailed Profile')).toBeInTheDocument();
      });
      expect(screen.getByText('ID: 1 | Sample Date: 2023-03-01')).toBeInTheDocument();
      expect(screen.getByText('Test Field')).toBeInTheDocument();
      expect(screen.getByText('Test Description')).toBeInTheDocument();

      // Nutrients
      expect(screen.getByText('10')).toBeInTheDocument(); // Nitrogen
      expect(screen.getByText('20')).toBeInTheDocument(); // Phosphorus
      expect(screen.getByText('30')).toBeInTheDocument(); // Potassium

      // Properties
      expect(screen.getByText('6.5')).toBeInTheDocument(); // pH
      expect(screen.getByText('2.5')).toBeInTheDocument(); // Organic Matter
    });
  });

  describe('SoilProfileForm', () => {
    const mockFields: Field[] = [
        { id: 101, name: 'Field A', area: 10, created_at: '', updated_at: '' },
        { id: 102, name: 'Field B', area: 20, created_at: '', updated_at: '' }
    ];

    beforeEach(() => {
        mockUseAgronomy.fields = mockFields;
    });

    it('renders create form correctly', async () => {
      render(
        <MemoryRouter>
          <SoilProfileForm />
        </MemoryRouter>
      );

      expect(screen.getByText('New Soil Profile')).toBeInTheDocument();
      expect(screen.getByLabelText(/Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Field/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Sample Date/i)).toBeInTheDocument();

      // Check for select options
      // Wait for fetchFields to be called? It is called in useEffect.
      expect(mockUseAgronomy.fetchFields).toHaveBeenCalled();

      // Select options might not be immediately available if fetchFields is async in real implementation,
      // but here we set mockUseAgronomy.fields directly.
      expect(screen.getByText('Field A')).toBeInTheDocument();
      expect(screen.getByText('Field B')).toBeInTheDocument();
    });

    it('submits create form with valid data', async () => {
      render(
        <MemoryRouter>
          <SoilProfileForm />
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Name/i), { target: { value: 'New Profile' } });
      fireEvent.change(screen.getByLabelText(/Field/i), { target: { value: '101' } });
      fireEvent.change(screen.getByLabelText(/Sample Date/i), { target: { value: '2023-04-01' } });

      // Numeric fields
      fireEvent.change(screen.getByLabelText(/Nitrogen \(ppm\)/i), { target: { value: '15' } });
      fireEvent.change(screen.getByLabelText(/Phosphorus \(ppm\)/i), { target: { value: '25' } });
      fireEvent.change(screen.getByLabelText(/Potassium \(ppm\)/i), { target: { value: '35' } });
      fireEvent.change(screen.getByLabelText(/^pH$/i), { target: { value: '7.0' } });
      fireEvent.change(screen.getByLabelText(/Organic Matter/i), { target: { value: '3.0' } });

      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(mockUseAgronomy.createSoilProfile).toHaveBeenCalledWith(expect.objectContaining({
          name: 'New Profile',
          field_id: 101,
          sample_date: '2023-04-01',
          nitrogen: 15,
          phosphorus: 25,
          potassium: 35,
          ph: 7.0,
          organic_matter: 3.0
        }));
      });
      expect(mockNavigate).toHaveBeenCalledWith('/agronomy/soil-profiles');
    });

    it('renders edit form with existing data', async () => {
      const mockProfile: SoilProfile = {
        id: 1,
        name: 'Existing Profile',
        field_id: 101,
        sample_date: '2023-05-01',
        description: 'Edit Description',
        nitrogen: 12,
        phosphorus: 22,
        potassium: 32,
        ph: 6.8,
        organic_matter: 2.8,
        created_at: '',
        updated_at: ''
      };
      mockUseAgronomy.soilProfiles = [mockProfile];

      render(
        <MemoryRouter initialEntries={['/agronomy/soil-profiles/1/edit']}>
           <Routes>
            <Route path="/agronomy/soil-profiles/:id/edit" element={<SoilProfileForm />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
         expect(screen.getByDisplayValue('Existing Profile')).toBeInTheDocument();
      });

      expect(screen.getByText('Edit Soil Profile')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2023-05-01')).toBeInTheDocument();
      expect(screen.getByDisplayValue('12')).toBeInTheDocument();
      expect(screen.getByDisplayValue('22')).toBeInTheDocument();
      expect(screen.getByDisplayValue('32')).toBeInTheDocument();
      expect(screen.getByDisplayValue('6.8')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2.8')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Edit Description')).toBeInTheDocument();
      // Verify field is selected
      expect(screen.getByLabelText(/Field/i)).toHaveValue('101');
    });

    it('submits edit form with updated data', async () => {
      const mockProfile: SoilProfile = {
        id: 1,
        name: 'Existing Profile',
        field_id: 101,
        sample_date: '2023-05-01',
        created_at: '',
        updated_at: ''
      };
      mockUseAgronomy.soilProfiles = [mockProfile];

      render(
        <MemoryRouter initialEntries={['/agronomy/soil-profiles/1/edit']}>
           <Routes>
            <Route path="/agronomy/soil-profiles/:id/edit" element={<SoilProfileForm />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
         expect(screen.getByDisplayValue('Existing Profile')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText(/Name/i), { target: { value: 'Updated Profile' } });
      fireEvent.change(screen.getByLabelText(/Nitrogen/i), { target: { value: '50' } });

      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(mockUseAgronomy.updateSoilProfile).toHaveBeenCalledWith(1, expect.objectContaining({
          name: 'Updated Profile',
          nitrogen: 50
        }));
      });
      expect(mockNavigate).toHaveBeenCalledWith('/agronomy/soil-profiles');
    });
  });
});
