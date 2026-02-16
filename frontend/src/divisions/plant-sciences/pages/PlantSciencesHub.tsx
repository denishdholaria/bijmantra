/**
 * Plant Sciences Hub — Federated Division Gateway
 * 
 * A mini-gateway for the Plant Sciences division, implementing the "Russian Doll" pattern
 * from the Antigravity analysis. This hub provides a focused entry point for the 83+ pages
 * within Plant Sciences, organized into 6 logical domains.
 * 
 * Per Think-Tank §5.1: "PlantSciencesHub.tsx (mini-gateway)" - Priority P1
 * Per Antigravity: "Russian Doll pattern — treat workspaces as separate applications"
 * 
 * Features:
 * - 6 domain cards with quick access to key pages
 * - Quick actions for common tasks
 * - Recent activity feed
 * - Cross-domain navigation hints
 * - Dark slate theme with emerald accents
 * 
 * @see docs/gupt/think-tank/think-tank.md §5.1 Implementation Roadmap
 */

import { Link } from 'react-router-dom';
import { 
  Wheat, GitMerge, Target, Microscope, TestTube2, Dna, 
  Map, BarChart3, Cpu, ArrowRight, Plus, Search, Clock,
  Sprout, FlaskConical, TrendingUp, Beaker, Eye,
  type LucideIcon
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDockStore } from '@/store/dockStore';

// ============================================================================
// Types
// ============================================================================

interface DomainCard {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  color: string;
  route: string;
  pages: { name: string; route: string }[];
  pageCount: number;
}

// ============================================================================
// Domain Definitions
// ============================================================================

const domains: DomainCard[] = [
  {
    id: 'breeding',
    name: 'Breeding Operations',
    description: 'Programs, trials, studies, germplasm management',
    icon: Wheat,
    color: 'from-emerald-500 to-green-600',
    route: '/programs',
    pageCount: 12,
    pages: [
      { name: 'Programs', route: '/programs' },
      { name: 'Trials', route: '/trials' },
      { name: 'Studies', route: '/studies' },
      { name: 'Germplasm', route: '/germplasm' },
      { name: 'Pipeline', route: '/pipeline' },
      { name: 'Locations', route: '/locations' },
    ],
  },
  {
    id: 'genetics',
    name: 'Genetics & Genomics',
    description: 'Genomic selection, QTL mapping, molecular breeding',
    icon: Dna,
    color: 'from-purple-500 to-violet-600',
    route: '/genomic-selection',
    pageCount: 18,
    pages: [
      { name: 'Genomic Selection', route: '/genomic-selection' },
      { name: 'QTL Mapping', route: '/qtl-mapping' },
      { name: 'Breeding Values', route: '/breeding-values' },
      { name: 'G×E Interaction', route: '/gxe-interaction' },
      { name: 'Genetic Diversity', route: '/genetic-diversity' },
      { name: 'Molecular Breeding', route: '/molecular-breeding' },
    ],
  },
  {
    id: 'phenomics',
    name: 'Phenomics',
    description: 'Traits, observations, data collection, quality',
    icon: Microscope,
    color: 'from-blue-500 to-cyan-600',
    route: '/traits',
    pageCount: 15,
    pages: [
      { name: 'Traits', route: '/traits' },
      { name: 'Observations', route: '/observations' },
      { name: 'Collect Data', route: '/observations/collect' },
      { name: 'Data Quality', route: '/dataquality' },
      { name: 'Images', route: '/images' },
      { name: 'Ontologies', route: '/ontologies' },
    ],
  },
  {
    id: 'germplasm-bank',
    name: 'Germplasm Bank',
    description: 'Crosses, pedigrees, seed lots, selection',
    icon: Sprout,
    color: 'from-amber-500 to-orange-600',
    route: '/crosses',
    pageCount: 14,
    pages: [
      { name: 'Crosses', route: '/crosses' },
      { name: 'Crossing Planner', route: '/crossingplanner' },
      { name: 'Pedigree', route: '/pedigree' },
      { name: '3D Pedigree', route: '/pedigree-3d' },
      { name: 'Seed Lots', route: '/seedlots' },
      { name: 'Selection Index', route: '/selectionindex' },
    ],
  },
  {
    id: 'molecular',
    name: 'Molecular Biology',
    description: 'Samples, variants, genotyping, allele matrices',
    icon: TestTube2,
    color: 'from-rose-500 to-pink-600',
    route: '/samples',
    pageCount: 12,
    pages: [
      { name: 'Samples', route: '/samples' },
      { name: 'Variants', route: '/variants' },
      { name: 'Allele Matrix', route: '/allelematrix' },
      { name: 'Plates', route: '/plates' },
      { name: 'Genome Maps', route: '/genomemaps' },
      { name: 'Calls', route: '/calls' },
    ],
  },
  {
    id: 'analytics',
    name: 'Analytics & WASM',
    description: 'High-performance compute, AI vision, yield prediction',
    icon: Cpu,
    color: 'from-slate-500 to-gray-600',
    route: '/wasm-genomics',
    pageCount: 12,
    pages: [
      { name: 'Sequence Viewer', route: '/viewer' },
      { name: 'WASM Genomics', route: '/wasm-genomics' },
      { name: 'WASM GBLUP', route: '/wasm-gblup' },
      { name: 'Statistics', route: '/statistics' },
      { name: 'Plant Vision', route: '/plant-vision' },
      { name: 'Yield Predictor', route: '/yield-predictor' },
      { name: 'Breeding Simulator', route: '/breeding-simulator' },
    ],
  },
];

