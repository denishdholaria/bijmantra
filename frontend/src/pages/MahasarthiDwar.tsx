/**
 * MahasarthiDwar - The Entry Gate
 * 
 * Full-page workspace selector with hero carousel design.
 * Features:
 * - Large hero card with swipeable workspaces
 * - Dot navigation indicators
 * - Quick-access pills below
 * - Smooth transitions and animations
 * - Full keyboard and touch support
 * - MyWorkspace custom workspaces section
 * - Auto-advance carousel on inactivity
 * - Error boundary for resilience
 * - Loading state for backend sync
 * 
 * @see docs/gupt/archieve/GATEWAY-WORKSPACE.md for specification
 * @see docs/gupt/archieve/MyWorkspace.md for custom workspace spec
 */

import { useState, useEffect, useRef, useCallback, Component, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Wheat, 
  Factory, 
  Microscope, 
  Building2, 
  Settings,
  ArrowRight,
  ArrowLeft,
  Star,
  Check,
  Sparkles,
  ChevronRight,
  Plus,
  Palette,
  AlertTriangle,
  RefreshCw,
  Loader2,
  Pause,
  Play,
  MoreVertical,
  Copy,
  Trash2,
  Folder,
  CloudSun,
  Droplets,
  Mountain,
  Leaf,
} from 'lucide-react';
import { getWorkspaceIcon } from '@/lib/workspace-icons';

// ============================================================================
// Error Boundary Component
// ============================================================================

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

class GatewayErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Gateway Error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      return (
        <div className="min-h-screen bg-prakruti-dhool-50 dark:bg-prakruti-dhool-900 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white dark:bg-prakruti-dhool-800 rounded-2xl shadow-xl p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-xl font-semibold text-prakruti-dhool-800 dark:text-prakruti-dhool-100 mb-2">
              Something went wrong
            </h2>
            <p className="text-prakruti-dhool-600 dark:text-prakruti-dhool-400 mb-6">
              The workspace gateway encountered an error. Please try again.
            </p>
            <button
              onClick={this.handleRetry}
              className="inline-flex items-center gap-2 px-6 py-3 bg-prakruti-patta text-white rounded-xl font-medium hover:bg-prakruti-patta-dark transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
            {this.state.error && (
              <details className="mt-4 text-left">
                <summary className="text-sm text-prakruti-dhool-500 cursor-pointer hover:text-prakruti-dhool-700">
                  Technical details
                </summary>
                <pre className="mt-2 p-3 bg-prakruti-dhool-100 dark:bg-prakruti-dhool-900 rounded-lg text-xs overflow-auto">
                  {this.state.error.message}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// ============================================================================
// Auto-Advance Configuration
// ============================================================================

const AUTO_ADVANCE_INTERVAL = 8000; // 8 seconds between auto-advances
const INACTIVITY_THRESHOLD = 5000; // 5 seconds of inactivity before auto-advance starts
import { useWorkspaceStore, useAllWorkspaces } from '@/store/workspaceStore';
import { useCustomWorkspaceStore, useCustomWorkspaces, useCanCreateWorkspace } from '@/store/customWorkspaceStore';
import { CreateWorkspaceWizard } from '@/components/workspace/CreateWorkspaceWizard';
import { FutureRoadmapSection } from '@/components/workspace/FutureRoadmapSection';
import { WORKSPACE_COLORS } from '@/types/customWorkspace';
import type { WorkspaceId } from '@/types/workspace';
import type { CustomWorkspace } from '@/types/customWorkspace';
import { cn } from '@/lib/utils';
import { 
  WORKSPACE_ICONS, 
  WORKSPACE_GRADIENTS, 
  WORKSPACE_PILL_COLORS, 
  WORKSPACE_RING_COLORS, 
  WORKSPACE_EMOJIS, 
  WORKSPACE_FEATURES 
} from '@/lib/workspace-config';


export function MahasarthiDwar() {
  const navigate = useNavigate();
  const workspaces = useAllWorkspaces();
  const { 
    setActiveWorkspace, 
    setDefaultWorkspace, 
    preferences,
    dismissGateway 
  } = useWorkspaceStore();
  
  // Custom workspaces
  const customWorkspaces = useCustomWorkspaces();
  const canCreateWorkspace = useCanCreateWorkspace();
  const { setActiveCustomWorkspace, clearActiveCustomWorkspace } = useCustomWorkspaceStore();
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  
  const [activeIndex, setActiveIndex] = useState(0);
  const [setAsDefault, setSetAsDefault] = useState(false);
  const [isEntering, setIsEntering] = useState(false);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [showMyWorkspaces, setShowMyWorkspaces] = useState(customWorkspaces.length > 0);
  
  // Auto-advance state
  const [isAutoAdvancing, setIsAutoAdvancing] = useState(true);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [lastInteraction, setLastInteraction] = useState(Date.now());
  const autoAdvanceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inactivityTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Backend sync state
  const [isSyncing, setIsSyncing] = useState(false);
  
  const heroRef = useRef<HTMLDivElement>(null);

  // Check if user has a default workspace and redirect
  useEffect(() => {
    if (preferences.defaultWorkspace && !preferences.showGatewayOnLogin) {
      const workspace = workspaces.find(w => w.id === preferences.defaultWorkspace);
      if (workspace) {
        setActiveWorkspace(preferences.defaultWorkspace);
        navigate(workspace.landingRoute, { replace: true });
      }
    }
  }, [preferences.defaultWorkspace, preferences.showGatewayOnLogin, workspaces, setActiveWorkspace, navigate]);

  const activeWorkspace = workspaces[activeIndex];
  const Icon = WORKSPACE_ICONS[activeWorkspace.id];

  // Track user interaction to pause auto-advance
  const recordInteraction = useCallback(() => {
    setLastInteraction(Date.now());
    setIsAutoAdvancing(false);
    
    // Clear existing inactivity timer
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
    }
    
    // Start new inactivity timer
    inactivityTimerRef.current = setTimeout(() => {
      setIsAutoAdvancing(true);
    }, INACTIVITY_THRESHOLD);
  }, []);

  // Auto-advance effect
  useEffect(() => {
    if (!isAutoAdvancing || isEntering) {
      if (autoAdvanceTimerRef.current) {
        clearInterval(autoAdvanceTimerRef.current);
        autoAdvanceTimerRef.current = null;
      }
      return;
    }

    autoAdvanceTimerRef.current = setInterval(() => {
      setActiveIndex(prev => (prev + 1) % workspaces.length);
    }, AUTO_ADVANCE_INTERVAL);

    return () => {
      if (autoAdvanceTimerRef.current) {
        clearInterval(autoAdvanceTimerRef.current);
      }
    };
  }, [isAutoAdvancing, isEntering, workspaces.length]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (autoAdvanceTimerRef.current) clearInterval(autoAdvanceTimerRef.current);
      if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
    };
  }, []);

  // Navigation functions
  const goToNext = useCallback(() => {
    recordInteraction();
    setActiveIndex(prev => (prev + 1) % workspaces.length);
  }, [workspaces.length, recordInteraction]);

  const goToPrev = useCallback(() => {
    recordInteraction();
    setActiveIndex(prev => (prev - 1 + workspaces.length) % workspaces.length);
  }, [workspaces.length, recordInteraction]);

  const goToIndex = useCallback((index: number) => {
    recordInteraction();
    setActiveIndex(index);
  }, [recordInteraction]);

  // Handle entering a workspace - defined before useEffect that uses it
  const handleEnterWorkspace = useCallback(() => {
    if (isEntering) return;
    
    setIsEntering(true);
    recordInteraction();
    
    // Clear any active custom workspace when entering a system workspace
    clearActiveCustomWorkspace();
    
    if (setAsDefault) {
      setIsSyncing(true);
      setDefaultWorkspace(activeWorkspace.id);
      // Simulate backend sync delay for UX feedback
      setTimeout(() => setIsSyncing(false), 300);
    }
    
    setActiveWorkspace(activeWorkspace.id);
    dismissGateway();
    
    setTimeout(() => {
      navigate(activeWorkspace.landingRoute, { replace: true });
    }, 500);
  }, [isEntering, activeWorkspace, setAsDefault, clearActiveCustomWorkspace, setDefaultWorkspace, setActiveWorkspace, dismissGateway, navigate, recordInteraction]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          e.preventDefault();
          goToNext();
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          e.preventDefault();
          goToPrev();
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          handleEnterWorkspace();
          break;
        case '1':
        case '2':
        case '3':
        case '4':
        case '5': {
          const index = parseInt(e.key) - 1;
          if (index < workspaces.length) {
            e.preventDefault();
            goToIndex(index);
          }
          break;
        }
        case 'd':
        case 'D':
          e.preventDefault();
          setSetAsDefault(prev => !prev);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToNext, goToPrev, goToIndex, workspaces.length, handleEnterWorkspace]);

  // Touch handlers for swipe
  const minSwipeDistance = 50;

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;
    
    if (isLeftSwipe) goToNext();
    if (isRightSwipe) goToPrev();
  };

  // Handle entering a custom workspace
  const handleEnterCustomWorkspace = (customWorkspace: CustomWorkspace) => {
    if (isEntering) return;
    
    setIsEntering(true);
    recordInteraction();
    setActiveCustomWorkspace(customWorkspace.id);
    dismissGateway();
    
    // Navigate to dashboard (custom workspaces don't have a specific landing)
    setTimeout(() => {
      navigate('/dashboard', { replace: true });
    }, 500);
  };

  // Toggle auto-advance manually
  const toggleAutoAdvance = () => {
    if (isAutoAdvancing) {
      setIsAutoAdvancing(false);
      if (inactivityTimerRef.current) {
        clearTimeout(inactivityTimerRef.current);
      }
    } else {
      setIsAutoAdvancing(true);
    }
  };

  // Handle custom workspace created
  const handleWorkspaceCreated = (workspaceId: string) => {
    setShowMyWorkspaces(true);
  };

  return (
    <div 
      className={cn(
        "min-h-screen bg-prakruti-dhool-50 dark:bg-prakruti-dhool-900 flex flex-col",
        isEntering && "animate-fade-out"
      )}
    >
      {/* Minimal Header */}
      <header className="pt-8 pb-4 text-center">
        <div className="inline-flex items-center gap-2 text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-400">
          <span className="text-lg">🌱</span>
          <span className="font-medium">Bijmantra</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 pb-8">
        {/* Hero Card */}
        <div 
          ref={heroRef}
          className="w-full max-w-2xl"
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
        >
          {/* Card Container */}
          <div 
            className={cn(
              "relative overflow-hidden rounded-3xl shadow-2xl",
              "transition-all duration-500 ease-out",
              `bg-gradient-to-br ${WORKSPACE_GRADIENTS[activeWorkspace.id]}`
            )}
          >
            {/* Decorative Elements */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div className="absolute -top-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
              <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-black/10 rounded-full blur-3xl" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[200px] opacity-5 select-none">
                {WORKSPACE_EMOJIS[activeWorkspace.id]}
              </div>
            </div>

            {/* Navigation Arrows */}
            <button
              onClick={goToPrev}
              className="absolute left-4 top-1/2 -translate-y-1/2 z-20 p-2 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-sm transition-all opacity-0 hover:opacity-100 focus:opacity-100 group-hover:opacity-100"
              aria-label="Previous workspace"
            >
              <ArrowLeft className="w-5 h-5 text-white" />
            </button>
            <button
              onClick={goToNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 z-20 p-2 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-sm transition-all opacity-0 hover:opacity-100 focus:opacity-100"
              aria-label="Next workspace"
            >
              <ArrowRight className="w-5 h-5 text-white" />
            </button>

            {/* Card Content */}
            <div className="relative z-10 p-8 md:p-12 text-white">
              {/* Icon & Badge Row */}
              <div className="flex items-start justify-between mb-6">
                <div className="p-4 bg-white/20 backdrop-blur-sm rounded-2xl">
                  <Icon className="w-10 h-10" />
                </div>
                {activeWorkspace.isBrAPIAligned && (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium">
                    <Sparkles className="w-4 h-4" />
                    <span>BrAPI</span>
                  </div>
                )}
              </div>

              {/* Title & Description */}
              <h1 className="text-4xl md:text-5xl font-bold mb-3 tracking-tight">
                {activeWorkspace.name}
              </h1>
              <p className="text-lg md:text-xl text-white/80 mb-8 max-w-lg">
                {activeWorkspace.longDescription || activeWorkspace.description}
              </p>

              {/* Feature Pills */}
              <div className="flex flex-wrap gap-2 mb-8">
                {WORKSPACE_FEATURES[activeWorkspace.id].map((feature, i) => (
                  <span 
                    key={i}
                    className="px-3 py-1 bg-white/15 backdrop-blur-sm rounded-full text-sm"
                  >
                    {feature}
                  </span>
                ))}
              </div>

              {/* Stats Row */}
              <div className="flex items-center gap-6 text-sm text-white/70">
                <span>{activeWorkspace.pageCount} pages</span>
                <span>•</span>
                <span>{activeWorkspace.targetUsers[0]}</span>
              </div>
            </div>

            {/* Enter Button - Inside Card */}
            <div className="relative z-10 px-8 md:px-12 pb-8 md:pb-12">
              <button
                onClick={handleEnterWorkspace}
                disabled={isEntering}
                className={cn(
                  "w-full py-4 px-6 rounded-2xl font-semibold text-lg",
                  "flex items-center justify-center gap-3",
                  "shadow-lg hover:shadow-xl transition-all",
                  "hover:scale-[1.02] active:scale-[0.98]",
                  "focus:outline-none focus:ring-4 focus:ring-white/50",
                  isEntering && "opacity-75 cursor-not-allowed"
                )}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  color: '#111827', // gray-900
                }}
              >
                {isEntering ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Opening...</span>
                  </>
                ) : (
                  <>
                    <span>Get Started</span>
                    <ChevronRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Dot Indicators */}
          <div className="flex items-center justify-center gap-2 mt-6">
            {workspaces.map((workspace, index) => (
              <button
                key={workspace.id}
                onClick={() => goToIndex(index)}
                className={cn(
                  "transition-all duration-300 rounded-full",
                  index === activeIndex 
                    ? "w-8 h-2 bg-prakruti-dhool-800 dark:bg-prakruti-dhool-100" 
                    : "w-2 h-2 bg-prakruti-dhool-300 dark:bg-prakruti-dhool-600 hover:bg-prakruti-dhool-400 dark:hover:bg-prakruti-dhool-500"
                )}
                aria-label={`Go to ${workspace.name}`}
                aria-current={index === activeIndex ? 'true' : 'false'}
              />
            ))}
            
            {/* Auto-advance toggle */}
            <button
              onClick={toggleAutoAdvance}
              className={cn(
                "ml-3 p-1.5 rounded-full transition-all",
                isAutoAdvancing 
                  ? "bg-prakruti-patta/20 text-prakruti-patta hover:bg-prakruti-patta/30" 
                  : "bg-prakruti-dhool-200 dark:bg-prakruti-dhool-700 text-prakruti-dhool-500 hover:bg-prakruti-dhool-300 dark:hover:bg-prakruti-dhool-600"
              )}
              aria-label={isAutoAdvancing ? 'Pause auto-advance' : 'Resume auto-advance'}
              title={isAutoAdvancing ? 'Auto-advancing (click to pause)' : 'Paused (click to resume)'}
            >
              {isAutoAdvancing ? (
                <Pause className="w-3 h-3" />
              ) : (
                <Play className="w-3 h-3" />
              )}
            </button>
          </div>
        </div>

        {/* Quick Access Pills */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
          {workspaces.map((workspace, index) => {
            const PillIcon = WORKSPACE_ICONS[workspace.id];
            const isActive = index === activeIndex;
            
            return (
              <button
                key={workspace.id}
                onClick={() => goToIndex(index)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all",
                  WORKSPACE_PILL_COLORS[workspace.id],
                  isActive && `ring-2 ${WORKSPACE_RING_COLORS[workspace.id]}`
                )}
              >
                <PillIcon className="w-4 h-4" />
                <span className="hidden sm:inline">{workspace.name}</span>
              </button>
            );
          })}
        </div>

        {/* Set as Default Option */}
        <label className="mt-8 flex items-center gap-3 cursor-pointer group">
          <div className="relative">
            <input
              type="checkbox"
              checked={setAsDefault}
              onChange={(e) => {
                recordInteraction();
                setSetAsDefault(e.target.checked);
              }}
              className="sr-only peer"
            />
            <div className={cn(
              "w-5 h-5 rounded-md border-2 transition-all flex items-center justify-center",
              setAsDefault 
                ? "border-prakruti-patta bg-prakruti-patta" 
                : "border-prakruti-dhool-300 dark:border-prakruti-dhool-600 group-hover:border-prakruti-dhool-400"
            )}>
              {setAsDefault && <Check className="w-3 h-3 text-white" />}
            </div>
          </div>
          <span className="text-sm text-prakruti-dhool-600 dark:text-prakruti-dhool-400 flex items-center gap-2">
            <Star className="w-4 h-4" />
            Set as default workspace
            {isSyncing && (
              <Loader2 className="w-3 h-3 animate-spin text-prakruti-patta" />
            )}
          </span>
        </label>

        {/* Keyboard Hints */}
        <div className="mt-6 flex items-center justify-center gap-4 text-xs text-prakruti-dhool-400 dark:text-prakruti-dhool-500">
          <span className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 bg-prakruti-dhool-200 dark:bg-prakruti-dhool-800 rounded font-mono">←</kbd>
            <kbd className="px-1.5 py-0.5 bg-prakruti-dhool-200 dark:bg-prakruti-dhool-800 rounded font-mono">→</kbd>
            <span className="ml-1">navigate</span>
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 bg-prakruti-dhool-200 dark:bg-prakruti-dhool-800 rounded font-mono">Enter</kbd>
            <span className="ml-1">select</span>
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 bg-prakruti-dhool-200 dark:bg-prakruti-dhool-800 rounded font-mono">D</kbd>
            <span className="ml-1">default</span>
          </span>
        </div>

        {/* My Workspaces Section */}
        {(customWorkspaces.length > 0 || canCreateWorkspace) && (
          <MyWorkspacesSection
            customWorkspaces={customWorkspaces}
            canCreate={canCreateWorkspace}
            onEnter={handleEnterCustomWorkspace}
            onCreate={() => setShowCreateWizard(true)}
            isEntering={isEntering}
          />
        )}

        {/* Future Roadmap Section */}
        <div className="w-full max-w-4xl mt-12 px-4">
          <FutureRoadmapSection 
            defaultCollapsed={true}
            maxVisible={6}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 text-center text-sm text-prakruti-dhool-400 dark:text-prakruti-dhool-500">
        <p>🌾 Thank you to all those who work in acres, not in hours.</p>
      </footer>

      {/* Create Workspace Wizard */}
      <CreateWorkspaceWizard
        open={showCreateWizard}
        onOpenChange={setShowCreateWizard}
        onCreated={handleWorkspaceCreated}
      />
    </div>
  );
}

