/**
 * IPM Strategies Page
 * Integrated Pest Management strategies with control methods and action thresholds
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
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import {
  AlertCircle,
  Eye,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Shield,
  Trash2,
} from 'lucide-react'
import {
  IPMStrategyRecord,
  formatDisplayDate,
  ipmMethodGroups,
  joinMultilineList,
  parseMultilineList,
  toNumberOrNull,
} from '../lib/cropProtection'

type IPMFormState = {
  field_id: string
  strategy_name: string
  crop_name: string
  target_pest: string
  pest_type: string
  economic_threshold: string
  action_threshold: string
  prevention_methods: string
  monitoring_methods: string
  biological_controls: string
  physical_controls: string
  chemical_controls: string
  implementation_start: string
  implementation_end: string
  growth_stages: string
  effectiveness_rating: string
  cost_effectiveness: string
  environmental_impact_score: string
  notes: string
}

const defaultFormState = (): IPMFormState => ({
  field_id: '',
  strategy_name: '',
  crop_name: '',
  target_pest: '',
  pest_type: 'insect',
  economic_threshold: '',
  action_threshold: '',
  prevention_methods: 'Use resistant variety\nSanitize volunteer hosts',
  monitoring_methods: 'Scout weekly\nTrack trap counts twice per week',
  biological_controls: 'Conserve beneficial insects',
  physical_controls: 'Install sticky traps',
  chemical_controls: 'Reserve targeted chemistry for threshold exceedance',
  implementation_start: new Date().toISOString().split('T')[0],
  implementation_end: '',
  growth_stages: 'Tillering\nFlowering',
  effectiveness_rating: '75',
  cost_effectiveness: '1.5',
  environmental_impact_score: '18',
  notes: '',
})

function toPayload(form: IPMFormState) {
  return {
    field_id: toNumberOrNull(form.field_id),
    strategy_name: form.strategy_name,
    crop_name: form.crop_name,
    target_pest: form.target_pest,
    pest_type: form.pest_type || null,
    economic_threshold: form.economic_threshold || null,
    action_threshold: form.action_threshold || null,
    prevention_methods: parseMultilineList(form.prevention_methods),
    monitoring_methods: parseMultilineList(form.monitoring_methods),
    biological_controls: parseMultilineList(form.biological_controls),
    physical_controls: parseMultilineList(form.physical_controls),
    chemical_controls: parseMultilineList(form.chemical_controls),
    implementation_start: form.implementation_start || null,
    implementation_end: form.implementation_end || null,
    growth_stages: parseMultilineList(form.growth_stages),
    effectiveness_rating: toNumberOrNull(form.effectiveness_rating),
    cost_effectiveness: toNumberOrNull(form.cost_effectiveness),
    environmental_impact_score: toNumberOrNull(form.environmental_impact_score),
    notes: form.notes || null,
  }
}

function toFormState(record: IPMStrategyRecord): IPMFormState {
  return {
    field_id: record.field_id !== null ? String(record.field_id) : '',
    strategy_name: record.strategy_name,
    crop_name: record.crop_name,
    target_pest: record.target_pest,
    pest_type: record.pest_type ?? 'insect',
    economic_threshold: record.economic_threshold ?? '',
    action_threshold: record.action_threshold ?? '',
    prevention_methods: joinMultilineList(record.prevention_methods),
    monitoring_methods: joinMultilineList(record.monitoring_methods),
    biological_controls: joinMultilineList(record.biological_controls),
    physical_controls: joinMultilineList(record.physical_controls),
    chemical_controls: joinMultilineList(record.chemical_controls),
    implementation_start: record.implementation_start?.slice(0, 10) ?? '',
    implementation_end: record.implementation_end?.slice(0, 10) ?? '',
    growth_stages: joinMultilineList(record.growth_stages),
    effectiveness_rating: record.effectiveness_rating !== null ? String(record.effectiveness_rating) : '',
    cost_effectiveness: record.cost_effectiveness !== null ? String(record.cost_effectiveness) : '',
    environmental_impact_score: record.environmental_impact_score !== null ? String(record.environmental_impact_score) : '',
    notes: record.notes ?? '',
  }
}

function StrategyForm({
  form,
  onChange,
}: {
  form: IPMFormState
  onChange: (next: IPMFormState) => void
}) {
  const update = (field: keyof IPMFormState, value: string) => {
    onChange({ ...form, [field]: value })
  }

  return (
    <div className="space-y-4 py-4 max-h-[70vh] overflow-y-auto">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Strategy Name</Label>
          <Input value={form.strategy_name} onChange={(event) => update('strategy_name', event.target.value)} placeholder="Rice hopper prevention plan" />
        </div>
        <div className="space-y-2">
          <Label>Field ID</Label>
          <Input type="number" min="1" value={form.field_id} onChange={(event) => update('field_id', event.target.value)} placeholder="Optional" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Crop Name</Label>
          <Input value={form.crop_name} onChange={(event) => update('crop_name', event.target.value)} placeholder="Rice" />
        </div>
        <div className="space-y-2">
          <Label>Target Pest</Label>
          <Input value={form.target_pest} onChange={(event) => update('target_pest', event.target.value)} placeholder="Brown planthopper" />
        </div>
        <div className="space-y-2">
          <Label>Pest Type</Label>
          <Input value={form.pest_type} onChange={(event) => update('pest_type', event.target.value)} placeholder="Insect" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Economic Threshold</Label>
          <Input value={form.economic_threshold} onChange={(event) => update('economic_threshold', event.target.value)} placeholder="2 hoppers per tiller" />
        </div>
        <div className="space-y-2">
          <Label>Action Threshold</Label>
          <Input value={form.action_threshold} onChange={(event) => update('action_threshold', event.target.value)} placeholder="4 hoppers per tiller" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Implementation Start</Label>
          <Input type="date" value={form.implementation_start} onChange={(event) => update('implementation_start', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Implementation End</Label>
          <Input type="date" value={form.implementation_end} onChange={(event) => update('implementation_end', event.target.value)} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Effectiveness Rating</Label>
          <Input type="number" min="0" max="100" step="0.1" value={form.effectiveness_rating} onChange={(event) => update('effectiveness_rating', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Cost Effectiveness</Label>
          <Input type="number" min="0" step="0.1" value={form.cost_effectiveness} onChange={(event) => update('cost_effectiveness', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Environmental Impact Score</Label>
          <Input type="number" min="0" step="0.1" value={form.environmental_impact_score} onChange={(event) => update('environmental_impact_score', event.target.value)} />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Growth Stages</Label>
        <Textarea value={form.growth_stages} onChange={(event) => update('growth_stages', event.target.value)} placeholder="One stage per line" rows={3} />
      </div>

      <div className="space-y-2">
        <Label>{ipmMethodGroups[0].label}</Label>
        <Textarea value={form.prevention_methods} onChange={(event) => update('prevention_methods', event.target.value)} placeholder="One tactic per line" rows={3} />
      </div>
      <div className="space-y-2">
        <Label>{ipmMethodGroups[1].label}</Label>
        <Textarea value={form.monitoring_methods} onChange={(event) => update('monitoring_methods', event.target.value)} placeholder="One tactic per line" rows={3} />
      </div>
      <div className="space-y-2">
        <Label>{ipmMethodGroups[2].label}</Label>
        <Textarea value={form.biological_controls} onChange={(event) => update('biological_controls', event.target.value)} placeholder="One tactic per line" rows={3} />
      </div>
      <div className="space-y-2">
        <Label>{ipmMethodGroups[3].label}</Label>
        <Textarea value={form.physical_controls} onChange={(event) => update('physical_controls', event.target.value)} placeholder="One tactic per line" rows={3} />
      </div>
      <div className="space-y-2">
        <Label>{ipmMethodGroups[4].label}</Label>
        <Textarea value={form.chemical_controls} onChange={(event) => update('chemical_controls', event.target.value)} placeholder="One tactic per line" rows={3} />
      </div>

      <div className="space-y-2">
        <Label>Notes</Label>
        <Textarea value={form.notes} onChange={(event) => update('notes', event.target.value)} placeholder="Resistance rotation guidance, scouting cadence, stewardship notes" rows={4} />
      </div>
    </div>
  )
}

export function IPMStrategies() {
  const [showCreate, setShowCreate] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRecord, setSelectedRecord] = useState<IPMStrategyRecord | null>(null)
  const [editingRecord, setEditingRecord] = useState<IPMStrategyRecord | null>(null)
  const [form, setForm] = useState<IPMFormState>(defaultFormState)
  const queryClient = useQueryClient()

  const { data: strategies, isLoading, error, refetch } = useQuery<IPMStrategyRecord[]>({
    queryKey: ['future', 'ipm-strategies'],
    queryFn: async () => apiClient.get('/api/v2/future/ipm-strategies/'),
  })

  const createMutation = useMutation({
    mutationFn: (payload: ReturnType<typeof toPayload>) => apiClient.post('/api/v2/future/ipm-strategies/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'ipm-strategies'] })
      toast.success('IPM strategy created')
      setShowCreate(false)
      setForm(defaultFormState())
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create strategy'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: ReturnType<typeof toPayload> }) => apiClient.put(`/api/v2/future/ipm-strategies/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'ipm-strategies'] })
      toast.success('IPM strategy updated')
      setShowCreate(false)
      setEditingRecord(null)
      setForm(defaultFormState())
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to update strategy'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/future/ipm-strategies/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'ipm-strategies'] })
      toast.success('Strategy deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete strategy'),
  })

  const filteredStrategies = useMemo(() => {
    return (strategies ?? []).filter((strategy) => {
      const haystack = [strategy.strategy_name, strategy.target_pest, strategy.crop_name, strategy.pest_type]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(searchQuery.toLowerCase())
    })
  }, [searchQuery, strategies])

  const metrics = useMemo(() => {
    const records = filteredStrategies
    return {
      total: records.length,
      withChemicalFallback: records.filter((entry) => (entry.chemical_controls ?? []).length > 0).length,
      averageEffectiveness:
        records.length > 0
          ? records.reduce((sum, entry) => sum + (entry.effectiveness_rating ?? 0), 0) / records.length
          : 0,
      active: records.filter((entry) => !entry.implementation_end || new Date(entry.implementation_end).getTime() >= Date.now()).length,
    }
  }, [filteredStrategies])

  const openCreateDialog = () => {
    setEditingRecord(null)
    setForm(defaultFormState())
    setShowCreate(true)
  }

  const openEditDialog = (record: IPMStrategyRecord) => {
    setEditingRecord(record)
    setForm(toFormState(record))
    setShowCreate(true)
  }

  const submitForm = () => {
    if (!form.strategy_name || !form.crop_name || !form.target_pest) {
      toast.error('Strategy name, crop, and target pest are required')
      return
    }

    const payload = toPayload(form)
    if (editingRecord) {
      updateMutation.mutate({ id: editingRecord.id, payload })
      return
    }

    createMutation.mutate(payload)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Shield className="h-8 w-8 text-emerald-500" />
            IPM Strategies
          </h1>
          <p className="text-muted-foreground mt-1 max-w-2xl">
            Build actionable prevention, monitoring, and intervention plans for each crop-pest combination.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button onClick={openCreateDialog}>
                <Plus className="mr-2 h-4 w-4" />
                New Strategy
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>{editingRecord ? 'Update IPM strategy' : 'Create IPM strategy'}</DialogTitle>
                <DialogDescription>Define thresholds, method stacks, and stewardship guidance for crop protection teams.</DialogDescription>
              </DialogHeader>
              <StrategyForm form={form} onChange={setForm} />
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button onClick={submitForm} disabled={createMutation.isPending || updateMutation.isPending}>
                  {editingRecord
                    ? updateMutation.isPending ? 'Saving...' : 'Save changes'
                    : createMutation.isPending ? 'Creating...' : 'Create strategy'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2"><CardDescription>Visible plans</CardDescription><CardTitle className="text-3xl">{isLoading ? '—' : metrics.total}</CardTitle></CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardDescription>Active plans</CardDescription><CardTitle className="text-3xl">{isLoading ? '—' : metrics.active}</CardTitle></CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardDescription>Average effectiveness</CardDescription><CardTitle className="text-3xl">{isLoading ? '—' : `${metrics.averageEffectiveness.toFixed(0)}%`}</CardTitle></CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardDescription>Chemical fallback plans</CardDescription><CardTitle className="text-3xl">{isLoading ? '—' : metrics.withChemicalFallback}</CardTitle></CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <CardTitle>Strategy library</CardTitle>
              <CardDescription>Search by crop, pest, or strategy name to find the right playbook.</CardDescription>
            </div>
            <div className="relative w-full lg:w-80">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input className="pl-9" placeholder="Search crop, pest, or strategy" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Failed to load IPM strategies.
                <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
              </AlertDescription>
            </Alert>
          )}

          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[1, 2, 3].map((entry) => <Skeleton key={entry} className="h-72" />)}
            </div>
          ) : filteredStrategies.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {filteredStrategies.map((strategy) => (
                <Card key={strategy.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="outline">{strategy.pest_type ?? 'General'}</Badge>
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="icon" aria-label="View strategy" onClick={() => setSelectedRecord(strategy)}>
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" aria-label="Edit strategy" onClick={() => openEditDialog(strategy)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Delete strategy"
                          onClick={() => {
                            if (window.confirm(`Delete ${strategy.strategy_name}?`)) {
                              deleteMutation.mutate(strategy.id)
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                    <CardTitle className="text-base mt-2">{strategy.strategy_name}</CardTitle>
                    <CardDescription>{strategy.crop_name} • {strategy.target_pest}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Economic threshold</span><span>{strategy.economic_threshold ?? '—'}</span></div>
                    <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Action threshold</span><span>{strategy.action_threshold ?? '—'}</span></div>
                    <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Effectiveness</span><span>{strategy.effectiveness_rating !== null ? `${strategy.effectiveness_rating.toFixed(0)}%` : '—'}</span></div>
                    <div className="rounded-2xl bg-muted/40 p-3 text-xs text-muted-foreground">
                      <p className="font-medium text-foreground">Primary tactics</p>
                      <div className="mt-2 space-y-1">
                        {(strategy.prevention_methods ?? []).slice(0, 2).map((item) => <div key={item}>• {item}</div>)}
                        {(strategy.monitoring_methods ?? []).slice(0, 1).map((item) => <div key={item}>• {item}</div>)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <Shield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No IPM strategies defined yet</p>
                <Button className="mt-4" onClick={openCreateDialog}>
                  <Plus className="h-4 w-4 mr-2" />Add first strategy
                </Button>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      <Dialog open={selectedRecord !== null} onOpenChange={(open) => !open && setSelectedRecord(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{selectedRecord?.strategy_name}</DialogTitle>
            <DialogDescription>{selectedRecord?.crop_name} • {selectedRecord?.target_pest}</DialogDescription>
          </DialogHeader>
          {selectedRecord && (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Thresholds & timing</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Economic threshold</span><span>{selectedRecord.economic_threshold ?? '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Action threshold</span><span>{selectedRecord.action_threshold ?? '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Start</span><span>{formatDisplayDate(selectedRecord.implementation_start)}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">End</span><span>{formatDisplayDate(selectedRecord.implementation_end)}</span></div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Performance metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Effectiveness</span><span>{selectedRecord.effectiveness_rating !== null ? `${selectedRecord.effectiveness_rating.toFixed(0)}%` : '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Cost effectiveness</span><span>{selectedRecord.cost_effectiveness ?? '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Environmental impact</span><span>{selectedRecord.environmental_impact_score ?? '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Growth stages</span><span>{(selectedRecord.growth_stages ?? []).join(', ') || '—'}</span></div>
                </CardContent>
              </Card>
              {[
                { title: 'Prevention', items: selectedRecord.prevention_methods },
                { title: 'Monitoring', items: selectedRecord.monitoring_methods },
                { title: 'Biological', items: selectedRecord.biological_controls },
                { title: 'Physical', items: selectedRecord.physical_controls },
                { title: 'Chemical', items: selectedRecord.chemical_controls },
              ].map((group) => (
                <Card key={group.title}>
                  <CardHeader>
                    <CardTitle className="text-base">{group.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-muted-foreground space-y-1">
                    {(group.items ?? []).length > 0 ? group.items?.map((item) => <div key={item}>• {item}</div>) : <div>No entries</div>}
                  </CardContent>
                </Card>
              ))}
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">Notes</CardTitle>
                </CardHeader>
                <CardContent className="whitespace-pre-wrap text-sm text-muted-foreground">
                  {selectedRecord.notes ?? 'No notes captured for this strategy.'}
                </CardContent>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
