/**
 * Future Roadmap Section Component
 * 
 * Displays the BijMantra expansion roadmap in the Workspace Gateway.
 * Designed to attract global talent by showcasing:
 * - Vision and ambition
 * - Technical challenges
 * - Collaboration opportunities
 * - Clear development timeline
 * 
 * @see docs/gupt/1-future.md for full roadmap
 */

import { useState } from 'react';
import { cn } from '@/lib/utils';
import {
  Sparkles,
  ChevronRight,
  ChevronDown,
  Globe,
  Users,
  Code,
  BookOpen,
  Rocket,
  ExternalLink,
  Calendar,
  Layers,
  GitBranch,
  Heart,
} from 'lucide-react';
import { 
  futureWorkspaces, 
  getFutureWorkspacesByTier,
  tierInfo,
  futureStats,
  type DevelopmentTier,
} from '@/framework/registry/futureWorkspaces';
import { FutureWorkspaceCard } from './FutureWorkspaceCard';

// ============================================================================
// Component Props
// ============================================================================

interface FutureRoadmapSectionProps {
  /** Whether to show in collapsed mode initially */
  defaultCollapsed?: boolean;
  /** Callback when user wants to contribute */
  onContribute?: () => void;
  /** Maximum workspaces to show before "Show More" */
  maxVisible?: number;
}

// ============================================================================
// Main Component
// ============================================================================

