import React, { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { MetricCard } from '@/components/analytics/MetricCard';
import { GripVertical } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface AnalyticsWidget {
  id: string;
  title: string;
  value: string | number;
  previousValue?: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

interface SortableItemProps {
  widget: AnalyticsWidget;
}

function SortableItem({ widget }: SortableItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: widget.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 10 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'relative group',
        isDragging ? 'opacity-50' : 'opacity-100'
      )}
    >
      <div
        {...attributes}
        {...listeners}
        className="absolute top-2 right-2 p-1 cursor-grab active:cursor-grabbing text-muted-foreground/30 group-hover:text-muted-foreground transition-colors z-20"
      >
        <GripVertical className="h-4 w-4" />
      </div>
      <MetricCard
        title={widget.title}
        value={widget.value}
        previousValue={widget.previousValue}
        unit={widget.unit}
        trend={widget.trend}
        description={widget.description}
        variant={widget.variant}
        className="h-full"
      />
    </div>
  );
}

const DEFAULT_WIDGETS: AnalyticsWidget[] = [
  {
    id: '1',
    title: 'Total Yield',
    value: 1250.5,
    previousValue: 1100,
    unit: 'kg/ha',
    trend: 'up',
    description: 'Average yield across all test plots',
  },
  {
    id: '2',
    title: 'Soil Moisture',
    value: 24.2,
    previousValue: 28.5,
    unit: '%',
    trend: 'down',
    description: 'Current average soil moisture level',
    variant: 'warning',
  },
  {
    id: '3',
    title: 'Active Trials',
    value: 14,
    previousValue: 12,
    trend: 'up',
    description: 'Number of ongoing field trials',
  },
  {
    id: '4',
    title: 'Pest Level',
    value: 'Low',
    trend: 'neutral',
    description: 'Observed pest activity in the region',
    variant: 'success',
  },
];

export function DragAndDropAnalyticsGrid() {
  const [widgets, setWidgets] = useState<AnalyticsWidget[]>(DEFAULT_WIDGETS);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setWidgets((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);

        return arrayMove(items, oldIndex, newIndex);
      });
    }
  }

  return (
    <div className="p-4 bg-background border rounded-xl shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">REEVU Analytics Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Drag and drop to rearrange widgets
        </p>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={widgets.map((w) => w.id)}
          strategy={rectSortingStrategy}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {widgets.map((widget) => (
              <SortableItem key={widget.id} widget={widget} />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
}

export default DragAndDropAnalyticsGrid;
