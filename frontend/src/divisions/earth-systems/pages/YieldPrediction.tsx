
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, Trash2, TrendingUp, Sprout } from 'lucide-react';
import { toast } from 'sonner';
import { cropIntelligenceYieldPredictionAPI, apiClient, YieldPredictionCreate } from '@/lib/api-client';

export default function YieldPrediction() {
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState<Partial<YieldPredictionCreate>>({
    yield_unit: 't/ha',
    confidence_level: 0.95,
    prediction_date: new Date().toISOString().split('T')[0]
  });

  // Fetch Predictions
  const { data: predictions, isLoading } = useQuery({
    queryKey: ['crop-intelligence-yield-predictions'],
    queryFn: () => cropIntelligenceYieldPredictionAPI.list(),
  });

  // Fetch Locations (Fields)
  const { data: locationsData } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiClient.getLocations(0, 100),
  });

  // Fetch Trials
  const { data: trialsData } = useQuery({
    queryKey: ['trials'],
    queryFn: () => apiClient.getTrials(0, 100),
  });

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: (data: YieldPredictionCreate) => cropIntelligenceYieldPredictionAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crop-intelligence-yield-predictions'] });
      setIsDialogOpen(false);
      toast.success('Yield prediction created successfully');
      setFormData({
        yield_unit: 't/ha',
        confidence_level: 0.95,
        prediction_date: new Date().toISOString().split('T')[0]
      });
    },
    onError: (error) => {
      console.error(error);
      toast.error('Failed to create yield prediction');
    }
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => cropIntelligenceYieldPredictionAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crop-intelligence-yield-predictions'] });
      toast.success('Yield prediction deleted');
    },
    onError: () => {
      toast.error('Failed to delete yield prediction');
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.field_id || !formData.crop_name || !formData.season || !formData.predicted_yield || !formData.model_name || !formData.prediction_date) {
      toast.error('Please fill in all required fields');
      return;
    }

    createMutation.mutate(formData as YieldPredictionCreate);
  };

  const handleInputChange = (field: keyof YieldPredictionCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const locations = locationsData?.result?.data || [];
  const trials = trialsData?.result?.data || [];

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <TrendingUp className="h-8 w-8 text-green-600" />
            Yield Prediction
          </h1>
          <p className="text-muted-foreground mt-1">
            AI-powered crop yield forecasting and analysis
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Prediction
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Yield Prediction</DialogTitle>
              <DialogDescription>
                Enter the details for the new yield forecast.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">

              <div className="space-y-2">
                <Label htmlFor="field">Field *</Label>
                <Select
                  onValueChange={(val) => handleInputChange('field_id', parseInt(val))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select Field" />
                  </SelectTrigger>
                  <SelectContent>
                    {locations.map((loc: any) => (
                      <SelectItem key={loc.locationDbId} value={loc.locationDbId}>
                        {loc.locationName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="trial">Trial (Optional)</Label>
                <Select
                  onValueChange={(val) => handleInputChange('trial_id', parseInt(val))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select Trial" />
                  </SelectTrigger>
                  <SelectContent>
                    {trials.map((trial: any) => (
                      <SelectItem key={trial.trialDbId} value={trial.trialDbId}>
                        {trial.trialName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="crop_name">Crop Name *</Label>
                <Input
                  id="crop_name"
                  value={formData.crop_name || ''}
                  onChange={(e) => handleInputChange('crop_name', e.target.value)}
                  placeholder="e.g. Wheat"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="variety">Variety</Label>
                <Input
                  id="variety"
                  value={formData.variety || ''}
                  onChange={(e) => handleInputChange('variety', e.target.value)}
                  placeholder="e.g. HD-2967"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="season">Season *</Label>
                <Input
                  id="season"
                  value={formData.season || ''}
                  onChange={(e) => handleInputChange('season', e.target.value)}
                  placeholder="e.g. Rabi 2025"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="prediction_date">Prediction Date *</Label>
                <Input
                  id="prediction_date"
                  type="date"
                  value={formData.prediction_date || ''}
                  onChange={(e) => handleInputChange('prediction_date', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="predicted_yield">Predicted Yield *</Label>
                <div className="flex gap-2">
                  <Input
                    id="predicted_yield"
                    type="number"
                    step="0.01"
                    value={formData.predicted_yield || ''}
                    onChange={(e) => handleInputChange('predicted_yield', parseFloat(e.target.value))}
                    placeholder="0.00"
                  />
                  <Input
                    className="w-24"
                    value={formData.yield_unit || 't/ha'}
                    onChange={(e) => handleInputChange('yield_unit', e.target.value)}
                    placeholder="Unit"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confidence">Confidence (0-1)</Label>
                <Input
                  id="confidence"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={formData.confidence_level || 0.95}
                  onChange={(e) => handleInputChange('confidence_level', parseFloat(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="model_name">Model Name *</Label>
                <Input
                  id="model_name"
                  value={formData.model_name || ''}
                  onChange={(e) => handleInputChange('model_name', e.target.value)}
                  placeholder="e.g. Hybrid-CNN-LSTM"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="model_version">Model Version</Label>
                <Input
                  id="model_version"
                  value={formData.model_version || ''}
                  onChange={(e) => handleInputChange('model_version', e.target.value)}
                  placeholder="e.g. v2.1.0"
                />
              </div>

              <div className="md:col-span-2 space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Input
                  id="notes"
                  value={formData.notes || ''}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  placeholder="Additional observations..."
                />
              </div>

              <div className="md:col-span-2 flex justify-end gap-2 mt-4">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Prediction'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Predictions</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : predictions && predictions.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Crop</TableHead>
                  <TableHead>Field / Location</TableHead>
                  <TableHead>Season</TableHead>
                  <TableHead className="text-right">Predicted Yield</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {predictions.map((item: any) => {
                  // Find location name if available
                  const locationName = locations.find((l: any) => parseInt(l.locationDbId) === item.field_id)?.locationName || `Field #${item.field_id}`;

                  return (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Sprout className="h-4 w-4 text-green-600" />
                          <div>
                            <div>{item.crop_name}</div>
                            {item.variety && <div className="text-xs text-muted-foreground">{item.variety}</div>}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{locationName}</TableCell>
                      <TableCell>{item.season}</TableCell>
                      <TableCell className="text-right font-bold">
                        {item.predicted_yield} <span className="text-muted-foreground font-normal text-xs">{item.yield_unit}</span>
                      </TableCell>
                      <TableCell>{new Date(item.prediction_date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{item.model_name}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={item.confidence_level > 0.8 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                          {(item.confidence_level * 100).toFixed(0)}%
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => {
                            if (confirm('Are you sure you want to delete this prediction?')) {
                              deleteMutation.mutate(item.id);
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p>No yield predictions found.</p>
              <p className="text-sm">Create a new prediction to get started.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
