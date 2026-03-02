import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import GanttChartTimeline, { GanttTask, GanttMilestone } from './GanttChartTimeline';
import React from 'react';

// Mock the Lucide icons to avoid issues in testing environment if any
vi.mock('lucide-react', () => ({
  Calendar: () => <div data-testid="calendar-icon" />,
  ChevronLeft: () => <div data-testid="chevron-left-icon" />,
  ChevronRight: () => <div data-testid="chevron-right-icon" />,
  Milestone: () => <div data-testid="milestone-icon" />,
  Info: () => <div data-testid="info-icon" />,
  Sprout: () => <div data-testid="sprout-icon" />,
  Search: () => <div data-testid="search-icon" />,
  CheckCircle: () => <div data-testid="check-circle-icon" />,
  Leaf: () => <div data-testid="leaf-icon" />,
  Sparkles: () => <div data-testid="sparkles-icon" />,
}));

const mockTasks: GanttTask[] = [
  {
    id: '1',
    name: 'F1 Hybridization',
    start: new Date(2025, 0, 1),
    end: new Date(2025, 2, 31),
    status: 'completed',
    progress: 100,
  },
  {
    id: '2',
    name: 'F2 Nursery',
    start: new Date(2025, 3, 1),
    end: new Date(2025, 6, 30),
    status: 'in-progress',
    progress: 45,
  }
];

const mockMilestones: GanttMilestone[] = [
  {
    id: 'm1',
    name: 'Initial Planting',
    date: new Date(2025, 0, 1),
    type: 'planting',
  }
];

describe('GanttChartTimeline', () => {
  it('renders correctly with tasks and milestones', () => {
    render(
      <GanttChartTimeline
        tasks={mockTasks}
        milestones={mockMilestones}
        startDate={new Date(2025, 0, 1)}
        endDate={new Date(2025, 11, 31)}
      />
    );

    expect(screen.getByText('Breeding Cycle Timeline')).toBeInTheDocument();
    expect(screen.getByText('F1 Hybridization')).toBeInTheDocument();
    expect(screen.getByText('F2 Nursery')).toBeInTheDocument();

    // Milestone names are visible on hover or in their absolute container
    expect(screen.getByText('Initial Planting')).toBeInTheDocument();
  });

  it('renders empty state when no tasks are provided', () => {
    render(
      <GanttChartTimeline
        tasks={[]}
        startDate={new Date(2025, 0, 1)}
        endDate={new Date(2025, 11, 31)}
      />
    );

    expect(screen.getByText('No tasks planned for this cycle.')).toBeInTheDocument();
  });

  it('displays the correct date range in the header', () => {
    render(
      <GanttChartTimeline
        tasks={mockTasks}
        startDate={new Date(2025, 0, 1)}
        endDate={new Date(2025, 5, 30)}
      />
    );

    expect(screen.getByText(/January 2025/)).toBeInTheDocument();
    expect(screen.getByText(/June 2025/)).toBeInTheDocument();
  });

  it('renders progress percentage for tasks', () => {
    render(
      <GanttChartTimeline
        tasks={mockTasks}
        startDate={new Date(2025, 0, 1)}
        endDate={new Date(2025, 11, 31)}
      />
    );

    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
  });
});
