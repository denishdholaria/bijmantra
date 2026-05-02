/**
 * Tests for InventoryPanel component
 * @vitest-environment jsdom
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InventoryPanel } from './InventoryPanel';
import { useInventory } from './useInventory';

vi.mock('./useInventory', () => ({
  useInventory: vi.fn(),
}));

describe('InventoryPanel', () => {
  it('renders loading state', () => {
    (useInventory as any).mockReturnValue({
      items: [],
      loading: true,
      error: null,
      filter: {},
      updateFilter: vi.fn(),
      reload: vi.fn(),
    });

    render(<InventoryPanel />);
    expect(screen.getByText('Loading inventory...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    (useInventory as any).mockReturnValue({
      items: [],
      loading: false,
      error: 'Failed to load',
      filter: {},
      updateFilter: vi.fn(),
      reload: vi.fn(),
    });

    render(<InventoryPanel />);
    expect(screen.getByText('Error: Failed to load')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    (useInventory as any).mockReturnValue({
      items: [],
      loading: false,
      error: null,
      filter: {},
      updateFilter: vi.fn(),
      reload: vi.fn(),
    });

    render(<InventoryPanel />);
    expect(screen.getByText('No inventory items found')).toBeInTheDocument();
  });
});
