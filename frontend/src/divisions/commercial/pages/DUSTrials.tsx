/**
 * DUS Trials Page
 * 
 * List and manage DUS (Distinctness, Uniformity, Stability) trials
 * for UPOV variety protection.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { Plus, Search, FileText, Leaf } from 'lucide-react';

import { apiClient } from '@/lib/api-client';

interface CropTemplate {
  code: string;
  name: string;
  scientific_name: string;
  character_count: number;
}

interface DUSTrial {
  trial_id: string;
  crop_code: string;
  trial_name: string;
  year: number;
  location: string;
  status: string;
  sample_size: number;
  entries: Array<{
    entry_id: string;
    variety_name: string;
    is_candidate: boolean;
    is_reference: boolean;
  }>;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-500',
  active: 'bg-blue-500',
  scoring: 'bg-amber-500',
  analysis: 'bg-purple-500',
  completed: 'bg-green-500',
  cancelled: 'bg-red-500',
};

export default function DUSTrials() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [cropFilter, setCropFilter] = useState<string>('all');
  const [yearFilter, setYearFilter] = useState<string>('all');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newTrial, setNewTrial] = useState({
    crop_code: '',
    trial_name: '',
    year: new Date().getFullYear(),
    location: '',
    sample_size: 100,
  });

  // Fetch crop templates
  const { data: cropsData } = useQuery({
    queryKey: ['dus-crops'],
    queryFn: async () => {
      const res = await apiClient.dusService.getCrops();
      return res;
    },
  });

  // Fetch trials
  const { data: trialsData, isLoading } = useQuery({
    queryKey: ['dus-trials', cropFilter, yearFilter],
    queryFn: async () => {
      const res = await apiClient.dusService.getTrials({
        crop_code: cropFilter,
        year: yearFilter
      });
      return res;
    },
  });

  // Create trial mutation
  const createMutation = useMutation({
    mutationFn: async (data: typeof newTrial) => {
      return apiClient.dusService.createTrial(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dus-trials'] });
      setIsCreateOpen(false);
      setNewTrial({
        crop_code: '',
        trial_name: '',
        year: new Date().getFullYear(),
        location: '',
        sample_size: 100,
      });
      toast.success('DUS trial created successfully');
    },
    onError: () => {
      toast.error('Failed to create trial');
    },
  });

  const crops: CropTemplate[] = cropsData?.crops || [];
  const trials: DUSTrial[] = trialsData?.trials || [];

  // Filter trials by search
  const filteredTrials = trials.filter(
    (t) =>
      t.trial_name.toLowerCase().includes(search.toLowerCase()) ||
      t.location.toLowerCase().includes(search.toLowerCase())
  );

  // Get unique years for filter
  const years = [...new Set(trials.map((t) => t.year))].sort((a, b) => b - a);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Leaf className="h-6 w-6" />
            DUS Testing
          </h1>
          <p className="text-muted-foreground">
            UPOV variety protection trials
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/commercial/dus/crops">
            <Button variant="outline">
              <FileText className="h-4 w-4 mr-2" />
              Crop Templates
            </Button>
          </Link>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Trial
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create DUS Trial</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Crop</Label>
                  <Select
                    value={newTrial.crop_code}
                    onValueChange={(v) => setNewTrial({ ...newTrial, crop_code: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select crop" />
                    </SelectTrigger>
                    <SelectContent>
                      {crops.map((crop) => (
                        <SelectItem key={crop.code} value={crop.code}>
                          {crop.name} ({crop.character_count} chars)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Trial Name</Label>
                  <Input
                    value={newTrial.trial_name}
                    onChange={(e) => setNewTrial({ ...newTrial, trial_name: e.target.value })}
                    placeholder="e.g., Rice DUS 2025-01"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Year</Label>
                    <Input
                      type="number"
                      value={newTrial.year}
                      onChange={(e) => setNewTrial({ ...newTrial, year: parseInt(e.target.value) })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Sample Size</Label>
                    <Input
                      type="number"
                      value={newTrial.sample_size}
                      onChange={(e) => setNewTrial({ ...newTrial, sample_size: parseInt(e.target.value) })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Location</Label>
                  <Input
                    value={newTrial.location}
                    onChange={(e) => setNewTrial({ ...newTrial, location: e.target.value })}
                    placeholder="e.g., IARI, New Delhi"
                  />
                </div>
                <Button
                  className="w-full"
                  onClick={() => createMutation.mutate(newTrial)}
                  disabled={!newTrial.crop_code || !newTrial.trial_name || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Trial'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{trials.length}</p>
            <p className="text-sm text-muted-foreground">Total Trials</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">
              {trials.filter((t) => t.status === 'active' || t.status === 'scoring').length}
            </p>
            <p className="text-sm text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">
              {trials.filter((t) => t.status === 'completed').length}
            </p>
            <p className="text-sm text-muted-foreground">Completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{crops.length}</p>
            <p className="text-sm text-muted-foreground">Crop Templates</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search trials..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <Select value={cropFilter} onValueChange={setCropFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Crop" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Crops</SelectItem>
                {crops.map((crop) => (
                  <SelectItem key={crop.code} value={crop.code}>
                    {crop.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={yearFilter} onValueChange={setYearFilter}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Years</SelectItem>
                {years.map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Trials Table */}
      <Card>
        <CardHeader>
          <CardTitle>DUS Trials</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : filteredTrials.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No trials found. Create your first DUS trial to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Trial Name</TableHead>
                  <TableHead>Crop</TableHead>
                  <TableHead>Year</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Entries</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTrials.map((trial) => (
                  <TableRow key={trial.trial_id}>
                    <TableCell className="font-medium">{trial.trial_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{trial.crop_code.toUpperCase()}</Badge>
                    </TableCell>
                    <TableCell>{trial.year}</TableCell>
                    <TableCell>{trial.location}</TableCell>
                    <TableCell>
                      <span className="text-sm">
                        {trial.entries?.filter((e) => e.is_candidate).length || 0} candidates,{' '}
                        {trial.entries?.filter((e) => e.is_reference).length || 0} references
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge className={STATUS_COLORS[trial.status] || 'bg-gray-500'}>
                        {trial.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Link to={`/commercial/dus/trials/${trial.trial_id}`}>
                        <Button variant="ghost" size="sm">
                          View →
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
