/**
 * Soil Tests Page
 * Display and manage soil test results with nutrient analysis
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
import { AlertCircle, Plus, Beaker, RefreshCw, Trash2 } from 'lucide-react'

interface SoilTest {
  id: string
  location_id: string
  sample_date: string
  lab_name: string | null
  ph: number | null
  organic_carbon_pct: number | null
  nitrogen_ppm: number | null
  phosphorus_ppm: number | null
  potassium_ppm: number | null
  texture_class: string | null
  created_at: string
}

const getNutrientStatus = (value: number | null, min: number, max: number) => {
  if (value === null) return { status: 'unknown', variant: 'outline' as const }
  if (value < min) return { status: 'low', variant: 'destructive' as const }
  if (value > max) return { status: 'high', variant: 'secondary' as const }
  return { status: 'optimal', variant: 'default' as const }
}

export function SoilTests() {
  const [showCreate, setShowCreate] = useState(false)
  const [newTest, setNewTest] = useState({
    location_id: '',
    sample_date: new Date().toISOString().split('T')[0],
    lab_name: '',
    ph: 7.0,
    organic_carbon_pct: 2.0,
    nitrogen_ppm: 50,
    phosphorus_ppm: 30,
    potassium_ppm: 200,
    texture_class: 'loam',
  })
  const queryClient = useQueryClient()

  const { data: tests, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'soil-tests'],
    queryFn: () => apiClient.get('/api/v2/future/soil-tests/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newTest) => apiClient.post('/api/v2/future/soil-tests/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'soil-tests'] })
      toast.success('Soil test created successfully')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create soil test'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v2/future/soil-tests/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'soil-tests'] })
      toast.success('Soil test deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
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
            <Beaker className="h-8 w-8 text-amber-500" />
            Soil Tests
          </h1>
          <p className="text-muted-foreground mt-1">
            Laboratory soil analysis results and nutrient levels
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Test</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Record Soil Test</DialogTitle>
                <DialogDescription>Enter laboratory soil analysis results</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Location ID</Label>
                    <Input
                      value={newTest.location_id}
                      onChange={(e) => setNewTest((p) => ({ ...p, location_id: e.target.value }))}
                      placeholder="LOC-001"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Sample Date</Label>
                    <Input
                      type="date"
                      value={newTest.sample_date}
                      onChange={(e) => setNewTest((p) => ({ ...p, sample_date: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Lab Name</Label>
                  <Input
                    value={newTest.lab_name}
                    onChange={(e) => setNewTest((p) => ({ ...p, lab_name: e.target.value }))}
                    placeholder="Agricultural Testing Lab"
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>pH</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newTest.ph}
                      onChange={(e) => setNewTest((p) => ({ ...p, ph: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Organic C (%)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={newTest.organic_carbon_pct}
                      onChange={(e) => setNewTest((p) => ({ ...p, organic_carbon_pct: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Texture</Label>
                    <Input
                      value={newTest.texture_class}
                      onChange={(e) => setNewTest((p) => ({ ...p, texture_class: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>N (ppm)</Label>
                    <Input
                      type="number"
                      value={newTest.nitrogen_ppm}
                      onChange={(e) => setNewTest((p) => ({ ...p, nitrogen_ppm: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>P (ppm)</Label>
                    <Input
                      type="number"
                      value={newTest.phosphorus_ppm}
                      onChange={(e) => setNewTest((p) => ({ ...p, phosphorus_ppm: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>K (ppm)</Label>
                    <Input
                      type="number"
                      value={newTest.potassium_ppm}
                      onChange={(e) => setNewTest((p) => ({ ...p, potassium_ppm: Number(e.target.value) }))}
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newTest)}
                  disabled={!newTest.location_id || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Test'}
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
            Failed to load soil tests.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
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
                  <TableHead>Location</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Lab</TableHead>
                  <TableHead className="text-center">pH</TableHead>
                  <TableHead className="text-center">N</TableHead>
                  <TableHead className="text-center">P</TableHead>
                  <TableHead className="text-center">K</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.isArray(tests) && tests.length > 0 ? (
                  tests.map((test: SoilTest) => (
                    <TableRow key={test.id}>
                      <TableCell className="font-medium">{test.location_id}</TableCell>
                      <TableCell>{formatDate(test.sample_date)}</TableCell>
                      <TableCell>{test.lab_name || '—'}</TableCell>
                      <TableCell className="text-center">
                        <Badge variant={getNutrientStatus(test.ph, 6.0, 7.5).variant}>
                          {test.ph?.toFixed(1) || '—'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant={getNutrientStatus(test.nitrogen_ppm, 40, 80).variant}>
                          {test.nitrogen_ppm || '—'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant={getNutrientStatus(test.phosphorus_ppm, 25, 50).variant}>
                          {test.phosphorus_ppm || '—'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant={getNutrientStatus(test.potassium_ppm, 150, 300).variant}>
                          {test.potassium_ppm || '—'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Delete test"
                          onClick={() => deleteMutation.mutate(test.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-12">
                      <Beaker className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">No soil tests recorded yet</p>
                      <Button className="mt-4" onClick={() => setShowCreate(true)}>
                        <Plus className="h-4 w-4 mr-2" />Add First Test
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
