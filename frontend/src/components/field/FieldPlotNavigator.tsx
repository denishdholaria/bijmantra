/**
 * Field Plot Navigator
 * 
 * Navigate between plots with large touch-friendly buttons and swipe gestures.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronLeft, ChevronRight, Grid3X3, SkipBack, SkipForward } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFieldMode } from '@/hooks/useFieldMode';

interface Plot {
  id: string;
  name: string;
  row?: number;
  column?: number;
  status?: 'pending' | 'complete' | 'skipped';
}

interface FieldPlotNavigatorProps {
  plots: Plot[];
  currentIndex: number;
  onNavigate: (index: number) => void;
  onComplete?: (plotId: string) => void;
  onSkip?: (plotId: string) => void;
  showProgress?: boolean;
  enableSwipe?: boolean;
  className?: string;
}

export function FieldPlotNavigator({
  plots,
  currentIndex,
  onNavigate,
  onComplete,
  onSkip,
  showProgress = true,
  enableSwipe = true,
  className,
}: FieldPlotNavigatorProps) {
  const { isFieldMode, triggerHaptic } = useFieldMode();
  const containerRef = useRef<HTMLDivElement>(null);
  const touchStartX = useRef<number | null>(null);
  const touchStartY = useRef<number | null>(null);

  const currentPlot = plots[currentIndex];
  const completedCount = plots.filter(p => p.status === 'complete').length;
  const progress = plots.length > 0 ? (completedCount / plots.length) * 100 : 0;

  const canGoPrev = currentIndex > 0;
  const canGoNext = currentIndex < plots.length - 1;

  const goToPrev = useCallback(() => {
    if (canGoPrev) {
      onNavigate(currentIndex - 1);
      triggerHaptic(30);
    }
  }, [canGoPrev, currentIndex, onNavigate, triggerHaptic]);

  const goToNext = useCallback(() => {
    if (canGoNext) {
      onNavigate(currentIndex + 1);
      triggerHaptic(30);
    }
  }, [canGoNext, currentIndex, onNavigate, triggerHaptic]);

  const goToFirst = useCallback(() => {
    onNavigate(0);
    triggerHaptic([30, 50, 30]);
  }, [onNavigate, triggerHaptic]);

  const goToLast = useCallback(() => {
    onNavigate(plots.length - 1);
    triggerHaptic([30, 50, 30]);
  }, [plots.length, onNavigate, triggerHaptic]);

  // Swipe gesture handling
  useEffect(() => {
    if (!enableSwipe || !containerRef.current) return;

    const container = containerRef.current;

    const handleTouchStart = (e: TouchEvent) => {
      touchStartX.current = e.touches[0].clientX;
      touchStartY.current = e.touches[0].clientY;
    };

    const handleTouchEnd = (e: TouchEvent) => {
      if (touchStartX.current === null || touchStartY.current === null) return;

      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;
      
      const deltaX = touchEndX - touchStartX.current;
      const deltaY = touchEndY - touchStartY.current;

      // Only trigger if horizontal swipe is dominant and significant
      if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
        if (deltaX > 0) {
          goToPrev();
        } else {
          goToNext();
        }
      }

      touchStartX.current = null;
      touchStartY.current = null;
    };

    container.addEventListener('touchstart', handleTouchStart, { passive: true });
    container.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      container.removeEventListener('touchstart', handleTouchStart);
      container.removeEventListener('touchend', handleTouchEnd);
    };
  }, [enableSwipe, goToPrev, goToNext]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        goToPrev();
      } else if (e.key === 'ArrowRight') {
        goToNext();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToPrev, goToNext]);

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'complete': return 'bg-green-500';
      case 'skipped': return 'bg-yellow-500';
      default: return 'bg-gray-300';
    }
  };

  const buttonSize = isFieldMode ? 'h-16 min-w-[64px]' : 'h-12 min-w-[48px]';
  const iconSize = isFieldMode ? 'h-8 w-8' : 'h-6 w-6';

  return (
    <div ref={containerRef} className={cn('space-y-4', className)}>
      {/* Current Plot Display */}
      <div className="text-center">
        <Badge 
          variant="outline" 
          className={cn(
            'px-4 py-2 font-mono',
            isFieldMode && 'text-xl px-6 py-3'
          )}
        >
          {currentPlot?.name || `Plot ${currentIndex + 1}`}
        </Badge>
        {currentPlot?.row !== undefined && currentPlot?.column !== undefined && (
          <p className={cn(
            'text-muted-foreground mt-1',
            isFieldMode ? 'text-base' : 'text-sm'
          )}>
            Row {currentPlot.row}, Column {currentPlot.column}
          </p>
        )}
      </div>

      {/* Progress Bar */}
      {showProgress && (
        <div className="space-y-1">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>{completedCount} of {plots.length} complete</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between gap-2">
        <Button
          variant="outline"
          size="icon"
          className={cn(buttonSize, 'rounded-lg')}
          onClick={goToFirst}
          disabled={!canGoPrev}
        >
          <SkipBack className={iconSize} />
        </Button>

        <Button
          variant="outline"
          className={cn(buttonSize, 'flex-1 rounded-lg', isFieldMode && 'text-lg')}
          onClick={goToPrev}
          disabled={!canGoPrev}
        >
          <ChevronLeft className={iconSize} />
          <span className="hidden sm:inline ml-1">Previous</span>
        </Button>

        <div className={cn(
          'flex items-center justify-center px-4 font-mono',
          isFieldMode ? 'text-xl' : 'text-lg'
        )}>
          {currentIndex + 1} / {plots.length}
        </div>

        <Button
          variant="outline"
          className={cn(buttonSize, 'flex-1 rounded-lg', isFieldMode && 'text-lg')}
          onClick={goToNext}
          disabled={!canGoNext}
        >
          <span className="hidden sm:inline mr-1">Next</span>
          <ChevronRight className={iconSize} />
        </Button>

        <Button
          variant="outline"
          size="icon"
          className={cn(buttonSize, 'rounded-lg')}
          onClick={goToLast}
          disabled={!canGoNext}
        >
          <SkipForward className={iconSize} />
        </Button>
      </div>

      {/* Quick Actions */}
      {(onComplete || onSkip) && (
        <div className="flex gap-2">
          {onSkip && (
            <Button
              variant="outline"
              className={cn('flex-1', isFieldMode && 'h-14 text-lg')}
              onClick={() => {
                onSkip(currentPlot.id);
                triggerHaptic(50);
              }}
            >
              Skip Plot
            </Button>
          )}
          {onComplete && (
            <Button
              className={cn('flex-1', isFieldMode && 'h-14 text-lg')}
              onClick={() => {
                onComplete(currentPlot.id);
                triggerHaptic([50, 30, 50]);
                if (canGoNext) goToNext();
              }}
            >
              Complete & Next
            </Button>
          )}
        </div>
      )}

      {/* Mini Plot Map */}
      <div className="flex flex-wrap gap-1 justify-center">
        {plots.slice(
          Math.max(0, currentIndex - 5),
          Math.min(plots.length, currentIndex + 6)
        ).map((plot, i) => {
          const actualIndex = Math.max(0, currentIndex - 5) + i;
          return (
            <button
              key={plot.id}
              className={cn(
                'w-3 h-3 rounded-sm transition-all',
                getStatusColor(plot.status),
                actualIndex === currentIndex && 'ring-2 ring-primary ring-offset-1 scale-125'
              )}
              onClick={() => {
                onNavigate(actualIndex);
                triggerHaptic(20);
              }}
              title={plot.name}
            />
          );
        })}
      </div>

      {enableSwipe && (
        <p className="text-center text-xs text-muted-foreground">
          ← Swipe to navigate →
        </p>
      )}
    </div>
  );
}

export default FieldPlotNavigator;
