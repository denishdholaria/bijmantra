import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NutrientTestList } from '../components/NutrientTestList';
import { SoilService } from '../services';
import { BrowserRouter } from 'react-router-dom';

// Mock SoilService
vi.mock('../services', () => ({
  SoilService: {
    getNutrientTests: vi.fn(),
    deleteNutrientTest: vi.fn(),
  },
}));

describe('NutrientTestList', () => {
  it('renders loading state initially', () => {
    // Mock implementation to return a promise that doesn't resolve immediately
    (SoilService.getNutrientTests as any).mockImplementation(() => new Promise(() => {}));

    render(<NutrientTestList />);
    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('renders list of tests after loading', async () => {
    const mockTests = [
      {
        id: 1,
        field_id: 101,
        sample_date: '2023-10-01',
        nitrogen: 10.5,
        phosphorus: 5.2,
        potassium: 8.1,
        ph: 6.5
      }
    ];

    (SoilService.getNutrientTests as any).mockResolvedValue(mockTests);

    render(<NutrientTestList />);

    // Wait for loading to finish and check for data
    expect(await screen.findByText('Nutrient Tests')).toBeDefined();
    expect(await screen.findByText('101')).toBeDefined();
    expect(await screen.findByText('10.5')).toBeDefined();
  });
});
