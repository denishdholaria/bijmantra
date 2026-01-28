/**
 * Dispatch History Page - View past dispatches
 * Connected to /api/v2/traceability endpoints
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Truck, Search, RefreshCw, Package, 
  Calendar, MapPin, User, ChevronDown, ChevronUp 
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface Dispatch {
  id: string;
  date: string;
  recipient: string;
  recipient_address: string;
  transfer_type: string;
  lots: { lot_id: string; variety: string; quantity_kg: number }[];
  total_quantity_kg: number;
  status: 'pending' | 'shipped' | 'delivered' | 'cancelled';
}

export function DispatchHistory() {
  const [dispatches, setDispatches] = useState<Dispatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Would fetch from a dispatches endpoint
      const response = await apiClient.traceabilityService.getTraceabilityTransfers();
      // Transform transfers to dispatch format
      const dispatchMap = new Map<string, Dispatch>();
      (response.data || []).forEach((transfer: any) => {
        const dispatchId = transfer.dispatch_id || `DSP-${transfer.id}`;
        if (!dispatchMap.has(dispatchId)) {
          dispatchMap.set(dispatchId, {
            id: dispatchId,
            date: transfer.transfer_date || transfer.created_at?.split('T')[0] || new Date().toISOString().split('T')[0],
            recipient: transfer.to_entity_name || 'Unknown',
            recipient_address: transfer.delivery_address || '',
            transfer_type: transfer.transfer_type || 'sale',
            lots: [],
            total_quantity_kg: 0,
            status: transfer.status || 'delivered',
          });
        }
        const dispatch = dispatchMap.get(dispatchId)!;
        dispatch.lots.push({
          lot_id: transfer.lot_id,
          variety: transfer.variety_name || '',
          quantity_kg: transfer.quantity_kg || 0,
        });
        dispatch.total_quantity_kg += transfer.quantity_kg || 0;
      });
      setDispatches(Array.from(dispatchMap.values()));
    } catch (err) {
      // No data available - show empty state
      setDispatches([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredDispatches = dispatches.filter(d =>
    d.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.recipient.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.lots.some(l => l.lot_id.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const totalDispatched = dispatches.reduce((sum, d) => sum + d.total_quantity_kg, 0);
  const deliveredCount = dispatches.filter(d => d.status === 'delivered').length;
  const pendingCount = dispatches.filter(d => d.status === 'pending' || d.status === 'shipped').length;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'delivered': return <Badge className="bg-green-100 text-green-700">Delivered</Badge>;
      case 'shipped': return <Badge className="bg-blue-100 text-blue-700">Shipped</Badge>;
      case 'pending': return <Badge className="bg-yellow-100 text-yellow-700">Pending</Badge>;
      case 'cancelled': return <Badge className="bg-red-100 text-red-700">Cancelled</Badge>;
      default: return <Badge>{status}</Badge>;
    }
  };

  const getTransferTypeBadge = (type: string) => {
    switch (type) {
      case 'sale': return <Badge variant="outline">Sale</Badge>;
      case 'internal': return <Badge variant="outline" className="border-purple-300 text-purple-700">Internal</Badge>;
      case 'donation': return <Badge variant="outline" className="border-green-300 text-green-700">Donation</Badge>;
      case 'sample': return <Badge variant="outline" className="border-orange-300 text-orange-700">Sample</Badge>;
      default: return <Badge variant="outline">{type}</Badge>;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Truck className="h-6 w-6 text-blue-600" />
            Dispatch History
          </h1>
          <p className="text-gray-500 text-sm">View and track past dispatches</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
              <Truck className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{dispatches.length}</p>
              <p className="text-sm text-gray-500">Total Dispatches</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
              <Package className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{(totalDispatched / 1000).toFixed(1)}t</p>
              <p className="text-sm text-gray-500">Total Dispatched</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
              <Package className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{deliveredCount}</p>
              <p className="text-sm text-gray-500">Delivered</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
              <Truck className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{pendingCount}</p>
              <p className="text-sm text-gray-500">In Transit</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Search dispatches..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Dispatches List */}
      <div className="space-y-4">
        {loading ? (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              Loading dispatch history...
            </CardContent>
          </Card>
        ) : filteredDispatches.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              <Truck className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No dispatches found</p>
            </CardContent>
          </Card>
        ) : (
          filteredDispatches.map((dispatch) => (
            <Card key={dispatch.id}>
              <CardContent className="p-4">
                <div 
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => setExpandedId(expandedId === dispatch.id ? null : dispatch.id)}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center">
                      <Truck className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{dispatch.id}</p>
                        {getStatusBadge(dispatch.status)}
                        {getTransferTypeBadge(dispatch.transfer_type)}
                      </div>
                      <p className="text-sm text-gray-500">{dispatch.recipient}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-medium">{dispatch.total_quantity_kg} kg</p>
                      <p className="text-sm text-gray-500">{dispatch.lots.length} lots</p>
                    </div>
                    <div className="text-right hidden md:block">
                      <p className="text-sm text-gray-500 flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {dispatch.date}
                      </p>
                    </div>
                    {expandedId === dispatch.id ? (
                      <ChevronUp className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedId === dispatch.id && (
                  <div className="mt-4 pt-4 border-t space-y-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="flex items-start gap-2">
                        <User className="h-4 w-4 text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium">Recipient</p>
                          <p className="text-sm text-gray-600">{dispatch.recipient}</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-2">
                        <MapPin className="h-4 w-4 text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium">Delivery Address</p>
                          <p className="text-sm text-gray-600">{dispatch.recipient_address}</p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-medium mb-2">Lots Included</p>
                      <div className="space-y-2">
                        {dispatch.lots.map((lot) => (
                          <div key={lot.lot_id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                            <div>
                              <p className="font-medium">{lot.lot_id}</p>
                              <p className="text-sm text-gray-500">{lot.variety}</p>
                            </div>
                            <p className="font-medium">{lot.quantity_kg} kg</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

export default DispatchHistory;
