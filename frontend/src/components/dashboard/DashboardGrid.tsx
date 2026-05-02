/**
 * Dashboard Grid Component
 *
 * Grid-based dashboard layout with drag-and-drop widget management.
 * Uses CSS Grid for layout (no external dependencies).
 */

import { useState, useCallback, ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { DashboardWidget, WidgetConfig } from './DashboardWidget';
import { Edit2, Save, Plus, LayoutGrid } from 'lucide-react';

interface DashboardGridProps {
  widgets: WidgetConfig[];
  onLayoutChange?: (widgets: WidgetConfig[]) => void;
  renderWidget: (config: WidgetConfig) => ReactNode;
  className?: string;
  columns?: number;
  rowHeight?: number;
  gap?: number;
  editable?: boolean;
}

export function DashboardGrid({
  widgets,
  onLayoutChange,
  renderWidget,
  className,
  columns = 12,
  rowHeight = 100,
  gap = 16,
  editable = true,
}: DashboardGridProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [localWidgets, setLocalWidgets] = useState(widgets);
  const [draggedWidget, setDraggedWidget] = useState<string | null>(null);


  // Handle widget removal
  const handleRemove = useCallback((id: string) => {
    setLocalWidgets((prev) => prev.filter((w) => w.id !== id));
  }, []);

  // Handle drag start
  const handleDragStart = (e: React.DragEvent, id: string) => {
    setDraggedWidget(id);
    e.dataTransfer.effectAllowed = 'move';
  };

  // Handle drag over
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  // Handle drop - swap positions
  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!draggedWidget || draggedWidget === targetId) return;

    setLocalWidgets((prev) => {
      const updated = [...prev];
      const draggedIdx = updated.findIndex((w) => w.id === draggedWidget);
      const targetIdx = updated.findIndex((w) => w.id === targetId);

      if (draggedIdx === -1 || targetIdx === -1) return prev;

      // Swap positions
      const draggedPos = { x: updated[draggedIdx].x, y: updated[draggedIdx].y };
      updated[draggedIdx] = { ...updated[draggedIdx], x: updated[targetIdx].x, y: updated[targetIdx].y };
      updated[targetIdx] = { ...updated[targetIdx], ...draggedPos };

      return updated;
    });
    setDraggedWidget(null);
  };

  // Save layout
  const handleSave = () => {
    setIsEditing(false);
    onLayoutChange?.(localWidgets);
  };

  // Cancel editing
  const handleCancel = () => {
    setIsEditing(false);
    setLocalWidgets(widgets);
  };

  // Calculate grid position styles
  const getWidgetStyle = (config: WidgetConfig) => ({
    gridColumn: `span ${config.w}`,
    gridRow: `span ${config.h}`,
  });

  return (
    <div className={cn('', className)}>
      {/* Toolbar */}
      {editable && (
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <LayoutGrid className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {localWidgets.length} widgets
            </span>
          </div>
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <Button variant="outline" size="sm" onClick={handleCancel}>
                  Cancel
                </Button>
                <Button size="sm" onClick={handleSave}>
                  <Save className="h-4 w-4 mr-1" />
                  Save Layout
                </Button>
              </>
            ) : (
              <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                <Edit2 className="h-4 w-4 mr-1" />
                Edit Layout
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Grid */}
      <div
        className="grid"
        style={{
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gridAutoRows: rowHeight,
          gap,
        }}
      >
        {localWidgets.map((config) => (
          <div
            key={config.id}
            style={getWidgetStyle(config)}
            draggable={isEditing}
            onDragStart={(e) => handleDragStart(e, config.id)}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, config.id)}
            className={cn(
              'transition-all',
              isEditing && 'cursor-move',
              draggedWidget === config.id && 'opacity-50'
            )}
          >
            <DashboardWidget
              config={config}
              isEditing={isEditing}
              onRemove={() => handleRemove(config.id)}
            >
              {renderWidget(config)}
            </DashboardWidget>
          </div>
        ))}
      </div>

      {/* Empty state */}
      {localWidgets.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <LayoutGrid className="h-12 w-12 mb-4 opacity-50" />
          <p className="text-sm">No widgets configured</p>
          {editable && (
            <Button variant="outline" size="sm" className="mt-4">
              <Plus className="h-4 w-4 mr-1" />
              Add Widget
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

export default DashboardGrid;
