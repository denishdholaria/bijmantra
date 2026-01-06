/**
 * Onboarding Wizard Component
 * 
 * Guides new users through initial setup and feature discovery.
 * Shows on first login and can be re-accessed from help menu.
 */

import { useState, useEffect } from 'react';
import { 
  ChevronRight, ChevronLeft, Check, X, Leaf, FlaskConical, 
  Database, Map, Sun, Satellite, Settings, BookOpen, Sparkles,
  Smartphone, Globe, Bell, Keyboard
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  content: React.ReactNode;
}

interface OnboardingWizardProps {
  onComplete: () => void;
  onSkip?: () => void;
  userName?: string;
}

const STORAGE_KEY = 'bijmantra-onboarding-complete';

export function OnboardingWizard({ onComplete, onSkip, userName }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedDivisions, setSelectedDivisions] = useState<string[]>([
    'plant-sciences', 'seed-bank', 'earth-systems'
  ]);
  const [preferences, setPreferences] = useState({
    fieldMode: false,
    notifications: true,
    offlineMode: true,
    darkMode: false,
  });

  const divisions = [
    { id: 'plant-sciences', name: 'Plant Sciences', icon: <Leaf className="h-5 w-5" />, description: 'Breeding, genomics, trials' },
    { id: 'seed-bank', name: 'Seed Bank', icon: <Database className="h-5 w-5" />, description: 'Germplasm conservation' },
    { id: 'earth-systems', name: 'Earth Systems', icon: <Map className="h-5 w-5" />, description: 'Weather, soil, GIS' },
    { id: 'sun-earth', name: 'Sun-Earth Systems', icon: <Sun className="h-5 w-5" />, description: 'Solar, photoperiod' },
    { id: 'sensors', name: 'Sensor Networks', icon: <Satellite className="h-5 w-5" />, description: 'IoT monitoring' },
    { id: 'commercial', name: 'Commercial', icon: <FlaskConical className="h-5 w-5" />, description: 'Licensing, DUS' },
    { id: 'space', name: 'Space Research', icon: <Satellite className="h-5 w-5" />, description: 'Interplanetary ag' },
    { id: 'knowledge', name: 'Knowledge', icon: <BookOpen className="h-5 w-5" />, description: 'Training, docs' },
  ];

  const toggleDivision = (id: string) => {
    setSelectedDivisions(prev =>
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    );
  };

  const steps: OnboardingStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to Bijmantra',
      description: 'Your comprehensive plant breeding platform',
      icon: <Sparkles className="h-6 w-6" />,
      content: (
        <div className="space-y-6 text-center">
          <div className="w-24 h-24 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
            <Leaf className="h-12 w-12 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">
              {userName ? `Welcome, ${userName}!` : 'Welcome!'}
            </h2>
            <p className="text-muted-foreground mt-2">
              Let's get you set up with Bijmantra, your all-in-one platform for 
              plant breeding, germplasm management, and agricultural research.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-4 pt-4">
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-2xl font-bold text-primary">469+</p>
              <p className="text-sm text-muted-foreground">API Endpoints</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-2xl font-bold text-primary">280+</p>
              <p className="text-sm text-muted-foreground">Pages</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-2xl font-bold text-primary">11</p>
              <p className="text-sm text-muted-foreground">Modules</p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'divisions',
      title: 'Choose Your Modules',
      description: 'Select the modules relevant to your work',
      icon: <Settings className="h-6 w-6" />,
      content: (
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Bijmantra is modular. Select the divisions you'll use most often. 
            You can always change this later in settings.
          </p>
          <div className="grid grid-cols-2 gap-3">
            {divisions.map((div) => (
              <button
                key={div.id}
                onClick={() => toggleDivision(div.id)}
                className={cn(
                  'p-4 rounded-lg border text-left transition-all',
                  selectedDivisions.includes(div.id)
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                )}
              >
                <div className="flex items-start gap-3">
                  <div className={cn(
                    'p-2 rounded-lg',
                    selectedDivisions.includes(div.id) ? 'bg-primary/10 text-primary' : 'bg-muted'
                  )}>
                    {div.icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{div.name}</p>
                      {selectedDivisions.includes(div.id) && (
                        <Check className="h-4 w-4 text-primary" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{div.description}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ),
    },
    {
      id: 'preferences',
      title: 'Set Your Preferences',
      description: 'Customize your experience',
      icon: <Settings className="h-6 w-6" />,
      content: (
        <div className="space-y-6">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <Smartphone className="h-5 w-5 text-muted-foreground" />
              <div>
                <Label className="font-medium">Field Mode</Label>
                <p className="text-sm text-muted-foreground">
                  High contrast, large buttons for outdoor use
                </p>
              </div>
            </div>
            <Switch
              checked={preferences.fieldMode}
              onCheckedChange={(v) => setPreferences(p => ({ ...p, fieldMode: v }))}
            />
          </div>

          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <Globe className="h-5 w-5 text-muted-foreground" />
              <div>
                <Label className="font-medium">Offline Mode</Label>
                <p className="text-sm text-muted-foreground">
                  Work without internet, sync when connected
                </p>
              </div>
            </div>
            <Switch
              checked={preferences.offlineMode}
              onCheckedChange={(v) => setPreferences(p => ({ ...p, offlineMode: v }))}
            />
          </div>

          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <Bell className="h-5 w-5 text-muted-foreground" />
              <div>
                <Label className="font-medium">Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Get alerts for important updates
                </p>
              </div>
            </div>
            <Switch
              checked={preferences.notifications}
              onCheckedChange={(v) => setPreferences(p => ({ ...p, notifications: v }))}
            />
          </div>
        </div>
      ),
    },
    {
      id: 'shortcuts',
      title: 'Quick Tips',
      description: 'Keyboard shortcuts and features',
      icon: <Keyboard className="h-6 w-6" />,
      content: (
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Here are some shortcuts to help you work faster:
          </p>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <span>Open Command Palette</span>
              <Badge variant="outline" className="font-mono">⌘ K</Badge>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <span>Quick Search</span>
              <Badge variant="outline" className="font-mono">⌘ /</Badge>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <span>Toggle Field Mode</span>
              <Badge variant="outline" className="font-mono">⌘ F</Badge>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <span>New Observation</span>
              <Badge variant="outline" className="font-mono">⌘ N</Badge>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <span>View Shortcuts</span>
              <Badge variant="outline" className="font-mono">?</Badge>
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            💡 Tip: Press <kbd className="px-1 py-0.5 bg-muted rounded text-xs">?</kbd> anytime 
            to see all available keyboard shortcuts.
          </p>
        </div>
      ),
    },
    {
      id: 'complete',
      title: "You're All Set!",
      description: 'Start exploring Bijmantra',
      icon: <Check className="h-6 w-6" />,
      content: (
        <div className="space-y-6 text-center">
          <div className="w-24 h-24 mx-auto bg-green-100 rounded-full flex items-center justify-center">
            <Check className="h-12 w-12 text-green-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Ready to Go!</h2>
            <p className="text-muted-foreground mt-2">
              Your workspace is configured. Here's what you can do next:
            </p>
          </div>
          <div className="grid gap-3 text-left">
            <div className="flex items-center gap-3 p-3 border rounded-lg">
              <FlaskConical className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">Create a Trial</p>
                <p className="text-sm text-muted-foreground">Set up your first breeding trial</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 border rounded-lg">
              <Database className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">Import Germplasm</p>
                <p className="text-sm text-muted-foreground">Add your genetic resources</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 border rounded-lg">
              <BookOpen className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">Explore Documentation</p>
                <p className="text-sm text-muted-foreground">Learn about all features</p>
              </div>
            </div>
          </div>
        </div>
      ),
    },
  ];

  const progress = ((currentStep + 1) / steps.length) * 100;
  const currentStepData = steps[currentStep];
  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  const handleNext = () => {
    if (isLastStep) {
      localStorage.setItem(STORAGE_KEY, 'true');
      // Save preferences
      localStorage.setItem('bijmantra-selected-divisions', JSON.stringify(selectedDivisions));
      localStorage.setItem('bijmantra-field-mode', JSON.stringify({ enabled: preferences.fieldMode }));
      onComplete();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setCurrentStep(prev => Math.max(0, prev - 1));
  };

  const handleSkip = () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    onSkip?.();
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <CardHeader className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-4 top-4"
            onClick={handleSkip}
          >
            <X className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg text-primary">
              {currentStepData.icon}
            </div>
            <div>
              <CardTitle>{currentStepData.title}</CardTitle>
              <CardDescription>{currentStepData.description}</CardDescription>
            </div>
          </div>
          <Progress value={progress} className="mt-4" />
          <p className="text-xs text-muted-foreground mt-1">
            Step {currentStep + 1} of {steps.length}
          </p>
        </CardHeader>

        <CardContent className="overflow-y-auto max-h-[50vh]">
          {currentStepData.content}
        </CardContent>

        <div className="p-6 border-t flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={handleBack}
            disabled={isFirstStep}
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            Back
          </Button>

          <div className="flex gap-1">
            {steps.map((_, i) => (
              <div
                key={i}
                className={cn(
                  'w-2 h-2 rounded-full transition-colors',
                  i === currentStep ? 'bg-primary' : 'bg-muted'
                )}
              />
            ))}
          </div>

          <Button onClick={handleNext}>
            {isLastStep ? (
              <>
                Get Started
                <Check className="h-4 w-4 ml-2" />
              </>
            ) : (
              <>
                Next
                <ChevronRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </Card>
    </div>
  );
}

// Hook to check if onboarding is complete
export function useOnboarding() {
  const [isComplete, setIsComplete] = useState(true);
  const [showWizard, setShowWizard] = useState(false);

  useEffect(() => {
    const complete = localStorage.getItem(STORAGE_KEY) === 'true';
    setIsComplete(complete);
    setShowWizard(!complete);
  }, []);

  const resetOnboarding = () => {
    localStorage.removeItem(STORAGE_KEY);
    setIsComplete(false);
    setShowWizard(true);
  };

  const completeOnboarding = () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    setIsComplete(true);
    setShowWizard(false);
  };

  return {
    isComplete,
    showWizard,
    setShowWizard,
    resetOnboarding,
    completeOnboarding,
  };
}
