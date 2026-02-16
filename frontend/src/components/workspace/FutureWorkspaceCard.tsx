/**
 * Future Workspace Card Component
 * 
 * Displays planned/future workspaces with "Coming Soon" badges,
 * skill requirements, and contribution opportunities.
 * 
 * Designed to attract global talent by showcasing:
 * - Technical challenges and technologies
 * - Research collaboration opportunities
 * - Skills needed for contribution
 * - Cross-domain integration vision
 */

import { useState } from 'react';
import { cn } from '@/lib/utils';
import {
  Sparkles,
  Clock,
  Users,
  Code,
  BookOpen,
  ChevronRight,
  ExternalLink,
  Layers,
  Zap,
  GitBranch,
  // Domain icons
  Wheat,
  Mountain,
  Shield,
  Droplets,
  TrendingUp,
  Leaf,
  ClipboardList,
  Bot,
  Package,
  Beef,
  Fish,
  type LucideIcon,
} from 'lucide-react';
import type { FutureWorkspace, DevelopmentTier } from '@/framework/registry/futureWorkspaces';

// ============================================================================
// Icon Mapping
// ============================================================================

const futureIcons: Record<string, LucideIcon> = {
  'Wheat': Wheat,
  'Mountain': Mountain,
  'Shield': Shield,
  'Droplets': Droplets,
  'TrendingUp': TrendingUp,
  'Leaf': Leaf,
  'ClipboardList': ClipboardList,
  'Bot': Bot,
  'Package': Package,
  'Beef': Beef,
  'Fish': Fish,
};

function getIcon(iconName: string): LucideIcon {
  return futureIcons[iconName] || Sparkles;
}

// ============================================================================
// Tier Badge Colors
// ============================================================================

