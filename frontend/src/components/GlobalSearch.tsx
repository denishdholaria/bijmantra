import * as React from 'react';
import { useNavigate } from 'react-router-dom';
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
import { cn } from '@/lib/utils';

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

// Demo search results - in production, this would come from an API
const demoResults: SearchResult[] = [
  { id: '1', type: 'germplasm', title: 'IR64', subtitle: 'Rice variety', path: '/germplasm/1', tags: ['rice', 'indica'] },
  { id: '2', type: 'germplasm', title: 'Swarna', subtitle: 'Rice variety', path: '/germplasm/2', tags: ['rice', 'indica'] },
  { id: '3', type: 'trial', title: 'Yield Trial 2025', subtitle: 'Multi-location trial', path: '/trials/1' },
  { id: '4', type: 'study', title: 'Disease Resistance Study', subtitle: 'Bacterial blight screening', path: '/studies/1' },
  { id: '5', type: 'location', title: 'IRRI Los Baños', subtitle: 'Philippines', path: '/locations/1' },
  { id: '6', type: 'person', title: 'Dr. Jane Smith', subtitle: 'Lead Breeder', path: '/people/1' },
  { id: '7', type: 'page', title: 'Dashboard', subtitle: 'Main dashboard', path: '/' },
  { id: '8', type: 'page', title: 'Germplasm Collection', subtitle: 'Browse all germplasm', path: '/germplasm' },
  { id: '9', type: 'page', title: 'Field Book', subtitle: 'Data collection', path: '/field-book' },
  { id: '10', type: 'page', title: 'Crossing Planner', subtitle: 'Plan crosses', path: '/crossing-planner' },
  { id: '11', type: 'setting', title: 'Profile Settings', subtitle: 'Update your profile', path: '/profile' },
  { id: '12', type: 'setting', title: 'System Settings', subtitle: 'Configure system', path: '/system-settings' },
];

const recentSearches = ['IR64', 'Yield Trial', 'Disease Resistance'];

export function GlobalSearch({ open, onOpenChange }: GlobalSearchProps) {
  const navigate = useNavigate();
  const [query, setQuery] = React.useState('');
  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const results = React.useMemo(() => {
    if (!query) return [];
    const lower = query.toLowerCase();
    return demoResults.filter(
      (r) =>
        r.title.toLowerCase().includes(lower) ||
        r.subtitle?.toLowerCase().includes(lower) ||
        r.tags?.some((t) => t.toLowerCase().includes(lower))
    );
  }, [query]);

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
  }, [query]);

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

          {query && results.length === 0 && (
            <div className="p-8 text-center text-muted-foreground">
              <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No results found for "{query}"</p>
              <p className="text-sm mt-1">Try a different search term</p>
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
