/**
 * Training Hub - BijMantra App Training
 * 
 * Interactive tutorials and guides for learning to use BijMantra.
 * NOT academic coursework - this is app onboarding and feature training.
 * 
 * Progress is stored in LocalStorage (similar to Languages.tsx settings).
 */

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import {
  Play,
  CheckCircle,
  Clock,
  Rocket,
  Target,
  Zap,
  BookOpen,
  Video,
  MousePointer,
  Keyboard,
  Monitor,
  Smartphone,
  Database,
  BarChart3,
  Leaf,
  FlaskConical,
  Map,
  Settings,
  Users,
  ArrowRight,
  Star,
  Trophy,
  RefreshCw,
} from 'lucide-react';

interface Tutorial {
  id: string;
  title: string;
  description: string;
  module: string;
  type: 'video' | 'interactive' | 'walkthrough';
  duration: string;
  steps: number;
  completed?: boolean;
  progress?: number;
}

interface QuickStart {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  route: string;
  time: string;
}

interface FeatureGuide {
  id: string;
  module: string;
  icon: React.ElementType;
  features: string[];
  tutorials: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

// Storage key for tutorial progress
const PROGRESS_STORAGE_KEY = 'bijmantra-tutorial-progress';

interface TutorialProgress {
  [tutorialId: string]: {
    completed: boolean;
    progress: number;
    lastAccessed?: string;
  };
}

// Load progress from LocalStorage
const loadProgress = (): TutorialProgress => {
  try {
    const stored = localStorage.getItem(PROGRESS_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
};

// Save progress to LocalStorage
const saveProgress = (progress: TutorialProgress) => {
  try {
    localStorage.setItem(PROGRESS_STORAGE_KEY, JSON.stringify(progress));
  } catch (e) {
    console.error('Failed to save tutorial progress:', e);
  }
};

// BijMantra-specific tutorials (static content - app documentation)
const tutorialDefinitions: Omit<Tutorial, 'completed' | 'progress'>[] = [
  {
    id: 'tut-1',
    title: 'Getting Started with BijMantra',
    description: 'Your first 10 minutes: Navigate the dashboard, understand the layout, and customize your workspace.',
    module: 'Getting Started',
    type: 'interactive',
    duration: '10 min',
    steps: 8,
  },
  {
    id: 'tut-2',
    title: 'Creating Your First Breeding Program',
    description: 'Step-by-step guide to set up a breeding program, define objectives, and add germplasm.',
    module: 'Core Breeding',
    type: 'walkthrough',
    duration: '15 min',
    steps: 12,
  },
  {
    id: 'tut-3',
    title: 'Recording Field Observations',
    description: 'Learn to use the Field Book, collect data offline, and sync when back online.',
    module: 'Field Operations',
    type: 'interactive',
    duration: '12 min',
    steps: 10,
  },
  {
    id: 'tut-4',
    title: 'Designing Field Trials',
    description: 'Create RCBD, Alpha-Lattice, and Augmented designs with automatic randomization.',
    module: 'Trial Design',
    type: 'video',
    duration: '8 min',
    steps: 6,
  },
  {
    id: 'tut-5',
    title: 'Using the Selection Index Calculator',
    description: 'Multi-trait selection using Smith-Hazel, Desired Gains, and custom indices.',
    module: 'Analytics',
    type: 'interactive',
    duration: '10 min',
    steps: 8,
  },
  {
    id: 'tut-6',
    title: 'Genomic Data & Allele Matrix',
    description: 'Import genotype data, visualize allele matrices, and run diversity analysis.',
    module: 'Genomics',
    type: 'walkthrough',
    duration: '20 min',
    steps: 15,
  },
  {
    id: 'tut-7',
    title: 'Seed Lot Traceability',
    description: 'Track seed lots from harvest to dispatch with full chain of custody.',
    module: 'Seed Operations',
    type: 'interactive',
    duration: '12 min',
    steps: 10,
  },
  {
    id: 'tut-8',
    title: 'Quality Gate Scanner',
    description: 'Use barcode scanning for quality control and lot approval workflow.',
    module: 'Seed Operations',
    type: 'video',
    duration: '6 min',
    steps: 5,
  },
  {
    id: 'tut-9',
    title: 'Cross Prediction & Planning',
    description: 'Predict cross outcomes and plan crossing blocks using breeding values.',
    module: 'Analytics',
    type: 'walkthrough',
    duration: '15 min',
    steps: 12,
  },
  {
    id: 'tut-10',
    title: 'Keyboard Shortcuts & Power User Tips',
    description: 'Master keyboard navigation, command palette, and productivity shortcuts.',
    module: 'Power User',
    type: 'interactive',
    duration: '8 min',
    steps: 10,
  },
  {
    id: 'tut-11',
    title: 'Offline Mode & Data Sync',
    description: 'Work without internet, manage sync queue, and resolve conflicts.',
    module: 'Mobile & Offline',
    type: 'video',
    duration: '7 min',
    steps: 6,
  },
  {
    id: 'tut-12',
    title: 'Import/Export & Data Integration',
    description: 'Import from Excel, export to BrAPI, and integrate with external systems.',
    module: 'Data Management',
    type: 'walkthrough',
    duration: '10 min',
    steps: 8,
  },
];

const quickStarts: QuickStart[] = [
  { id: 'qs-1', title: 'Register Germplasm', description: 'Add new accessions to your collection', icon: Leaf, route: '/germplasm/new', time: '2 min' },
  { id: 'qs-2', title: 'Create a Trial', description: 'Set up a new field trial', icon: Map, route: '/trials/new', time: '3 min' },
  { id: 'qs-3', title: 'Record Observations', description: 'Collect phenotype data', icon: FlaskConical, route: '/fieldbook', time: '5 min' },
  { id: 'qs-4', title: 'Run Analysis', description: 'Analyze trial results', icon: BarChart3, route: '/statistics', time: '5 min' },
  { id: 'qs-5', title: 'Track Seed Lot', description: 'Check lot status and history', icon: Database, route: '/seed-operations/track', time: '1 min' },
  { id: 'qs-6', title: 'Configure Settings', description: 'Customize your workspace', icon: Settings, route: '/settings', time: '3 min' },
];

const featureGuides: FeatureGuide[] = [
  { id: 'fg-1', module: 'Plant Sciences', icon: Leaf, features: ['Programs', 'Trials', 'Germplasm', 'Crosses', 'Pedigree'], tutorials: 5, difficulty: 'beginner' },
  { id: 'fg-2', module: 'Field Operations', icon: Map, features: ['Field Book', 'Trial Design', 'Observations', 'Field Layout'], tutorials: 4, difficulty: 'beginner' },
  { id: 'fg-3', module: 'Genomics', icon: Database, features: ['Allele Matrix', 'Variants', 'Diversity', 'GWAS', 'Genomic Selection'], tutorials: 5, difficulty: 'advanced' },
  { id: 'fg-4', module: 'Seed Operations', icon: FlaskConical, features: ['Quality Gate', 'Traceability', 'Inventory', 'Dispatch'], tutorials: 4, difficulty: 'intermediate' },
  { id: 'fg-5', module: 'Analytics', icon: BarChart3, features: ['Selection Index', 'Breeding Values', 'G×E Analysis', 'Statistics'], tutorials: 4, difficulty: 'advanced' },
  { id: 'fg-6', module: 'Mobile & Offline', icon: Smartphone, features: ['Offline Mode', 'Data Sync', 'Field Mode', 'PWA Install'], tutorials: 3, difficulty: 'beginner' },
];

export function TrainingHub() {
  const [selectedModule, setSelectedModule] = useState<string | null>(null);
  const [tutorialProgress, setTutorialProgress] = useState<TutorialProgress>({});
  const { toast } = useToast();

  // Load progress from LocalStorage on mount
  useEffect(() => {
    setTutorialProgress(loadProgress());
  }, []);

  // Merge static definitions with user progress
  const tutorials: Tutorial[] = tutorialDefinitions.map(def => ({
    ...def,
    completed: tutorialProgress[def.id]?.completed || false,
    progress: tutorialProgress[def.id]?.progress || 0,
  }));

  const modules = [...new Set(tutorials.map(t => t.module))];
  const completedCount = tutorials.filter(t => t.completed).length;
  const inProgressCount = tutorials.filter(t => t.progress && t.progress > 0 && !t.completed).length;

  const filteredTutorials = selectedModule 
    ? tutorials.filter(t => t.module === selectedModule)
    : tutorials;

  // Handle starting/continuing a tutorial
  const handleStartTutorial = (tutorialId: string) => {
    const current = tutorialProgress[tutorialId] || { completed: false, progress: 0 };
    const newProgress = {
      ...tutorialProgress,
      [tutorialId]: {
        ...current,
        progress: current.progress || 10, // Start at 10% if new
        lastAccessed: new Date().toISOString(),
      },
    };
    setTutorialProgress(newProgress);
    saveProgress(newProgress);
    toast({ title: 'Tutorial Started', description: 'Progress will be saved automatically.' });
  };

  // Handle completing a tutorial
  const handleCompleteTutorial = (tutorialId: string) => {
    const newProgress = {
      ...tutorialProgress,
      [tutorialId]: {
        completed: true,
        progress: 100,
        lastAccessed: new Date().toISOString(),
      },
    };
    setTutorialProgress(newProgress);
    saveProgress(newProgress);
    toast({ title: 'Tutorial Completed! 🎉', description: 'Great job! Your progress has been saved.' });
  };

  // Handle resetting all progress
  const handleResetProgress = () => {
    setTutorialProgress({});
    saveProgress({});
    toast({ title: 'Progress Reset', description: 'All tutorial progress has been cleared.' });
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return <Video className="h-4 w-4" />;
      case 'interactive': return <MousePointer className="h-4 w-4" />;
      case 'walkthrough': return <BookOpen className="h-4 w-4" />;
      default: return <Play className="h-4 w-4" />;
    }
  };

  const getDifficultyColor = (diff: string) => {
    switch (diff) {
      case 'beginner': return 'bg-green-100 text-green-700';
      case 'intermediate': return 'bg-yellow-100 text-yellow-700';
      case 'advanced': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Rocket className="h-8 w-8 text-primary" />
            Learn BijMantra
          </h1>
          <p className="text-muted-foreground mt-1">
            Interactive tutorials to master every feature of the platform
          </p>
        </div>
        <Button variant="outline" onClick={handleResetProgress}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Reset Progress
        </Button>
      </div>

      {/* Progress Overview */}
      <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
        <CardContent className="py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="h-16 w-16 rounded-full bg-primary/20 flex items-center justify-center">
                <Trophy className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Your Learning Progress</h3>
                <p className="text-sm text-muted-foreground">
                  {completedCount} of {tutorials.length} tutorials completed
                </p>
                <Progress value={(completedCount / tutorials.length) * 100} className="h-2 w-48 mt-2" />
              </div>
            </div>
            <div className="flex gap-8 text-center">
              <div>
                <p className="text-3xl font-bold text-green-600">{completedCount}</p>
                <p className="text-xs text-muted-foreground">Completed</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-yellow-600">{inProgressCount}</p>
                <p className="text-xs text-muted-foreground">In Progress</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-gray-400">{tutorials.length - completedCount - inProgressCount}</p>
                <p className="text-xs text-muted-foreground">Not Started</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="tutorials">
        <TabsList>
          <TabsTrigger value="tutorials">Tutorials</TabsTrigger>
          <TabsTrigger value="quick-start">Quick Start</TabsTrigger>
          <TabsTrigger value="by-module">By Module</TabsTrigger>
          <TabsTrigger value="shortcuts">Shortcuts</TabsTrigger>
        </TabsList>

        {/* Tutorials Tab */}
        <TabsContent value="tutorials" className="space-y-4 mt-4">
          {/* Module Filter */}
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={selectedModule === null ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedModule(null)}
            >
              All
            </Button>
            {modules.map(mod => (
              <Button
                key={mod}
                variant={selectedModule === mod ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedModule(mod)}
              >
                {mod}
              </Button>
            ))}
          </div>

          {/* Tutorial List */}
          <div className="grid gap-4">
            {filteredTutorials.map(tutorial => (
              <Card key={tutorial.id} className={tutorial.completed ? 'border-green-200 bg-green-50/50' : ''}>
                <CardContent className="py-4">
                  <div className="flex items-center gap-4">
                    <div className={`h-12 w-12 rounded-lg flex items-center justify-center ${
                      tutorial.completed ? 'bg-green-100' : tutorial.progress ? 'bg-yellow-100' : 'bg-gray-100'
                    }`}>
                      {tutorial.completed ? (
                        <CheckCircle className="h-6 w-6 text-green-600" />
                      ) : (
                        getTypeIcon(tutorial.type)
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium">{tutorial.title}</h3>
                        <Badge variant="outline" className="text-xs">{tutorial.module}</Badge>
                        <Badge variant="secondary" className="text-xs capitalize">{tutorial.type}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{tutorial.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {tutorial.duration}
                        </span>
                        <span>{tutorial.steps} steps</span>
                      </div>
                      {tutorial.progress && !tutorial.completed && (
                        <div className="mt-2">
                          <Progress value={tutorial.progress} className="h-1.5 w-48" />
                          <span className="text-xs text-muted-foreground">{tutorial.progress}% complete</span>
                        </div>
                      )}
                    </div>
                    <Button 
                      variant={tutorial.completed ? 'outline' : 'default'}
                      onClick={() => tutorial.completed 
                        ? handleStartTutorial(tutorial.id) 
                        : tutorial.progress && tutorial.progress > 0
                          ? handleCompleteTutorial(tutorial.id)
                          : handleStartTutorial(tutorial.id)
                      }
                    >
                      {tutorial.completed ? (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Redo
                        </>
                      ) : tutorial.progress && tutorial.progress > 0 ? (
                        <>
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Complete
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-2" />
                          Start
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Quick Start Tab */}
        <TabsContent value="quick-start" className="mt-4">
          <div className="mb-4">
            <h3 className="text-lg font-semibold">Jump Right In</h3>
            <p className="text-sm text-muted-foreground">Quick tasks to get you started immediately</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {quickStarts.map(qs => {
              const QsIcon = qs.icon as React.ComponentType<{ className?: string }>;
              return (
              <Card key={qs.id} className="hover:border-primary/50 transition-colors cursor-pointer">
                <CardContent className="py-4">
                  <div className="flex items-start gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <QsIcon className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">{qs.title}</h4>
                      <p className="text-sm text-muted-foreground">{qs.description}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {qs.time}
                        </span>
                        <Button variant="ghost" size="sm">
                          Go <ArrowRight className="h-3 w-3 ml-1" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
            })}
          </div>
        </TabsContent>

        {/* By Module Tab */}
        <TabsContent value="by-module" className="mt-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featureGuides.map(guide => {
              const GuideIcon = guide.icon as React.ComponentType<{ className?: string }>;
              return (
              <Card key={guide.id}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <GuideIcon className="h-5 w-5 text-primary" />
                    </div>
                    <Badge variant="outline" className={getDifficultyColor(guide.difficulty)}>{guide.difficulty}</Badge>
                  </div>
                  <CardTitle className="text-lg mt-2">{guide.module}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {guide.features.map(f => (
                      <Badge key={f} variant="outline" className="text-xs">{f}</Badge>
                    ))}
                  </div>
                  <p className="text-sm text-muted-foreground">{guide.tutorials} tutorials available</p>
                  <Button className="w-full mt-3" variant="outline">
                    Explore Module
                  </Button>
                </CardContent>
              </Card>
            );
            })}
          </div>
        </TabsContent>

        {/* Shortcuts Tab */}
        <TabsContent value="shortcuts" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Keyboard className="h-5 w-5" />
                Essential Keyboard Shortcuts
              </CardTitle>
              <CardDescription>Master these to work faster in BijMantra</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Navigation</h4>
                  <div className="space-y-2">
                    {[
                      { keys: '⌘ K', action: 'Open Command Palette' },
                      { keys: '⌘ /', action: 'Show Keyboard Shortcuts' },
                      { keys: 'G then D', action: 'Go to Dashboard' },
                      { keys: 'G then P', action: 'Go to Programs' },
                      { keys: 'G then T', action: 'Go to Trials' },
                      { keys: 'G then G', action: 'Go to Germplasm' },
                    ].map(s => (
                      <div key={s.keys} className="flex items-center justify-between py-1">
                        <span className="text-sm">{s.action}</span>
                        <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono">{s.keys}</kbd>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-3">Actions</h4>
                  <div className="space-y-2">
                    {[
                      { keys: 'N', action: 'New Item (context-aware)' },
                      { keys: 'E', action: 'Edit Selected' },
                      { keys: '⌘ S', action: 'Save' },
                      { keys: '⌘ Enter', action: 'Submit Form' },
                      { keys: 'Esc', action: 'Close Dialog / Cancel' },
                      { keys: '?', action: 'Show Help' },
                    ].map(s => (
                      <div key={s.keys} className="flex items-center justify-between py-1">
                        <span className="text-sm">{s.action}</span>
                        <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono">{s.keys}</kbd>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="mt-6 p-4 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  <Zap className="h-4 w-4 inline mr-1 text-yellow-500" />
                  <strong>Pro tip:</strong> Press <kbd className="px-1.5 py-0.5 bg-background rounded text-xs font-mono">⌘ K</kbd> anywhere to open the Command Palette and search for any action.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default TrainingHub;
