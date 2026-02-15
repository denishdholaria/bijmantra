/**
 * Pest Observations Page
 * Field scouting records with pest identification and severity tracking
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { AlertCircle, Plus, Bug, RefreshCw, Trash2, Eye } from 'lucide-react'

interface PestObservation {
  id: string
  pest_name: string
  pest_type: string
  crop_id: string
  location_id: string
  observation_date: string
  severity: string
  affected_area_pct: number | null
  life_stage: string | null
  notes: string | null
  created_at: string
}

const PEST_TYPES = ['insect', 'mite', 'nematode', 'rodent', 'bird', 'weed', 'other']
const SEVERITY_LEVELS = [
  { value: 'trace', label: 'Trace', color: 'bg-slate-500' },
  { value: 'light', label: 'Light', color: 'bg-green-500' },
  { value: 'moderate', label: 'Moderate', color: 'bg-yellow-500' },
  { value: 'severe', label: 'Severe', color: 'bg-orange-500' },
  { value: 'critical', label: 'Critical', color: 'bg-red-500' },
]
const LIFE_STAGES = ['egg', 'larva', 'nymph', 'pupa', 'adult', 'mixed']

const getSeverityInfo = (level: string) => SEVERITY_LEVELS.find(s => s.value === level) || SEVERITY_LEVELS[0]

export function PestObservations() {
  const [showCreate, setShowCreate] = useState(false)
  const [newObservation, setNewObservation] = useState({
    pest_name: '',
    pest_type: 'insect',
    crop_id: '',
    location_id: '',
    observation_date: new Date().toISOString().split('T')[0],
    severity: 'light',
    affected_area_pct: 5,
    life_stage: 'adult',
    notes: '',
  })
  const queryClient = useQueryClient()

  const { data: observations, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'pest-observations'],
    queryFn: () => apiClient.get('/api/v2/future/pest-observations/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newObservation) => apiClient.post('/api/v2/future/pest-observation/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'pest-observations'] })
      toast.success('Pest observation recorded')
      setShowCreate(false)
      setNewObservation(prev => ({ ...prev, pest_name: '', notes: '' }))
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create observation'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v2/future/pest-observation/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'pest-observations'] })
      toast.success('Observation deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Bug className="h-8 w-8 text-amber-500" />
            Pest Observations
          </h1>
          <p className="text-muted-foreground mt-1">
            Field scouting records and pest identification
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Observation</Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Record Pest Observation</DialogTitle>
                <DialogDescription>Document pest sighting from field scouting</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Pest Name</Label>
                    <Input
                      value={newObservation.pest_name}
                      onChange={(e) => setNewObservation((p) => ({ ...p, pest_name: e.target.value }))}
                      placeholder="Aphid, Armyworm, etc."
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Pest Type</Label>
                    <Select value={newObservation.pest_type}
                      onValueChange={(v) => setNewObservation((p) => ({ ...p, pest_type: v }))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {PEST_TYPES.map((t) => (
                          <SelectItem key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Crop ID</Label>
                    <Input value={newObservation.crop_id}
                      onChange={(e) => setNewObservation((p) => ({ ...p, crop_id: e.target.value }))}
                      placeholder="CROP-001" />
                  </div>
                  <div className="space-y-2">
                    <Label>Location ID</Label>
                    <Input value={newObservation.location_id}
                      onChange={(e) => setNewObservation((p) => ({ ...p, location_id: e.target.value }))}
                      placeholder="LOC-001" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Observation Date</Label>
                    <Input type="date" value={newObservation.observation_date}
                      onChange={(e) => setNewObservation((p) => ({ ...p, observation_date: e.target.value }))} />
                  </div>
                  <div className="space-y-2">
                    <Label>Life Stage</Label>
                    <Select value={newObservation.life_stage}
                      onValueChange={(v) => setNewObservation((p) => ({ ...p, life_stage: v }))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {LIFE_STAGES.map((s) => (
                          <SelectItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Severity</Label>
                    <Select value={newObservation.severity}
                      onValueChange={(v) => setNewObservation((p) => ({ ...p, severity: v }))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {SEVERITY_LEVELS.map((s) => (
                          <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Affected Area (%)</Label>
                    <Input type="number" min="0" max="100" value={newObservation.affected_area_pct}
                      onChange={(e) => setNewObservation((p) => ({ ...p, affected_area_pct: Number(e.target.value) }))} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea value={newObservation.notes}
                    onChange={(e) => setNewObservation((p) => ({ ...p, notes: e.target.value }))}
                    placeholder="Additional observations..." rows={3} />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button onClick={() => createMutation.mutate(newObservation)}
                  disabled={!newObservation.pest_name || !newObservation.crop_id || createMutation.isPending}>
                  {createMutation.isPending ? 'Recording...' : 'Record Observation'}
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
            Failed to load pest observations.
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
                  <TableHead>Pest</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Crop</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-center">Severity</TableHead>
                  <TableHead className="text-center">Area %</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.isArray(observations) && observations.length > 0 ? (
                  observations.map((obs: PestObservation) => {
                    const severity = getSeverityInfo(obs.severity)
                    return (
                      <TableRow key={obs.id}>
                        <TableCell className="font-medium">{obs.pest_name}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {obs.pest_type}
                          </Badge>
                        </TableCell>
                        <TableCell>{obs.crop_id}</TableCell>
                        <TableCell>{obs.location_id}</TableCell>
                        <TableCell>{formatDate(obs.observation_date)}</TableCell>
                        <TableCell className="text-center">
                          <Badge className={`${severity.color} text-white`}>{severity.label}</Badge>
                        </TableCell>
                        <TableCell className="text-center">{obs.affected_area_pct ?? '—'}%</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            {obs.notes && (
                              <Button variant="ghost" size="icon" aria-label="View notes" title={obs.notes}>
                                <Eye className="h-4 w-4" />
                              </Button>
                            )}
                            <Button variant="ghost" size="icon" aria-label="Delete observation"
                              onClick={() => deleteMutation.mutate(obs.id)}>
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-12">
                      <Bug className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">No pest observations recorded yet</p>
                      <Button className="mt-4" onClick={() => setShowCreate(true)}>
                        <Plus className="h-4 w-4 mr-2" />Add First Observation
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
