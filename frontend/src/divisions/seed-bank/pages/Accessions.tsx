/**
 * Accessions List Page
 * 
 * Browse and manage germplasm accessions in the seed bank.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';

interface Accession {
  id: string;
  accessionNumber: string;
  genus: string;
  species: string;
  commonName: string;
  origin: string;
  collectionDate: string;
  vault: string;
  seedCount: number;
  viability: number;
  status: 'active' | 'depleted' | 'regenerating';
}

export function Accessions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const { data, isLoading, error } = useQuery({
    queryKey: ['seed-bank', 'accessions', page, search],
    queryFn: async () => ({
      data: [
        { id: '1', accessionNumber: 'ACC-2024-0001', genus: 'Triticum', species: 'aestivum', commonName: 'Bread Wheat', origin: 'India', collectionDate: '2024-03-15', vault: 'Base A', seedCount: 5000, viability: 98, status: 'active' },
        { id: '2', accessionNumber: 'ACC-2024-0002', genus: 'Oryza', species: 'sativa', commonName: 'Rice', origin: 'Thailand', collectionDate: '2024-02-20', vault: 'Base A', seedCount: 8000, viability: 95, status: 'active' },
        { id: '3', accessionNumber: 'ACC-2023-0456', genus: 'Zea', species: 'mays', commonName: 'Maize', origin: 'Mexico', collectionDate: '2023-08-10', vault: 'Active', seedCount: 200, viability: 72, status: 'regenerating' },
        { id: '4', accessionNumber: 'ACC-2022-0789', genus: 'Glycine', species: 'max', commonName: 'Soybean', origin: 'China', collectionDate: '2022-05-05', vault: 'Base B', seedCount: 3500, viability: 91, status: 'active' },
        { id: '5', accessionNumber: 'ACC-2021-0234', genus: 'Solanum', species: 'lycopersicum', commonName: 'Tomato', origin: 'Peru', collectionDate: '2021-11-22', vault: 'Cryo', seedCount: 1000, viability: 99, status: 'active' },
      ] as Accession[],
      pagination: { currentPage: 0, totalPages: 5, totalCount: 100 },
    }),
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

  const accessions = data?.data || [];
  const pagination = data?.pagination;

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
              <h3 className="text-lg font-semibold text-red-600">Error Loading Accessions</h3>
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
                            {acc.accessionNumber}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-sm italic text-gray-700">
                          {acc.genus} {acc.species}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">{acc.commonName}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{acc.origin}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{acc.vault}</td>
                        <td className="px-4 py-3 text-sm text-right font-mono">{acc.seedCount.toLocaleString()}</td>
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
              {pagination && pagination.totalPages > 1 && (
                <div className="px-4 py-3 border-t flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    Page {pagination.currentPage + 1} of {pagination.totalPages} ({pagination.totalCount} accessions)
                  </span>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= pagination.totalPages - 1}>
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
