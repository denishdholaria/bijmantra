import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { PedigreeTree } from './PedigreeTree';
import type { PedigreeNode } from './types';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

function buildPedigree(generation = 0, maxDepth = 4, prefix = 'Root'): PedigreeNode {
  const node: PedigreeNode = {
    id: `${prefix}-${generation + 1}`,
    name: `${prefix} Generation ${generation + 1}`,
    generation,
    type: generation === 0 ? 'progeny' : 'ancestor',
    sire: null,
    dam: null,
  };

  if (generation < maxDepth) {
    node.sire = buildPedigree(generation + 1, maxDepth, `${prefix} Sire`);
    node.dam = buildPedigree(generation + 1, maxDepth, `${prefix} Dam`);
  }

  return node;
}

describe('PedigreeTree', () => {
  it('renders only the selected germplasm at 1 generation depth', () => {
    render(<PedigreeTree tree={buildPedigree()} maxGenerations={1} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('Root Generation 1')).toBeInTheDocument();
    expect(screen.queryByText('Root Sire Generation 2')).not.toBeInTheDocument();
    expect(screen.queryByText('Unknown sire')).not.toBeInTheDocument();
    expect(screen.getByText('Rendering up to 1 generations of ancestry.')).toBeInTheDocument();
  });

  it('caps recursive rendering at 3 generations and preserves missing-parent placeholders', () => {
    const tree = buildPedigree();
    if (tree.dam) {
      tree.dam.sire = null;
    }

    render(<PedigreeTree tree={tree} maxGenerations={3} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('Root Generation 1')).toBeInTheDocument();
    expect(screen.getByText('Root Sire Generation 2')).toBeInTheDocument();
    expect(screen.getByText('Root Sire Sire Generation 3')).toBeInTheDocument();
    expect(screen.queryByText('Root Sire Sire Sire Generation 4')).not.toBeInTheDocument();
    expect(screen.getByText('Unknown sire')).toBeInTheDocument();
  });

  it('renders ancestors through 5 generations', () => {
    render(<PedigreeTree tree={buildPedigree()} maxGenerations={5} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('Root Generation 1')).toBeInTheDocument();
    expect(screen.getByText('Root Sire Sire Sire Sire Generation 5')).toBeInTheDocument();
    expect(screen.getByText('Root Dam Dam Dam Dam Generation 5')).toBeInTheDocument();
  });
});