/**
 * MyWorkspaces Section Component
 * Displays user's custom workspaces with create option
 */
interface MyWorkspacesSectionProps {
  customWorkspaces: CustomWorkspace[];
  canCreate: boolean;
  onEnter: (workspace: CustomWorkspace) => void;
  onCreate: () => void;
  isEntering: boolean;
}

function MyWorkspacesSection({ 
  customWorkspaces, 
  canCreate, 
  onEnter, 
  onCreate,
  isEntering 
}: MyWorkspacesSectionProps) {
  const { deleteWorkspace, duplicateWorkspace } = useCustomWorkspaceStore();
  
  if (customWorkspaces.length === 0 && !canCreate) {
    return null;
  }
  
  return (
    <div className="w-full max-w-2xl mt-12">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Palette className="w-5 h-5 text-prakruti-dhool-500" />
          <h2 className="text-lg font-semibold text-prakruti-dhool-700 dark:text-prakruti-dhool-300">
            My Workspaces
          </h2>
        </div>
        {canCreate && (
          <button
            onClick={onCreate}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-prakruti-patta hover:text-prakruti-patta-dark dark:text-prakruti-patta-light transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create New
          </button>
        )}
      </div>
      
      {/* Custom Workspace Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {customWorkspaces.map(workspace => (
          <CustomWorkspaceCard
            key={workspace.id}
            workspace={workspace}
            onEnter={() => onEnter(workspace)}
            onDuplicate={() => duplicateWorkspace(workspace.id)}
            onDelete={() => deleteWorkspace(workspace.id)}
            disabled={isEntering}
          />
        ))}
        
        {/* Create New Card (if no workspaces yet) */}
        {customWorkspaces.length === 0 && canCreate && (
          <button
            onClick={onCreate}
            className="flex items-center gap-3 p-4 rounded-xl border-2 border-dashed border-prakruti-dhool-300 dark:border-prakruti-dhool-700 hover:border-prakruti-patta dark:hover:border-prakruti-patta-light hover:bg-prakruti-dhool-100/50 dark:hover:bg-prakruti-dhool-800/50 transition-all"
          >
            <div className="w-12 h-12 rounded-xl bg-prakruti-dhool-200 dark:bg-prakruti-dhool-700 flex items-center justify-center">
              <Plus className="w-6 h-6 text-prakruti-dhool-500" />
            </div>
            <div className="text-left">
              <p className="font-medium text-prakruti-dhool-700 dark:text-prakruti-dhool-300">Create Custom Workspace</p>
              <p className="text-sm text-prakruti-dhool-500">Select your favorite pages</p>
            </div>
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Custom Workspace Card Component
 */
interface CustomWorkspaceCardProps {
  workspace: CustomWorkspace;
  onEnter: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  disabled?: boolean;
}

function CustomWorkspaceCard({ 
  workspace, 
  onEnter, 
  onDuplicate, 
  onDelete,
  disabled 
}: CustomWorkspaceCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const colorConfig = WORKSPACE_COLORS[workspace.color];
  const IconComponent = getWorkspaceIcon(workspace.icon, Folder);
  
  return (
    <div
      className={cn(
        "relative group flex items-center gap-3 p-4 rounded-xl border transition-all cursor-pointer",
        colorConfig.bg,
        colorConfig.border,
        "hover:shadow-md",
        disabled && "opacity-50 cursor-not-allowed"
      )}
      onClick={disabled ? undefined : onEnter}
    >
      {/* Icon */}
      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorConfig.gradient} flex items-center justify-center shadow-md flex-shrink-0`}>
        <IconComponent className="w-6 h-6 text-white" />
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-prakruti-dhool-800 dark:text-prakruti-dhool-100 truncate">
          {workspace.name}
        </h3>
        <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-400">
          {workspace.pageIds.length} pages
        </p>
      </div>
      
      {/* Menu Button */}
      <div className="relative">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowMenu(!showMenu);
          }}
          className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-prakruti-dhool-200 dark:hover:bg-prakruti-dhool-700 transition-all"
        >
          <MoreVertical className="w-4 h-4 text-prakruti-dhool-500" />
        </button>
        
        {/* Dropdown Menu */}
        {showMenu && (
          <>
            <div 
              className="fixed inset-0 z-10" 
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(false);
              }} 
            />
            <div className="absolute right-0 top-full mt-1 z-20 bg-white dark:bg-prakruti-dhool-800 rounded-lg shadow-lg border border-prakruti-dhool-200 dark:border-prakruti-dhool-700 py-1 min-w-[120px]">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenu(false);
                  onDuplicate();
                }}
                className="w-full px-3 py-2 text-left text-sm hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-700 flex items-center gap-2"
              >
                <Copy className="w-4 h-4" />
                Duplicate
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenu(false);
                  onDelete();
                }}
                className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </>
        )}
      </div>
      
      {/* Enter Arrow */}
      <ChevronRight className="w-5 h-5 text-prakruti-dhool-400 opacity-0 group-hover:opacity-100 transition-opacity" />
    </div>
  );
}

export default MahasarthiDwar;

/**
 * Wrapped Gateway with Error Boundary
 * Use this as the default export for route registration
 */
export function MahasarthiDwarWithErrorBoundary() {
  return (
    <GatewayErrorBoundary>
      <MahasarthiDwar />
    </GatewayErrorBoundary>
  );
}
