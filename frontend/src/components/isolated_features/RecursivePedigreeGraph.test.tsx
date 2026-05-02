import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RecursivePedigreeGraph } from './RecursivePedigreeGraph';
import { PedigreeNode } from '@/lib/api-client';

const mockPedigreeData: PedigreeNode = {
  id: 'root',
  name: 'Root Germplasm',
  generation: 0,
  sire: {
    id: 'sire1',
    name: 'Sire 1',
    generation: 1,
    sire: {
      id: 'sire1_sire',
      name: 'Sire 1 Sire',
      generation: 2,
    },
    dam: {
      id: 'sire1_dam',
      name: 'Sire 1 Dam',
      generation: 2,
    },
  },
  dam: {
    id: 'dam1',
    name: 'Dam 1',
    generation: 1,
  },
};

describe('RecursivePedigreeGraph', () => {
  it('renders "No pedigree data available" when data is null', () => {
    render(<RecursivePedigreeGraph data={null} />);
    expect(screen.getByText(/no pedigree data available/i)).toBeInTheDocument();
  });

  it('renders the SVG container when data is provided', () => {
    const { container } = render(<RecursivePedigreeGraph data={mockPedigreeData} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('renders nodes with correct names', () => {
    const { container } = render(<RecursivePedigreeGraph data={mockPedigreeData} />);
    // D3 renders text elements for node names
    expect(container.textContent).toContain('Root Germplasm');
    expect(container.textContent).toContain('Sire 1');
    expect(container.textContent).toContain('Dam 1');
    expect(container.textContent).toContain('Sire 1 Sire');
  });

  it('provides zoom and reset controls', () => {
    render(<RecursivePedigreeGraph data={mockPedigreeData} />);
    expect(screen.getByLabelText(/zoom in/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/zoom out/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/reset view/i)).toBeInTheDocument();
  });
});
