import { useState } from 'react';
import { Search, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useDebounce } from '@/hooks/useDebounce';
import { useAccessionSearch } from './hooks/useAccessionSearch';

interface AccessionSearchPageProps {
  onSelectAccession?: (accessionId: string) => void;
  selectedAccessionId?: string | null;
}

const PAGE_SIZE = 10;

function getStatusTone(status: string) {
  const normalized = status.toLowerCase();
  if (normalized.includes('active')) {
    return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300';
  }
  if (normalized.includes('depleted') || normalized.includes('failed')) {
    return 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300';
  }
  return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300';
}

export function AccessionSearchPage({
  onSelectAccession,
  selectedAccessionId,
}: AccessionSearchPageProps) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const debouncedQuery = useDebounce(query, 300);

  const searchQuery = useAccessionSearch({
    query: debouncedQuery,
    page,
    pageSize: PAGE_SIZE,
  });

  const result = searchQuery.data;
  const items = result?.items ?? [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-4">
          <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <CardTitle className="text-2xl">Accession Search</CardTitle>
              <CardDescription>
                Search by accession number, germplasm name, species, or free-text keywords.
              </CardDescription>
            </div>
            <Button
              variant="outline"
              onClick={() => searchQuery.refetch()}
              disabled={searchQuery.isFetching}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${searchQuery.isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>

          <div className="relative max-w-xl">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              aria-label="Search accessions"
              className="pl-9"
              placeholder="Try IR64, wheat, accession code, or collection keywords"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(0);
              }}
            />
          </div>
        </CardHeader>
      </Card>

      {searchQuery.isLoading ? (
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-80" />
          </CardHeader>
          <CardContent className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-12 w-full" />
            ))}
          </CardContent>
        </Card>
      ) : searchQuery.isError ? (
        <Card className="border-destructive/40">
          <CardHeader>
            <CardTitle>Unable to load accessions</CardTitle>
            <CardDescription>
              {searchQuery.error instanceof Error
                ? searchQuery.error.message
                : 'The search request failed.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => searchQuery.refetch()}>Retry Search</Button>
          </CardContent>
        </Card>
      ) : items.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No matching accessions</CardTitle>
            <CardDescription>
              Refine the search phrase, try a species name, or remove extra filters from the query.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <Card>
          <CardHeader className="gap-2">
            <CardTitle>Search Results</CardTitle>
            <CardDescription>
              Showing {items.length} accession{items.length === 1 ? '' : 's'} on page {page + 1}
              {result ? ` of ${result.totalPages}` : ''}.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Accession</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Species</TableHead>
                  <TableHead>Institute</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => {
                  const isSelected = item.id === selectedAccessionId;
                  return (
                    <TableRow
                      key={item.id}
                      data-state={isSelected ? 'selected' : undefined}
                    >
                      <TableCell className="font-medium">
                        <button
                          type="button"
                          className="text-left text-primary hover:underline"
                          onClick={() => onSelectAccession?.(item.id)}
                        >
                          {item.accessionNumber}
                        </button>
                      </TableCell>
                      <TableCell>{item.name}</TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span>{item.species}</span>
                          {item.subspecies ? (
                            <span className="text-xs text-muted-foreground">{item.subspecies}</span>
                          ) : null}
                        </div>
                      </TableCell>
                      <TableCell>{item.institute}</TableCell>
                      <TableCell>
                        <Badge className={getStatusTone(item.status)}>{item.status}</Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>

            <div className="flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                {result?.total ?? items.length} total accession
                {result && result.total === 1 ? '' : 's'} in the current result set.
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((currentPage) => Math.max(0, currentPage - 1))}
                  disabled={page === 0}
                >
                  <ChevronLeft className="mr-1 h-4 w-4" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setPage((currentPage) =>
                      result ? Math.min(result.totalPages - 1, currentPage + 1) : currentPage + 1
                    )
                  }
                  disabled={Boolean(result && page >= result.totalPages - 1)}
                >
                  Next
                  <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
