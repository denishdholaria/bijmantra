import { useState, useCallback, createContext, useContext, ReactNode } from 'react';
import { ChevronLeft, ChevronRight, Check, Circle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface WizardStep {
  id: string;
  title: string;
  description?: string;
  icon?: ReactNode;
  content: ReactNode;
  validate?: () => boolean | Promise<boolean>;
  optional?: boolean;
}

interface FormWizardProps {
  steps: WizardStep[];
  onComplete: (data: Record<string, unknown>) => void | Promise<void>;
  onCancel?: () => void;
  title?: string;
  description?: string;
  showProgress?: boolean;
  allowSkip?: boolean;
  className?: string;
}

interface WizardContextValue {
  currentStep: number;
  totalSteps: number;
  data: Record<string, unknown>;
  setData: (key: string, value: unknown) => void;
  updateData: (updates: Record<string, unknown>) => void;
  goNext: () => void;
  goPrev: () => void;
  goToStep: (step: number) => void;
  isFirstStep: boolean;
  isLastStep: boolean;
}

const WizardContext = createContext<WizardContextValue | null>(null);

export function useWizard() {
  const context = useContext(WizardContext);
  if (!context) {
    throw new Error('useWizard must be used within FormWizard');
  }
  return context;
}

export function FormWizard({
  steps,
  onComplete,
  onCancel,
  title,
  description,
  showProgress = true,
  allowSkip = false,
  className,
}: FormWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setDataState] = useState<Record<string, unknown>>({});
  const [isValidating, setIsValidating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<number, string>>({});
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  const totalSteps = steps.length;
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === totalSteps - 1;
  const progress = ((currentStep + 1) / totalSteps) * 100;

  const setData = useCallback((key: string, value: unknown) => {
    setDataState(prev => ({ ...prev, [key]: value }));
  }, []);

  const updateData = useCallback((updates: Record<string, unknown>) => {
    setDataState(prev => ({ ...prev, ...updates }));
  }, []);

  const validateCurrentStep = async (): Promise<boolean> => {
    const step = steps[currentStep];
    if (!step.validate) return true;

    setIsValidating(true);
    try {
      const isValid = await step.validate();
      if (!isValid) {
        setErrors(prev => ({ ...prev, [currentStep]: 'Please complete all required fields' }));
      } else {
        setErrors(prev => {
          const next = { ...prev };
          delete next[currentStep];
          return next;
        });
      }
      return isValid;
    } catch (error) {
      setErrors(prev => ({ ...prev, [currentStep]: 'Validation failed' }));
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const goNext = async () => {
    const isValid = await validateCurrentStep();
    if (!isValid && !allowSkip) return;

    setCompletedSteps(prev => new Set([...prev, currentStep]));

    if (isLastStep) {
      setIsSubmitting(true);
      try {
        await onComplete(data);
      } finally {
        setIsSubmitting(false);
      }
    } else {
      setCurrentStep(prev => Math.min(prev + 1, totalSteps - 1));
    }
  };

  const goPrev = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const goToStep = (step: number) => {
    if (step < currentStep || completedSteps.has(step - 1) || step === 0) {
      setCurrentStep(step);
    }
  };

  const currentStepData = steps[currentStep];

  const contextValue: WizardContextValue = {
    currentStep,
    totalSteps,
    data,
    setData,
    updateData,
    goNext,
    goPrev,
    goToStep,
    isFirstStep,
    isLastStep,
  };

  return (
    <WizardContext.Provider value={contextValue}>
      <Card className={cn('w-full max-w-2xl mx-auto', className)}>
        {/* Header */}
        {(title || description) && (
          <CardHeader>
            {title && <CardTitle>{title}</CardTitle>}
            {description && <CardDescription>{description}</CardDescription>}
          </CardHeader>
        )}

        <CardContent className="space-y-6">
          {/* Progress */}
          {showProgress && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  Step {currentStep + 1} of {totalSteps}
                </span>
                <span className="font-medium">{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}

          {/* Step Indicators */}
          <div className="flex items-center justify-center gap-2">
            {steps.map((step, index) => {
              const isCompleted = completedSteps.has(index);
              const isCurrent = index === currentStep;
              const hasError = errors[index];
              const isClickable = index < currentStep || completedSteps.has(index - 1) || index === 0;

              return (
                <button
                  key={step.id}
                  onClick={() => isClickable && goToStep(index)}
                  disabled={!isClickable}
                  className={cn(
                    'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
                    isCurrent && 'bg-primary/10 text-primary',
                    isCompleted && !isCurrent && 'text-green-600',
                    hasError && 'text-destructive',
                    !isClickable && 'opacity-50 cursor-not-allowed',
                    isClickable && !isCurrent && 'hover:bg-muted'
                  )}
                >
                  <div className={cn(
                    'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
                    isCurrent && 'bg-primary text-primary-foreground',
                    isCompleted && !isCurrent && 'bg-green-100 text-green-600',
                    hasError && 'bg-destructive/10 text-destructive',
                    !isCurrent && !isCompleted && !hasError && 'bg-muted'
                  )}>
                    {hasError ? (
                      <AlertCircle className="h-3 w-3" />
                    ) : isCompleted ? (
                      <Check className="h-3 w-3" />
                    ) : (
                      index + 1
                    )}
                  </div>
                  <span className="hidden sm:inline text-sm">{step.title}</span>
                </button>
              );
            })}
          </div>

          {/* Current Step Content */}
          <div className="min-h-[200px]">
            <div className="mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                {currentStepData.icon}
                {currentStepData.title}
              </h3>
              {currentStepData.description && (
                <p className="text-sm text-muted-foreground mt-1">
                  {currentStepData.description}
                </p>
              )}
            </div>

            {errors[currentStep] && (
              <div className="mb-4 p-3 bg-destructive/10 text-destructive text-sm rounded-lg flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                {errors[currentStep]}
              </div>
            )}

            {currentStepData.content}
          </div>
        </CardContent>

        {/* Footer */}
        <CardFooter className="flex justify-between">
          <div>
            {onCancel && (
              <Button variant="ghost" onClick={onCancel}>
                Cancel
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {!isFirstStep && (
              <Button variant="outline" onClick={goPrev} disabled={isValidating || isSubmitting}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>
            )}
            <Button onClick={goNext} disabled={isValidating || isSubmitting}>
              {isValidating ? (
                'Validating...'
              ) : isSubmitting ? (
                'Submitting...'
              ) : isLastStep ? (
                <>
                  Complete
                  <Check className="h-4 w-4 ml-1" />
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
    </WizardContext.Provider>
  );
}

// Helper component for wizard step content
export function WizardStepContent({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('space-y-4', className)}>{children}</div>;
}

// Helper component for wizard field
export function WizardField({ 
  label, 
  required, 
  error, 
  children 
}: { 
  label: string; 
  required?: boolean; 
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
