/**
 * Harvest Management Page
 * 
 * Plan and record harvests, manage quality checks, and track storage.
 * Connects to /api/v2/harvest endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
import {
  Wheat,
  Plus,
  Calendar,
  Package,
  Scale,
  Thermometer,
  Droplets,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Warehouse,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface HarvestPlan {
  id: string;
  study_id: string;
  study_name: string;
  planned_date: string;
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled';
  notes?: string;
}

interface HarvestRecord {
  id: string;
  plan_id: string;
  plot_id: string;
  germplasm_name: string;
  harvest_date: string;
  wet_weight: number;
  dry_weight?: number;
  moisture_content?: number;
  quality_grade?: string;
  storage_unit?: string;
}

interface StorageUnit {
  id: string;
  name: string;
  type: string;
  capacity: number;
  current_stock: number;
  temperature?: number;
  humidity?: number;
}

// Demo data
const DEMO_PLANS: HarvestPlan[] = [
  { id: 'hp1', study_id: 's1', study_name: 'Rice Yield Trial 2024', planned_date: '2024-11-15', status: 'completed' },
  { id: 'hp2', study_id: 's2', study_name: 'Wheat Multi-Location', planned_date: '2024-12-01', status: 'in_progress' },
  { id: 'hp3', study_id: 's3', study_name: 'Maize Hybrid Evaluation', planned_date: '2024-12-20', status: 'planned' },
];

const DEMO_RECORDS: HarvestRecord[] = [
  { id: 'hr1', plan_id: 'hp1', plot_id: 'P001', germplasm_name: 'IR64', harvest_date: '2024-11-15', wet_weight: 5.2, dry_weight: 4.5, moisture_content: 13.5, quality_grade: 'A', storage_unit: 'Bin-01' },
  { id: 'hr2', plan_id: 'hp1', plot_id: 'P002', germplasm_name: 'Swarna', harvest_date: '2024-11-15', wet_weight: 4.8, dry_weight: 4.1, moisture_content: 14.2, quality_grade: 'A', storage_unit: 'Bin-01' },
  { id: 'hr3', plan_id: 'hp1', plot_id: 'P003', germplasm_name: 'MTU1010', harvest_date: '2024-11-16', wet_weight: 5.5, dry_weight: 4.7, moisture_content: 14.5, quality_grade: 'B', storage_unit: 'Bin-02' },
  { id: 'hr4', plan_id: 'hp2', plot_id: 'W001', germplasm_name: 'HD2967', harvest_date: '2024-12-01', wet_weight: 3.8, moisture_content: 12.0 },
  { id: 'hr5', plan_id: 'hp2', plot_id: 'W002', germplasm_name: 'PBW343', harvest_date: '2024-12-01', wet_weight: 4.1, moisture_content: 11.8 },
];

const DEMO_STORAGE: StorageUnit[] = [
  { id: 'su1', name: 'Bin-01', type: 'Grain Bin', capacity: 1000, current_stock: 450, temperature: 18, humidity: 55 },
  { id: 'su2', name: 'Bin-02', type: 'Grain Bin', capacity: 1000, current_stock: 280, temperature: 19, humidity: 58 },
  { id: 'su3', name: 'Cold-01', type: 'Cold Storage', capacity: 500, current_stock: 120, temperature: 4, humidity: 45 },
  { id: 'su4', name: 'Warehouse-A', type: 'Warehouse', capacity: 5000, current_stock: 2100, temperature: 22, humidity: 60 },
];

export function HarvestManagement() {
  const [activeTab, setActiveTab] = useState('plans');
  const [showNewPlan, setShowNewPlan] = useState(false);
  const [showNewRecord, setShowNewRecord] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [newPlan, setNewPlan] = useState({ study_id: '', planned_date: '', notes: '' });
  const [newRecord, setNewRecord] = useState({ plot_id: '', wet_weight: 0, moisture_content: 0 });
  const queryClient = useQueryClient();

  // Fetch harvest plans
  const { data: plans = DEMO_PLANS } = useQuery<HarvestPlan[]>({
    queryKey: ['harvest-plans'],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v2/harvest/plans`);
        if (!res.ok) return DEMO_PLANS;
        const data = await res.json();
        return Array.isArray(data) ? data : (data.plans || DEMO_PLANS);
      } catch {
        return DEMO_PLANS;
      }
    },
  });

  // Fetch harvest records
  const { data: records = DEMO_RECORDS } = useQuery<HarvestRecord[]>({
    queryKey: ['harvest-records', selectedPlan],
    queryFn: async () => {
      try {
        const url = selectedPlan 
          ? `${API_BASE}/api/v2/harvest/records?plan_id=${selectedPlan}`
          : `${API_BASE}/api/v2/harvest/records`;
        const res = await fetch(url);
        if (!res.ok) return selectedPlan ? DEMO_RECORDS.filter(r => r.plan_id === selectedPlan) : DEMO_RECORDS;
        const data = await res.json();
        return Array.isArray(data) ? data : (data.records || DEMO_RECORDS);
      } catch {
        return selectedPlan ? DEMO_RECORDS.filter(r => r.plan_id === selectedPlan) : DEMO_RECORDS;
      }
    },
  });

  // Fetch storage units
  const { data: storage = DEMO_STORAGE } = useQuery<StorageUnit[]>({
    queryKey: ['storage-units'],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v2/harvest/storage`);
        if (!res.ok) return DEMO_STORAGE;
        const data = await res.json();
        return Array.isArray(data) ? data : (data.units || DEMO_STORAGE);
      } catch {
        return DEMO_STORAGE;
      }
    },
  });

  // Create plan mutation
  const createPlanMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/harvest/plans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPlan),
      });
      if (!res.ok) throw new Error('Failed to create plan');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['harvest-plans'] });
      setShowNewPlan(false);
      setNewPlan({ study_id: '', planned_date: '', notes: '' });
    },
  });

  // Record harvest mutation
  const recordHarvestMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/harvest/records`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newRecord, plan_id: selectedPlan }),
      });
      if (!res.ok) throw new Error('Failed to record harvest');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['harvest-records'] });
      setShowNewRecord(false);
      setNewRecord({ plot_id: '', wet_weight: 0, moisture_content: 0 });
    },
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle2 className="h-3 w-3 mr-1" />Completed</Badge>;
      case 'in_progress':
        return <Badge className="bg-blue-100 text-blue-800"><Clock className="h-3 w-3 mr-1" />In Progress</Badge>;
      case 'planned':
        return <Badge className="bg-yellow-100 text-yellow-800"><Calendar className="h-3 w-3 mr-1" />Planned</Badge>;
      case 'cancelled':
        return <Badge className="bg-red-100 text-red-800"><AlertTriangle className="h-3 w-3 mr-1" />Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getGradeBadge = (grade?: string) => {
    if (!grade) return null;
    const colors: Record<string, string> = {
      'A': 'bg-green-100 text-green-800',
      'B': 'bg-blue-100 text-blue-800',
      'C': 'bg-yellow-100 text-yellow-800',
      'D': 'bg-red-100 text-red-800',
    };
    return <Badge className={colors[grade] || 'bg-gray-100'}>{grade}</Badge>;
  };

  // Calculate stats
  const totalHarvested = records.reduce((sum, r) => sum + (r.dry_weight || r.wet_weight), 0);
  const avgMoisture = records.length > 0 
    ? records.reduce((sum, r) => sum + (r.moisture_content || 0), 0) / records.filter(r => r.moisture_content).length
    : 0;
  const totalCapacity = storage.reduce((sum, s) => sum + s.capacity, 0);
  const totalStock = storage.reduce((sum, s) => sum + s.current_stock, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Wheat className="h-6 w-6" />
            Harvest Management
          </h1>
          <p className="text-muted-foreground">
            Plan harvests, record yields, and manage storage
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Scale className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{totalHarvested.toFixed(1)} kg</p>
                <p className="text-xs text-muted-foreground">Total Harvested</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Droplets className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{avgMoisture.toFixed(1)}%</p>
                <p className="text-xs text-muted-foreground">Avg Moisture</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Warehouse className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{((totalStock / totalCapacity) * 100).toFixed(0)}%</p>
                <p className="text-xs text-muted-foreground">Storage Used</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Package className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{records.length}</p>
                <p className="text-xs text-muted-foreground">Harvest Records</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="plans">
            <Calendar className="h-4 w-4 mr-2" />
            Harvest Plans
          </TabsTrigger>
          <TabsTrigger value="records">
            <Scale className="h-4 w-4 mr-2" />
            Records
          </TabsTrigger>
          <TabsTrigger value="storage">
            <Warehouse className="h-4 w-4 mr-2" />
            Storage
          </TabsTrigger>
        </TabsList>

        {/* Plans Tab */}
        <TabsContent value="plans">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Harvest Plans</span>
                <Dialog open={showNewPlan} onOpenChange={setShowNewPlan}>
                  <DialogTrigger asChild>
                    <Button size="sm">
                      <Plus className="h-4 w-4 mr-1" />
                      New Plan
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create Harvest Plan</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label>Study</Label>
                        <Input
                          value={newPlan.study_id}
                          onChange={(e) => setNewPlan({ ...newPlan, study_id: e.target.value })}
                          placeholder="Study ID or name"
                        />
                      </div>
                      <div>
                        <Label>Planned Date</Label>
                        <Input
                          type="date"
                          value={newPlan.planned_date}
                          onChange={(e) => setNewPlan({ ...newPlan, planned_date: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>Notes</Label>
                        <Input
                          value={newPlan.notes}
                          onChange={(e) => setNewPlan({ ...newPlan, notes: e.target.value })}
                          placeholder="Optional notes"
                        />
                      </div>
                      <Button onClick={() => createPlanMutation.mutate()} className="w-full">
                        Create Plan
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Study</TableHead>
                    <TableHead>Planned Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Records</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {plans.map(plan => {
                    const planRecords = records.filter(r => r.plan_id === plan.id);
                    return (
                      <TableRow key={plan.id}>
                        <TableCell className="font-medium">{plan.study_name}</TableCell>
                        <TableCell>{plan.planned_date}</TableCell>
                        <TableCell>{getStatusBadge(plan.status)}</TableCell>
                        <TableCell>{planRecords.length}</TableCell>
                        <TableCell>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => {
                              setSelectedPlan(plan.id);
                              setActiveTab('records');
                            }}
                          >
                            View Records
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Records Tab */}
        <TabsContent value="records">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span>Harvest Records</span>
                  <Select value={selectedPlan || 'all'} onValueChange={(v) => setSelectedPlan(v === 'all' ? null : v)}>
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="Filter by plan" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Plans</SelectItem>
                      {plans.map(p => (
                        <SelectItem key={p.id} value={p.id}>{p.study_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Dialog open={showNewRecord} onOpenChange={setShowNewRecord}>
                  <DialogTrigger asChild>
                    <Button size="sm" disabled={!selectedPlan}>
                      <Plus className="h-4 w-4 mr-1" />
                      Record Harvest
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Record Harvest</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label>Plot ID</Label>
                        <Input
                          value={newRecord.plot_id}
                          onChange={(e) => setNewRecord({ ...newRecord, plot_id: e.target.value })}
                          placeholder="e.g., P001"
                        />
                      </div>
                      <div>
                        <Label>Wet Weight (kg)</Label>
                        <Input
                          type="number"
                          step="0.1"
                          value={newRecord.wet_weight}
                          onChange={(e) => setNewRecord({ ...newRecord, wet_weight: parseFloat(e.target.value) })}
                        />
                      </div>
                      <div>
                        <Label>Moisture Content (%)</Label>
                        <Input
                          type="number"
                          step="0.1"
                          value={newRecord.moisture_content}
                          onChange={(e) => setNewRecord({ ...newRecord, moisture_content: parseFloat(e.target.value) })}
                        />
                      </div>
                      <Button onClick={() => recordHarvestMutation.mutate()} className="w-full">
                        Record
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Plot</TableHead>
                    <TableHead>Germplasm</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Wet (kg)</TableHead>
                    <TableHead className="text-right">Dry (kg)</TableHead>
                    <TableHead className="text-right">Moisture</TableHead>
                    <TableHead>Grade</TableHead>
                    <TableHead>Storage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {records.map(record => (
                    <TableRow key={record.id}>
                      <TableCell className="font-mono">{record.plot_id}</TableCell>
                      <TableCell>{record.germplasm_name}</TableCell>
                      <TableCell>{record.harvest_date}</TableCell>
                      <TableCell className="text-right font-mono">{record.wet_weight.toFixed(2)}</TableCell>
                      <TableCell className="text-right font-mono">{record.dry_weight?.toFixed(2) || '-'}</TableCell>
                      <TableCell className="text-right font-mono">{record.moisture_content?.toFixed(1)}%</TableCell>
                      <TableCell>{getGradeBadge(record.quality_grade)}</TableCell>
                      <TableCell>{record.storage_unit || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Storage Tab */}
        <TabsContent value="storage">
          <div className="grid md:grid-cols-2 gap-4">
            {storage.map(unit => (
              <Card key={unit.id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{unit.name}</span>
                    <Badge variant="outline">{unit.type}</Badge>
                  </CardTitle>
                  <CardDescription>
                    {unit.current_stock} / {unit.capacity} kg ({((unit.current_stock / unit.capacity) * 100).toFixed(0)}% full)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Capacity bar */}
                  <div className="h-3 bg-gray-200 rounded-full overflow-hidden mb-4">
                    <div 
                      className="h-full bg-green-500 transition-all"
                      style={{ width: `${(unit.current_stock / unit.capacity) * 100}%` }}
                    />
                  </div>
                  
                  {/* Environment */}
                  <div className="flex gap-4 text-sm">
                    {unit.temperature !== undefined && (
                      <div className="flex items-center gap-1">
                        <Thermometer className="h-4 w-4 text-red-500" />
                        <span>{unit.temperature}°C</span>
                      </div>
                    )}
                    {unit.humidity !== undefined && (
                      <div className="flex items-center gap-1">
                        <Droplets className="h-4 w-4 text-blue-500" />
                        <span>{unit.humidity}%</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default HarvestManagement;
