/**
 * Tests for CrossManagementPanel component
 * @vitest-environment jsdom
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CrossManagementPanel } from './CrossManagementPanel';
import { useCrossManagement } from './useCrossManagement';

vi.mock('./useCrossManagement', () => ({
  useCrossManagement: vi.fn(),
}));

describe('CrossManagementPanel', () => {
  it('renders loading state', () => {
    (useCrossManagement as any).mockReturnValue({
      crosses: [],
      loading: true,
      error: null,
      filter: {},
      updateFilter: vi.fn(),
      reload: vi.fn(),
    });

    render(<CrossManagementPanel />);
    expect(screen.getByText('Loading crosses...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    (useCrossManagement as any).mockReturnValue({
      crosses: [],
      loading: false,
      error: 'Failed to load',
      filter: {},
      updateFilter: vi.fn(),
      reload: vi.fn(),
    });

    render(<CrossManagementPanel />);
    expect(screen.getByText('Error: Failed to load')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    (useCrossManagement as any).mockReturnValue({
      crosses: [],
      loading: false,
      error: null,
      filter: {},
      updateFilter: vi.fn(),
      reload: vi.fn(),
    });

    render(<CrossManagementPanel />);
    expect(screen.getByText('No crosses found')).toBeInTheDocument();
  });
});
