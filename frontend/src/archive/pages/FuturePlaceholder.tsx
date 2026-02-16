/**
 * Future Placeholder Page
 * 
 * Displayed when users navigate to a planned/future module.
 * Designed to:
 * - Communicate the vision for the module
 * - Attract contributors by showing skills needed
 * - Provide clear timeline expectations
 * - Link to contribution opportunities
 * 
 * @see docs/gupt/1-future.md for full roadmap
 */

import { useLocation, useNavigate, Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  Sparkles,
  Clock,
  Users,
  Code,
  BookOpen,
  ArrowLeft,
  ExternalLink,
  Rocket,
  Heart,
  GitBranch,
  Layers,
  ChevronRight,
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
import { getFutureDivision, type FutureDivision } from '@/framework/registry/futureDivisions';

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
// Tier Colors
// ============================================================================

const tierColors: Record<string, { gradient: string; badge: string }> = {
  'tier-1': {
    gradient: 'from-emerald-500 to-teal-600',
    badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  },
  'tier-2': {
    gradient: 'from-blue-500 to-indigo-600',
    badge: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  },
  'tier-3': {
    gradient: 'from-purple-500 to-violet-600',
    badge: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  },
  'tier-4': {
    gradient: 'from-amber-500 to-orange-600',
    badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  },
};

const tierLabels: Record<string, string> = {
  'tier-1': 'Foundation Module',
  'tier-2': 'Strategic Expansion',
  'tier-3': 'Advanced Research',
  'tier-4': 'Future Technology',
};

// ============================================================================
// Component
// ============================================================================

export default function FuturePlaceholder() {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Extract division ID from path
  const pathParts = location.pathname.split('/').filter(Boolean);
  const divisionId = pathParts[0];
  
  // Get division info
  const division = getFutureDivision(divisionId);
  
  // Fallback for unknown future routes
  if (!division) {
    return <GenericFuturePlaceholder />;
  }
  
  const Icon = getIcon(division.icon);
  const tierStyle = tierColors[division.tier] || tierColors['tier-1'];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Hero Section */}
      <div className={cn(
        'relative overflow-hidden',
        `bg-gradient-to-br ${tierStyle.gradient}`
      )}>
        {/* Decorative Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-white/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-black/10 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[300px] opacity-5 select-none">
            <Icon className="w-full h-full" />
          </div>
        </div>

        {/* Content */}
        <div className="relative z-10 max-w-4xl mx-auto px-6 py-16 text-white">
          {/* Back Button */}
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 px-3 py-1.5 mb-8 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg text-sm transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>

          {/* Badges */}
          <div className="flex flex-wrap items-center gap-2 mb-6">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm font-medium">
              <Sparkles className="w-4 h-4" />
              Coming Soon
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm">
              <Clock className="w-4 h-4" />
              {division.timeline}
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm">
              {tierLabels[division.tier]}
            </span>
          </div>

          {/* Title */}
          <div className="flex items-start gap-6 mb-8">
            <div className="p-4 bg-white/20 backdrop-blur-sm rounded-2xl shrink-0">
              <Icon className="w-12 h-12" />
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-bold mb-3">{division.name}</h1>
              <p className="text-xl text-white/80 max-w-2xl">{division.description}</p>
            </div>
          </div>

          {/* Capabilities Preview */}
          <div className="flex flex-wrap gap-2">
            {division.capabilities.map((cap, i) => (
              <span 
                key={i}
                className="px-3 py-1.5 bg-white/15 backdrop-blur-sm rounded-full text-sm"
              >
                {cap}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Vision Statement */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 shadow-lg border border-slate-200 dark:border-slate-700 mb-8">
          <div className="flex items-start gap-4">
            <div className={cn(
              'p-3 rounded-xl text-white shrink-0',
              `bg-gradient-to-br ${tierStyle.gradient}`
            )}>
              <Rocket className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200 mb-2">
                This Module is Under Development
              </h2>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                The <strong>{division.name}</strong> module is part of BijMantra's expansion roadmap. 
                We're building comprehensive agricultural intelligence that spans from soil science 
                to market economics, from crop protection to sustainability tracking.
              </p>
            </div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          {/* Skills Needed */}
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 shadow-lg border border-slate-200 dark:border-slate-700">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4">
              <Users className="w-5 h-5 text-purple-500" />
              Skills We're Looking For
            </h3>
            <div className="space-y-2">
              {division.skillsNeeded.map((skill, i) => (
                <div 
                  key={i}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm',
                    tierStyle.badge
                  )}
                >
                  {skill}
                </div>
              ))}
            </div>
          </div>

          {/* Planned Sections */}
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 shadow-lg border border-slate-200 dark:border-slate-700">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4">
              <Layers className="w-5 h-5 text-blue-500" />
              Planned Sections
            </h3>
            <div className="space-y-3">
              {division.sections?.map((section) => (
                <div key={section.id} className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-600" />
                  <span className="text-slate-700 dark:text-slate-300">{section.name}</span>
                  {section.items && (
                    <span className="text-xs text-slate-400">
                      ({section.items.length} pages)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className={cn(
          'p-8 rounded-2xl text-white',
          `bg-gradient-to-r ${tierStyle.gradient}`
        )}>
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-white/20 rounded-xl">
                <Heart className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-1">Help Build This Module</h3>
                <p className="text-white/80">
                  We're looking for domain experts and developers to help bring this vision to life.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <a
                href="https://bijmantra.org"
                target="_blank"
                rel="noopener noreferrer"
                className="px-5 py-2.5 bg-white/20 hover:bg-white/30 rounded-xl font-medium transition-colors flex items-center gap-2"
              >
                <BookOpen className="w-4 h-4" />
                Learn More
              </a>
              <a
                href="https://github.com/bijmantra/bijmantra"
                target="_blank"
                rel="noopener noreferrer"
                className="px-5 py-2.5 bg-white text-slate-800 hover:bg-white/90 rounded-xl font-semibold transition-colors flex items-center gap-2"
              >
                <GitBranch className="w-4 h-4" />
                Contribute
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>

        {/* Related Links */}
        <div className="mt-8 p-6 rounded-2xl bg-slate-100 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4">
            Explore Available Modules
          </h3>
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
            <QuickLink to="/programs" label="Plant Breeding" description="Programs, trials, genomics" />
            <QuickLink to="/seed-bank" label="Seed Bank" description="Conservation, vaults" />
            <QuickLink to="/earth-systems" label="Environment" description="Weather, soil, climate" />
            <QuickLink to="/seed-operations" label="Seed Commerce" description="Lab, processing, dispatch" />
            <QuickLink to="/space-research" label="Space Research" description="Interplanetary agriculture" />
            <QuickLink to="/dashboard" label="Dashboard" description="Overview & insights" />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-200 dark:border-slate-800 py-8 text-center">
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          🌾 Thank you to all those who work in acres, not in hours.
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

function QuickLink({ to, label, description }: { to: string; label: string; description: string }) {
  return (
    <Link
      to={to}
      className="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 transition-colors group"
    >
      <div>
        <div className="font-medium text-slate-800 dark:text-slate-200">{label}</div>
        <div className="text-xs text-slate-500 dark:text-slate-400">{description}</div>
      </div>
      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300 transition-colors" />
    </Link>
  );
}

function GenericFuturePlaceholder() {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-6">
      <div className="max-w-md text-center">
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white">
          <Sparkles className="w-10 h-10" />
        </div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-200 mb-3">
          Coming Soon
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          This module is part of BijMantra's future roadmap. We're working hard to bring 
          comprehensive agricultural intelligence to researchers and farmers worldwide.
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg font-medium hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
          >
            Go Back
          </button>
          <Link
            to="/dashboard"
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg font-medium hover:opacity-90 transition-opacity"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
