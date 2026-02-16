/**
 * Accessions List Page
 * 
 * Browse and manage germplasm accessions in the seed bank.
 */

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient } from '@/lib/api-client';
import { RefreshCw } from 'lucide-react';

interface Accession {
  id: string;
  accession_number: string;
  genus: string;
  species: string;
  common_name: string;
  origin: string;
  collection_date: string;
  vault_id: string;
  seed_count: number;
  viability: number;
  status: 'active' | 'depleted' | 'regenerating';
}

interface AccessionResponse {
  items: Accession[];
  total: number;
  page?: number;
  page_size?: number;
}

export function Accessions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [page, setPage] = useState(0);
  const queryClient = useQueryClient();
  const pageSize = 20;

  const { data, isLoading, error } = useQuery<AccessionResponse>({
    queryKey: ['seed-bank', 'accessions', page, search],
    queryFn: async () => {
      return await apiClient.accessionService.getAccessions(page, pageSize, search || undefined);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    setSearchParams(search ? { search } : {});
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'depleted': return 'bg-red-100 text-red-800';
      case 'regenerating': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getViabilityColor = (viability: number) => {
    if (viability >= 85) return 'text-green-600';
    if (viability >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const accessions = data?.items || [];
  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="space-y-4 lg:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Accessions</h1>
          <p className="text-gray-600 mt-1">Manage germplasm accessions in the seed bank</p>
        </div>
        <Button asChild>
          <Link to="/seed-bank/accessions/new">🌱 Register Accession</Link>
        </Button>
      </div>

      {/* Search & Filters */}
      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search by accession number, species, or origin..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
            <Button type="submit">🔍 Search</Button>
            {search && (
              <Button type="button" variant="outline" onClick={() => { setSearch(''); setSearchParams({}); }}>
                Clear
              </Button>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Accessions Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {Array(5).fill(0).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Accessions</h3>
              <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
              <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['seed-bank', 'accessions'] })}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : accessions.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">🌱</div>
              <h3 className="text-xl font-bold mb-2">No Accessions Found</h3>
              <p className="text-gray-600 mb-4">Start building your germplasm collection</p>
              <Button asChild>
                <Link to="/seed-bank/accessions/new">Register First Accession</Link>
              </Button>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px]">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Accession #</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Species</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Common Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Origin</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vault</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Seeds</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Viability</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {accessions.map((acc) => (
                      <tr key={acc.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <Link to={`/seed-bank/accessions/${acc.id}`} className="font-medium text-green-600 hover:underline">
                            {acc.accession_number}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-sm italic text-gray-700">
                          {acc.genus} {acc.species}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">{acc.common_name}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{acc.origin}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{acc.vault_id}</td>
                        <td className="px-4 py-3 text-sm text-right font-mono">{acc.seed_count.toLocaleString()}</td>
                        <td className={`px-4 py-3 text-sm text-right font-medium ${getViabilityColor(acc.viability)}`}>
                          {acc.viability}%
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(acc.status)}`}>
                            {acc.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Link to={`/seed-bank/accessions/${acc.id}`} className="text-blue-600 hover:underline text-sm">
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-4 py-3 border-t flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    Page {page + 1} of {totalPages} ({data?.total || 0} accessions)
                  </span>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default Accessions;
