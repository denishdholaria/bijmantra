/**
 * Create Dispatch Page - Create new seed dispatch orders
 * Connected to /api/v2/traceability endpoints
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Truck, Package, Search, Plus, Minus, 
  CheckCircle, AlertCircle, MapPin 
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface AvailableLot {
  lot_id: string;
  variety_name: string;
  crop: string;
  seed_class: string;
  quantity_kg: number;
  germination_percent?: number;
}

interface DispatchItem {
  lot_id: string;
  variety_name: string;
  quantity_kg: number;
  available_kg: number;
}

export function CreateDispatch() {
  const [availableLots, setAvailableLots] = useState<AvailableLot[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [dispatchItems, setDispatchItems] = useState<DispatchItem[]>([]);
  const [dispatch, setDispatch] = useState({
    to_entity_id: '',
    to_entity_name: '',
    transfer_type: 'sale',
    delivery_address: '',
    contact_person: '',
    contact_phone: '',
    notes: '',
  });
  const [success, setSuccess] = useState(false);

  const fetchLots = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getTraceabilityLots(undefined, undefined, undefined, 'active');
      setAvailableLots(res.data || []);
    } catch (err) {
      // No data available - show empty state
      setAvailableLots([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLots();
  }, []);

  const addLotToDispatch = (lot: AvailableLot) => {
    if (dispatchItems.find(i => i.lot_id === lot.lot_id)) return;
    setDispatchItems([...dispatchItems, {
      lot_id: lot.lot_id,
      variety_name: lot.variety_name,
      quantity_kg: Math.min(100, lot.quantity_kg),
      available_kg: lot.quantity_kg,
    }]);
  };

  const removeLotFromDispatch = (lotId: string) => {
    setDispatchItems(dispatchItems.filter(i => i.lot_id !== lotId));
  };

  const updateItemQuantity = (lotId: string, quantity: number) => {
    setDispatchItems(dispatchItems.map(i => 
      i.lot_id === lotId ? { ...i, quantity_kg: Math.min(quantity, i.available_kg) } : i
    ));
  };

  const totalQuantity = dispatchItems.reduce((sum, i) => sum + i.quantity_kg, 0);

  const handleSubmit = async () => {
    if (dispatchItems.length === 0) {
      alert('Please add at least one lot to dispatch');
      return;
    }
    if (!dispatch.to_entity_name || !dispatch.delivery_address) {
      alert('Please fill in recipient details');
      return;
    }

    setSubmitting(true);
    try {
      // Record transfer for each lot
      for (const item of dispatchItems) {
        await apiClient.recordLotTransfer(item.lot_id, {
          from_entity_id: 'SELF',
          from_entity_name: 'Seed Company',
          to_entity_id: dispatch.to_entity_id || dispatch.to_entity_name.toUpperCase().replace(/\s/g, '-'),
          to_entity_name: dispatch.to_entity_name,
          quantity_kg: item.quantity_kg,
          transfer_type: dispatch.transfer_type,
        });
      }
      setSuccess(true);
      setDispatchItems([]);
      setDispatch({
        to_entity_id: '',
        to_entity_name: '',
        transfer_type: 'sale',
        delivery_address: '',
        contact_person: '',
        contact_phone: '',
        notes: '',
      });
    } catch (err) {
      // API call failed - show error, no demo fallback
      alert('Failed to create dispatch. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredLots = availableLots.filter(lot =>
    lot.lot_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lot.variety_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lot.crop.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (success) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <Card className="border-green-300 bg-green-50">
          <CardContent className="py-12 text-center">
            <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-600" />
            <h2 className="text-2xl font-bold text-green-800 mb-2">Dispatch Created!</h2>
            <p className="text-green-700 mb-6">
              Your dispatch order has been recorded and is ready for shipment.
            </p>
            <Button onClick={() => setSuccess(false)}>
              Create Another Dispatch
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Truck className="h-6 w-6 text-blue-600" />
          Create Dispatch
        </h1>
        <p className="text-gray-500 text-sm">Create a new seed dispatch order</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Available Lots */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Available Lots</CardTitle>
            <CardDescription>Select lots to add to dispatch</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search lots..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="max-h-96 overflow-y-auto space-y-2">
              {loading ? (
                <p className="text-center text-gray-500 py-4">Loading lots...</p>
              ) : filteredLots.length === 0 ? (
                <p className="text-center text-gray-500 py-4">No lots available</p>
              ) : (
                filteredLots.map((lot) => {
                  const isAdded = dispatchItems.some(i => i.lot_id === lot.lot_id);
                  return (
                    <div
                      key={lot.lot_id}
                      className={`p-3 rounded-lg border ${isAdded ? 'border-green-300 bg-green-50' : 'border-gray-200'}`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{lot.lot_id}</p>
                          <p className="text-sm text-gray-500">{lot.variety_name} • {lot.crop}</p>
                          <div className="flex gap-2 mt-1">
                            <Badge className="bg-blue-100 text-blue-700">{lot.seed_class}</Badge>
                            <span className="text-sm text-gray-500">{lot.quantity_kg} kg</span>
                            {lot.germination_percent && (
                              <span className="text-sm text-gray-500">• {lot.germination_percent}% germ</span>
                            )}
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant={isAdded ? 'outline' : 'default'}
                          onClick={() => isAdded ? removeLotFromDispatch(lot.lot_id) : addLotToDispatch(lot)}
                        >
                          {isAdded ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>

        {/* Dispatch Details */}
        <div className="space-y-6">
          {/* Selected Items */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center justify-between">
                <span>Dispatch Items</span>
                <Badge>{dispatchItems.length} lots • {totalQuantity} kg</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dispatchItems.length === 0 ? (
                <p className="text-center text-gray-500 py-4">
                  <Package className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                  No lots selected
                </p>
              ) : (
                <div className="space-y-3">
                  {dispatchItems.map((item) => (
                    <div key={item.lot_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div>
                        <p className="font-medium">{item.lot_id}</p>
                        <p className="text-sm text-gray-500">{item.variety_name}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          value={item.quantity_kg}
                          onChange={(e) => updateItemQuantity(item.lot_id, Number(e.target.value))}
                          className="w-24 text-right"
                          min={1}
                          max={item.available_kg}
                        />
                        <span className="text-sm text-gray-500">kg</span>
                        <Button variant="ghost" size="sm" onClick={() => removeLotFromDispatch(item.lot_id)}>
                          <Minus className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recipient Details */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recipient Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Recipient Name *</Label>
                  <Input
                    value={dispatch.to_entity_name}
                    onChange={(e) => setDispatch({...dispatch, to_entity_name: e.target.value})}
                    placeholder="Company/Dealer name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Transfer Type</Label>
                  <Select value={dispatch.transfer_type} onValueChange={(v) => setDispatch({...dispatch, transfer_type: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sale">Sale</SelectItem>
                      <SelectItem value="internal">Internal Transfer</SelectItem>
                      <SelectItem value="donation">Donation</SelectItem>
                      <SelectItem value="sample">Sample</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Delivery Address *</Label>
                <Textarea
                  value={dispatch.delivery_address}
                  onChange={(e) => setDispatch({...dispatch, delivery_address: e.target.value})}
                  placeholder="Full delivery address"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Contact Person</Label>
                  <Input
                    value={dispatch.contact_person}
                    onChange={(e) => setDispatch({...dispatch, contact_person: e.target.value})}
                    placeholder="Name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Contact Phone</Label>
                  <Input
                    value={dispatch.contact_phone}
                    onChange={(e) => setDispatch({...dispatch, contact_phone: e.target.value})}
                    placeholder="Phone number"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={dispatch.notes}
                  onChange={(e) => setDispatch({...dispatch, notes: e.target.value})}
                  placeholder="Special instructions..."
                  rows={2}
                />
              </div>

              <Button 
                onClick={handleSubmit} 
                disabled={submitting || dispatchItems.length === 0}
                className="w-full"
              >
                {submitting ? 'Creating Dispatch...' : `Create Dispatch (${totalQuantity} kg)`}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default CreateDispatch;
