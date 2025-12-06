/**
 * Irrigation Page
 *
 * Track water usage and irrigation events.
 * Connected to backend: /api/v2/field-environment/irrigation
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface IrrigationEvent {
  id: string;
  field_id: string;
  irrigation_type: string;
  event_date: string;
  duration_hours: number;
  water_volume: number;
  source: string;
  cost: number | null;
  notes: string;
}

interface WaterSummary {
  field_id: string;
  total_events: number;
  total_volume_m3: number;
  total_hours: number;
  total_cost: number;
  avg_volume_per_event: number;
}

export function Irrigation() {
  const [events, setEvents] = useState<IrrigationEvent[]>([]);
  const [summary, setSummary] = useState<WaterSummary | null>(null);
  const [irrigationTypes, setIrrigationTypes] = useState<{value: string; name: string}[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    field_id: 'field-001',
    irrigation_type: 'drip',
    duration_hours: 2,
    water_volume: 50,
    source: 'borewell',
    cost: 0,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [eventsRes, typesRes, summaryRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/field-environment/irrigation`),
        fetch(`${API_BASE}/api/v2/field-environment/irrigation-types`),
        fetch(`${API_BASE}/api/v2/field-environment/irrigation/summary/field-001`),
      ]);
      if (eventsRes.ok) setEvents(await eventsRes.json());
      if (typesRes.ok) {
        const data = await typesRes.json();
        setIrrigationTypes(data.irrigation_types || []);
      }
      if (summaryRes.ok) setSummary(await summaryRes.json());
    } catch (error) {
      console.error('Failed to fetch irrigation data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEvent = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/field-environment/irrigation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        toast({ title: 'Success', description: 'Irrigation event logged' });
        setDialogOpen(false);
        fetchData();
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to log event', variant: 'destructive' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Irrigation</h1>
          <p className="text-gray-600 mt-1">Track water usage and irrigation events</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild><Button>+ Log Irrigation</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Log Irrigation Event</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Field ID</Label><Input value={formData.field_id} onChange={(e) => setFormData({...formData, field_id: e.target.value})} /></div>
                <div><Label>Type</Label>
                  <Select value={formData.irrigation_type} onValueChange={(v) => setFormData({...formData, irrigation_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{irrigationTypes.map((t) => (<SelectItem key={t.value} value={t.value}>{t.name.replace('_', ' ')}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Duration (hours)</Label><Input type="number" step="0.5" value={formData.duration_hours} onChange={(e) => setFormData({...formData, duration_hours: parseFloat(e.target.value)})} /></div>
                <div><Label>Volume (m³)</Label><Input type="number" value={formData.water_volume} onChange={(e) => setFormData({...formData, water_volume: parseFloat(e.target.value)})} /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Source</Label><Input placeholder="borewell, canal..." value={formData.source} onChange={(e) => setFormData({...formData, source: e.target.value})} /></div>
                <div><Label>Cost</Label><Input type="number" value={formData.cost} onChange={(e) => setFormData({...formData, cost: parseFloat(e.target.value)})} /></div>
              </div>
              <Button onClick={handleAddEvent} className="w-full">Log Event</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <p className="text-3xl font-bold text-blue-700">{summary?.total_volume_m3.toLocaleString() || 0}</p>
            <p className="text-sm text-blue-600">Total Water (m³)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{summary?.total_events || 0}</p>
            <p className="text-sm text-gray-600">Irrigation Events</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{summary?.total_hours.toFixed(1) || 0}</p>
            <p className="text-sm text-gray-600">Total Hours</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">₹{summary?.total_cost.toLocaleString() || 0}</p>
            <p className="text-sm text-gray-600">Total Cost</p>
          </CardContent>
        </Card>
      </div>

      {/* Events Table */}
      <Card>
        <CardHeader><CardTitle>💧 Irrigation History</CardTitle></CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {loading ? <p className="p-4 text-gray-500">Loading...</p> : events.length === 0 ? <p className="p-4 text-gray-500">No irrigation events yet</p> : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Field</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Duration</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Volume</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {events.map((e) => (
                  <tr key={e.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-600">{e.event_date}</td>
                    <td className="px-4 py-3 font-medium">{e.field_id}</td>
                    <td className="px-4 py-3 capitalize">{e.irrigation_type.replace('_', ' ')}</td>
                    <td className="px-4 py-3 text-right">{e.duration_hours}h</td>
                    <td className="px-4 py-3 text-right">{e.water_volume} m³</td>
                    <td className="px-4 py-3 text-gray-600">{e.source || '-'}</td>
                    <td className="px-4 py-3 text-right">{e.cost ? `₹${e.cost}` : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default Irrigation;
