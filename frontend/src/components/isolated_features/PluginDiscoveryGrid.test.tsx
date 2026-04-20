import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import PluginDiscoveryGrid from './PluginDiscoveryGrid';

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  Search: () => <div data-testid="icon-search" />,
  Filter: () => <div data-testid="icon-filter" />,
  Cpu: () => <div data-testid="icon-cpu" />,
  Dna: () => <div data-testid="icon-dna" />,
  Sprout: () => <div data-testid="icon-sprout" />,
  Globe: () => <div data-testid="icon-globe" />,
  Database: () => <div data-testid="icon-database" />,
  ShieldCheck: () => <div data-testid="icon-shield" />,
  Download: () => <div data-testid="icon-download" />,
  Check: () => <div data-testid="icon-check" />,
  Plus: () => <div data-testid="icon-plus" />,
  Trash2: () => <div data-testid="icon-trash" />,
  ExternalLink: () => <div data-testid="icon-external" />,
  Star: () => <div data-testid="icon-star" />,
  Clock: () => <div data-testid="icon-clock" />,
  LayoutGrid: () => <div data-testid="icon-grid" />,
  Zap: () => <div data-testid="icon-zap" />,
}));

// Mock Shadcn components that might use Portals or complex logic
vi.mock('@/components/ui/select', () => ({
  Select: ({ children, onValueChange, value }: { children: React.ReactNode, onValueChange: (v: string) => void, value: string }) => (
    <select value={value} onChange={(e) => onValueChange(e.target.value)}>
      {children}
    </select>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectValue: ({ placeholder }: { placeholder: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectItem: ({ children, value }: { children: React.ReactNode, value: string }) => <option value={value}>{children}</option>,
}));

describe('PluginDiscoveryGrid', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the component with header and initial plugins', () => {
    render(<PluginDiscoveryGrid />);

    expect(screen.getByText('Plugin Discovery')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search plugins/i)).toBeInTheDocument();

    // Check for some mock plugins
    expect(screen.getByText('REEVU Genomic Reasoner')).toBeInTheDocument();
    expect(screen.getByText('BrAPI v2.1 Adapter')).toBeInTheDocument();
    expect(screen.getByText('Prakruti Weather Sync')).toBeInTheDocument();
  });

  it('filters plugins based on search query', () => {
    render(<PluginDiscoveryGrid />);

    const searchInput = screen.getByPlaceholderText(/Search plugins/i);

    fireEvent.change(searchInput, { target: { value: 'Genomic' } });

    expect(screen.getByText('REEVU Genomic Reasoner')).toBeInTheDocument();
    expect(screen.queryByText('BrAPI v2.1 Adapter')).not.toBeInTheDocument();
  });

  it('filters plugins based on category', () => {
    render(<PluginDiscoveryGrid />);

    const categorySelect = screen.getByDisplayValue('All Categories');

    fireEvent.change(categorySelect, { target: { value: 'AI' } });

    expect(screen.getByText('REEVU Genomic Reasoner')).toBeInTheDocument();
    expect(screen.getByText('REEVU Trial Predictor')).toBeInTheDocument();
    expect(screen.queryByText('BrAPI v2.1 Adapter')).not.toBeInTheDocument();
  });

  it('toggles installation status when button is clicked', () => {
    render(<PluginDiscoveryGrid />);

    // "Prakruti Weather Sync" is initially 'available'
    const weatherPlugin = screen.getByText('Prakruti Weather Sync').closest('.group');
    expect(weatherPlugin).toBeInTheDocument();

    const installButton = screen.getAllByRole('button', { name: /Install/i }).find(btn =>
      btn.closest('.group')?.contains(screen.getByText('Prakruti Weather Sync'))
    );

    expect(installButton).toBeInTheDocument();
    fireEvent.click(installButton!);

    // Now it should show "Uninstall"
    const uninstallButton = screen.getAllByRole('button', { name: /Uninstall/i }).find(btn =>
      btn.closest('.group')?.contains(screen.getByText('Prakruti Weather Sync'))
    );
    expect(uninstallButton).toBeInTheDocument();
  });

  it('shows empty state when no plugins match search', () => {
    render(<PluginDiscoveryGrid />);

    const searchInput = screen.getByPlaceholderText(/Search plugins/i);
    fireEvent.change(searchInput, { target: { value: 'NonExistentPlugin' } });

    expect(screen.getByText('No plugins found')).toBeInTheDocument();
  });
});