export function FutureRoadmapSection({ 
  defaultCollapsed = true,
  onContribute,
  maxVisible = 6,
}: FutureRoadmapSectionProps) {
  const [isExpanded, setIsExpanded] = useState(!defaultCollapsed);
  const [selectedTier, setSelectedTier] = useState<DevelopmentTier | 'all'>('all');
  const [showAll, setShowAll] = useState(false);

  // Filter workspaces by tier
  const filteredWorkspaces = selectedTier === 'all' 
    ? futureWorkspaces 
    : getFutureWorkspacesByTier(selectedTier);

  const visibleWorkspaces = showAll 
    ? filteredWorkspaces 
    : filteredWorkspaces.slice(0, maxVisible);

  const hasMore = filteredWorkspaces.length > maxVisible;

  // Handle contribute action
  const handleContribute = () => {
    if (onContribute) {
      onContribute();
    } else {
      // Default: open GitHub
      window.open('https://github.com/bijmantra/bijmantra', '_blank');
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* Section Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 hover:from-purple-100 hover:to-indigo-100 dark:hover:from-purple-900/30 dark:hover:to-indigo-900/30 transition-all group"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg text-white">
            <Rocket className="w-5 h-5" />
          </div>
          <div className="text-left">
            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              Future Roadmap
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium">
                <Sparkles className="w-3 h-3" />
                {futureStats.totalWorkspaces} Modules Planned
              </span>
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Join us in building the future of agricultural intelligence
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 hidden sm:block">
            ~{futureStats.totalEstimatedPages} pages planned
          </span>
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-slate-400 group-hover:text-slate-600 transition-colors" />
          ) : (
            <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-slate-600 transition-colors" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 space-y-6 animate-in slide-in-from-top-2 duration-300">
          {/* Vision Statement */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800/50 dark:to-slate-900/50 border border-slate-200 dark:border-slate-700">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl text-white shrink-0">
                <Globe className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">
                  Cross-Domain Agricultural Intelligence
                </h3>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed mb-4">
                  BijMantra is expanding beyond plant breeding to become a comprehensive 
                  agricultural intelligence platform. We're building modules that unify 
                  fragmented agricultural knowledge — from soil science to market economics, 
                  from crop protection to sustainability tracking.
                </p>
                <blockquote className="pl-4 border-l-2 border-emerald-500 text-slate-500 dark:text-slate-400 italic">
                  "Understanding one domain without seeing its interaction with others 
                  produces incomplete, sometimes misleading conclusions."
                </blockquote>
              </div>
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard
              icon={<Layers className="w-5 h-5" />}
              label="Planned Modules"
              value={futureStats.totalWorkspaces.toString()}
              color="from-purple-500 to-indigo-600"
            />
            <StatCard
              icon={<Code className="w-5 h-5" />}
              label="Estimated Pages"
              value={`~${futureStats.totalEstimatedPages}`}
              color="from-blue-500 to-cyan-600"
            />
            <StatCard
              icon={<Calendar className="w-5 h-5" />}
              label="Timeline"
              value="2026-2029"
              color="from-emerald-500 to-teal-600"
            />
            <StatCard
              icon={<GitBranch className="w-5 h-5" />}
              label="Open Source"
              value="AGPL-3.0"
              color="from-amber-500 to-orange-600"
            />
          </div>

          {/* Tier Filter */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-slate-500 dark:text-slate-400 mr-2">Filter by tier:</span>
            <TierButton
              tier="all"
              label="All"
              count={futureWorkspaces.length}
              isActive={selectedTier === 'all'}
              onClick={() => setSelectedTier('all')}
            />
            <TierButton
              tier="tier-1"
              label="Foundation"
              count={futureStats.tier1Count}
              isActive={selectedTier === 'tier-1'}
              onClick={() => setSelectedTier('tier-1')}
            />
            <TierButton
              tier="tier-2"
              label="Strategic"
              count={futureStats.tier2Count}
              isActive={selectedTier === 'tier-2'}
              onClick={() => setSelectedTier('tier-2')}
            />
            <TierButton
              tier="tier-3"
              label="Advanced"
              count={futureStats.tier3Count}
              isActive={selectedTier === 'tier-3'}
              onClick={() => setSelectedTier('tier-3')}
            />
          </div>

          {/* Workspace Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {visibleWorkspaces.map(workspace => (
              <FutureWorkspaceCard
                key={workspace.id}
                workspace={workspace}
                variant="compact"
                onContribute={handleContribute}
              />
            ))}
          </div>

          {/* Show More Button */}
          {hasMore && !showAll && (
            <div className="text-center">
              <button
                onClick={() => setShowAll(true)}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors"
              >
                Show {filteredWorkspaces.length - maxVisible} more modules
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Call to Action */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl">
                  <Heart className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-1">Join the Mission</h3>
                  <p className="text-white/80 text-sm">
                    We're looking for domain experts, developers, and researchers to help build 
                    the future of agricultural intelligence.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <a
                  href="https://bijmantra.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                >
                  <BookOpen className="w-4 h-4" />
                  Learn More
                </a>
                <button
                  onClick={handleContribute}
                  className="px-4 py-2 bg-white text-purple-600 hover:bg-white/90 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
                >
                  <Users className="w-4 h-4" />
                  Contribute
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Skills We're Looking For */}
          <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-500" />
              Skills We're Looking For
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {[
                'Agronomy & Crop Science',
                'Soil Science',
                'Plant Pathology',
                'Agricultural Economics',
                'Machine Learning / AI',
                'Computer Vision',
                'Full-Stack Development',
                'GIS & Remote Sensing',
                'IoT & Sensors',
                'Data Science',
                'UX Design',
                'Technical Writing',
              ].map((skill, i) => (
                <div 
                  key={i}
                  className="px-3 py-2 bg-white dark:bg-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600"
                >
                  {skill}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  return (
    <div className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
      <div className={cn(
        'w-10 h-10 rounded-lg flex items-center justify-center text-white mb-3',
        `bg-gradient-to-br ${color}`
      )}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-slate-800 dark:text-slate-200">{value}</div>
      <div className="text-sm text-slate-500 dark:text-slate-400">{label}</div>
    </div>
  );
}

interface TierButtonProps {
  tier: DevelopmentTier | 'all';
  label: string;
  count: number;
  isActive: boolean;
  onClick: () => void;
}

function TierButton({ tier, label, count, isActive, onClick }: TierButtonProps) {
  const tierColors: Record<DevelopmentTier | 'all', string> = {
    'all': 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
    'tier-1': 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    'tier-2': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'tier-3': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    'tier-4': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
        isActive 
          ? cn(tierColors[tier], 'ring-2 ring-offset-2 ring-offset-white dark:ring-offset-slate-900', 
              tier === 'all' ? 'ring-slate-400' : 
              tier === 'tier-1' ? 'ring-emerald-500' :
              tier === 'tier-2' ? 'ring-blue-500' :
              tier === 'tier-3' ? 'ring-purple-500' : 'ring-amber-500')
          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
      )}
    >
      {label}
      <span className="ml-1.5 text-xs opacity-70">({count})</span>
    </button>
  );
}

export default FutureRoadmapSection;
