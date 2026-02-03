/**
 * Yield Prediction Page
 * AI/ML based yield forecasting
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { AlertCircle, Plus, TrendingUp, RefreshCw, Trash2, BrainCircuit } from 'lucide-react'

interface YieldPredictionRecord {
  id: number
  field_id: number
  crop_name: string
  season: string
  predicted_yield: number
  yield_unit: string
  confidence_level: number
  model_name: string
  created_at: string
}

export function YieldPrediction() {
  const [showCreate, setShowCreate] = useState(false)
  const [newPred, setNewPred] = useState({
    field_id: 1,
    crop_name: '',
    season: new Date().getFullYear().toString(),
    planting_date: new Date().toISOString().split('T')[0],
    target_year: new Date().getFullYear(),
  })
  const queryClient = useQueryClient()

  const { data: predictions, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'yield-prediction'],
    queryFn: () => apiClient.get('/api/v2/future/yield-prediction/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newPred) => apiClient.post('/api/v2/future/yield-prediction/predict?save=true', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'yield-prediction'] })
      toast.success('Prediction generated & saved')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to generate prediction'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/future/yield-prediction/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'yield-prediction'] })
      toast.success('Prediction deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <TrendingUp className="h-8 w-8 text-purple-600" />
            Yield Forecast
          </h1>
          <p className="text-muted-foreground mt-1">
            AI-driven crop yield predictions
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="bg-purple-600 hover:bg-purple-700">
                <Plus className="h-4 w-4 mr-2" />Run Prediction
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Generate Yield Forecast</DialogTitle>
                <DialogDescription>Run ensemble models to predict harvest yield</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Field ID</Label>
                    <Input
                      type="number"
                      value={newPred.field_id}
                      onChange={(e) => setNewPred((p) => ({ ...p, field_id: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Crop Name</Label>
                    <Input
                      value={newPred.crop_name}
                      onChange={(e) => setNewPred((p) => ({ ...p, crop_name: e.target.value }))}
                      placeholder="e.g. Corn"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Season</Label>
                    <Input
                      value={newPred.season}
                      onChange={(e) => setNewPred((p) => ({ ...p, season: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Planting Date</Label>
                    <Input
                      type="date"
                      value={newPred.planting_date}
                      onChange={(e) => setNewPred((p) => ({ ...p, planting_date: e.target.value }))}
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newPred)}
                  className="bg-purple-600 hover:bg-purple-700"
                  disabled={!newPred.crop_name || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Processing...' : 'Run & Save'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load predictions.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      )}

      {/* Data Table */}
      {!isLoading && !error && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>Crop</TableHead>
                  <TableHead>Season</TableHead>
                  <TableHead className="text-center">Predicted Yield</TableHead>
                  <TableHead className="text-center">Confidence</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.isArray(predictions) && predictions.length > 0 ? (
                  predictions.map((pred: YieldPredictionRecord) => (
                    <TableRow key={pred.id}>
                      <TableCell className="font-medium">{pred.field_id}</TableCell>
                      <TableCell>{pred.crop_name}</TableCell>
                      <TableCell>{pred.season}</TableCell>
                      <TableCell className="text-center font-bold text-purple-700">
                        {pred.predicted_yield.toFixed(1)} {pred.yield_unit}
                      </TableCell>
                      <TableCell className="text-center">
                        {(pred.confidence_level * 100).toFixed(0)}%
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{pred.model_name}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Delete prediction"
                          onClick={() => deleteMutation.mutate(pred.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12">
                      <BrainCircuit className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">No predictions generated yet</p>
                      <Button className="mt-4" onClick={() => setShowCreate(true)}>
                        <Plus className="h-4 w-4 mr-2" />Run First Prediction
                      </Button>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
