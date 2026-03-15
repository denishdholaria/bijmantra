/**
 * Germplasm Exchange Page
 *
 * Manage incoming and outgoing germplasm requests and transfers.
 */

import { FormEvent, useState } from 'react';
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
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api-client';
import type { SeedBankAccessionListResponse } from '@/lib/api/seed-bank/accessions';
import type { SeedBankExchange } from '@/lib/api/seed-bank/exchanges';

interface ExchangeFormState {
  type: 'incoming' | 'outgoing';
  institutionName: string;
  smta: boolean;
  notes: string;
  accessionIds: string[];
}

const initialFormState: ExchangeFormState = {
  type: 'outgoing',
  institutionName: '',
  smta: true,
  notes: '',
  accessionIds: [],
};

export function GermplasmExchange() {
  const [filter, setFilter] = useState<'all' | 'incoming' | 'outgoing'>('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formState, setFormState] = useState<ExchangeFormState>(initialFormState);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: requests = [], isLoading } = useQuery<SeedBankExchange[]>({
    queryKey: ['seed-bank', 'exchanges'],
    queryFn: () => apiClient.exchangeService.getExchanges(),
  });

  const { data: accessionResponse } = useQuery<SeedBankAccessionListResponse>({
    queryKey: ['seed-bank', 'accessions', 'exchange-selector'],
    queryFn: () => apiClient.accessionService.getAccessions(),
  });

  const availableAccessions = accessionResponse?.data || [];
  const filteredRequests = requests.filter(request => filter === 'all' || request.type === filter);

  const createExchangeMutation = useMutation({
    mutationFn: () => apiClient.exchangeService.createExchange({
      type: formState.type,
      institution_name: formState.institutionName.trim(),
      accession_ids: formState.accessionIds,
      smta: formState.smta,
      notes: formState.notes.trim() || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seed-bank', 'exchanges'] });
      setShowCreateDialog(false);
      setFormState(initialFormState);
      toast({
        title: 'Exchange request created',
        description: 'The germplasm exchange request was saved successfully.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Unable to create exchange request',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const pendingCount = requests.filter(request => request.status === 'pending').length;
  const incomingCount = requests.filter(request => request.type === 'incoming').length;
  const outgoingCount = requests.filter(request => request.type === 'outgoing').length;

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      shipped: 'bg-purple-100 text-purple-800',
      received: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const toggleAccessionSelection = (accessionId: string) => {
    setFormState(current => ({
      ...current,
      accessionIds: current.accessionIds.includes(accessionId)
        ? current.accessionIds.filter(id => id !== accessionId)
        : [...current.accessionIds, accessionId],
    }));
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formState.institutionName.trim()) {
      toast({
        title: 'Institution name is required',
        description: 'Provide the institution handling this exchange request.',
        variant: 'destructive',
      });
      return;
    }

    createExchangeMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Germplasm Exchange</h1>
          <p className="text-gray-600 mt-1">Manage germplasm requests and transfers</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>New Request</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create Germplasm Exchange Request</DialogTitle>
              <DialogDescription>
                Save an incoming or outgoing exchange request against live seed bank accessions.
              </DialogDescription>
            </DialogHeader>
            <form className="space-y-6" onSubmit={handleSubmit}>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="exchange-type">Exchange type</Label>
                  <select
                    id="exchange-type"
                    className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={formState.type}
                    onChange={event => setFormState(current => ({ ...current, type: event.target.value as 'incoming' | 'outgoing' }))}
                  >
                    <option value="incoming">Incoming</option>
                    <option value="outgoing">Outgoing</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="institution-name">Institution</Label>
                  <Input
                    id="institution-name"
                    value={formState.institutionName}
                    onChange={event => setFormState(current => ({ ...current, institutionName: event.target.value }))}
                    placeholder="IRRI, CIMMYT, USDA-GRIN"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="exchange-notes">Notes</Label>
                <Textarea
                  id="exchange-notes"
                  value={formState.notes}
                  onChange={event => setFormState(current => ({ ...current, notes: event.target.value }))}
                  placeholder="Purpose, shipping context, or compliance notes"
                />
              </div>

              <label className="flex items-center gap-3 rounded-md border p-3">
                <Checkbox
                  checked={formState.smta}
                  onCheckedChange={checked => setFormState(current => ({ ...current, smta: checked === true }))}
                />
                <div>
                  <p className="font-medium">Standard Material Transfer Agreement</p>
                  <p className="text-sm text-gray-500">Mark whether this exchange is covered by an SMTA.</p>
                </div>
              </label>

              <div className="space-y-3">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <Label>Accessions</Label>
                    <p className="text-sm text-gray-500">Select the accessions included in this request.</p>
                  </div>
                  <Badge variant="secondary">{formState.accessionIds.length} selected</Badge>
                </div>

                {availableAccessions.length === 0 ? (
                  <div className="rounded-md border border-dashed p-4 text-sm text-gray-500">
                    No accessions are available yet. Create accessions first, or save the exchange request without linked accessions.
                  </div>
                ) : (
                  <div className="max-h-64 space-y-2 overflow-y-auto rounded-md border p-3">
                    {availableAccessions.map(accession => (
                      <label key={accession.id} className="flex items-start gap-3 rounded-md border p-3">
                        <Checkbox
                          checked={formState.accessionIds.includes(accession.id)}
                          onCheckedChange={() => toggleAccessionSelection(accession.id)}
                        />
                        <div className="flex-1">
                          <div className="flex items-center justify-between gap-4">
                            <div>
                              <p className="font-medium">{accession.accession_number}</p>
                              <p className="text-sm text-gray-500">{accession.genus} {accession.species}</p>
                            </div>
                            <Badge variant="outline">{accession.seed_count ?? 0} seeds</Badge>
                          </div>
                          <p className="mt-1 text-sm text-gray-500">{accession.origin} {accession.collection_site ? `• ${accession.collection_site}` : ''}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createExchangeMutation.isPending}>
                  {createExchangeMutation.isPending ? 'Saving...' : 'Create Request'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-2xl font-semibold text-gray-900">{requests.length}</p>
            <p className="text-sm text-gray-500">Total requests</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-2xl font-semibold text-gray-900">{incomingCount}/{outgoingCount}</p>
            <p className="text-sm text-gray-500">Incoming / outgoing</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-2xl font-semibold text-gray-900">{pendingCount}</p>
            <p className="text-sm text-gray-500">Pending approval</p>
          </CardContent>
        </Card>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {(['all', 'incoming', 'outgoing'] as const).map((f) => (
          <Button key={f} variant={filter === f ? 'default' : 'outline'} size="sm" onClick={() => setFilter(f)}>
            {f === 'all' ? 'All' : f === 'incoming' ? 'Incoming' : 'Outgoing'}
          </Button>
        ))}
      </div>

      {/* Requests Table */}
      <Card>
        <CardHeader>
          <CardTitle>Exchange Requests</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading exchange requests...</div>
          ) : filteredRequests.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {requests.length === 0
                ? 'No exchange requests have been recorded for this organization yet.'
                : 'No exchange requests match the selected filter.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Request #</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Institution</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Accessions</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">SMTA</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredRequests.map(req => (
                    <tr key={req.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-green-600">{req.request_number}</td>
                      <td className="px-4 py-3 text-center">
                        <span className="inline-flex rounded-full bg-gray-100 px-2 py-1 text-xs font-medium capitalize text-gray-700">
                          {req.type}
                        </span>
                      </td>
                      <td className="px-4 py-3">{req.institution_name}</td>
                      <td className="px-4 py-3 text-right font-mono">{req.accession_count}</td>
                      <td className="px-4 py-3 text-center">{req.smta ? 'Yes' : 'No'}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(req.status)}`}>
                          {req.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{new Date(req.request_date).toLocaleDateString()}</td>
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

export default GermplasmExchange;
