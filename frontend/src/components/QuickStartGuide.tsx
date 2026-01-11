/**
 * Quick Start Guide Component
 * 
 * Interactive checklist for new users to get started with Bijmantra.
 * Tracks progress and provides contextual guidance.
 */

import { useState, useEffect } from 'react';
import { 
  CheckCircle, Circle, ChevronRight, Rocket, 
  Leaf, FlaskConical, Database, BarChart3,
  Settings, BookOpen, ExternalLink
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Link } from 'react-router-dom';

interface QuickStartStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  link: string;
  linkLabel: string;
  estimatedTime: string;
}

const QUICK_START_STEPS: QuickStartStep[] = [
  {
    id: 'profile',
    title: 'Complete Your Profile',
    description: 'Set up your preferences, language, and notification settings',
    icon: <Settings className="h-5 w-5" />,
    link: '/profile',
    linkLabel: 'Go to Profile',
    estimatedTime: '2 min',
  },
  {
    id: 'program',
    title: 'Create a Breeding Program',
    description: 'Set up your first breeding program to organize trials and germplasm',
    icon: <Leaf className="h-5 w-5" />,
    link: '/programs',
    linkLabel: 'Create Program',
    estimatedTime: '3 min',
  },
  {
    id: 'germplasm',
    title: 'Add Germplasm',
    description: 'Import or register your genetic resources and accessions',
    icon: <Database className="h-5 w-5" />,
    link: '/germplasm',
    linkLabel: 'Add Germplasm',
    estimatedTime: '5 min',
  },
  {
    id: 'trial',
    title: 'Create Your First Trial',
    description: 'Design and set up a breeding trial with your germplasm',
    icon: <FlaskConical className="h-5 w-5" />,
    link: '/trials',
    linkLabel: 'Create Trial',
    estimatedTime: '5 min',
  },
  {
    id: 'observation',
    title: 'Record Observations',
    description: 'Start collecting phenotypic data for your trials',
    icon: <BarChart3 className="h-5 w-5" />,
    link: '/observations',
    linkLabel: 'Record Data',
    estimatedTime: '3 min',
  },
  {
    id: 'explore',
    title: 'Explore Features',
    description: 'Discover advanced tools like genomics, analysis, and AI assistant',
    icon: <BookOpen className="h-5 w-5" />,
    link: '/help',
    linkLabel: 'View Guide',
    estimatedTime: '5 min',
  },
];

const STORAGE_KEY = 'bijmantra-quickstart-progress';

interface QuickStartGuideProps {
  onComplete?: () => void;
  compact?: boolean;
}

