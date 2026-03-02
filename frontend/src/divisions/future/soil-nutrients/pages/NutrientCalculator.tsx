/**
 * Nutrient Calculator / Fertilizer Recommendations Page
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
import { AlertCircle, Plus, ClipboardList, RefreshCw, Trash2, Sprout } from 'lucide-react'

// Backend schema for FertilizerRecommendation
interface FertilizerRecommendation {
  id: string
  field_id: string
  crop_name: string
  target_yield: number
  nitrogen_recommendation: number
  phosphorus_recommendation: number
  potassium_recommendation: number
  soil_test_id: string | null
  created_at: string
}

export function NutrientCalculator() {
  const [showCreate, setShowCreate] = useState(false)
  const [newRec, setNewRec] = useState({
    field_id: '',
    crop_name: '',
    target_yield: 100,
    nitrogen_recommendation: 120,
    phosphorus_recommendation: 60,
    potassium_recommendation: 80,
    soil_test_id: null as string | null,
  })
  const queryClient = useQueryClient()

  const { data: recommendations, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'fertilizer-recommendations'],
    queryFn: () => apiClient.get('/api/v2/future/fertilizer-recommendations/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newRec) => apiClient.post('/api/v2/future/fertilizer-recommendations/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'fertilizer-recommendations'] })
      toast.success('Recommendation created')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create recommendation'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v2/future/fertilizer-recommendations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'fertilizer-recommendations'] })
      toast.success('Recommendation deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <ClipboardList className="h-8 w-8 text-emerald-600" />
            Nutrient Calculator
          </h1>
          <p className="text-muted-foreground mt-1">
            Fertilizer recommendations and 4R nutrient stewardship
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="bg-emerald-600 hover:bg-emerald-700">
                <Plus className="h-4 w-4 mr-2" />New Rx
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Fertilizer Prescription</DialogTitle>
                <DialogDescription>Generate nutrient recommendations based on soil data</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Field ID</Label>
                    <Input
                      value={newRec.field_id}
                      onChange={(e) => setNewRec((p) => ({ ...p, field_id: e.target.value }))}
                      placeholder="FIELD-001"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Crop</Label>
                    <Input
                      value={newRec.crop_name}
                      onChange={(e) => setNewRec((p) => ({ ...p, crop_name: e.target.value }))}
                      placeholder="Wheat"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                    <Label>Target Yield (kg/ha)</Label>
                    <Input
                      type="number"
                      value={newRec.target_yield}
                      onChange={(e) => setNewRec((p) => ({ ...p, target_yield: Number(e.target.value) }))}
                    />
                </div>

                {/* Recommendations */}
                <div className="grid grid-cols-3 gap-4 border-t pt-4">
                  <div className="space-y-2">
                    <Label className="text-emerald-700 font-semibold">Rec N</Label>
                    <Input
                      type="number"
                      value={newRec.nitrogen_recommendation}
                      onChange={(e) => setNewRec((p) => ({ ...p, nitrogen_recommendation: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-emerald-700 font-semibold">Rec P</Label>
                    <Input
                      type="number"
                      value={newRec.phosphorus_recommendation}
                      onChange={(e) => setNewRec((p) => ({ ...p, phosphorus_recommendation: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-emerald-700 font-semibold">Rec K</Label>
                    <Input
                      type="number"
                      value={newRec.potassium_recommendation}
                      onChange={(e) => setNewRec((p) => ({ ...p, potassium_recommendation: Number(e.target.value) }))}
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newRec)}
                  className="bg-emerald-600 hover:bg-emerald-700"
                  disabled={!newRec.field_id || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Calculating...' : 'Save Rx'}
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
            Failed to load recommendations.
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
                  <TableHead>Target Yield</TableHead>
                  <TableHead className="text-center">Rec N (kg/ha)</TableHead>
                  <TableHead className="text-center">Rec P (kg/ha)</TableHead>
                  <TableHead className="text-center">Rec K (kg/ha)</TableHead>
                  <TableHead className="text-right">Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.isArray(recommendations) && recommendations.length > 0 ? (
                  recommendations.map((rec: FertilizerRecommendation) => (
                    <TableRow key={rec.id}>
                      <TableCell className="font-medium">{rec.field_id}</TableCell>
                      <TableCell>
                        <span className="flex items-center gap-2">
                            <Sprout className="h-4 w-4 text-green-500" />
                            {rec.crop_name}
                        </span>
                      </TableCell>
                      <TableCell>{rec.target_yield}</TableCell>
                      <TableCell className="text-center font-bold text-emerald-700">{rec.nitrogen_recommendation}</TableCell>
                      <TableCell className="text-center font-bold text-emerald-700">{rec.phosphorus_recommendation}</TableCell>
                      <TableCell className="text-center font-bold text-emerald-700">{rec.potassium_recommendation}</TableCell>
                      <TableCell className="text-right text-muted-foreground">{formatDate(rec.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Delete recommendation"
                          onClick={() => deleteMutation.mutate(rec.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-12">
                      <Sprout className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">No recommendations generated yet</p>
                      <Button className="mt-4" onClick={() => setShowCreate(true)}>
                        <Plus className="h-4 w-4 mr-2" />Create Prescription
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
