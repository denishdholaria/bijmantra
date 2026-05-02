/**
 * Dispatch History Page - View past dispatches
 * Connected to /api/v2/dispatch endpoints
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
  dispatch_id: string;
  dispatch_number: string;
  date: string;
  recipient_name: string;
  recipient_address: string;
  transfer_type: string;
  items: { lot_id: string; variety_name: string; quantity_kg: number }[];
  total_quantity_kg: number;
  status: string;
  invoice_number?: string | null;
  tracking_number?: string | null;
  carrier?: string | null;
}

export function DispatchHistory() {
  const [dispatches, setDispatches] = useState<Dispatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const shippedStatuses = ['shipped', 'in_transit', 'delivered'];
  const inTransitStatuses = ['shipped', 'in_transit'];

  const formatTotalDispatched = (quantityKg: number) => {
    if (quantityKg >= 1000) {
      return `${(quantityKg / 1000).toFixed(1)}t`;
    }

    return `${quantityKg.toFixed(quantityKg >= 100 ? 0 : 1)}kg`;
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await apiClient.dispatchService.getDispatches();
      setDispatches((response.data || []).map((dispatch: any) => ({
        dispatch_id: dispatch.dispatch_id,
        dispatch_number: dispatch.dispatch_number || dispatch.dispatch_id,
        date: (dispatch.delivered_at || dispatch.shipped_at || dispatch.created_at || new Date().toISOString()).split('T')[0],
        recipient_name: dispatch.recipient_name || 'Unknown',
        recipient_address: dispatch.recipient_address || '',
        transfer_type: dispatch.transfer_type || 'sale',
        items: (dispatch.items || []).map((item: any) => ({
          lot_id: item.lot_id,
          variety_name: item.variety_name || '',
          quantity_kg: item.quantity_kg || 0,
        })),
        total_quantity_kg: dispatch.total_quantity_kg || 0,
        status: dispatch.status || 'draft',
        invoice_number: dispatch.invoice_number,
        tracking_number: dispatch.tracking_number,
        carrier: dispatch.carrier,
      })));
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
    d.dispatch_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.recipient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.items.some(l => l.lot_id.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const totalDispatched = dispatches
    .filter(d => shippedStatuses.includes(d.status))
    .reduce((sum, d) => sum + d.total_quantity_kg, 0);
  const deliveredCount = dispatches.filter(d => d.status === 'delivered').length;
  const pendingCount = dispatches.filter(d => inTransitStatuses.includes(d.status)).length;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'delivered': return <Badge className="bg-green-100 text-green-700">Delivered</Badge>;
      case 'approved': return <Badge className="bg-indigo-100 text-indigo-700">Approved</Badge>;
      case 'draft': return <Badge className="bg-slate-100 text-slate-700">Draft</Badge>;
      case 'pending_approval': return <Badge className="bg-yellow-100 text-yellow-700">Pending Approval</Badge>;
      case 'picking': return <Badge className="bg-amber-100 text-amber-700">Picking</Badge>;
      case 'packed': return <Badge className="bg-cyan-100 text-cyan-700">Packed</Badge>;
      case 'shipped': return <Badge className="bg-blue-100 text-blue-700">Shipped</Badge>;
      case 'in_transit': return <Badge className="bg-sky-100 text-sky-700">In Transit</Badge>;
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
              <p className="text-2xl font-bold">{formatTotalDispatched(totalDispatched)}</p>
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
            <Card key={dispatch.dispatch_id}>
              <CardContent className="p-4">
                <div 
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => setExpandedId(expandedId === dispatch.dispatch_id ? null : dispatch.dispatch_id)}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center">
                      <Truck className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{dispatch.dispatch_number}</p>
                        {getStatusBadge(dispatch.status)}
                        {getTransferTypeBadge(dispatch.transfer_type)}
                      </div>
                      <p className="text-sm text-gray-500">{dispatch.recipient_name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-medium">{dispatch.total_quantity_kg} kg</p>
                      <p className="text-sm text-gray-500">{dispatch.items.length} lots</p>
                    </div>
                    <div className="text-right hidden md:block">
                      <p className="text-sm text-gray-500 flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {dispatch.date}
                      </p>
                    </div>
                    {expandedId === dispatch.dispatch_id ? (
                      <ChevronUp className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedId === dispatch.dispatch_id && (
                  <div className="mt-4 pt-4 border-t space-y-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="flex items-start gap-2">
                        <User className="h-4 w-4 text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium">Recipient</p>
                          <p className="text-sm text-gray-600">{dispatch.recipient_name}</p>
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

                    {(dispatch.invoice_number || dispatch.tracking_number || dispatch.carrier) && (
                      <div className="grid md:grid-cols-3 gap-4">
                        {dispatch.invoice_number && (
                          <div>
                            <p className="text-sm font-medium">Invoice</p>
                            <p className="text-sm text-gray-600">{dispatch.invoice_number}</p>
                          </div>
                        )}
                        {dispatch.tracking_number && (
                          <div>
                            <p className="text-sm font-medium">Tracking</p>
                            <p className="text-sm text-gray-600">{dispatch.tracking_number}</p>
                          </div>
                        )}
                        {dispatch.carrier && (
                          <div>
                            <p className="text-sm font-medium">Carrier</p>
                            <p className="text-sm text-gray-600">{dispatch.carrier}</p>
                          </div>
                        )}
                      </div>
                    )}

                    <div>
                      <p className="text-sm font-medium mb-2">Lots Included</p>
                      <div className="space-y-2">
                        {dispatch.items.map((lot) => (
                          <div key={lot.lot_id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                            <div>
                              <p className="font-medium">{lot.lot_id}</p>
                              <p className="text-sm text-gray-500">{lot.variety_name}</p>
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
