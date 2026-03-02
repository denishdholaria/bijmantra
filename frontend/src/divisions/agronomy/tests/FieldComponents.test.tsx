import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import FieldList from '../pages/FieldList';
import FieldDetail from '../pages/FieldDetail';
import FieldForm from '../pages/FieldForm';
import { Field } from '../types';

// Hoist mocks to ensure they are available before imports
const { mockUseAgronomy, mockAgronomyApi, mockNavigate } = vi.hoisted(() => {
  return {
    mockUseAgronomy: {
      fields: [] as Field[],
      loading: false,
      fetchFields: vi.fn(),
      deleteField: vi.fn(),
      createField: vi.fn(),
      updateField: vi.fn(),
    },
    mockAgronomyApi: {
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

describe('Field Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mutable state in mocks
    mockUseAgronomy.fields = [];
    mockUseAgronomy.loading = false;
  });

  describe('FieldList', () => {
    it('renders loading state', () => {
      mockUseAgronomy.loading = true;
      render(
        <MemoryRouter>
          <FieldList />
        </MemoryRouter>
      );
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders empty state', () => {
      render(
        <MemoryRouter>
          <FieldList />
        </MemoryRouter>
      );
      expect(screen.getByText('No fields found.')).toBeInTheDocument();
      expect(mockUseAgronomy.fetchFields).toHaveBeenCalled();
    });

    it('renders list of fields', () => {
      const mockFields: Field[] = [
        { id: 1, name: 'Field 1', area: 10, location_description: 'Loc 1', created_at: '', updated_at: '' },
        { id: 2, name: 'Field 2', area: 20, location_description: 'Loc 2', created_at: '', updated_at: '' },
      ];
      mockUseAgronomy.fields = mockFields;

      render(
        <MemoryRouter>
          <FieldList />
        </MemoryRouter>
      );

      expect(screen.getByText('Field 1')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Loc 1')).toBeInTheDocument();
      expect(screen.getByText('Field 2')).toBeInTheDocument();
    });

    it('calls deleteField when delete button is clicked', () => {
      const mockFields: Field[] = [
        { id: 1, name: 'Field 1', area: 10, location_description: 'Loc 1', created_at: '', updated_at: '' },
      ];
      mockUseAgronomy.fields = mockFields;

      render(
        <MemoryRouter>
          <FieldList />
        </MemoryRouter>
      );

      // Find delete button. It might be better to use aria-label or role if possible.
      // In the component: <button onClick={() => deleteField(field.id)} ...>Delete</button>
      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]);

      expect(mockUseAgronomy.deleteField).toHaveBeenCalledWith(1);
    });
  });

  describe('FieldDetail', () => {
    it('renders loading state initially', async () => {
      // Mock API to return a promise that doesn't resolve immediately
      mockAgronomyApi.getField.mockReturnValue(new Promise(() => {}));

      render(
        <MemoryRouter initialEntries={['/agronomy/fields/1']}>
          <Routes>
            <Route path="/agronomy/fields/:id" element={<FieldDetail />} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders field details', async () => {
      const mockField: Field = {
        id: 1,
        name: 'Detailed Field',
        area: 50,
        location_description: 'Detailed Location',
        created_at: '',
        updated_at: ''
      };
      mockAgronomyApi.getField.mockResolvedValue(mockField);

      render(
        <MemoryRouter initialEntries={['/agronomy/fields/1']}>
          <Routes>
            <Route path="/agronomy/fields/:id" element={<FieldDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Detailed Field')).toBeInTheDocument();
      });
      expect(screen.getByText('ID: 1')).toBeInTheDocument();
      expect(screen.getByText('50 hectares')).toBeInTheDocument();
      expect(screen.getByText('Detailed Location')).toBeInTheDocument();
    });
  });

  describe('FieldForm', () => {
    it('renders create form correctly', () => {
      render(
        <MemoryRouter>
          <FieldForm />
        </MemoryRouter>
      );

      expect(screen.getByText('New Field')).toBeInTheDocument();
      // Using regex for flexible matching of labels
      expect(screen.getByLabelText(/Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Area/i)).toBeInTheDocument();
    });

    it('submits create form with valid data', async () => {
      render(
        <MemoryRouter>
          <FieldForm />
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Name/i), { target: { value: 'New Field' } });
      fireEvent.change(screen.getByLabelText(/Area/i), { target: { value: '15.5' } });
      fireEvent.change(screen.getByLabelText(/Location Description/i), { target: { value: 'New Location' } });

      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(mockUseAgronomy.createField).toHaveBeenCalledWith(expect.objectContaining({
          name: 'New Field',
          area: 15.5,
          location_description: 'New Location',
        }));
      });
      // In FieldForm, navigate is called after submission
      expect(mockNavigate).toHaveBeenCalledWith('/agronomy/fields');
    });

    it('renders edit form with existing data', async () => {
       const mockField: Field = {
        id: 1,
        name: 'Existing Field',
        area: 25,
        location_description: 'Existing Location',
        created_at: '',
        updated_at: ''
      };
      // For edit, the component finds the field from `fields` array in context
      mockUseAgronomy.fields = [mockField];

      render(
        <MemoryRouter initialEntries={['/agronomy/fields/1/edit']}>
           <Routes>
            <Route path="/agronomy/fields/:id/edit" element={<FieldForm />} />
          </Routes>
        </MemoryRouter>
      );

      // Wait for form to populate
      await waitFor(() => {
         expect(screen.getByDisplayValue('Existing Field')).toBeInTheDocument();
      });
      expect(screen.getByDisplayValue('25')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Existing Location')).toBeInTheDocument();
      expect(screen.getByText('Edit Field')).toBeInTheDocument();
    });

    it('submits edit form with updated data', async () => {
      const mockField: Field = {
        id: 1,
        name: 'Existing Field',
        area: 25,
        location_description: 'Existing Location',
        created_at: '',
        updated_at: ''
      };
      mockUseAgronomy.fields = [mockField];

      render(
        <MemoryRouter initialEntries={['/agronomy/fields/1/edit']}>
           <Routes>
            <Route path="/agronomy/fields/:id/edit" element={<FieldForm />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
         expect(screen.getByDisplayValue('Existing Field')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText(/Name/i), { target: { value: 'Updated Field' } });
      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(mockUseAgronomy.updateField).toHaveBeenCalledWith(1, expect.objectContaining({
          name: 'Updated Field',
          area: 25,
        }));
      });
      expect(mockNavigate).toHaveBeenCalledWith('/agronomy/fields');
    });
  });
});
