/**
 * Workspace Gateway Page - Apple/Google Inspired Redesign
 * 
 * Full-page workspace selector with hero carousel design.
 * Features:
 * - Large hero card with swipeable workspaces
 * - Dot navigation indicators
 * - Quick-access pills below
 * - Smooth transitions and animations
 * - Full keyboard and touch support
 * 
 * @see docs/confidential/archieve/GATEWAY-WORKSPACE.md for specification
 */

import { useState, useEffect, useRef, useCallback } from 'react';
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
  ChevronRight
} from 'lucide-react';
import { useWorkspaceStore, useAllWorkspaces } from '@/store/workspaceStore';
import type { WorkspaceId } from '@/types/workspace';
import { cn } from '@/lib/utils';

// Icon mapping for workspaces
const workspaceIcons: Record<WorkspaceId, React.ElementType> = {
  breeding: Wheat,
  'seed-ops': Factory,
  research: Microscope,
  genebank: Building2,
  admin: Settings,
};

// Gradient backgrounds for hero cards - Prakruti Design System
const heroGradients: Record<WorkspaceId, string> = {
  breeding: 'from-prakruti-patta via-prakruti-patta-light to-emerald-600',      // Leaf green
  'seed-ops': 'from-prakruti-neela via-prakruti-neela-light to-blue-600',       // Sky blue
  research: 'from-purple-600 via-fuchsia-500 to-pink-500',                       // Innovation purple
  genebank: 'from-prakruti-sona via-prakruti-sona-light to-amber-500',          // Gold harvest
  admin: 'from-prakruti-mitti via-prakruti-mitti-light to-prakruti-dhool-600',  // Earth tones
};

// Accent colors for pills - Prakruti Design System
const pillColors: Record<WorkspaceId, string> = {
  breeding: 'bg-prakruti-patta-pale text-prakruti-patta dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light hover:bg-prakruti-patta-100 dark:hover:bg-prakruti-patta/30',
  'seed-ops': 'bg-prakruti-neela-pale text-prakruti-neela dark:bg-prakruti-neela/20 dark:text-prakruti-neela-light hover:bg-prakruti-neela-100 dark:hover:bg-prakruti-neela/30',
  research: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/60',
  genebank: 'bg-prakruti-sona-pale text-prakruti-sona-dark dark:bg-prakruti-sona/20 dark:text-prakruti-sona-light hover:bg-prakruti-sona-100 dark:hover:bg-prakruti-sona/30',
  admin: 'bg-prakruti-mitti-50 text-prakruti-mitti-dark dark:bg-prakruti-mitti/20 dark:text-prakruti-mitti-light hover:bg-prakruti-mitti-100 dark:hover:bg-prakruti-mitti/30',
};

// Ring colors for active pills - Prakruti Design System
const pillActiveRing: Record<WorkspaceId, string> = {
  breeding: 'ring-prakruti-patta',
  'seed-ops': 'ring-prakruti-neela',
  research: 'ring-purple-500',
  genebank: 'ring-prakruti-sona',
  admin: 'ring-prakruti-mitti',
};

// Decorative emojis for each workspace
const workspaceEmojis: Record<WorkspaceId, string> = {
  breeding: '🌾',
  'seed-ops': '📦',
  research: '🔬',
  genebank: '🏛️',
  admin: '⚙️',
};

// Feature highlights for each workspace
const workspaceFeatures: Record<WorkspaceId, string[]> = {
  breeding: ['BrAPI v2.1 Compliant', 'Genomic Selection', 'Cross Prediction', 'Pedigree Tracking'],
  'seed-ops': ['Quality Testing', 'Inventory Management', 'Dispatch Logistics', 'DUS Testing'],
  research: ['AI Plant Vision', 'WASM Analytics', 'Space Agriculture', 'Advanced Tools'],
  genebank: ['Vault Management', 'Conservation', 'Germplasm Exchange', 'Environmental Monitoring'],
  admin: ['User Management', 'System Health', 'Integrations', 'Audit Logs'],
};

export function WorkspaceGateway() {
  const navigate = useNavigate();
  const workspaces = useAllWorkspaces();
  const { 
    setActiveWorkspace, 
    setDefaultWorkspace, 
    preferences,
    dismissGateway 
  } = useWorkspaceStore();
  
  const [activeIndex, setActiveIndex] = useState(0);
  const [setAsDefault, setSetAsDefault] = useState(false);
  const [isEntering, setIsEntering] = useState(false);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
  
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
  const Icon = workspaceIcons[activeWorkspace.id];

  // Navigation functions
  const goToNext = useCallback(() => {
    setActiveIndex(prev => (prev + 1) % workspaces.length);
  }, [workspaces.length]);

  const goToPrev = useCallback(() => {
    setActiveIndex(prev => (prev - 1 + workspaces.length) % workspaces.length);
  }, [workspaces.length]);

  const goToIndex = useCallback((index: number) => {
    setActiveIndex(index);
  }, []);

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
        case '5':
          const index = parseInt(e.key) - 1;
          if (index < workspaces.length) {
            e.preventDefault();
            goToIndex(index);
          }
          break;
        case 'd':
        case 'D':
          e.preventDefault();
          setSetAsDefault(prev => !prev);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToNext, goToPrev, goToIndex, workspaces.length]);

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

  const handleEnterWorkspace = () => {
    if (isEntering) return;
    
    setIsEntering(true);
    
    if (setAsDefault) {
      setDefaultWorkspace(activeWorkspace.id);
    }
    
    setActiveWorkspace(activeWorkspace.id);
    dismissGateway();
    
    setTimeout(() => {
      navigate(activeWorkspace.landingRoute, { replace: true });
    }, 500);
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
              `bg-gradient-to-br ${heroGradients[activeWorkspace.id]}`
            )}
          >
            {/* Decorative Elements */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div className="absolute -top-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
              <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-black/10 rounded-full blur-3xl" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[200px] opacity-5 select-none">
                {workspaceEmojis[activeWorkspace.id]}
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
                {workspaceFeatures[activeWorkspace.id].map((feature, i) => (
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
                  "bg-white text-gray-900",
                  "flex items-center justify-center gap-3",
                  "shadow-lg hover:shadow-xl transition-all",
                  "hover:scale-[1.02] active:scale-[0.98]",
                  "focus:outline-none focus:ring-4 focus:ring-white/50",
                  isEntering && "opacity-75 cursor-not-allowed"
                )}
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
          </div>
        </div>

        {/* Quick Access Pills */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
          {workspaces.map((workspace, index) => {
            const PillIcon = workspaceIcons[workspace.id];
            const isActive = index === activeIndex;
            
            return (
              <button
                key={workspace.id}
                onClick={() => goToIndex(index)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all",
                  pillColors[workspace.id],
                  isActive && `ring-2 ${pillActiveRing[workspace.id]}`
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
              onChange={(e) => setSetAsDefault(e.target.checked)}
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
      </main>

      {/* Footer */}
      <footer className="py-6 text-center text-sm text-prakruti-dhool-400 dark:text-prakruti-dhool-500">
        <p>🌾 Thank you to all those who work in acres, not in hours.</p>
      </footer>
    </div>
  );
}

export default WorkspaceGateway;
