import * as React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Dna,
  FlaskConical,
  Leaf,
  MapPin,
  Users,
  FileText,
  Settings,
  Clock,
  ArrowRight,
  Command,
  Filter,
  Wheat,
  Factory,
  Microscope,
  Building2,
  CloudRain,
  Droplets,
  Mountain,
  Loader2,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { useActiveWorkspace } from '@/store/workspaceStore';
import { isRouteInWorkspace } from '@/framework/registry/workspaces';
import type { WorkspaceId } from '@/types/workspace';
import { apiClient } from '@/lib/api-client';

interface SearchResult {
  id: string;
  type: 'germplasm' | 'trial' | 'study' | 'location' | 'person' | 'page' | 'setting';
  title: string;
  subtitle?: string;
  path: string;
  tags?: string[];
}

interface GlobalSearchProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const typeIcons: Record<SearchResult['type'], React.ReactNode> = {
  germplasm: <Dna className="h-4 w-4" />,
  trial: <FlaskConical className="h-4 w-4" />,
  study: <Leaf className="h-4 w-4" />,
  location: <MapPin className="h-4 w-4" />,
  person: <Users className="h-4 w-4" />,
  page: <FileText className="h-4 w-4" />,
  setting: <Settings className="h-4 w-4" />,
};

const typeLabels: Record<SearchResult['type'], string> = {
  germplasm: 'Germplasm',
  trial: 'Trial',
  study: 'Study',
  location: 'Location',
  person: 'Person',
  page: 'Page',
  setting: 'Setting',
};

// Static page results - these are navigation shortcuts, not data
const staticPageResults: SearchResult[] = [
  { id: 'page-1', type: 'page', title: 'Dashboard', subtitle: 'Main dashboard', path: '/' },
  { id: 'page-2', type: 'page', title: 'Germplasm Collection', subtitle: 'Browse all germplasm', path: '/germplasm' },
  { id: 'page-3', type: 'page', title: 'Field Book', subtitle: 'Data collection', path: '/field-book' },
  { id: 'page-4', type: 'page', title: 'Crossing Planner', subtitle: 'Plan crosses', path: '/crossing-planner' },
  { id: 'page-5', type: 'page', title: 'Trials', subtitle: 'Manage trials', path: '/trials' },
  { id: 'page-6', type: 'page', title: 'Studies', subtitle: 'Research studies', path: '/studies' },
  { id: 'page-7', type: 'page', title: 'Locations', subtitle: 'Field locations', path: '/locations' },
  { id: 'setting-1', type: 'setting', title: 'Profile Settings', subtitle: 'Update your profile', path: '/profile' },
  { id: 'setting-2', type: 'setting', title: 'System Settings', subtitle: 'Configure system', path: '/system-settings' },
];

const recentSearches = ['IR64', 'Yield Trial', 'Disease Resistance'];

// Debounce hook for search
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value);
  React.useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

// Workspace icons for badges
const workspaceIcons: Record<WorkspaceId, React.ReactNode> = {
  breeding: <Wheat className="h-3 w-3" />,
  'seed-ops': <Factory className="h-3 w-3" />,
  research: <Microscope className="h-3 w-3" />,
  genebank: <Building2 className="h-3 w-3" />,
  admin: <Settings className="h-4 w-4 text-slate-500" />,
  atmosphere: <CloudRain className="h-4 w-4 text-blue-500" />,
  hydrology: <Droplets className="h-4 w-4 text-cyan-500" />,
  lithosphere: <Mountain className="h-4 w-4 text-amber-700" />,
  biosphere: <Leaf className="h-4 w-4 text-green-600" />,
};

