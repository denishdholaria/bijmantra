import { useState, useMemo } from 'react';
import { Search, Filter, SortAsc, SortDesc, Grid, List, X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface SearchFilter {
  id: string;
  label: string;
  type: 'select' | 'multiselect' | 'range' | 'boolean';
  options?: { value: string; label: string }[];
  value?: string | string[] | boolean | [number, number];
}

interface SortOption {
  id: string;
  label: string;
  field: string;
}

interface SearchResultsProps<T> {
  results: T[];
  isLoading?: boolean;
  totalCount?: number;
  query?: string;
  onQueryChange?: (query: string) => void;
  filters?: SearchFilter[];
  onFilterChange?: (filterId: string, value: unknown) => void;
  sortOptions?: SortOption[];
  currentSort?: string;
  sortDirection?: 'asc' | 'desc';
  onSortChange?: (sortId: string, direction: 'asc' | 'desc') => void;
  renderItem: (item: T, index: number) => React.ReactNode;
  renderGridItem?: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
  className?: string;
}

export function SearchResults<T>({
  results,
  isLoading = false,
  totalCount,
  query = '',
  onQueryChange,
  filters = [],
  onFilterChange,
  sortOptions = [],
  currentSort,
  sortDirection = 'asc',
  onSortChange,
  renderItem,
  renderGridItem,
  keyExtractor,
  emptyMessage = 'No results found',
  className,
}: SearchResultsProps<T>) {
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [showFilters, setShowFilters] = useState(false);

  const activeFilters = filters.filter(f => {
    if (f.type === 'boolean') return f.value === true;
    if (f.type === 'multiselect') return Array.isArray(f.value) && f.value.length > 0;
    return f.value !== undefined && f.value !== '';
  });

  const clearFilter = (filterId: string) => {
    const filter = filters.find(f => f.id === filterId);
    if (!filter || !onFilterChange) return;
    
    if (filter.type === 'boolean') onFilterChange(filterId, false);
    else if (filter.type === 'multiselect') onFilterChange(filterId, []);
    else onFilterChange(filterId, undefined);
  };

  const clearAllFilters = () => {
    filters.forEach(f => clearFilter(f.id));
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search..."
            value={query}
            onChange={(e) => onQueryChange?.(e.target.value)}
            className="pl-9"
          />
          {query && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
              onClick={() => onQueryChange?.('')}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {filters.length > 0 && (
          <Button
            variant={showFilters ? 'secondary' : 'outline'}
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
            {activeFilters.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {activeFilters.length}
              </Badge>
            )}
          </Button>
        )}

        {sortOptions.length > 0 && (
          <Select
            value={currentSort}
            onValueChange={(v) => onSortChange?.(v, sortDirection)}
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              {sortOptions.map((option) => (
                <SelectItem key={option.id} value={option.id}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {currentSort && (
          <Button
            variant="outline"
            size="icon"
            onClick={() => onSortChange?.(currentSort, sortDirection === 'asc' ? 'desc' : 'asc')}
          >
            {sortDirection === 'asc' ? (
              <SortAsc className="h-4 w-4" />
            ) : (
              <SortDesc className="h-4 w-4" />
            )}
          </Button>
        )}

        {renderGridItem && (
          <div className="flex border rounded-md">
            <Button
              variant={viewMode === 'list' ? 'secondary' : 'ghost'}
              size="icon"
              className="rounded-r-none"
              onClick={() => setViewMode('list')}
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
              size="icon"
              className="rounded-l-none"
              onClick={() => setViewMode('grid')}
            >
              <Grid className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && filters.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4">
              {filters.map((filter) => (
                <div key={filter.id} className="min-w-[150px]">
                  <label className="text-sm font-medium mb-1 block">{filter.label}</label>
                  {filter.type === 'select' && filter.options && (
                    <Select
                      value={filter.value as string || '__all__'}
                      onValueChange={(v) => onFilterChange?.(filter.id, v === '__all__' ? undefined : v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">All</SelectItem>
                        {filter.options.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                  {filter.type === 'boolean' && (
                    <label className="flex items-center gap-2 mt-2">
                      <Checkbox
                        checked={filter.value as boolean || false}
                        onCheckedChange={(checked) => onFilterChange?.(filter.id, !!checked)}
                      />
                      <span className="text-sm">Enabled</span>
                    </label>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Filters */}
      {activeFilters.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Active filters:</span>
          {activeFilters.map((filter) => (
            <Badge key={filter.id} variant="secondary" className="gap-1">
              {filter.label}: {String(filter.value)}
              <button onClick={() => clearFilter(filter.id)} className="ml-1 hover:text-destructive">
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          <Button variant="ghost" size="sm" onClick={clearAllFilters}>
            Clear all
          </Button>
        </div>
      )}

      {/* Results Count */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {isLoading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Searching...
            </span>
          ) : (
            `${results.length}${totalCount ? ` of ${totalCount}` : ''} results`
          )}
        </span>
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : results.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>{emptyMessage}</p>
          {query && <p className="text-sm mt-1">Try adjusting your search or filters</p>}
        </div>
      ) : viewMode === 'grid' && renderGridItem ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {results.map((item, index) => (
            <div key={keyExtractor(item)}>{renderGridItem(item, index)}</div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {results.map((item, index) => (
            <div key={keyExtractor(item)}>{renderItem(item, index)}</div>
          ))}
        </div>
      )}
    </div>
  );
}

// Hook for managing search state
export function useSearchState<T>(
  initialQuery = '',
  initialFilters: Record<string, unknown> = {},
  initialSort?: { field: string; direction: 'asc' | 'desc' }
) {
  const [query, setQuery] = useState(initialQuery);
  const [filters, setFilters] = useState(initialFilters);
  const [sort, setSort] = useState(initialSort);

  const updateFilter = (key: string, value: unknown) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({});
  };

  const updateSort = (field: string, direction: 'asc' | 'desc') => {
    setSort({ field, direction });
  };

  const reset = () => {
    setQuery(initialQuery);
    setFilters(initialFilters);
    setSort(initialSort);
  };

  return {
    query,
    setQuery,
    filters,
    updateFilter,
    clearFilters,
    sort,
    updateSort,
    reset,
  };
}
