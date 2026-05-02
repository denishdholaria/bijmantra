import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import BiometricImageAnnotator, { BoundingBox } from './BiometricImageAnnotator';
import '@testing-library/jest-dom';

// Mock the Tooltip components since they often cause issues in JSDOM
vi.mock('@/components/ui/tooltip', () => ({
  Tooltip: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TooltipTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TooltipContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock Radix Select
vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onValueChange }: { children: React.ReactNode, value: string, onValueChange: (v: string) => void }) => (
    <select value={value} onChange={(e) => onValueChange(e.target.value)}>{children}</select>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectValue: ({ placeholder }: { placeholder: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectItem: ({ children, value }: { children: React.ReactNode, value: string }) => <option value={value}>{children}</option>,
}));

describe('BiometricImageAnnotator', () => {
  const mockImageUrl = 'https://example.com/biometric.jpg';
  const mockLabels = ['Eye', 'Nose', 'Mouth'];
  const mockInitialBoxes: BoundingBox[] = [
    { id: '1', x: 0.1, y: 0.1, width: 0.2, height: 0.2, label: 'Eye', color: '#ef4444' }
  ];

  beforeEach(() => {
    // Mock Image object
    global.Image = class {
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      src: string = '';
      width: number = 800;
      height: number = 600;
      crossOrigin: string | null = null;
      constructor() {
        setTimeout(() => {
          if (this.onload) this.onload();
        }, 0);
      }
    } as unknown as typeof Image;

    // Mock HTMLCanvasElement.getContext
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
      clearRect: vi.fn(),
      drawImage: vi.fn(),
      strokeRect: vi.fn(),
      fillRect: vi.fn(),
      fillText: vi.fn(),
      measureText: vi.fn().mockReturnValue({ width: 50 }),
      setLineDash: vi.fn(),
    }) as unknown as any;

    // Mock getBoundingClientRect for canvas
    HTMLCanvasElement.prototype.getBoundingClientRect = vi.fn().mockReturnValue({
      left: 0,
      top: 0,
      width: 800,
      height: 600,
      bottom: 600,
      right: 800,
      x: 0,
      y: 0,
      toJSON: () => {},
    });
  });

  it('renders the annotator with correct initial state', async () => {
    render(
      <BiometricImageAnnotator
        imageUrl={mockImageUrl}
        labels={mockLabels}
        initialBoxes={mockInitialBoxes}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/1 Objects/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/Draw Bounding Box/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Select Tool/i)).toBeInTheDocument();
    expect(screen.getByText(/Save Labels/i)).toBeInTheDocument();
  });

  it('switches between tools', async () => {
    render(<BiometricImageAnnotator imageUrl={mockImageUrl} />);

    const drawBtn = screen.getByLabelText(/Draw Bounding Box/i);
    const selectBtn = screen.getByLabelText(/Select Tool/i);

    fireEvent.click(selectBtn);
    expect(screen.getByText(/Mode: Navigation/i)).toBeInTheDocument();

    fireEvent.click(drawBtn);
    expect(screen.getByText(/Mode: Annotation/i)).toBeInTheDocument();
  });

  it('calls onSave when save button is clicked', () => {
    const onSave = vi.fn();
    render(
      <BiometricImageAnnotator
        imageUrl={mockImageUrl}
        initialBoxes={mockInitialBoxes}
        onSave={onSave}
      />
    );

    const saveBtn = screen.getByText(/Save Labels/i);
    fireEvent.click(saveBtn);

    expect(onSave).toHaveBeenCalledWith(mockInitialBoxes);
  });

  it('can zoom in and out', async () => {
    render(<BiometricImageAnnotator imageUrl={mockImageUrl} />);

    const zoomInBtn = screen.getByLabelText(/Zoom In/i);
    const zoomOutBtn = screen.getByLabelText(/Zoom Out/i);
    const resetBtn = screen.getByLabelText(/Reset Zoom/i);

    fireEvent.click(zoomInBtn);
    expect(screen.getByText(/125%/i)).toBeInTheDocument();

    fireEvent.click(zoomOutBtn);
    expect(screen.getByText(/100%/i)).toBeInTheDocument();

    fireEvent.click(zoomOutBtn);
    expect(screen.getByText(/75%/i)).toBeInTheDocument();

    fireEvent.click(resetBtn);
    expect(screen.getByText(/100%/i)).toBeInTheDocument();
  });
});
