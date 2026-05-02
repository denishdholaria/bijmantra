import React, { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  Cpu,
  Dna,
  Sprout,
  Globe,
  Database,
  ShieldCheck,
  Download,
  Check,
  Trash2,
  Star,
  Clock,
  LayoutGrid,
  Zap
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { cn } from '@/lib/utils';

// ============================================================================
// Types & Interfaces
// ============================================================================

export type PluginCategory = 'AI' | 'Genomics' | 'Trials' | 'Environment' | 'IoT' | 'Database' | 'Security';

export interface Plugin {
  id: string;
  name: string;
  description: string;
  longDescription?: string;
  version: string;
  author: string;
  category: PluginCategory;
  status: 'installed' | 'available' | 'beta';
  icon: React.ReactNode;
  tags: string[];
  downloads: number;
  rating: number;
  lastUpdated: string;
  isREEVU?: boolean;
}

// ============================================================================
// Mock Data
// ============================================================================

const MOCK_PLUGINS: Plugin[] = [
  {
    id: 'reevu-genomic-reasoner',
    name: 'REEVU Genomic Reasoner',
    description: 'AI-powered scientific reasoning for complex genomic datasets.',
    version: '2.1.0',
    author: 'BijMantra AI',
    category: 'AI',
    status: 'installed',
    icon: <Cpu className="h-8 w-8 text-purple-500" />,
    tags: ['AI', 'Genomics', 'Reasoning'],
    downloads: 12500,
    rating: 4.9,
    lastUpdated: '2025-12-15',
    isREEVU: true,
  },
  {
    id: 'brapi-v2-adapter',
    name: 'BrAPI v2.1 Adapter',
    description: 'Full compatibility with Breeding API v2.1 endpoints.',
    version: '1.0.5',
    author: 'BrAPI Community',
    category: 'Database',
    status: 'installed',
    icon: <Database className="h-8 w-8 text-blue-500" />,
    tags: ['Standard', 'Data Exchange'],
    downloads: 45000,
    rating: 4.7,
    lastUpdated: '2025-11-20',
  },
  {
    id: 'prakruti-weather-sync',
    name: 'Prakruti Weather Sync',
    description: 'Real-time synchronization with global meteorological stations.',
    version: '3.2.0',
    author: 'Earth Systems',
    category: 'Environment',
    status: 'available',
    icon: <Globe className="h-8 w-8 text-green-500" />,
    tags: ['Weather', 'Sync', 'IoT'],
    downloads: 8200,
    rating: 4.5,
    lastUpdated: '2025-12-01',
  },
  {
    id: 'pheno-capture-mobile',
    name: 'PhenoCapture Mobile',
    description: 'Enhanced field data collection with offline image processing.',
    version: '4.0.1',
    author: 'Field Ops Team',
    category: 'Trials',
    status: 'installed',
    icon: <Sprout className="h-8 w-8 text-emerald-500" />,
    tags: ['Mobile', 'Offline', 'Phenotyping'],
    downloads: 15600,
    rating: 4.8,
    lastUpdated: '2025-12-10',
  },
  {
    id: 'dna-variant-analyzer',
    name: 'DNA Variant Analyzer',
    description: 'High-performance variant calling and population structure analysis.',
    version: '1.8.0',
    author: 'Genomics Lab',
    category: 'Genomics',
    status: 'available',
    icon: <Dna className="h-8 w-8 text-indigo-500" />,
    tags: ['Variants', 'Analysis', 'Performance'],
    downloads: 3400,
    rating: 4.6,
    lastUpdated: '2025-10-15',
  },
  {
    id: 'secure-vault-encryption',
    name: 'SecureVault Encryption',
    description: 'Enterprise-grade encryption for sensitive germplasm records.',
    version: '5.0.0',
    author: 'Security Division',
    category: 'Security',
    status: 'installed',
    icon: <ShieldCheck className="h-8 w-8 text-slate-500" />,
    tags: ['Security', 'Encryption', 'Privacy'],
    downloads: 21000,
    rating: 4.9,
    lastUpdated: '2025-12-20',
  },
  {
    id: 'reevu-trial-predictor',
    name: 'REEVU Trial Predictor',
    description: 'Predict trial outcomes using multi-season historical data.',
    version: '1.2.0-beta',
    author: 'BijMantra AI',
    category: 'AI',
    status: 'beta',
    icon: <Zap className="h-8 w-8 text-amber-500" />,
    tags: ['AI', 'Prediction', 'Beta'],
    downloads: 1200,
    rating: 4.4,
    lastUpdated: '2025-12-18',
    isREEVU: true,
  },
];

// ============================================================================
// Main Component
// ============================================================================

export function PluginDiscoveryGrid() {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<PluginCategory | 'All'>('All');
  const [statusFilter, setStatusFilter] = useState<'All' | 'installed' | 'available' | 'beta'>('All');
  const [sortBy, setSortBy] = useState<'newest' | 'popular' | 'rating'>('popular');
  const [plugins, setPlugins] = useState<Plugin[]>(MOCK_PLUGINS);

  // Filter and Sort Logic
  const filteredPlugins = useMemo(() => {
    let result = plugins.filter(plugin => {
      const matchesSearch =
        plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        plugin.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        plugin.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesCategory = categoryFilter === 'All' || plugin.category === categoryFilter;
      const matchesStatus = statusFilter === 'All' || plugin.status === statusFilter;

      return matchesSearch && matchesCategory && matchesStatus;
    });

    result = [...result].sort((a, b) => {
      if (sortBy === 'newest') return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime();
      if (sortBy === 'popular') return b.downloads - a.downloads;
      if (sortBy === 'rating') return b.rating - a.rating;
      return 0;
    });

    return result;
  }, [plugins, searchQuery, categoryFilter, statusFilter, sortBy]);

  // Actions
  const handleToggleInstall = (id: string) => {
    setPlugins(prev => prev.map(p => {
      if (p.id === id) {
        return {
          ...p,
          status: p.status === 'installed' ? 'available' : 'installed'
        };
      }
      return p;
    }));
  };

  return (
    <div className="w-full space-y-6 p-1">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Plugin Discovery</h2>
          <p className="text-muted-foreground">Extend your workspace with specialized modules and AI capabilities.</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="px-3 py-1 bg-purple-50 dark:bg-purple-950/30 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800">
            <Cpu className="h-3.5 w-3.5 mr-1.5" />
            REEVU Powered
          </Badge>
          <Badge variant="outline" className="px-3 py-1">
            {plugins.filter(p => p.status === 'installed').length} Installed
          </Badge>
        </div>
      </div>

      {/* Filters Toolbar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search plugins, tags, or authors..."
            className="pl-9 w-full"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Select
            value={categoryFilter}
            onValueChange={(v: string) => setCategoryFilter(v as PluginCategory | 'All')}
          >
            <SelectTrigger className="w-full sm:w-[140px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All">All Categories</SelectItem>
              <SelectItem value="AI">AI</SelectItem>
              <SelectItem value="Genomics">Genomics</SelectItem>
              <SelectItem value="Trials">Trials</SelectItem>
              <SelectItem value="Environment">Environment</SelectItem>
              <SelectItem value="IoT">IoT</SelectItem>
              <SelectItem value="Database">Database</SelectItem>
              <SelectItem value="Security">Security</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={statusFilter}
            onValueChange={(v: string) => setStatusFilter(v as 'All' | 'installed' | 'available' | 'beta')}
          >
            <SelectTrigger className="w-full sm:w-[140px]">
              <Check className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All">All Status</SelectItem>
              <SelectItem value="installed">Installed</SelectItem>
              <SelectItem value="available">Available</SelectItem>
              <SelectItem value="beta">Beta</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={sortBy}
            onValueChange={(v: string) => setSortBy(v as 'newest' | 'popular' | 'rating')}
          >
            <SelectTrigger className="w-full sm:w-[140px]">
              <LayoutGrid className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="popular">Most Popular</SelectItem>
              <SelectItem value="newest">Newest</SelectItem>
              <SelectItem value="rating">Top Rated</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Grid */}
      {filteredPlugins.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredPlugins.map((plugin) => (
            <PluginCard
              key={plugin.id}
              plugin={plugin}
              onToggleInstall={() => handleToggleInstall(plugin.id)}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 text-center border rounded-xl bg-muted/20 border-dashed">
          <Search className="h-10 w-10 text-muted-foreground mb-4 opacity-50" />
          <h3 className="text-lg font-medium">No plugins found</h3>
          <p className="text-muted-foreground max-w-xs mx-auto">
            Try adjusting your search or filters to find what you're looking for.
          </p>
          <Button variant="link" onClick={() => { setSearchQuery(''); setCategoryFilter('All'); setStatusFilter('All'); }}>
            Clear all filters
          </Button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Sub-components
// ============================================================================

interface PluginCardProps {
  plugin: Plugin;
  onToggleInstall: () => void;
}

function PluginCard({ plugin, onToggleInstall }: PluginCardProps) {
  const isInstalled = plugin.status === 'installed';
  const isBeta = plugin.status === 'beta';

  return (
    <Card className={cn(
      "group flex flex-col h-full transition-all hover:shadow-md hover:border-primary/50 overflow-hidden",
      plugin.isREEVU && "border-purple-200 dark:border-purple-900/50 bg-purple-50/10"
    )}>
      <CardHeader className="relative pb-2">
        <div className="flex items-start justify-between">
          <div className="p-2 rounded-lg bg-background border shadow-sm group-hover:scale-110 transition-transform">
            {plugin.icon}
          </div>
          <div className="flex flex-col items-end gap-1">
            {plugin.isREEVU && (
              <Badge variant="secondary" className="bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 text-[10px] h-5 uppercase tracking-wider font-bold">
                REEVU
              </Badge>
            )}
            {isBeta && (
              <Badge variant="outline" className="text-[10px] h-5 uppercase tracking-wider font-bold border-amber-200 text-amber-700 bg-amber-50">
                BETA
              </Badge>
            )}
          </div>
        </div>
        <CardTitle className="mt-4 line-clamp-1">{plugin.name}</CardTitle>
        <CardDescription className="line-clamp-2 h-10 text-xs">
          {plugin.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 pb-4">
        <div className="flex flex-wrap gap-1.5 mb-4">
          {plugin.tags.slice(0, 3).map(tag => (
            <Badge key={tag} variant="secondary" className="text-[10px] font-normal py-0">
              {tag}
            </Badge>
          ))}
        </div>

        <div className="space-y-2 text-xs text-muted-foreground">
          <div className="flex items-center justify-between">
            <span className="flex items-center">
              <Star className="h-3 w-3 mr-1 fill-amber-400 text-amber-400" />
              {plugin.rating}
            </span>
            <span className="flex items-center">
              <Download className="h-3 w-3 mr-1" />
              {plugin.downloads.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="truncate max-w-[100px]">{plugin.author}</span>
            <span className="flex items-center">
              <Clock className="h-3 w-3 mr-1" />
              {new Date(plugin.lastUpdated).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}
            </span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-0 border-t bg-muted/30 p-3">
        {isInstalled ? (
          <div className="flex items-center w-full gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1 text-xs h-8 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 dark:border-red-900/50 dark:hover:bg-red-950/30"
              onClick={onToggleInstall}
            >
              <Trash2 className="h-3 w-3 mr-1.5" />
              Uninstall
            </Button>
            <Button size="sm" className="flex-1 text-xs h-8">
              Configure
            </Button>
          </div>
        ) : (
          <Button
            className="w-full text-xs h-8"
            variant={plugin.isREEVU ? "default" : "secondary"}
            onClick={onToggleInstall}
          >
            <Download className="h-3 w-3 mr-1.5" />
            Install {isBeta ? 'Beta' : ''}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}

export default PluginDiscoveryGrid;
