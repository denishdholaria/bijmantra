import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { DragAndDropAnalyticsGrid } from './DragAndDropAnalyticsGrid';
import React from 'react';

// Mock dnd-kit components as they might need a specific environment
vi.mock('@dnd-kit/core', async () => {
  const actual = await vi.importActual('@dnd-kit/core');
  return {
    ...actual as any,
    DndContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  };
});

vi.mock('@dnd-kit/sortable', async () => {
  const actual = await vi.importActual('@dnd-kit/sortable');
  return {
    ...actual as any,
    SortableContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    useSortable: () => ({
      attributes: {},
      listeners: {},
      setNodeRef: () => {},
      transform: null,
      transition: null,
      isDragging: false,
    }),
  };
});

describe('DragAndDropAnalyticsGrid', () => {
  it('renders the dashboard title', () => {
    render(<DragAndDropAnalyticsGrid />);
    expect(screen.getByText(/REEVU Analytics Dashboard/i)).toBeInTheDocument();
  });

  it('renders all default widgets', () => {
    render(<DragAndDropAnalyticsGrid />);
    expect(screen.getByText('Total Yield')).toBeInTheDocument();
    expect(screen.getByText('Soil Moisture')).toBeInTheDocument();
    expect(screen.getByText('Active Trials')).toBeInTheDocument();
    expect(screen.getByText('Pest Level')).toBeInTheDocument();
  });

  it('renders widget values correctly', () => {
    render(<DragAndDropAnalyticsGrid />);
    expect(screen.getByText('1,250.5')).toBeInTheDocument();
    expect(screen.getByText('24.2')).toBeInTheDocument();
    expect(screen.getByText('14')).toBeInTheDocument();
    expect(screen.getByText('Low')).toBeInTheDocument();
  });
});
