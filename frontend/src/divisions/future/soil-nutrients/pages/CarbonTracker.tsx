/**
 * Carbon Tracker Page
 * Monitor soil carbon sequestration and estimate credits
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
import { AlertCircle, Plus, Leaf, RefreshCw, Trash2, Calculator } from 'lucide-react'

// Backend schema for CarbonSequestration
interface CarbonSequestration {
  id: string
  field_id: string
  measurement_date: string
  soil_organic_carbon_pct: number
  bulk_density_g_cm3: number
  soil_depth_cm: number
  sequestered_carbon_tonnes_ha: number
  methodology: string
  verified: boolean
  created_at: string
}

export function CarbonTracker() {
  const [showCreate, setShowCreate] = useState(false)
  const [showCalculator, setShowCalculator] = useState(false)
  
  // New Record State
  const [newRec, setNewRec] = useState({
    field_id: '',
    measurement_date: new Date().toISOString().split('T')[0],
    soil_organic_carbon_pct: 1.5,
    bulk_density_g_cm3: 1.2,
    soil_depth_cm: 30,
    methodology: 'loss_on_ignition',
  })

  // Calculator State
  const [calcInput, setCalcInput] = useState({ carbon_tonnes: 10, standard: 'verra' })
  const [calcResult, setCalcResult] = useState<any>(null)

  const queryClient = useQueryClient()

  // Fetch Records
  const { data: records, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'carbon-sequestration'],
    queryFn: () => apiClient.get('/api/v2/future/carbon-sequestration/'),
  })

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newRec) => apiClient.post('/api/v2/future/carbon-sequestration/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'carbon-sequestration'] })
      toast.success('Carbon record logged')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to log record'),
  })

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v2/future/carbon-sequestration/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'carbon-sequestration'] })
      toast.success('Record deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  // Estimate Credits Mutation
  const estimateMutation = useMutation({
    mutationFn: (params: { carbon_tonnes: number; standard: string }) => 
        apiClient.post(`/api/v2/future/carbon-sequestration/estimate-credits?carbon_tonnes=${params.carbon_tonnes}&verification_standard=${params.standard}`),
    onSuccess: (data) => {
        setCalcResult(data)
    },
    onError: () => toast.error('Failed to estimate credits')
  })

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
            <Leaf className="h-8 w-8 text-green-600" />
            Carbon Tracker
          </h1>
          <p className="text-muted-foreground mt-1">
            Soil carbon sequestration monitoring and credit estimation
          </p>
        </div>
        <div className="flex gap-2">
          {/* Credit Calculator */}
          <Dialog open={showCalculator} onOpenChange={setShowCalculator}>
            <DialogTrigger asChild>
                <Button variant="outline">
                    <Calculator className="h-4 w-4 mr-2" /> Estimate Credits
                </Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Carbon Credit Estimator</DialogTitle>
                    <DialogDescription>Estimate potential credits from sequestered carbon</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label>Sequestered Carbon (Tonnes)</Label>
                        <Input 
                            type="number" 
                            value={calcInput.carbon_tonnes} 
                            onChange={e => setCalcInput({...calcInput, carbon_tonnes: Number(e.target.value)})} 
                        />
                    </div>
                    {calcResult && (
                        <div className="bg-slate-50 dark:bg-slate-900 p-4 rounded-md space-y-2 text-sm">
                             <div className="flex justify-between">
                                <span>CO2 Equivalent:</span>
                                <span className="font-bold">{calcResult.co2_equivalent_tonnes} t</span>
                             </div>
                             <div className="flex justify-between text-green-600">
                                <span>Est. Credits:</span>
                                <span className="font-bold text-lg">{calcResult.estimated_credits}</span>
                             </div>
                             <p className="text-xs text-muted-foreground mt-2">{calcResult.note}</p>
                        </div>
                    )}
                </div>
                <DialogFooter>
                    <Button onClick={() => estimateMutation.mutate(calcInput)}>Calculate</Button>
                </DialogFooter>
            </DialogContent>
          </Dialog>

          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>

          {/* New Record Modal */}
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="bg-green-600 hover:bg-green-700">
                <Plus className="h-4 w-4 mr-2" />Log Sequestration
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Log Carbon Data</DialogTitle>
                <DialogDescription>Record Soil Organic Carbon (SOC) measurements</DialogDescription>
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
                        <Label>Date</Label>
                        <Input
                        type="date"
                        value={newRec.measurement_date}
                        onChange={(e) => setNewRec((p) => ({ ...p, measurement_date: e.target.value }))}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                        <Label>SOC %</Label>
                        <Input
                        type="number"
                        step="0.1"
                        value={newRec.soil_organic_carbon_pct}
                        onChange={(e) => setNewRec((p) => ({ ...p, soil_organic_carbon_pct: Number(e.target.value) }))}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>Bulk Density</Label>
                        <Input
                        type="number"
                        step="0.1"
                        value={newRec.bulk_density_g_cm3}
                        onChange={(e) => setNewRec((p) => ({ ...p, bulk_density_g_cm3: Number(e.target.value) }))}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>Depth (cm)</Label>
                        <Input
                        type="number"
                        value={newRec.soil_depth_cm}
                        onChange={(e) => setNewRec((p) => ({ ...p, soil_depth_cm: Number(e.target.value) }))}
                        />
                    </div>
                </div>
                <div className="space-y-2">
                    <Label>Methodology</Label>
                    <Input
                    value={newRec.methodology}
                    onChange={(e) => setNewRec((p) => ({ ...p, methodology: e.target.value }))}
                    />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newRec)}
                  className="bg-green-600 hover:bg-green-700"
                  disabled={!newRec.field_id || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Saving...' : 'Save Record'}
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
            Failed to load carbon records.
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
                  <TableHead>Date</TableHead>
                  <TableHead className="text-center">SOC %</TableHead>
                  <TableHead className="text-center">Sequestered (t/ha)</TableHead>
                  <TableHead>Methodology</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.isArray(records) && records.length > 0 ? (
                  records.map((rec: CarbonSequestration) => (
                    <TableRow key={rec.id}>
                      <TableCell className="font-medium">{rec.field_id}</TableCell>
                      <TableCell>{formatDate(rec.measurement_date)}</TableCell>
                      <TableCell className="text-center">{rec.soil_organic_carbon_pct}%</TableCell>
                      <TableCell className="text-center font-bold text-green-700">
                        {rec.sequestered_carbon_tonnes_ha.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">{rec.methodology}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Delete record"
                          onClick={() => deleteMutation.mutate(rec.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-12">
                      <Leaf className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">No carbon sequestration records found</p>
                      <Button className="mt-4" onClick={() => setShowCreate(true)}>
                        <Plus className="h-4 w-4 mr-2" />Log First Record
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
