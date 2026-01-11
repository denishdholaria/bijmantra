/**
 * Germplasm Exchange Page
 * 
 * Manage incoming and outgoing germplasm requests and transfers.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ExchangeRequest {
  id: string;
  type: 'incoming' | 'outgoing';
  requestNumber: string;
  institution: string;
  accessions: number;
  status: 'pending' | 'approved' | 'shipped' | 'received' | 'rejected';
  requestDate: string;
  smta: boolean;
}

export function GermplasmExchange() {
  const [filter, setFilter] = useState<'all' | 'incoming' | 'outgoing'>('all');

  const { data: requests } = useQuery<ExchangeRequest[]>({
    queryKey: ['seed-bank', 'exchanges'],
    queryFn: async () => [
      { id: '1', type: 'outgoing', requestNumber: 'EX-2024-045', institution: 'CIMMYT', accessions: 25, status: 'approved', requestDate: '2024-11-20', smta: true },
      { id: '2', type: 'incoming', requestNumber: 'EX-2024-044', institution: 'IRRI', accessions: 50, status: 'shipped', requestDate: '2024-11-15', smta: true },
      { id: '3', type: 'outgoing', requestNumber: 'EX-2024-043', institution: 'ICRISAT', accessions: 15, status: 'pending', requestDate: '2024-11-10', smta: true },
      { id: '4', type: 'incoming', requestNumber: 'EX-2024-042', institution: 'USDA-GRIN', accessions: 30, status: 'received', requestDate: '2024-11-05', smta: true },
    ],
  });

  const filteredRequests = requests?.filter(r => filter === 'all' || r.type === filter) || [];

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Germplasm Exchange</h1>
          <p className="text-gray-600 mt-1">Manage germplasm requests and transfers</p>
        </div>
        <Button>📝 New Request</Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {(['all', 'incoming', 'outgoing'] as const).map((f) => (
          <Button key={f} variant={filter === f ? 'default' : 'outline'} size="sm" onClick={() => setFilter(f)}>
            {f === 'all' ? '📋 All' : f === 'incoming' ? '📥 Incoming' : '📤 Outgoing'}
          </Button>
        ))}
      </div>

      {/* Requests Table */}
      <Card>
        <CardHeader>
          <CardTitle>Exchange Requests</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
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
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredRequests.map((req) => (
                  <tr key={req.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-green-600">{req.requestNumber}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-lg">{req.type === 'incoming' ? '📥' : '📤'}</span>
                    </td>
                    <td className="px-4 py-3">{req.institution}</td>
                    <td className="px-4 py-3 text-right font-mono">{req.accessions}</td>
                    <td className="px-4 py-3 text-center">{req.smta ? '✅' : '❌'}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(req.status)}`}>
                        {req.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{new Date(req.requestDate).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="outline" size="sm">View</Button>
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

export default GermplasmExchange;