export function GlobalSearch({ open, onOpenChange }: GlobalSearchProps) {
  const navigate = useNavigate();
  const [query, setQuery] = React.useState('');
  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const [filterByWorkspace, setFilterByWorkspace] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const activeWorkspace = useActiveWorkspace();
  
  // Debounce search query to avoid excessive API calls
  const debouncedQuery = useDebounce(query, 300);

  // Search germplasm from API
  const { data: germplasmResults, isLoading: germplasmLoading } = useQuery({
    queryKey: ['global-search-germplasm', debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery || debouncedQuery.length < 2) return [];
      try {
        const response = await apiClient.germplasmService.getGermplasm(0, 10, debouncedQuery);
        const data = response?.result?.data || [];
        return data.map((g: any) => ({
          id: `germplasm-${g.germplasmDbId}`,
          type: 'germplasm' as const,
          title: g.germplasmName || g.germplasmDbId,
          subtitle: g.commonCropName || g.genus || 'Germplasm',
          path: `/germplasm/${g.germplasmDbId}`,
          tags: [g.commonCropName, g.subtaxa].filter(Boolean),
        }));
      } catch {
        return [];
      }
    },
    enabled: debouncedQuery.length >= 2,
    staleTime: 30000,
  });

  // Search trials from API
  const { data: trialResults, isLoading: trialsLoading } = useQuery({
    queryKey: ['global-search-trials', debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery || debouncedQuery.length < 2) return [];
      try {
        const response = await apiClient.trialService.getTrials(0, 10);
        const data = response?.result?.data || [];
        // Filter client-side since BrAPI trials endpoint may not support name search
        return data
          .filter((t: any) => 
            t.trialName?.toLowerCase().includes(debouncedQuery.toLowerCase()) ||
            t.trialDescription?.toLowerCase().includes(debouncedQuery.toLowerCase())
          )
          .slice(0, 5)
          .map((t: any) => ({
            id: `trial-${t.trialDbId}`,
            type: 'trial' as const,
            title: t.trialName || t.trialDbId,
            subtitle: t.trialDescription || 'Trial',
            path: `/trials/${t.trialDbId}`,
          }));
      } catch {
        return [];
      }
    },
    enabled: debouncedQuery.length >= 2,
    staleTime: 30000,
  });

  // Search studies from API
  const { data: studyResults, isLoading: studiesLoading } = useQuery({
    queryKey: ['global-search-studies', debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery || debouncedQuery.length < 2) return [];
      try {
        const response = await apiClient.studyService.getStudies(0, 10);
        const data = response?.result?.data || [];
        return data
          .filter((s: any) => 
            s.studyName?.toLowerCase().includes(debouncedQuery.toLowerCase()) ||
            s.studyDescription?.toLowerCase().includes(debouncedQuery.toLowerCase())
          )
          .slice(0, 5)
          .map((s: any) => ({
            id: `study-${s.studyDbId}`,
            type: 'study' as const,
            title: s.studyName || s.studyDbId,
            subtitle: s.studyDescription || 'Study',
            path: `/studies/${s.studyDbId}`,
          }));
      } catch {
        return [];
      }
    },
    enabled: debouncedQuery.length >= 2,
    staleTime: 30000,
  });

  // Search locations from API
  const { data: locationResults, isLoading: locationsLoading } = useQuery({
    queryKey: ['global-search-locations', debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery || debouncedQuery.length < 2) return [];
      try {
        const response = await apiClient.locationService.getLocations(0, 10);
        const data = response?.result?.data || [];
        return data
          .filter((l: any) => 
            l.locationName?.toLowerCase().includes(debouncedQuery.toLowerCase()) ||
            l.countryName?.toLowerCase().includes(debouncedQuery.toLowerCase())
          )
          .slice(0, 5)
          .map((l: any) => ({
            id: `location-${l.locationDbId}`,
            type: 'location' as const,
            title: l.locationName || l.locationDbId,
            subtitle: l.countryName || 'Location',
            path: `/locations/${l.locationDbId}`,
          }));
      } catch {
        return [];
      }
    },
    enabled: debouncedQuery.length >= 2,
    staleTime: 30000,
  });

  const isLoading = germplasmLoading || trialsLoading || studiesLoading || locationsLoading;

  // Combine API results with static page results
  const results = React.useMemo(() => {
    if (!query) return [];
    const lower = query.toLowerCase();
    
    // Filter static pages/settings by query
    const filteredPages = staticPageResults.filter(
      (r) =>
        r.title.toLowerCase().includes(lower) ||
        r.subtitle?.toLowerCase().includes(lower)
    );
    
    // Combine all results
    let allResults: SearchResult[] = [
      ...(germplasmResults || []),
      ...(trialResults || []),
      ...(studyResults || []),
      ...(locationResults || []),
      ...filteredPages,
    ];
    
    // Filter by workspace if enabled
    if (filterByWorkspace && activeWorkspace) {
      allResults = allResults.filter(r => isRouteInWorkspace(r.path, activeWorkspace.id));
    }
    
    return allResults;
  }, [query, germplasmResults, trialResults, studyResults, locationResults, filterByWorkspace, activeWorkspace]);

  const groupedResults = React.useMemo(() => {
    const groups: Record<string, SearchResult[]> = {};
    results.forEach((r) => {
      if (!groups[r.type]) groups[r.type] = [];
      groups[r.type].push(r);
    });
    return groups;
  }, [results]);

  const flatResults = React.useMemo(() => {
    return Object.values(groupedResults).flat();
  }, [groupedResults]);

  React.useEffect(() => {
    if (open) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  React.useEffect(() => {
    setSelectedIndex(0);
  }, [query, filterByWorkspace, germplasmResults, trialResults, studyResults, locationResults]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, flatResults.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && flatResults[selectedIndex]) {
      e.preventDefault();
      navigate(flatResults[selectedIndex].path);
      onOpenChange(false);
    }
  };

  const handleSelect = (result: SearchResult) => {
    navigate(result.path);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl p-0 gap-0">
        <DialogHeader className="sr-only">
          <DialogTitle>Search</DialogTitle>
        </DialogHeader>
        <div className="flex items-center border-b px-3">
          <Search className="h-4 w-4 text-muted-foreground mr-2" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search germplasm, trials, pages..."
            className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 h-12"
          />
          <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            <span className="text-xs">ESC</span>
          </kbd>
        </div>

        {/* Workspace filter toggle */}
        {activeWorkspace && (
          <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Label htmlFor="workspace-filter" className="text-sm text-muted-foreground cursor-pointer">
                Search in {activeWorkspace.name} only
              </Label>
            </div>
            <Switch
              id="workspace-filter"
              checked={filterByWorkspace}
              onCheckedChange={setFilterByWorkspace}
              aria-label={`Filter results to ${activeWorkspace.name} workspace`}
            />
          </div>
        )}

        <ScrollArea className="max-h-[400px]">
          {!query && (
            <div className="p-4">
              <p className="text-xs font-medium text-muted-foreground mb-2">
                Recent Searches
              </p>
              <div className="space-y-1">
                {recentSearches.map((search) => (
                  <button
                    key={search}
                    className="flex items-center gap-2 w-full px-2 py-1.5 text-sm rounded hover:bg-accent"
                    onClick={() => setQuery(search)}
                  >
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    {search}
                  </button>
                ))}
              </div>

              <p className="text-xs font-medium text-muted-foreground mt-4 mb-2">
                Quick Actions
              </p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { label: 'New Germplasm', path: '/germplasm/new', icon: Dna },
                  { label: 'New Trial', path: '/trials/new', icon: FlaskConical },
                  { label: 'Field Book', path: '/field-book', icon: FileText },
                  { label: 'Settings', path: '/settings', icon: Settings },
                ].map((action) => (
                  <button
                    key={action.path}
                    className="flex items-center gap-2 px-3 py-2 text-sm rounded border hover:bg-accent"
                    onClick={() => {
                      navigate(action.path);
                      onOpenChange(false);
                    }}
                  >
                    <action.icon className="h-4 w-4" />
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {query && results.length === 0 && !isLoading && (
            <div className="p-8 text-center text-muted-foreground">
              <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No results found for "{query}"</p>
              <p className="text-sm mt-1">Try a different search term</p>
            </div>
          )}

          {query && isLoading && (
            <div className="p-8 text-center text-muted-foreground">
              <Loader2 className="h-8 w-8 mx-auto mb-2 animate-spin" />
              <p>Searching...</p>
            </div>
          )}

          {query && results.length > 0 && (
            <div className="p-2">
              {Object.entries(groupedResults).map(([type, items]) => (
                <div key={type} className="mb-2">
                  <p className="text-xs font-medium text-muted-foreground px-2 py-1">
                    {typeLabels[type as SearchResult['type']]}
                  </p>
                  {items.map((result) => {
                    const index = flatResults.indexOf(result);
                    return (
                      <button
                        key={result.id}
                        className={cn(
                          'flex items-center gap-3 w-full px-2 py-2 rounded text-left',
                          index === selectedIndex
                            ? 'bg-accent'
                            : 'hover:bg-accent/50'
                        )}
                        onClick={() => handleSelect(result)}
                        onMouseEnter={() => setSelectedIndex(index)}
                      >
                        <div className="flex-shrink-0 text-muted-foreground">
                          {typeIcons[result.type]}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {result.title}
                          </p>
                          {result.subtitle && (
                            <p className="text-xs text-muted-foreground truncate">
                              {result.subtitle}
                            </p>
                          )}
                        </div>
                        {result.tags && result.tags.length > 0 && (
                          <div className="flex gap-1">
                            {result.tags.slice(0, 2).map((tag) => (
                              <Badge
                                key={tag}
                                variant="secondary"
                                className="text-xs"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                        <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100" />
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        <div className="flex items-center justify-between border-t px-3 py-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="px-1 rounded bg-muted">↑</kbd>
              <kbd className="px-1 rounded bg-muted">↓</kbd>
              to navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 rounded bg-muted">↵</kbd>
              to select
            </span>
          </div>
          <span className="flex items-center gap-1">
            <Command className="h-3 w-3" />K to open
          </span>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default GlobalSearch;
