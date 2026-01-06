/**
 * Viability Testing Page
 * 
 * Schedule and track germination tests for seed viability monitoring.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ViabilityTest {
  id: string;
  batchNumber: string;
  accessionNumber: string;
  species: string;
  testDate: string;
  seedsTested: number;
  germinated: number;
  germinationRate: number;
  status: 'scheduled' | 'in-progress' | 'completed';
  technician?: string;
}

export function ViabilityTesting() {
  const [view, setView] = useState<'pending' | 'completed'>('pending');

  const { data: tests } = useQuery<ViabilityTest[]>({
    queryKey: ['seed-bank', 'viability-tests', view],
    queryFn: async () => [
      { id: '1', batchNumber: 'VT-2024-091', accessionNumber: 'ACC-2024-0001', species: 'Triticum aestivum', testDate: '2024-12-10', seedsTested: 100, germinated: 0, germinationRate: 0, status: 'scheduled' },
      { id: '2', batchNumber: 'VT-2024-090', accessionNumber: 'ACC-2023-0456', species: 'Zea mays', testDate: '2024-12-05', seedsTested: 100, germinated: 45, germinationRate: 0, status: 'in-progress', technician: 'Dr. Sharma' },
      { id: '3', batchNumber: 'VT-2024-089', accessionNumber: 'ACC-2022-0789', species: 'Glycine max', testDate: '2024-11-28', seedsTested: 100, germinated: 98, germinationRate: 98, status: 'completed', technician: 'Dr. Patel' },
      { id: '4', batchNumber: 'VT-2024-088', accessionNumber: 'ACC-2021-0234', species: 'Solanum lycopersicum', testDate: '2024-11-25', seedsTested: 100, germinated: 72, germinationRate: 72, status: 'completed', technician: 'Dr. Kumar' },
    ],
  });

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      scheduled: 'bg-blue-100 text-blue-800',
      'in-progress': 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const getViabilityColor = (rate: number) => {
    if (rate >= 85) return 'text-green-600';
    if (rate >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Viability Testing</h1>
          <p className="text-gray-600 mt-1">Schedule and track germination tests</p>
        </div>
        <Button>🔬 Schedule Test</Button>
      </div>

      {/* View Toggle */}
      <div className="flex gap-2">
        <Button variant={view === 'pending' ? 'default' : 'outline'} size="sm" onClick={() => setView('pending')}>
          ⏳ Pending Tests
        </Button>
        <Button variant={view === 'completed' ? 'default' : 'outline'} size="sm" onClick={() => setView('completed')}>
          ✅ Completed
        </Button>
      </div>

      {/* Tests Table */}
      <Card>
        <CardHeader>
          <CardTitle>Viability Tests</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Accession</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Species</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Test Date</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Result</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {tests?.map((test) => (
                  <tr key={test.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-green-600">{test.batchNumber}</td>
                    <td className="px-4 py-3 font-mono text-sm">{test.accessionNumber}</td>
                    <td className="px-4 py-3 italic text-gray-700">{test.species}</td>
                    <td className="px-4 py-3 text-sm">{new Date(test.testDate).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(test.status)}`}>
                        {test.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {test.status === 'completed' ? (
                        <span className={`font-bold ${getViabilityColor(test.germinationRate)}`}>
                          {test.germinationRate}%
                        </span>
                      ) : test.status === 'in-progress' ? (
                        <span className="text-gray-500">{test.germinated}/{test.seedsTested}</span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="outline" size="sm">
                        {test.status === 'scheduled' ? 'Start' : test.status === 'in-progress' ? 'Update' : 'View'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ViabilityTesting;