// Quick actions for common tasks
const quickActions = [
  { name: 'New Trial', route: '/trials/new', icon: FlaskConical },
  { name: 'Find Germplasm', route: '/germplasm-search', icon: Search },
  { name: 'Record Observations', route: '/observations/collect', icon: Eye },
  { name: 'Plan Crosses', route: '/crossingplanner', icon: GitMerge },
];

// ============================================================================
// Component
// ============================================================================

export function PlantSciencesHub() {
  const { recentItems } = useDockStore();
  
  // Filter recent items to Plant Sciences routes
  const plantSciencesRecent = recentItems.filter(item => {
    const plantSciencesRoutes = [
      '/programs', '/trials', '/studies', '/germplasm', '/crosses', '/traits',
      '/observations', '/samples', '/genomic-selection', '/breeding-values',
      '/qtl-mapping', '/wasm', '/statistics', '/pedigree', '/seedlots',
    ];
    return plantSciencesRoutes.some(route => item.path.startsWith(route));
  }).slice(0, 4);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 shadow-lg shadow-emerald-500/20">
              <Wheat className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Plant Sciences</h1>
              <p className="text-slate-400 mt-1">
                Breeding, genomics, phenotyping, and field operations
              </p>
            </div>
          </div>
          
          {/* Stats */}
          <div className="flex items-center gap-6 mt-6 text-sm">
            <div className="flex items-center gap-2 text-slate-400">
              <span className="text-2xl font-bold text-emerald-400">83</span>
              <span>pages</span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <span className="text-2xl font-bold text-emerald-400">6</span>
              <span>domains</span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <span className="text-2xl font-bold text-emerald-400">100%</span>
              <span>BrAPI compliant</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Quick Actions
          </h2>
          <div className="flex flex-wrap gap-3">
            {quickActions.map(action => (
              <Link
                key={action.route}
                to={action.route}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700 hover:border-emerald-500/50 hover:text-white transition-all group"
              >
                <action.icon className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium">{action.name}</span>
              </Link>
            ))}
          </div>
        </div>

        {/* Domain Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {domains.map(domain => (
            <div
              key={domain.id}
              className="group rounded-xl bg-slate-800/50 border border-slate-700/50 hover:border-slate-600 transition-all overflow-hidden"
            >
              {/* Card Header */}
              <div className={cn(
                'p-4 bg-gradient-to-r',
                domain.color
              )}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <domain.icon className="w-6 h-6 text-white" />
                    <div>
                      <h3 className="font-semibold text-white">{domain.name}</h3>
                      <p className="text-xs text-white/70">{domain.pageCount} pages</p>
                    </div>
                  </div>
                  <Link
                    to={domain.route}
                    className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                    aria-label={`Go to ${domain.name}`}
                  >
                    <ArrowRight className="w-4 h-4 text-white" />
                  </Link>
                </div>
              </div>
              
              {/* Card Body */}
              <div className="p-4">
                <p className="text-sm text-slate-400 mb-4">{domain.description}</p>
                <div className="space-y-1">
                  {domain.pages.map(page => (
                    <Link
                      key={page.route}
                      to={page.route}
                      className="flex items-center justify-between px-2 py-1.5 rounded text-sm text-slate-300 hover:text-white hover:bg-slate-700/50 transition-colors"
                    >
                      <span>{page.name}</span>
                      <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-50 transition-opacity" />
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Activity */}
        {plantSciencesRecent.length > 0 && (
          <div className="rounded-xl bg-slate-800/30 border border-slate-700/50 p-6">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="w-4 h-4 text-slate-400" />
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Recent Activity
              </h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {plantSciencesRecent.map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:bg-slate-700/50 hover:border-slate-600 transition-all"
                >
                  <div className="p-2 rounded bg-slate-700/50">
                    <Clock className="w-4 h-4 text-slate-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-200 truncate">
                      {item.label}
                    </div>
                    <div className="text-xs text-slate-500 truncate">
                      {item.path}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Cross-Domain Hints */}
        <div className="mt-8 p-6 rounded-xl bg-gradient-to-r from-emerald-900/20 to-cyan-900/20 border border-emerald-500/20">
          <div className="flex items-start gap-4">
            <div className="p-2 rounded-lg bg-emerald-500/10">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h3 className="font-medium text-white mb-1">Cross-Domain Intelligence</h3>
              <p className="text-sm text-slate-400 mb-3">
                Plant Sciences integrates with Seed Bank for germplasm conservation, 
                Environment for climate data, and Seed Operations for variety release.
              </p>
              <div className="flex flex-wrap gap-2">
                <Link
                  to="/seed-bank"
                  className="text-xs px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 transition-colors"
                >
                  Seed Bank →
                </Link>
                <Link
                  to="/earth-systems"
                  className="text-xs px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors"
                >
                  Environment →
                </Link>
                <Link
                  to="/seed-operations"
                  className="text-xs px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 transition-colors"
                >
                  Seed Operations →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PlantSciencesHub;
