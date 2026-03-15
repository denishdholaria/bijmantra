/**
 * Viability Testing Page
 *
 * Schedule and track germination tests for seed viability monitoring.
 */

import { FormEvent, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api-client';
import type { SeedBankAccession, SeedBankAccessionListResponse } from '@/lib/api/seed-bank/accessions';
import type { SeedBankViabilityTest } from '@/lib/api/seed-bank/viability';

interface ViabilityTestView extends SeedBankViabilityTest {
  accession?: SeedBankAccession;
}

interface ViabilityFormState {
  accessionId: string;
  testDate: string;
  seedsTested: string;
}

const initialFormState: ViabilityFormState = {
  accessionId: '',
  testDate: new Date().toISOString().slice(0, 10),
  seedsTested: '100',
};

export function ViabilityTesting() {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [view, setView] = useState<'pending' | 'completed'>('pending');
  const [formState, setFormState] = useState<ViabilityFormState>(initialFormState);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: tests = [], isLoading } = useQuery<SeedBankViabilityTest[]>({
    queryKey: ['seed-bank', 'viability-tests'],
    queryFn: () => apiClient.viabilityService.getViabilityTests(),
  });

  const { data: accessionResponse } = useQuery<SeedBankAccessionListResponse>({
    queryKey: ['seed-bank', 'accessions', 'viability-selector'],
    queryFn: () => apiClient.accessionService.getAccessions(),
  });

  const accessions = accessionResponse?.data || [];
  const accessionLookup = useMemo(
    () => new Map(accessions.map(accession => [accession.id, accession])),
    [accessions],
  );

  const testViews: ViabilityTestView[] = useMemo(
    () => tests.map(test => ({ ...test, accession: accessionLookup.get(test.accession_id) })),
    [accessionLookup, tests],
  );

  const filteredTests = useMemo(
    () => testViews.filter(test => view === 'pending' ? test.status !== 'completed' : test.status === 'completed'),
    [testViews, view],
  );

  const createViabilityTestMutation = useMutation({
    mutationFn: () => apiClient.viabilityService.createViabilityTest({
      accession_id: formState.accessionId,
      test_date: `${formState.testDate}T00:00:00`,
      seeds_tested: Number(formState.seedsTested),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seed-bank', 'viability-tests'] });
      setShowCreateDialog(false);
      setFormState(initialFormState);
      toast({
        title: 'Viability test scheduled',
        description: 'The live viability queue has been updated.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Unable to schedule viability test',
        description: error.message,
        variant: 'destructive',
      });
    },
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

  const pendingCount = testViews.filter(test => test.status !== 'completed').length;
  const completedCount = testViews.filter(test => test.status === 'completed').length;
  const averageCompletedRate = completedCount > 0
    ? Math.round(
      testViews
        .filter(test => test.status === 'completed')
        .reduce((sum, test) => sum + test.germination_rate, 0) / completedCount,
    )
    : 0;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!formState.accessionId) {
      toast({
        title: 'Accession is required',
        description: 'Select an accession before scheduling a viability test.',
        variant: 'destructive',
      });
      return;
    }

    if (!formState.testDate) {
      toast({
        title: 'Test date is required',
        description: 'Choose a test date before scheduling the viability test.',
        variant: 'destructive',
      });
      return;
    }

    if (!formState.seedsTested || Number.isNaN(Number(formState.seedsTested)) || Number(formState.seedsTested) <= 0) {
      toast({
        title: 'Seeds tested must be positive',
        description: 'Enter a positive seed count for the viability test.',
        variant: 'destructive',
      });
      return;
    }

    createViabilityTestMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Viability Testing</h1>
          <p className="text-gray-600 mt-1">Schedule and track germination tests</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>Schedule Test</Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Schedule Viability Test</DialogTitle>
              <DialogDescription>
                Add a germination test using live seed-bank accessions.
              </DialogDescription>
            </DialogHeader>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="viability-accession">Accession</Label>
                <select
                  id="viability-accession"
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={formState.accessionId}
                  onChange={event => setFormState(current => ({ ...current, accessionId: event.target.value }))}
                >
                  <option value="">Select an accession</option>
                  {accessions.map(accession => (
                    <option key={accession.id} value={accession.id}>
                      {accession.accession_number} - {accession.genus} {accession.species}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="viability-date">Test date</Label>
                  <Input
                    id="viability-date"
                    type="date"
                    value={formState.testDate}
                    onChange={event => setFormState(current => ({ ...current, testDate: event.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="viability-seeds-tested">Seeds tested</Label>
                  <Input
                    id="viability-seeds-tested"
                    type="number"
                    min="1"
                    value={formState.seedsTested}
                    onChange={event => setFormState(current => ({ ...current, seedsTested: event.target.value }))}
                  />
                </div>
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createViabilityTestMutation.isPending}>
                  {createViabilityTestMutation.isPending ? 'Saving...' : 'Schedule Test'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{pendingCount}</div>
            <div className="text-sm text-gray-500">Pending Tests</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{completedCount}</div>
            <div className="text-sm text-gray-500">Completed Tests</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{testViews.length}</div>
            <div className="text-sm text-gray-500">Total Scheduled</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-amber-600">{averageCompletedRate}%</div>
            <div className="text-sm text-gray-500">Avg Completed Rate</div>
          </CardContent>
        </Card>
      </div>

      {/* View Toggle */}
      <div className="flex gap-2">
        <Button variant={view === 'pending' ? 'default' : 'outline'} size="sm" onClick={() => setView('pending')}>
          Pending Tests
        </Button>
        <Button variant={view === 'completed' ? 'default' : 'outline'} size="sm" onClick={() => setView('completed')}>
          Completed
        </Button>
      </div>

      {/* Tests Table */}
      <Card>
        <CardHeader>
          <CardTitle>Viability Tests</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading viability tests...</div>
          ) : filteredTests.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {view === 'pending'
                ? 'No pending viability tests are scheduled for this organization yet.'
                : 'No completed viability tests are available for this organization yet.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch #</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Accession</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Species</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Test Date</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Seeds</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredTests.map(test => (
                    <tr key={test.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-green-600">{test.batch_number}</td>
                      <td className="px-4 py-3 font-mono text-sm">{test.accession?.accession_number || test.accession_id}</td>
                      <td className="px-4 py-3 italic text-gray-700">{test.accession ? `${test.accession.genus} ${test.accession.species}` : 'Unknown accession'}</td>
                      <td className="px-4 py-3 text-sm">{new Date(test.test_date).toLocaleDateString()}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(test.status)}`}>
                          {test.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm">{test.seeds_tested}</td>
                      <td className="px-4 py-3 text-right">
                        {test.status === 'completed' ? (
                          <span className={`font-bold ${getViabilityColor(test.germination_rate)}`}>
                            {test.germination_rate}%
                          </span>
                        ) : test.status === 'in-progress' ? (
                          <span className="text-gray-500">{test.germinated}/{test.seeds_tested}</span>
                        ) : (
                          <span className="text-gray-400">Scheduled</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ViabilityTesting;
