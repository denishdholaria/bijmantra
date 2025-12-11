/**
 * Feature Tour Component
 * 
 * Interactive walkthrough for feature discovery.
 * Highlights UI elements and provides step-by-step guidance.
 */

import { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { X, ChevronLeft, ChevronRight, Check, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface TourStep {
  target: string; // CSS selector
  title: string;
  content: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  action?: () => void;
  actionLabel?: string;
}

interface FeatureTourProps {
  steps: TourStep[];
  tourId: string;
  onComplete?: () => void;
  onSkip?: () => void;
  autoStart?: boolean;
}

const STORAGE_PREFIX = 'bijmantra-tour-';

export function FeatureTour({ 
  steps, 
  tourId, 
  onComplete, 
  onSkip,
  autoStart = false 
}: FeatureTourProps) {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  const storageKey = `${STORAGE_PREFIX}${tourId}`;

  // Check if tour was completed
  useEffect(() => {
    const completed = localStorage.getItem(storageKey);
    if (!completed && autoStart) {
      setIsActive(true);
    }
  }, [storageKey, autoStart]);

  // Find and highlight target element
  useEffect(() => {
    if (!isActive || !steps[currentStep]) return;

    const target = document.querySelector(steps[currentStep].target);
    if (target) {
      const rect = target.getBoundingClientRect();
      setTargetRect(rect);
      
      // Scroll into view if needed
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
      setTargetRect(null);
    }
  }, [isActive, currentStep, steps]);

  const handleNext = useCallback(() => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      handleComplete();
    }
  }, [currentStep, steps.length]);

  const handlePrev = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  }, [currentStep]);

  const handleComplete = useCallback(() => {
    localStorage.setItem(storageKey, 'true');
    setIsActive(false);
    setCurrentStep(0);
    onComplete?.();
  }, [storageKey, onComplete]);

  const handleSkip = useCallback(() => {
    localStorage.setItem(storageKey, 'true');
    setIsActive(false);
    setCurrentStep(0);
    onSkip?.();
  }, [storageKey, onSkip]);

  const startTour = useCallback(() => {
    setCurrentStep(0);
    setIsActive(true);
  }, []);

  const resetTour = useCallback(() => {
    localStorage.removeItem(storageKey);
  }, [storageKey]);

  if (!isActive) {
    return null;
  }

  const step = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;
  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  // Calculate tooltip position
  const getTooltipStyle = (): React.CSSProperties => {
    if (!targetRect) {
      return {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    }

    const padding = 16;
    const tooltipWidth = 320;
    const tooltipHeight = 200;
    const placement = step.placement || 'bottom';

    let top = 0;
    let left = 0;

    switch (placement) {
      case 'top':
        top = targetRect.top - tooltipHeight - padding;
        left = targetRect.left + targetRect.width / 2 - tooltipWidth / 2;
        break;
      case 'bottom':
        top = targetRect.bottom + padding;
        left = targetRect.left + targetRect.width / 2 - tooltipWidth / 2;
        break;
      case 'left':
        top = targetRect.top + targetRect.height / 2 - tooltipHeight / 2;
        left = targetRect.left - tooltipWidth - padding;
        break;
      case 'right':
        top = targetRect.top + targetRect.height / 2 - tooltipHeight / 2;
        left = targetRect.right + padding;
        break;
    }

    // Keep within viewport
    left = Math.max(padding, Math.min(left, window.innerWidth - tooltipWidth - padding));
    top = Math.max(padding, Math.min(top, window.innerHeight - tooltipHeight - padding));

    return {
      position: 'fixed',
      top,
      left,
      width: tooltipWidth,
    };
  };

  return createPortal(
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-[9998]">
        {/* Dark overlay with cutout for target */}
        <svg className="absolute inset-0 w-full h-full">
          <defs>
            <mask id="tour-mask">
              <rect x="0" y="0" width="100%" height="100%" fill="white" />
              {targetRect && (
                <rect
                  x={targetRect.left - 4}
                  y={targetRect.top - 4}
                  width={targetRect.width + 8}
                  height={targetRect.height + 8}
                  rx="4"
                  fill="black"
                />
              )}
            </mask>
          </defs>
          <rect
            x="0"
            y="0"
            width="100%"
            height="100%"
            fill="rgba(0, 0, 0, 0.5)"
            mask="url(#tour-mask)"
          />
        </svg>

        {/* Highlight border */}
        {targetRect && (
          <div
            className="absolute border-2 border-primary rounded-lg pointer-events-none animate-pulse"
            style={{
              top: targetRect.top - 4,
              left: targetRect.left - 4,
              width: targetRect.width + 8,
              height: targetRect.height + 8,
            }}
          />
        )}
      </div>

      {/* Tooltip */}
      <Card className="z-[9999] shadow-xl" style={getTooltipStyle()}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{step.title}</CardTitle>
            <Button variant="ghost" size="icon" onClick={handleSkip}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <Progress value={progress} className="h-1" />
        </CardHeader>
        <CardContent className="pb-4">
          <p className="text-sm text-muted-foreground">{step.content}</p>
          {step.action && step.actionLabel && (
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={step.action}
            >
              {step.actionLabel}
            </Button>
          )}
        </CardContent>
        <CardFooter className="flex items-center justify-between pt-0">
          <span className="text-xs text-muted-foreground">
            Step {currentStep + 1} of {steps.length}
          </span>
          <div className="flex gap-2">
            {!isFirstStep && (
              <Button variant="outline" size="sm" onClick={handlePrev}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            )}
            {isFirstStep && (
              <Button variant="ghost" size="sm" onClick={handleSkip}>
                <SkipForward className="h-4 w-4 mr-1" />
                Skip
              </Button>
            )}
            <Button size="sm" onClick={handleNext}>
              {isLastStep ? (
                <>
                  <Check className="h-4 w-4 mr-1" />
                  Done
                </>
              ) : (
                <>
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </>
              )}
            </Button>
          </div>
        </CardFooter>
      </Card>
    </>,
    document.body
  );
}

