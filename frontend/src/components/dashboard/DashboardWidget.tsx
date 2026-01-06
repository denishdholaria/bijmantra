/**
 * Dashboard Widget Component
 *
 * Draggable, resizable widget container for dashboard customization.
 */

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  GripVertical,
  Maximize2,
  Minimize2,
  X,
  Settings,
  RefreshCw,
} from 'lucide-react';

export interface WidgetConfig {
  id: string;
  type: string;
  title: string;
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  minH?: number;
  maxW?: number;
  maxH?: number;
  settings?: Record<string, any>;
}

interface DashboardWidgetProps {
  config: WidgetConfig;
  children: ReactNode;
  isEditing?: boolean;
  isLoading?: boolean;
  onRemove?: () => void;
  onSettings?: () => void;
  onRefresh?: () => void;
  onMaximize?: () => void;
  className?: string;
  dragHandleClass?: string;
}


export function DashboardWidget({
  config,
  children,
  isEditing = false,
  isLoading = false,
  onRemove,
  onSettings,
  onRefresh,
  onMaximize,
  className,
  dragHandleClass = 'drag-handle',
}: DashboardWidgetProps) {
  return (
    <Card
      className={cn(
        'h-full flex flex-col overflow-hidden',
        isEditing && 'ring-2 ring-primary/20',
        className
      )}
    >
      <CardHeader className="p-3 pb-2 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isEditing && (
              <div className={cn('cursor-grab active:cursor-grabbing', dragHandleClass)}>
                <GripVertical className="h-4 w-4 text-muted-foreground" />
              </div>
            )}
            <CardTitle className="text-sm font-medium">{config.title}</CardTitle>
          </div>
          <div className="flex items-center gap-1">
            {isLoading && (
              <RefreshCw className="h-3 w-3 animate-spin text-muted-foreground" />
            )}
            {onRefresh && !isLoading && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={onRefresh}
              >
                <RefreshCw className="h-3 w-3" />
              </Button>
            )}
            {onSettings && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={onSettings}
              >
                <Settings className="h-3 w-3" />
              </Button>
            )}
            {onMaximize && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={onMaximize}
              >
                <Maximize2 className="h-3 w-3" />
              </Button>
            )}
            {isEditing && onRemove && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-destructive hover:text-destructive"
                onClick={onRemove}
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-3 pt-0 flex-1 overflow-auto">
        {children}
      </CardContent>
    </Card>
  );
}

export default DashboardWidget;