export function QuickStartGuide({ onComplete, compact = false }: QuickStartGuideProps) {
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [dismissed, setDismissed] = useState(false);

  // Load progress from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const data = JSON.parse(stored);
        setCompletedSteps(data.completed || []);
        setDismissed(data.dismissed || false);
      } catch {
        // Ignore
      }
    }
  }, []);

  // Save progress
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      completed: completedSteps,
      dismissed,
    }));
  }, [completedSteps, dismissed]);

  const toggleStep = (stepId: string) => {
    setCompletedSteps(prev => 
      prev.includes(stepId)
        ? prev.filter(id => id !== stepId)
        : [...prev, stepId]
    );
  };

  const progress = (completedSteps.length / QUICK_START_STEPS.length) * 100;
  const isComplete = completedSteps.length === QUICK_START_STEPS.length;

  useEffect(() => {
    if (isComplete) {
      onComplete?.();
    }
  }, [isComplete, onComplete]);

  if (dismissed && !isComplete) {
    return (
      <Card className="border-dashed">
        <CardContent className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Rocket className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              Quick Start Guide ({completedSteps.length}/{QUICK_START_STEPS.length} complete)
            </span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setDismissed(false)}>
            Resume
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Rocket className="h-4 w-4" />
              Quick Start
            </CardTitle>
            <Badge variant={isComplete ? 'default' : 'secondary'}>
              {completedSteps.length}/{QUICK_START_STEPS.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={progress} className="h-2 mb-3" />
          <div className="space-y-2">
            {QUICK_START_STEPS.slice(0, 3).map((step) => {
              const isCompleted = completedSteps.includes(step.id);
              return (
                <div
                  key={step.id}
                  className={cn(
                    'flex items-center gap-2 text-sm',
                    isCompleted && 'text-muted-foreground line-through'
                  )}
                >
                  {isCompleted ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <Circle className="h-4 w-4" />
                  )}
                  <span>{step.title}</span>
                </div>
              );
            })}
            {QUICK_START_STEPS.length > 3 && (
              <p className="text-xs text-muted-foreground">
                +{QUICK_START_STEPS.length - 3} more steps
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Rocket className="h-5 w-5" />
              Quick Start Guide
            </CardTitle>
            <CardDescription>
              Complete these steps to get the most out of Bijmantra
            </CardDescription>
          </div>
          {!isComplete && (
            <Button variant="ghost" size="sm" onClick={() => setDismissed(true)}>
              Dismiss
            </Button>
          )}
        </div>
        <div className="flex items-center gap-4 mt-4">
          <Progress value={progress} className="flex-1" />
          <span className="text-sm font-medium">
            {completedSteps.length}/{QUICK_START_STEPS.length}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {QUICK_START_STEPS.map((step, index) => {
            const isCompleted = completedSteps.includes(step.id);
            const isNext = !isCompleted && 
              QUICK_START_STEPS.slice(0, index).every(s => completedSteps.includes(s.id));

            return (
              <div
                key={step.id}
                className={cn(
                  'flex items-start gap-4 p-4 rounded-lg border transition-colors',
                  isCompleted && 'bg-green-50 border-green-200',
                  isNext && 'bg-primary/5 border-primary/20',
                  !isCompleted && !isNext && 'opacity-60'
                )}
              >
                <button
                  onClick={() => toggleStep(step.id)}
                  className={cn(
                    'mt-0.5 p-1 rounded-full transition-colors',
                    isCompleted 
                      ? 'text-green-500 hover:bg-green-100' 
                      : 'text-muted-foreground hover:bg-muted'
                  )}
                >
                  {isCompleted ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <Circle className="h-5 w-5" />
                  )}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      'p-1.5 rounded-lg',
                      isCompleted ? 'bg-green-100 text-green-600' : 'bg-muted'
                    )}>
                      {step.icon}
                    </div>
                    <div>
                      <h4 className={cn(
                        'font-medium',
                        isCompleted && 'line-through text-muted-foreground'
                      )}>
                        {step.title}
                      </h4>
                      <p className="text-sm text-muted-foreground">{step.description}</p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    ~{step.estimatedTime}
                  </Badge>
                  {!isCompleted && (
                    <Link to={step.link}>
                      <Button size="sm" variant={isNext ? 'default' : 'ghost'}>
                        {step.linkLabel}
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {isComplete && (
          <div className="mt-6 p-4 bg-green-50 rounded-lg text-center">
            <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <h4 className="font-medium text-green-800">All Done!</h4>
            <p className="text-sm text-green-600">
              You've completed the quick start guide. Explore more features!
            </p>
            <div className="flex justify-center gap-2 mt-3">
              <Link to="/help">
                <Button variant="outline" size="sm">
                  <BookOpen className="h-4 w-4 mr-2" />
                  Documentation
                </Button>
              </Link>
              <Link to="/dev-progress">
                <Button variant="outline" size="sm">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Dev Progress
                </Button>
              </Link>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Hook for checking quick start progress
export function useQuickStartProgress() {
  const [progress, setProgress] = useState({ completed: 0, total: QUICK_START_STEPS.length });

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const data = JSON.parse(stored);
        setProgress({
          completed: (data.completed || []).length,
          total: QUICK_START_STEPS.length,
        });
      } catch {
        // Ignore
      }
    }
  }, []);

  return {
    ...progress,
    percentage: (progress.completed / progress.total) * 100,
    isComplete: progress.completed === progress.total,
  };
}