// Hook for managing tours
export function useTour(tourId: string) {
  const storageKey = `${STORAGE_PREFIX}${tourId}`;
  const [isCompleted, setIsCompleted] = useState(true);

  useEffect(() => {
    setIsCompleted(localStorage.getItem(storageKey) === 'true');
  }, [storageKey]);

  const startTour = useCallback(() => {
    localStorage.removeItem(storageKey);
    setIsCompleted(false);
    // Force re-render by dispatching custom event
    window.dispatchEvent(new CustomEvent('tour-start', { detail: tourId }));
  }, [storageKey, tourId]);

  const completeTour = useCallback(() => {
    localStorage.setItem(storageKey, 'true');
    setIsCompleted(true);
  }, [storageKey]);

  const resetTour = useCallback(() => {
    localStorage.removeItem(storageKey);
    setIsCompleted(false);
  }, [storageKey]);

  return {
    isCompleted,
    startTour,
    completeTour,
    resetTour,
  };
}

// Pre-defined tours
export const DASHBOARD_TOUR: TourStep[] = [
  {
    target: '[data-tour="nav-modules"]',
    title: 'Module Navigation',
    content: 'Access all Bijmantra modules from here. Each module contains specialized tools for different aspects of plant breeding.',
    placement: 'right',
  },
  {
    target: '[data-tour="command-palette"]',
    title: 'Command Palette',
    content: 'Press ⌘K to quickly search and navigate to any page, entity, or action.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="quick-actions"]',
    title: 'Quick Actions',
    content: 'Common actions are always accessible here. The actions change based on your current page.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="veena-ai"]',
    title: 'Veena AI Assistant',
    content: 'Ask Veena anything about plant breeding or get help with tasks. She can search your data and provide insights.',
    placement: 'left',
  },
];

export const TRIAL_TOUR: TourStep[] = [
  {
    target: '[data-tour="trial-list"]',
    title: 'Your Trials',
    content: 'View and manage all your breeding trials here. Click on a trial to see details.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="create-trial"]',
    title: 'Create New Trial',
    content: 'Start a new trial by clicking this button. You can choose from different trial designs.',
    placement: 'left',
  },
  {
    target: '[data-tour="trial-filters"]',
    title: 'Filter & Search',
    content: 'Use filters to find specific trials by program, season, or status.',
    placement: 'bottom',
  },
];

export const GERMPLASM_TOUR: TourStep[] = [
  {
    target: '[data-tour="germplasm-search"]',
    title: 'Search Germplasm',
    content: 'Search by name, accession number, or any trait. Use advanced filters for precise results.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="germplasm-import"]',
    title: 'Import Data',
    content: 'Import germplasm from CSV files or connect to BrAPI-compatible databases.',
    placement: 'left',
  },
];