const tierColors: Record<DevelopmentTier, { bg: string; text: string; border: string }> = {
  'tier-1': {
    bg: 'bg-emerald-100 dark:bg-emerald-900/30',
    text: 'text-emerald-700 dark:text-emerald-400',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
  'tier-2': {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800',
  },
  'tier-3': {
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    text: 'text-purple-700 dark:text-purple-400',
    border: 'border-purple-200 dark:border-purple-800',
  },
  'tier-4': {
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-200 dark:border-amber-800',
  },
};

const tierLabels: Record<DevelopmentTier, string> = {
  'tier-1': 'Foundation',
  'tier-2': 'Strategic',
  'tier-3': 'Advanced',
  'tier-4': 'Future Tech',
};

// ============================================================================
// Component Props
// ============================================================================

interface FutureWorkspaceCardProps {
  workspace: FutureWorkspace;
  variant?: 'compact' | 'expanded' | 'hero';
  onContribute?: () => void;
  onLearnMore?: () => void;
}

// ============================================================================
// Compact Card (for grid display)
// ============================================================================

export function FutureWorkspaceCard({ 
  workspace, 
  variant = 'compact',
  onContribute,
  onLearnMore,
}: FutureWorkspaceCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const Icon = getIcon(workspace.icon);
  const tierStyle = tierColors[workspace.tier];

  if (variant === 'hero') {
    return (
      <FutureWorkspaceHero 
        workspace={workspace} 
        onContribute={onContribute}
        onLearnMore={onLearnMore}
      />
    );
  }

  if (variant === 'expanded') {
    return (
      <FutureWorkspaceExpanded 
        workspace={workspace}
        onContribute={onContribute}
        onLearnMore={onLearnMore}
      />
    );
  }

  return (
    <div
      className={cn(
        'relative group rounded-2xl border-2 border-dashed transition-all duration-300',
        'bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm',
        'border-slate-200 dark:border-slate-700',
        'hover:border-slate-300 dark:hover:border-slate-600',
        'hover:shadow-lg hover:scale-[1.02]',
        'cursor-pointer overflow-hidden'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onLearnMore}
    >
      {/* Coming Soon Badge */}
      <div className="absolute top-3 right-3 z-10">
        <span className={cn(
          'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
          tierStyle.bg, tierStyle.text
        )}>
          <Clock className="w-3 h-3" />
          {workspace.timeline}
        </span>
      </div>

      {/* Gradient Overlay on Hover */}
      <div className={cn(
        'absolute inset-0 opacity-0 transition-opacity duration-300',
        `bg-gradient-to-br ${workspace.color}`,
        isHovered && 'opacity-5'
      )} />

      {/* Content */}
      <div className="relative p-5">
        {/* Icon & Title */}
        <div className="flex items-start gap-3 mb-3">
          <div className={cn(
            'p-2.5 rounded-xl transition-all duration-300',
            'bg-slate-100 dark:bg-slate-700',
            isHovered && `bg-gradient-to-br ${workspace.color} text-white`
          )}>
            <Icon className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 truncate">
              {workspace.name}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {workspace.description}
            </p>
          </div>
        </div>

        {/* Tier & Pages */}
        <div className="flex items-center gap-2 mb-3">
          <span className={cn(
            'px-2 py-0.5 rounded text-xs font-medium',
            tierStyle.bg, tierStyle.text
          )}>
            {tierLabels[workspace.tier]}
          </span>
          <span className="text-xs text-slate-400">
            ~{workspace.estimatedPages} pages
          </span>
        </div>

        {/* Key Technologies (truncated) */}
        <div className="flex flex-wrap gap-1 mb-3">
          {workspace.technologies.slice(0, 3).map((tech, i) => (
            <span 
              key={i}
              className="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-xs text-slate-600 dark:text-slate-400"
            >
              {tech.split(' ')[0]}
            </span>
          ))}
          {workspace.technologies.length > 3 && (
            <span className="px-2 py-0.5 text-xs text-slate-400">
              +{workspace.technologies.length - 3}
            </span>
          )}
        </div>

        {/* Hover Action */}
        <div className={cn(
          'flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-700',
          'transition-opacity duration-300',
          isHovered ? 'opacity-100' : 'opacity-50'
        )}>
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <Users className="w-3 h-3" />
            {workspace.skillsNeeded.length} skills needed
          </span>
          <span className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
            Learn more
            <ChevronRight className="w-3 h-3" />
          </span>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Expanded Card (for modal/detail view)
// ============================================================================

function FutureWorkspaceExpanded({ 
  workspace,
  onContribute,
  onLearnMore,
}: Omit<FutureWorkspaceCardProps, 'variant'>) {
  const Icon = getIcon(workspace.icon);
  const tierStyle = tierColors[workspace.tier];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl overflow-hidden max-w-2xl w-full">
      {/* Header with Gradient */}
      <div className={cn(
        'relative p-6 text-white',
        `bg-gradient-to-br ${workspace.color}`
      )}>
        {/* Decorative */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-white/10 rounded-full blur-2xl" />
        </div>

        <div className="relative">
          {/* Badges */}
          <div className="flex items-center gap-2 mb-4">
            <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium">
              <Sparkles className="w-4 h-4" />
              Coming Soon
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm">
              <Clock className="w-4 h-4" />
              {workspace.timeline}
            </span>
          </div>

          {/* Title */}
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
              <Icon className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">{workspace.name}</h2>
              <p className="text-white/80">{workspace.description}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Long Description */}
        <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
          {workspace.longDescription}
        </p>

        {/* Capabilities */}
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
            <Zap className="w-4 h-4 text-amber-500" />
            Key Capabilities
          </h3>
          <div className="grid grid-cols-2 gap-2">
            {workspace.capabilities.map((cap, i) => (
              <div 
                key={i}
                className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                {cap}
              </div>
            ))}
          </div>
        </div>

        {/* Technologies */}
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
            <Code className="w-4 h-4 text-blue-500" />
            Technologies
          </h3>
          <div className="flex flex-wrap gap-2">
            {workspace.technologies.map((tech, i) => (
              <span 
                key={i}
                className="px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-300"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* Skills Needed */}
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
            <Users className="w-4 h-4 text-purple-500" />
            Skills Needed
          </h3>
          <div className="flex flex-wrap gap-2">
            {workspace.skillsNeeded.map((skill, i) => (
              <span 
                key={i}
                className={cn(
                  'px-3 py-1 rounded-lg text-sm border',
                  tierStyle.bg, tierStyle.text, tierStyle.border
                )}
              >
                {skill}
              </span>
            ))}
          </div>
        </div>

        {/* Research Areas */}
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
            <BookOpen className="w-4 h-4 text-rose-500" />
            Research Collaboration Areas
          </h3>
          <div className="flex flex-wrap gap-2">
            {workspace.researchAreas.map((area, i) => (
              <span 
                key={i}
                className="px-3 py-1 bg-rose-50 dark:bg-rose-900/20 text-rose-700 dark:text-rose-400 rounded-lg text-sm"
              >
                {area}
              </span>
            ))}
          </div>
        </div>

        {/* Cross-Domain Integrations */}
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
            <GitBranch className="w-4 h-4 text-cyan-500" />
            Cross-Domain Integrations
          </h3>
          <div className="flex flex-wrap gap-2">
            {workspace.crossDomainIntegrations.map((domain, i) => (
              <span 
                key={i}
                className="px-3 py-1 bg-cyan-50 dark:bg-cyan-900/20 text-cyan-700 dark:text-cyan-400 rounded-lg text-sm"
              >
                {domain}
              </span>
            ))}
          </div>
        </div>

        {/* Target Users */}
        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <Users className="w-4 h-4" />
          <span>Target Users: {workspace.targetUsers.join(', ')}</span>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="px-6 py-4 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Layers className="w-4 h-4" />
          <span>~{workspace.estimatedPages} pages planned</span>
        </div>
        <div className="flex items-center gap-3">
          {onLearnMore && (
            <button
              onClick={onLearnMore}
              className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
            >
              View Roadmap
            </button>
          )}
          {onContribute && (
            <button
              onClick={onContribute}
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium text-white transition-all',
                `bg-gradient-to-r ${workspace.color}`,
                'hover:shadow-lg hover:scale-105'
              )}
            >
              <span className="flex items-center gap-2">
                Contribute
                <ExternalLink className="w-4 h-4" />
              </span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Hero Card (for featured display)
// ============================================================================

function FutureWorkspaceHero({ 
  workspace,
  onContribute,
  onLearnMore,
}: Omit<FutureWorkspaceCardProps, 'variant'>) {
  const Icon = getIcon(workspace.icon);

  return (
    <div className={cn(
      'relative overflow-hidden rounded-3xl shadow-2xl',
      `bg-gradient-to-br ${workspace.color}`
    )}>
      {/* Decorative Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-black/10 rounded-full blur-3xl" />
      </div>

      {/* Content */}
      <div className="relative z-10 p-8 md:p-12 text-white">
        {/* Badges */}
        <div className="flex items-center gap-2 mb-6">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium">
            <Sparkles className="w-4 h-4" />
            Coming Soon
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm">
            <Clock className="w-4 h-4" />
            {workspace.timeline}
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm">
            {tierLabels[workspace.tier]}
          </span>
        </div>

        {/* Icon & Title */}
        <div className="flex items-start gap-4 mb-6">
          <div className="p-4 bg-white/20 backdrop-blur-sm rounded-2xl">
            <Icon className="w-10 h-10" />
          </div>
          <div>
            <h2 className="text-3xl md:text-4xl font-bold mb-2">{workspace.name}</h2>
            <p className="text-lg text-white/80 max-w-xl">{workspace.longDescription}</p>
          </div>
        </div>

        {/* Capabilities Preview */}
        <div className="flex flex-wrap gap-2 mb-8">
          {workspace.capabilities.slice(0, 5).map((cap, i) => (
            <span 
              key={i}
              className="px-3 py-1 bg-white/15 backdrop-blur-sm rounded-full text-sm"
            >
              {cap}
            </span>
          ))}
          {workspace.capabilities.length > 5 && (
            <span className="px-3 py-1 bg-white/15 backdrop-blur-sm rounded-full text-sm">
              +{workspace.capabilities.length - 5} more
            </span>
          )}
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6 text-sm text-white/70 mb-8">
          <span className="flex items-center gap-1">
            <Layers className="w-4 h-4" />
            ~{workspace.estimatedPages} pages
          </span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Code className="w-4 h-4" />
            {workspace.technologies.length} technologies
          </span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            {workspace.skillsNeeded.length} skills needed
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          {onLearnMore && (
            <button
              onClick={onLearnMore}
              className="px-6 py-3 bg-white/95 text-gray-900 rounded-xl font-semibold hover:bg-white transition-all hover:scale-105 flex items-center gap-2"
            >
              View Roadmap
              <ChevronRight className="w-5 h-5" />
            </button>
          )}
          {onContribute && (
            <button
              onClick={onContribute}
              className="px-6 py-3 bg-white/20 backdrop-blur-sm text-white rounded-xl font-semibold hover:bg-white/30 transition-all flex items-center gap-2"
            >
              Contribute
              <ExternalLink className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default FutureWorkspaceCard;
