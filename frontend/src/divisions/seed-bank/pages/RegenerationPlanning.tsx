/**
 * Regeneration Planning Page
 *
 * Plan and track seed regeneration activities for maintaining viability.
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
import type { SeedBankRegenerationTask } from '@/lib/api/seed-bank/regeneration';

interface RegenerationTaskView extends SeedBankRegenerationTask {
  accession?: SeedBankAccession;
}

interface RegenerationFormState {
  accessionId: string;
  reason: 'low-viability' | 'low-quantity' | 'scheduled';
  priority: 'high' | 'medium' | 'low';
  targetQuantity: string;
  plannedSeason: string;
}

const initialFormState: RegenerationFormState = {
  accessionId: '',
  reason: 'low-viability',
  priority: 'medium',
  targetQuantity: '',
  plannedSeason: '',
};

export function RegenerationPlanning() {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formState, setFormState] = useState<RegenerationFormState>(initialFormState);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: tasks = [], isLoading } = useQuery<SeedBankRegenerationTask[]>({
    queryKey: ['seed-bank', 'regeneration-tasks'],
    queryFn: () => apiClient.regenerationService.getRegenerationTasks(),
  });

  const { data: accessionResponse } = useQuery<SeedBankAccessionListResponse>({
    queryKey: ['seed-bank', 'accessions', 'regeneration-selector'],
    queryFn: () => apiClient.accessionService.getAccessions(),
  });

  const accessions = accessionResponse?.data || [];
  const accessionLookup = useMemo(
    () => new Map(accessions.map(accession => [accession.id, accession])),
    [accessions],
  );

  const taskViews: RegenerationTaskView[] = useMemo(
    () => tasks.map(task => ({ ...task, accession: accessionLookup.get(task.accession_id) })),
    [accessionLookup, tasks],
  );

  const createTaskMutation = useMutation({
    mutationFn: () => apiClient.regenerationService.createRegenerationTask({
      accession_id: formState.accessionId,
      reason: formState.reason,
      priority: formState.priority,
      target_quantity: Number(formState.targetQuantity),
      planned_season: formState.plannedSeason.trim() || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seed-bank', 'regeneration-tasks'] });
      setShowCreateDialog(false);
      setFormState(initialFormState);
      toast({
        title: 'Regeneration task created',
        description: 'The regeneration queue has been updated with the new task.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Unable to create regeneration task',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const getPriorityBadge = (priority: string) => {
    const styles: Record<string, string> = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800',
    };
    return styles[priority] || 'bg-gray-100 text-gray-800';
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      planned: 'bg-blue-100 text-blue-800',
      'in-progress': 'bg-purple-100 text-purple-800',
      harvested: 'bg-orange-100 text-orange-800',
      completed: 'bg-green-100 text-green-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const getReasonIcon = (reason: string) => {
    switch (reason) {
      case 'low-viability': return '⚠️';
      case 'low-quantity': return '📉';
      case 'scheduled': return '📅';
      default: return '📋';
    }
  };

  const highPriorityCount = taskViews.filter(task => task.priority === 'high').length;
  const inProgressCount = taskViews.filter(task => task.status === 'in-progress').length;
  const completedCount = taskViews.filter(task => task.status === 'completed').length;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formState.accessionId) {
      toast({
        title: 'Accession is required',
        description: 'Select an accession before creating a regeneration task.',
        variant: 'destructive',
      });
      return;
    }

    if (!formState.targetQuantity || Number.isNaN(Number(formState.targetQuantity)) || Number(formState.targetQuantity) <= 0) {
      toast({
        title: 'Target quantity is required',
        description: 'Enter a positive target quantity for the regeneration task.',
        variant: 'destructive',
      });
      return;
    }

    createTaskMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Regeneration Planning</h1>
          <p className="text-gray-600 mt-1">Plan and track seed regeneration activities</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>Plan Regeneration</Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Create Regeneration Task</DialogTitle>
              <DialogDescription>
                Add a new regeneration task using live seed-bank accessions.
              </DialogDescription>
            </DialogHeader>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="regeneration-accession">Accession</Label>
                <select
                  id="regeneration-accession"
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
                  <Label htmlFor="regeneration-reason">Reason</Label>
                  <select
                    id="regeneration-reason"
                    className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={formState.reason}
                    onChange={event => setFormState(current => ({ ...current, reason: event.target.value as RegenerationFormState['reason'] }))}
                  >
                    <option value="low-viability">Low viability</option>
                    <option value="low-quantity">Low quantity</option>
                    <option value="scheduled">Scheduled regeneration</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="regeneration-priority">Priority</Label>
                  <select
                    id="regeneration-priority"
                    className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={formState.priority}
                    onChange={event => setFormState(current => ({ ...current, priority: event.target.value as RegenerationFormState['priority'] }))}
                  >
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="regeneration-target">Target quantity</Label>
                  <Input
                    id="regeneration-target"
                    type="number"
                    min="1"
                    value={formState.targetQuantity}
                    onChange={event => setFormState(current => ({ ...current, targetQuantity: event.target.value }))}
                    placeholder="2500"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="regeneration-season">Planned season</Label>
                  <Input
                    id="regeneration-season"
                    value={formState.plannedSeason}
                    onChange={event => setFormState(current => ({ ...current, plannedSeason: event.target.value }))}
                    placeholder="Kharif 2026"
                  />
                </div>
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createTaskMutation.isPending}>
                  {createTaskMutation.isPending ? 'Saving...' : 'Create Task'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{highPriorityCount}</div>
            <div className="text-sm text-gray-500">High Priority</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{inProgressCount}</div>
            <div className="text-sm text-gray-500">In Progress</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{taskViews.length}</div>
            <div className="text-sm text-gray-500">Total Planned</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{completedCount}</div>
            <div className="text-sm text-gray-500">Completed</div>
          </CardContent>
        </Card>
      </div>

      {/* Tasks Table */}
      <Card>
        <CardHeader>
          <CardTitle>Regeneration Queue</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading regeneration tasks...</div>
          ) : taskViews.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No regeneration tasks are scheduled for this organization yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Accession</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Species</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Reason</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Priority</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Viability</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Target</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Season</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {taskViews.map(task => (
                    <tr key={task.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-sm text-green-600">{task.accession?.accession_number || task.accession_id}</td>
                      <td className="px-4 py-3 italic text-gray-700">{task.accession ? `${task.accession.genus} ${task.accession.species}` : 'Unknown accession'}</td>
                      <td className="px-4 py-3 text-center">
                        <span title={task.reason}>{getReasonIcon(task.reason)}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityBadge(task.priority)}`}>
                          {task.priority}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-medium">{task.accession?.viability != null ? `${task.accession.viability}%` : '—'}</td>
                      <td className="px-4 py-3 text-right font-mono text-sm">{task.accession?.seed_count ?? '—'}</td>
                      <td className="px-4 py-3 text-right font-mono text-sm">{task.target_quantity}</td>
                      <td className="px-4 py-3 text-sm">{task.planned_season || '—'}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(task.status)}`}>
                          {task.status}
                        </span>
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

export default RegenerationPlanning;
