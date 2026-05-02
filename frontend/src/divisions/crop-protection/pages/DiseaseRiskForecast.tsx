/**
 * Disease Risk Forecast Page
 * Weather-based disease prediction models with risk levels and alerts
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import {
  AlertCircle,
  AlertTriangle,
  CalendarClock,
  Eye,
  Plus,
  RefreshCw,
  ShieldAlert,
  Trash2,
} from 'lucide-react'
import {
  DiseaseRiskForecastRecord,
  formatDisplayDate,
  formatDisplayDateTime,
  parseMultilineList,
  riskLevels,
  riskRank,
  toDayBoundary,
  toNumberOrNull,
} from '../lib/cropProtection'

type DiseaseForecastFormState = {
  location_id: string
  forecast_date: string
  valid_from: string
  valid_until: string
  disease_name: string
  crop_name: string
  risk_level: string
  risk_score: string
  model_name: string
  model_version: string
  contributing_factors: string
  recommended_actions: string
}

const defaultFormState = (): DiseaseForecastFormState => {
  const today = new Date().toISOString().split('T')[0]
  return {
    location_id: '',
    forecast_date: today,
    valid_from: toDayBoundary(today, 'start'),
    valid_until: toDayBoundary(today, 'end'),
    disease_name: '',
    crop_name: '',
    risk_level: 'medium',
    risk_score: '0.45',
    model_name: 'Integrated disease risk model',
    model_version: '1.0',
    contributing_factors: 'temperature: 28°C\nhumidity: 88%\nleaf_wetness_hours: 11',
    recommended_actions: 'Scout hotspot blocks\nReview resistant varieties\nPrepare preventative spray window',
  }
}

function toPayload(form: DiseaseForecastFormState) {
  const contributingFactors = Object.fromEntries(
    parseMultilineList(form.contributing_factors).map((entry) => {
      const [key, ...value] = entry.split(':')
      return [key.trim(), value.join(':').trim() || true]
    })
  )

  return {
    location_id: toNumberOrNull(form.location_id),
    forecast_date: form.forecast_date,
    valid_from: form.valid_from,
    valid_until: form.valid_until,
    disease_name: form.disease_name,
    crop_name: form.crop_name,
    risk_level: form.risk_level,
    risk_score: toNumberOrNull(form.risk_score),
    contributing_factors: Object.keys(contributingFactors).length > 0 ? contributingFactors : null,
    recommended_actions: parseMultilineList(form.recommended_actions),
    model_name: form.model_name,
    model_version: form.model_version,
  }
}

function ForecastForm({
  form,
  onChange,
}: {
  form: DiseaseForecastFormState
  onChange: (next: DiseaseForecastFormState) => void
}) {
  const update = (field: keyof DiseaseForecastFormState, value: string) => {
    onChange({ ...form, [field]: value })
  }

  return (
    <div className="space-y-4 py-4 max-h-[70vh] overflow-y-auto">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Disease Name</Label>
          <Input value={form.disease_name} onChange={(event) => update('disease_name', event.target.value)} placeholder="Late blight" />
        </div>
        <div className="space-y-2">
          <Label>Crop Name</Label>
          <Input value={form.crop_name} onChange={(event) => update('crop_name', event.target.value)} placeholder="Potato" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="space-y-2">
          <Label>Location ID</Label>
          <Input type="number" min="1" value={form.location_id} onChange={(event) => update('location_id', event.target.value)} placeholder="Optional" />
        </div>
        <div className="space-y-2">
          <Label>Forecast Date</Label>
          <Input type="date" value={form.forecast_date} onChange={(event) => update('forecast_date', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Risk Level</Label>
          <Select value={form.risk_level} onValueChange={(value) => update('risk_level', value)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {riskLevels.map((level) => (
                <SelectItem key={level.value} value={level.value}>
                  {level.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Risk Score (0-1)</Label>
          <Input type="number" min="0" max="1" step="0.01" value={form.risk_score} onChange={(event) => update('risk_score', event.target.value)} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Valid From</Label>
          <Input type="datetime-local" value={form.valid_from.slice(0, 16)} onChange={(event) => update('valid_from', `${event.target.value}:00`)} />
        </div>
        <div className="space-y-2">
          <Label>Valid Until</Label>
          <Input type="datetime-local" value={form.valid_until.slice(0, 16)} onChange={(event) => update('valid_until', `${event.target.value}:00`)} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Model Name</Label>
          <Input value={form.model_name} onChange={(event) => update('model_name', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Model Version</Label>
          <Input value={form.model_version} onChange={(event) => update('model_version', event.target.value)} />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Contributing Factors</Label>
        <Textarea value={form.contributing_factors} onChange={(event) => update('contributing_factors', event.target.value)} placeholder="temperature: 28°C" rows={4} />
      </div>

      <div className="space-y-2">
        <Label>Recommended Actions</Label>
        <Textarea value={form.recommended_actions} onChange={(event) => update('recommended_actions', event.target.value)} placeholder="One action per line" rows={4} />
      </div>
    </div>
  )
}

export function DiseaseRiskForecastPage() {
  const queryClient = useQueryClient()
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [selectedRecord, setSelectedRecord] = useState<DiseaseRiskForecastRecord | null>(null)
  const [riskFilter, setRiskFilter] = useState('all')
  const [form, setForm] = useState<DiseaseForecastFormState>(defaultFormState)

  const { data: forecasts, isLoading, error, refetch } = useQuery<DiseaseRiskForecastRecord[]>({
    queryKey: ['future', 'disease-risk-forecasts'],
    queryFn: async () => apiClient.get('/api/v2/future/disease-risk-forecasts/'),
  })

  const { data: activeForecasts } = useQuery<DiseaseRiskForecastRecord[]>({
    queryKey: ['future', 'disease-risk-forecasts', 'active'],
    queryFn: async () => apiClient.get('/api/v2/future/disease-risk-forecasts/active'),
  })

  const { data: highRiskForecasts } = useQuery<DiseaseRiskForecastRecord[]>({
    queryKey: ['future', 'disease-risk-forecasts', 'high-risk'],
    queryFn: async () => apiClient.get('/api/v2/future/disease-risk-forecasts/high-risk'),
  })

  const createMutation = useMutation({
    mutationFn: (payload: ReturnType<typeof toPayload>) => apiClient.post('/api/v2/future/disease-risk-forecasts/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'disease-risk-forecasts'] })
      toast.success('Disease risk forecast created')
      setForm(defaultFormState())
      setIsCreateOpen(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create forecast'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/api/v2/future/disease-risk-forecasts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'disease-risk-forecasts'] })
      toast.success('Forecast deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete forecast'),
  })

  const filteredForecasts = useMemo(() => {
    return (forecasts ?? []).filter((record) => riskFilter === 'all' || record.risk_level.toLowerCase() === riskFilter)
      .sort((left, right) => riskRank(right.risk_level) - riskRank(left.risk_level))
  }, [forecasts, riskFilter])

  const riskSummary = useMemo(() => {
    return riskLevels.map((level) => ({
      ...level,
      count: (forecasts ?? []).filter((entry) => entry.risk_level.toLowerCase() === level.value).length,
    }))
  }, [forecasts])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            Disease Risk Forecasts
          </h1>
          <p className="text-muted-foreground mt-1 max-w-2xl">
            Maintain live disease windows with explicit validity ranges, contributing factors, and field-ready recommendations.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Forecast
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>Create disease risk forecast</DialogTitle>
                <DialogDescription>Publish a forecast window tied to a disease model and actionable guidance.</DialogDescription>
              </DialogHeader>
              <ForecastForm form={form} onChange={setForm} />
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => {
                    if (!form.disease_name || !form.crop_name || !form.forecast_date || !form.model_name || !form.model_version) {
                      toast.error('Disease, crop, date, model name, and model version are required')
                      return
                    }
                    createMutation.mutate(toPayload(form))
                  }}
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create forecast'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        {isLoading
          ? [1, 2, 3, 4].map((entry) => <Skeleton key={entry} className="h-28" />)
          : riskSummary.map((risk) => (
              <Card key={risk.value} className={`border-l-4 ${risk.color.replace('bg-', 'border-')}`}>
                <CardHeader className="pb-2">
                  <CardDescription>{risk.label} risk</CardDescription>
                  <CardTitle className="text-3xl">{risk.count}</CardTitle>
                </CardHeader>
              </Card>
            ))}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load disease forecasts.
            <Button variant="link" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">All forecasts</TabsTrigger>
          <TabsTrigger value="active">Active windows</TabsTrigger>
          <TabsTrigger value="high-risk">High risk</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="flex justify-end">
            <Select value={riskFilter} onValueChange={setRiskFilter}>
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="Filter by risk" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All risk levels</SelectItem>
                {riskLevels.map((risk) => (
                  <SelectItem key={risk.value} value={risk.value}>
                    {risk.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {isLoading ? (
            <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
              {[1, 2, 3].map((entry) => <Skeleton key={entry} className="h-64" />)}
            </div>
          ) : (
            <ForecastGrid forecasts={filteredForecasts} onDelete={(id) => deleteMutation.mutate(id)} onSelect={setSelectedRecord} />
          )}
        </TabsContent>

        <TabsContent value="active">
          <ForecastGrid forecasts={activeForecasts ?? []} onDelete={(id) => deleteMutation.mutate(id)} onSelect={setSelectedRecord} emptyMessage="No active forecast windows are currently open." />
        </TabsContent>

        <TabsContent value="high-risk">
          <ForecastGrid forecasts={highRiskForecasts ?? []} onDelete={(id) => deleteMutation.mutate(id)} onSelect={setSelectedRecord} emptyMessage="No high-risk forecasts at the moment." />
        </TabsContent>
      </Tabs>

      <Dialog open={selectedRecord !== null} onOpenChange={(open) => !open && setSelectedRecord(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedRecord?.disease_name}</DialogTitle>
            <DialogDescription>{selectedRecord?.crop_name}</DialogDescription>
          </DialogHeader>
          {selectedRecord && (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Forecast window</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Forecast date</span><span>{formatDisplayDate(selectedRecord.forecast_date)}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Valid from</span><span>{formatDisplayDateTime(selectedRecord.valid_from)}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Valid until</span><span>{formatDisplayDateTime(selectedRecord.valid_until)}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Model</span><span>{selectedRecord.model_name} v{selectedRecord.model_version}</span></div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Risk drivers</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {Object.entries(selectedRecord.contributing_factors ?? {}).length > 0 ? (
                    Object.entries(selectedRecord.contributing_factors ?? {}).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between gap-4">
                        <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</span>
                        <span>{String(value)}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-muted-foreground">No contributing factors recorded.</p>
                  )}
                </CardContent>
              </Card>
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">Recommended actions</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    {(selectedRecord.recommended_actions ?? []).length > 0 ? (
                      selectedRecord.recommended_actions?.map((action) => <li key={action}>• {action}</li>)
                    ) : (
                      <li>No actions provided.</li>
                    )}
                  </ul>
                </CardContent>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function ForecastGrid({
  forecasts,
  onDelete,
  onSelect,
  emptyMessage = 'No disease forecasts recorded yet.',
}: {
  forecasts: DiseaseRiskForecastRecord[]
  onDelete: (id: number) => void
  onSelect: (record: DiseaseRiskForecastRecord) => void
  emptyMessage?: string
}) {
  if (forecasts.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <ShieldAlert className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <p className="text-muted-foreground">{emptyMessage}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
      {forecasts.map((record) => {
        const level = riskLevels.find((entry) => entry.value === record.risk_level.toLowerCase()) ?? riskLevels[0]

        return (
          <Card key={record.id} className={`border-l-4 ${level.color.replace('bg-', 'border-')}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between gap-2">
                <Badge className={`${level.color} text-white`}>{level.label}</Badge>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="icon" aria-label="View forecast" onClick={() => onSelect(record)}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Delete forecast"
                    onClick={() => {
                      if (window.confirm(`Delete ${record.disease_name} forecast for ${record.crop_name}?`)) {
                        onDelete(record.id)
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
              <CardTitle className="text-base">{record.disease_name}</CardTitle>
              <CardDescription>{record.crop_name} • {record.location_id ? `Location #${record.location_id}` : 'Location optional'}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center justify-between gap-4">
                <span className="text-muted-foreground">Forecast date</span>
                <span>{formatDisplayDate(record.forecast_date)}</span>
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-muted-foreground">Valid window</span>
                <span className="text-right">{formatDisplayDateTime(record.valid_from)} → {formatDisplayDateTime(record.valid_until)}</span>
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-muted-foreground">Risk score</span>
                <span>{record.risk_score !== null ? `${Math.round(record.risk_score * 100)}%` : '—'}</span>
              </div>
              <div className="rounded-2xl bg-muted/40 p-3 text-xs text-muted-foreground">
                <div className="mb-1 flex items-center gap-2 font-medium text-foreground">
                  <CalendarClock className="h-3.5 w-3.5" />
                  Action snapshot
                </div>
                {(record.recommended_actions ?? []).slice(0, 2).map((action) => (
                  <div key={action}>• {action}</div>
                ))}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
