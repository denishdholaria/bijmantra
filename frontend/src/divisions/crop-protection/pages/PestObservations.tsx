/**
 * Pest Observations Page
 * Field scouting records with pest identification and severity tracking
 */
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
import {
  AlertCircle,
  Bug,
  Eye,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from 'lucide-react'
import {
  PestObservationRecord,
  formatDisplayDate,
  pestTypes,
  toNumberOrNull,
} from '../lib/cropProtection'

type PestObservationFormState = {
  field_id: string
  study_id: string
  observation_date: string
  observation_time: string
  observer_name: string
  pest_name: string
  pest_type: string
  pest_stage: string
  crop_name: string
  growth_stage: string
  plant_part_affected: string
  severity_score: string
  incidence_percent: string
  count_per_plant: string
  count_per_trap: string
  area_affected_percent: string
  sample_location: string
  lat: string
  lon: string
  notes: string
}

const defaultFormState = (): PestObservationFormState => ({
  field_id: '',
  study_id: '',
  observation_date: new Date().toISOString().split('T')[0],
  observation_time: '',
  observer_name: '',
  pest_name: '',
  pest_type: 'insect',
  pest_stage: '',
  crop_name: '',
  growth_stage: '',
  plant_part_affected: '',
  severity_score: '3',
  incidence_percent: '',
  count_per_plant: '',
  count_per_trap: '',
  area_affected_percent: '',
  sample_location: '',
  lat: '',
  lon: '',
  notes: '',
})

function toPayload(form: PestObservationFormState) {
  return {
    field_id: Number(form.field_id),
    study_id: toNumberOrNull(form.study_id),
    observation_date: form.observation_date,
    observation_time: form.observation_time ? `${form.observation_date}T${form.observation_time}:00` : null,
    observer_name: form.observer_name || null,
    pest_name: form.pest_name,
    pest_type: form.pest_type,
    pest_stage: form.pest_stage || null,
    crop_name: form.crop_name,
    growth_stage: form.growth_stage || null,
    plant_part_affected: form.plant_part_affected || null,
    severity_score: toNumberOrNull(form.severity_score),
    incidence_percent: toNumberOrNull(form.incidence_percent),
    count_per_plant: toNumberOrNull(form.count_per_plant),
    count_per_trap: toNumberOrNull(form.count_per_trap),
    area_affected_percent: toNumberOrNull(form.area_affected_percent),
    sample_location: form.sample_location || null,
    lat: toNumberOrNull(form.lat),
    lon: toNumberOrNull(form.lon),
    notes: form.notes || null,
  }
}

function toFormState(record: PestObservationRecord): PestObservationFormState {
  const observationTime = record.observation_time ? new Date(record.observation_time).toISOString().slice(11, 16) : ''

  return {
    field_id: String(record.field_id),
    study_id: record.study_id ? String(record.study_id) : '',
    observation_date: record.observation_date.slice(0, 10),
    observation_time: observationTime,
    observer_name: record.observer_name ?? '',
    pest_name: record.pest_name,
    pest_type: record.pest_type,
    pest_stage: record.pest_stage ?? '',
    crop_name: record.crop_name,
    growth_stage: record.growth_stage ?? '',
    plant_part_affected: record.plant_part_affected ?? '',
    severity_score: record.severity_score !== null ? String(record.severity_score) : '',
    incidence_percent: record.incidence_percent !== null ? String(record.incidence_percent) : '',
    count_per_plant: record.count_per_plant !== null ? String(record.count_per_plant) : '',
    count_per_trap: record.count_per_trap !== null ? String(record.count_per_trap) : '',
    area_affected_percent: record.area_affected_percent !== null ? String(record.area_affected_percent) : '',
    sample_location: record.sample_location ?? '',
    lat: record.lat !== null ? String(record.lat) : '',
    lon: record.lon !== null ? String(record.lon) : '',
    notes: record.notes ?? '',
  }
}

function severityTone(score: number | null) {
  if (score === null) return 'bg-slate-500'
  if (score >= 8) return 'bg-red-500'
  if (score >= 6) return 'bg-orange-500'
  if (score >= 4) return 'bg-yellow-500'
  return 'bg-green-500'
}

function PestObservationForm({
  form,
  onChange,
}: {
  form: PestObservationFormState
  onChange: (next: PestObservationFormState) => void
}) {
  const update = (field: keyof PestObservationFormState, value: string) => {
    onChange({ ...form, [field]: value })
  }

  return (
    <div className="space-y-4 py-4 max-h-[70vh] overflow-y-auto">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Pest Name</Label>
          <Input value={form.pest_name} onChange={(event) => update('pest_name', event.target.value)} placeholder="Brown planthopper" />
        </div>
        <div className="space-y-2">
          <Label>Pest Type</Label>
          <Select value={form.pest_type} onValueChange={(value) => update('pest_type', value)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {pestTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Crop Name</Label>
          <Input value={form.crop_name} onChange={(event) => update('crop_name', event.target.value)} placeholder="Rice" />
        </div>
        <div className="space-y-2">
          <Label>Field ID</Label>
          <Input type="number" min="1" value={form.field_id} onChange={(event) => update('field_id', event.target.value)} placeholder="101" />
        </div>
        <div className="space-y-2">
          <Label>Study ID</Label>
          <Input type="number" min="1" value={form.study_id} onChange={(event) => update('study_id', event.target.value)} placeholder="Optional" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Observation Date</Label>
          <Input type="date" value={form.observation_date} onChange={(event) => update('observation_date', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Observation Time</Label>
          <Input type="time" value={form.observation_time} onChange={(event) => update('observation_time', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Observer</Label>
          <Input value={form.observer_name} onChange={(event) => update('observer_name', event.target.value)} placeholder="Scouting lead" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Severity Score (0-10)</Label>
          <Input type="number" min="0" max="10" step="0.1" value={form.severity_score} onChange={(event) => update('severity_score', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Incidence (%)</Label>
          <Input type="number" min="0" max="100" step="0.1" value={form.incidence_percent} onChange={(event) => update('incidence_percent', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Area Affected (%)</Label>
          <Input type="number" min="0" max="100" step="0.1" value={form.area_affected_percent} onChange={(event) => update('area_affected_percent', event.target.value)} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Pest Stage</Label>
          <Input value={form.pest_stage} onChange={(event) => update('pest_stage', event.target.value)} placeholder="Adult" />
        </div>
        <div className="space-y-2">
          <Label>Growth Stage</Label>
          <Input value={form.growth_stage} onChange={(event) => update('growth_stage', event.target.value)} placeholder="Tillering" />
        </div>
        <div className="space-y-2">
          <Label>Plant Part Affected</Label>
          <Input value={form.plant_part_affected} onChange={(event) => update('plant_part_affected', event.target.value)} placeholder="Leaf sheath" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Count per Plant</Label>
          <Input type="number" min="0" step="0.1" value={form.count_per_plant} onChange={(event) => update('count_per_plant', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Count per Trap</Label>
          <Input type="number" min="0" step="0.1" value={form.count_per_trap} onChange={(event) => update('count_per_trap', event.target.value)} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Sample Location</Label>
          <Input value={form.sample_location} onChange={(event) => update('sample_location', event.target.value)} placeholder="North block" />
        </div>
        <div className="space-y-2">
          <Label>Latitude</Label>
          <Input type="number" step="0.000001" value={form.lat} onChange={(event) => update('lat', event.target.value)} placeholder="Optional" />
        </div>
        <div className="space-y-2">
          <Label>Longitude</Label>
          <Input type="number" step="0.000001" value={form.lon} onChange={(event) => update('lon', event.target.value)} placeholder="Optional" />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Notes</Label>
        <Textarea value={form.notes} onChange={(event) => update('notes', event.target.value)} placeholder="Weather, trap count rationale, or action recommendation" rows={4} />
      </div>
    </div>
  )
}

export function PestObservations() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [pestTypeFilter, setPestTypeFilter] = useState<string>('all')
  const [minSeverityFilter, setMinSeverityFilter] = useState<string>('all')
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<PestObservationRecord | null>(null)
  const [selectedRecord, setSelectedRecord] = useState<PestObservationRecord | null>(null)
  const [form, setForm] = useState<PestObservationFormState>(defaultFormState)

  const { data: observations, isLoading, error, refetch } = useQuery<PestObservationRecord[]>({
    queryKey: ['future', 'pest-observations'],
    queryFn: async () => apiClient.get('/api/v2/future/pest-observations/'),
  })

  const createMutation = useMutation({
    mutationFn: (payload: ReturnType<typeof toPayload>) => apiClient.post('/api/v2/future/pest-observations/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'pest-observations'] })
      toast.success('Pest observation recorded')
      setIsFormOpen(false)
      setForm(defaultFormState())
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create observation'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: ReturnType<typeof toPayload> }) => apiClient.put(`/api/v2/future/pest-observations/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'pest-observations'] })
      toast.success('Observation updated')
      setIsFormOpen(false)
      setEditingRecord(null)
      setForm(defaultFormState())
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to update observation'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/future/pest-observations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'pest-observations'] })
      toast.success('Observation deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete observation'),
  })

  const filteredObservations = useMemo(() => {
    return (observations ?? []).filter((record) => {
      const matchesQuery =
        searchQuery.length === 0 ||
        [record.pest_name, record.crop_name, record.observer_name, record.sample_location]
          .filter(Boolean)
          .some((value) => value?.toLowerCase().includes(searchQuery.toLowerCase()))

      const matchesType = pestTypeFilter === 'all' || record.pest_type === pestTypeFilter
      const matchesSeverity = minSeverityFilter === 'all' || (record.severity_score ?? 0) >= Number(minSeverityFilter)

      return matchesQuery && matchesType && matchesSeverity
    })
  }, [minSeverityFilter, observations, pestTypeFilter, searchQuery])

  const metrics = useMemo(() => {
    const records = filteredObservations
    return {
      total: records.length,
      urgent: records.filter((record) => (record.severity_score ?? 0) >= 6).length,
      averageSeverity:
        records.length > 0
          ? records.reduce((sum, record) => sum + (record.severity_score ?? 0), 0) / records.length
          : 0,
      affectedArea:
        records.reduce((sum, record) => sum + (record.area_affected_percent ?? 0), 0),
    }
  }, [filteredObservations])

  const submitForm = () => {
    if (!form.pest_name || !form.crop_name || !form.field_id || !form.observation_date) {
      toast.error('Pest name, crop name, field ID, and observation date are required')
      return
    }

    const payload = toPayload(form)
    if (editingRecord) {
      updateMutation.mutate({ id: editingRecord.id, payload })
      return
    }

    createMutation.mutate(payload)
  }

  const openCreateDialog = () => {
    setEditingRecord(null)
    setForm(defaultFormState())
    setIsFormOpen(true)
  }

  const openEditDialog = (record: PestObservationRecord) => {
    setEditingRecord(record)
    setForm(toFormState(record))
    setIsFormOpen(true)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Bug className="h-8 w-8 text-amber-500" />
            Pest Observations
          </h1>
          <p className="text-muted-foreground mt-1 max-w-2xl">
            Record scouting observations, quantify severity, and surface the field records that should trigger intervention.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
            <DialogTrigger asChild>
              <Button onClick={openCreateDialog}>
                <Plus className="mr-2 h-4 w-4" />
                New Observation
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>{editingRecord ? 'Update pest observation' : 'Record pest observation'}</DialogTitle>
                <DialogDescription>
                  Capture threshold data, scouting context, and notes for field follow-up.
                </DialogDescription>
              </DialogHeader>
              <PestObservationForm form={form} onChange={setForm} />
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsFormOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={submitForm} disabled={createMutation.isPending || updateMutation.isPending}>
                  {editingRecord
                    ? updateMutation.isPending ? 'Saving...' : 'Save changes'
                    : createMutation.isPending ? 'Recording...' : 'Record observation'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Visible records</CardDescription>
            <CardTitle className="text-3xl">{isLoading ? '—' : metrics.total}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Urgent observations</CardDescription>
            <CardTitle className="text-3xl text-orange-600">{isLoading ? '—' : metrics.urgent}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Average severity</CardDescription>
            <CardTitle className="text-3xl">{isLoading ? '—' : metrics.averageSeverity.toFixed(1)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total affected area</CardDescription>
            <CardTitle className="text-3xl">{isLoading ? '—' : `${metrics.affectedArea.toFixed(1)}%`}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader className="gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <CardTitle>Scouting queue</CardTitle>
            <CardDescription>Filter by crop, pest type, and action threshold to prioritize follow-up.</CardDescription>
          </div>
          <div className="grid gap-3 md:grid-cols-3 lg:min-w-[720px]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input className="pl-9" placeholder="Search pest, crop, or observer" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} />
            </div>
            <Select value={pestTypeFilter} onValueChange={setPestTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Pest type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All pest types</SelectItem>
                {pestTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={minSeverityFilter} onValueChange={setMinSeverityFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Minimum severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All severities</SelectItem>
                <SelectItem value="4">4+ Monitor closely</SelectItem>
                <SelectItem value="6">6+ Action threshold</SelectItem>
                <SelectItem value="8">8+ Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {error && (
            <Alert variant="destructive" className="m-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Failed to load pest observations.
                <Button variant="link" size="sm" onClick={() => refetch()}>
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {isLoading && (
            <div className="space-y-4 p-6">
              {[1, 2, 3].map((entry) => (
                <Skeleton key={entry} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!isLoading && !error && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Pest</TableHead>
                  <TableHead>Crop</TableHead>
                  <TableHead>Field</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-center">Severity</TableHead>
                  <TableHead className="text-center">Incidence</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredObservations.length > 0 ? (
                  filteredObservations.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{record.pest_name}</div>
                          <div className="text-xs text-muted-foreground">{record.pest_stage ?? 'Stage not captured'}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          <span>{record.crop_name}</span>
                          <Badge variant="outline" className="w-fit text-xs capitalize">
                            {record.pest_type}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div>Field #{record.field_id}</div>
                          <div className="text-xs text-muted-foreground">{record.sample_location ?? 'Unspecified zone'}</div>
                        </div>
                      </TableCell>
                      <TableCell>{formatDisplayDate(record.observation_date)}</TableCell>
                      <TableCell className="text-center">
                        <Badge className={`${severityTone(record.severity_score)} text-white`}>
                          {record.severity_score?.toFixed(1) ?? '—'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">{record.incidence_percent !== null ? `${record.incidence_percent.toFixed(1)}%` : '—'}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" aria-label="View observation" onClick={() => setSelectedRecord(record)}>
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" aria-label="Edit observation" onClick={() => openEditDialog(record)}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Delete observation"
                            onClick={() => {
                              if (window.confirm(`Delete ${record.pest_name} observation from ${record.crop_name}?`)) {
                                deleteMutation.mutate(record.id)
                              }
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} className="py-14 text-center">
                      <Bug className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                      <p className="text-muted-foreground">No pest observations match the current filters.</p>
                      <Button className="mt-4" onClick={openCreateDialog}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add observation
                      </Button>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={selectedRecord !== null} onOpenChange={(open) => !open && setSelectedRecord(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedRecord?.pest_name}</DialogTitle>
            <DialogDescription>
              {selectedRecord ? `${selectedRecord.crop_name} • Field #${selectedRecord.field_id}` : 'Observation details'}
            </DialogDescription>
          </DialogHeader>
          {selectedRecord && (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Scouting context</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Date</span><span>{formatDisplayDate(selectedRecord.observation_date)}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Observer</span><span>{selectedRecord.observer_name ?? '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Growth stage</span><span>{selectedRecord.growth_stage ?? '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Plant part</span><span>{selectedRecord.plant_part_affected ?? '—'}</span></div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Quantified pressure</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Severity score</span><span>{selectedRecord.severity_score?.toFixed(1) ?? '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Incidence</span><span>{selectedRecord.incidence_percent !== null ? `${selectedRecord.incidence_percent.toFixed(1)}%` : '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Area affected</span><span>{selectedRecord.area_affected_percent !== null ? `${selectedRecord.area_affected_percent.toFixed(1)}%` : '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Count / plant</span><span>{selectedRecord.count_per_plant ?? '—'}</span></div>
                </CardContent>
              </Card>
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">Notes</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {selectedRecord.notes ?? 'No notes captured for this observation.'}
                </CardContent>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
