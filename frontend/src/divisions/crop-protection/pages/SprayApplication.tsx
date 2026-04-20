import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { useToast } from '@/hooks/useToast'
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Droplets,
  Eye,
  FileText,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  User,
} from 'lucide-react'
import {
  SprayApplicationRecord,
  SprayComplianceReport,
  formatDisplayDate,
  toNumberOrNull,
} from '../lib/cropProtection'

type SprayFormState = {
  field_id: string
  application_date: string
  product_name: string
  product_type: string
  active_ingredient: string
  rate_per_ha: string
  rate_unit: string
  total_area_ha: string
  water_volume_l_ha: string
  applicator_name: string
  equipment_used: string
  target_pest: string
  pre_harvest_interval_days: string
  re_entry_interval_hours: string
  notes: string
}

const defaultFormState = (): SprayFormState => ({
  field_id: '',
  application_date: new Date().toISOString().split('T')[0],
  product_name: '',
  product_type: '',
  active_ingredient: '',
  rate_per_ha: '',
  rate_unit: 'L',
  total_area_ha: '',
  water_volume_l_ha: '',
  applicator_name: '',
  equipment_used: '',
  target_pest: '',
  pre_harvest_interval_days: '',
  re_entry_interval_hours: '',
  notes: '',
})

function toPayload(form: SprayFormState) {
  return {
    field_id: toNumberOrNull(form.field_id),
    application_date: form.application_date,
    product_name: form.product_name,
    product_type: form.product_type || null,
    active_ingredient: form.active_ingredient || null,
    rate_per_ha: toNumberOrNull(form.rate_per_ha),
    rate_unit: form.rate_unit || null,
    total_area_ha: toNumberOrNull(form.total_area_ha),
    water_volume_l_ha: toNumberOrNull(form.water_volume_l_ha),
    applicator_name: form.applicator_name || null,
    equipment_used: form.equipment_used || null,
    target_pest: form.target_pest || null,
    pre_harvest_interval_days: toNumberOrNull(form.pre_harvest_interval_days),
    re_entry_interval_hours: toNumberOrNull(form.re_entry_interval_hours),
    notes: form.notes || null,
  }
}

function toFormState(record: SprayApplicationRecord): SprayFormState {
  return {
    field_id: record.field_id !== null ? String(record.field_id) : '',
    application_date: record.application_date.slice(0, 10),
    product_name: record.product_name,
    product_type: record.product_type ?? '',
    active_ingredient: record.active_ingredient ?? '',
    rate_per_ha: record.rate_per_ha !== null ? String(record.rate_per_ha) : '',
    rate_unit: record.rate_unit ?? 'L',
    total_area_ha: record.total_area_ha !== null ? String(record.total_area_ha) : '',
    water_volume_l_ha: record.water_volume_l_ha !== null ? String(record.water_volume_l_ha) : '',
    applicator_name: record.applicator_name ?? '',
    equipment_used: record.equipment_used ?? '',
    target_pest: record.target_pest ?? '',
    pre_harvest_interval_days: record.pre_harvest_interval_days !== null ? String(record.pre_harvest_interval_days) : '',
    re_entry_interval_hours: record.re_entry_interval_hours !== null ? String(record.re_entry_interval_hours) : '',
    notes: record.notes ?? '',
  }
}

function SprayForm({
  form,
  onChange,
}: {
  form: SprayFormState
  onChange: (next: SprayFormState) => void
}) {
  const update = (field: keyof SprayFormState, value: string) => {
    onChange({ ...form, [field]: value })
  }

  return (
    <div className="grid gap-4 py-4 max-h-[70vh] overflow-y-auto">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Product Name</Label>
          <Input value={form.product_name} onChange={(event) => update('product_name', event.target.value)} placeholder="Fungicide X" />
        </div>
        <div className="space-y-2">
          <Label>Product Type</Label>
          <Input value={form.product_type} onChange={(event) => update('product_type', event.target.value)} placeholder="Fungicide" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Application Date</Label>
          <Input type="date" value={form.application_date} onChange={(event) => update('application_date', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Field ID</Label>
          <Input type="number" min="1" value={form.field_id} onChange={(event) => update('field_id', event.target.value)} placeholder="Optional" />
        </div>
        <div className="space-y-2">
          <Label>Target Pest</Label>
          <Input value={form.target_pest} onChange={(event) => update('target_pest', event.target.value)} placeholder="Blast complex" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <div className="space-y-2">
          <Label>Rate / ha</Label>
          <Input type="number" min="0" step="0.01" value={form.rate_per_ha} onChange={(event) => update('rate_per_ha', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Rate Unit</Label>
          <Input value={form.rate_unit} onChange={(event) => update('rate_unit', event.target.value)} placeholder="L" />
        </div>
        <div className="space-y-2">
          <Label>Total Area (ha)</Label>
          <Input type="number" min="0" step="0.01" value={form.total_area_ha} onChange={(event) => update('total_area_ha', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Water Volume (L/ha)</Label>
          <Input type="number" min="0" step="0.1" value={form.water_volume_l_ha} onChange={(event) => update('water_volume_l_ha', event.target.value)} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Applicator Name</Label>
          <Input value={form.applicator_name} onChange={(event) => update('applicator_name', event.target.value)} placeholder="License holder" />
        </div>
        <div className="space-y-2">
          <Label>Equipment Used</Label>
          <Input value={form.equipment_used} onChange={(event) => update('equipment_used', event.target.value)} placeholder="Boom sprayer" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Active Ingredient</Label>
          <Input value={form.active_ingredient} onChange={(event) => update('active_ingredient', event.target.value)} placeholder="Azoxystrobin" />
        </div>
        <div className="space-y-2">
          <Label>PHI (days)</Label>
          <Input type="number" min="0" value={form.pre_harvest_interval_days} onChange={(event) => update('pre_harvest_interval_days', event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>REI (hours)</Label>
          <Input type="number" min="0" value={form.re_entry_interval_hours} onChange={(event) => update('re_entry_interval_hours', event.target.value)} />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Notes</Label>
        <Textarea value={form.notes} onChange={(event) => update('notes', event.target.value)} placeholder="Weather, observed efficacy, residue constraints" rows={4} />
      </div>
    </div>
  )
}

export function SprayApplication() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRecord, setSelectedRecord] = useState<SprayApplicationRecord | null>(null)
  const [editingRecord, setEditingRecord] = useState<SprayApplicationRecord | null>(null)
  const [form, setForm] = useState<SprayFormState>(defaultFormState)

  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: applications, isLoading, error, refetch } = useQuery<SprayApplicationRecord[]>({
    queryKey: ['future', 'spray-applications'],
    queryFn: async () => apiClient.get('/api/v2/future/spray-applications/'),
  })

  const { data: complianceReport } = useQuery<SprayComplianceReport>({
    queryKey: ['future', 'spray-applications', 'compliance-report'],
    queryFn: async () => apiClient.get('/api/v2/future/spray-applications/compliance-report'),
  })

  const createMutation = useMutation({
    mutationFn: async (payload: ReturnType<typeof toPayload>) => apiClient.post('/api/v2/future/spray-applications/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'spray-applications'] })
      toast({ title: 'Application recorded', description: 'Spray application logged successfully.', type: 'success' })
      setIsDialogOpen(false)
      setForm(defaultFormState())
    },
    onError: () => {
      toast({ title: 'Error', description: 'Failed to record spray application.', type: 'error' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: ReturnType<typeof toPayload> }) => apiClient.put(`/api/v2/future/spray-applications/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'spray-applications'] })
      toast({ title: 'Application updated', description: 'Spray application changes saved.', type: 'success' })
      setEditingRecord(null)
      setIsDialogOpen(false)
      setForm(defaultFormState())
    },
    onError: () => {
      toast({ title: 'Error', description: 'Failed to update spray application.', type: 'error' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => apiClient.delete(`/api/v2/future/spray-applications/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'spray-applications'] })
      toast({ title: 'Application deleted', description: 'Spray record removed.', type: 'success' })
    },
    onError: () => {
      toast({ title: 'Error', description: 'Failed to delete spray application.', type: 'error' })
    },
  })

  const filteredApplications = useMemo(() => {
    return (applications ?? []).filter((record) => {
      const haystack = [record.product_name, record.product_type, record.target_pest, record.applicator_name]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(searchQuery.toLowerCase())
    })
  }, [applications, searchQuery])

  const totalArea = filteredApplications.reduce((sum, record) => sum + (record.total_area_ha ?? 0), 0)

  const openCreateDialog = () => {
    setEditingRecord(null)
    setForm(defaultFormState())
    setIsDialogOpen(true)
  }

  const openEditDialog = (record: SprayApplicationRecord) => {
    setEditingRecord(record)
    setForm(toFormState(record))
    setIsDialogOpen(true)
  }

  const handleSubmit = () => {
    if (!form.product_name || !form.application_date) {
      toast({ title: 'Validation error', description: 'Product name and application date are required.', type: 'error' })
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
            <Droplets className="h-8 w-8 text-blue-600" />
            Spray Applications
          </h1>
          <p className="text-muted-foreground mt-1 max-w-2xl">
            Track treatment operations with actual application rates, PHI/REI compliance, and treated area totals.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700" onClick={openCreateDialog}>
                <Plus className="mr-2 h-4 w-4" />
                Record Spray
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[760px]">
              <DialogHeader>
                <DialogTitle>{editingRecord ? 'Update spray application' : 'Record spray application'}</DialogTitle>
                <DialogDescription>Capture operational details and the compliance intervals required for safe use.</DialogDescription>
              </DialogHeader>
              <SprayForm form={form} onChange={setForm} />
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
                  {editingRecord
                    ? updateMutation.isPending ? 'Saving...' : 'Save changes'
                    : createMutation.isPending ? 'Logging...' : 'Log application'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
            <Droplets className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? <Skeleton className="h-8 w-16" /> : filteredApplications.length}</div>
            <p className="text-xs text-muted-foreground">Visible records in the current search</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Area Treated</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? <Skeleton className="h-8 w-16" /> : `${totalArea.toFixed(1)} ha`}</div>
            <p className="text-xs text-muted-foreground">Summed directly from recorded applications</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Rate</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? <Skeleton className="h-8 w-16" /> : `${(complianceReport?.compliance_rate ?? 0).toFixed(0)}%`}</div>
            <p className="text-xs text-muted-foreground">Records with PHI and REI captured</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliant Records</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? <Skeleton className="h-8 w-16" /> : complianceReport?.compliant_applications ?? 0}</div>
            <p className="text-xs text-muted-foreground">Safe interval data available</p>
          </CardContent>
        </Card>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>Failed to load spray applications. Please try again later.</AlertDescription>
        </Alert>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle>Application history</CardTitle>
                <CardDescription>Review treatment records, applicator details, and safety intervals.</CardDescription>
              </div>
              <div className="relative w-full lg:w-72">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search products or target pests"
                  className="pl-8"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((entry) => <Skeleton key={entry} className="h-12 w-full" />)}
              </div>
            ) : filteredApplications.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                <Droplets className="mx-auto mb-3 h-12 w-12 opacity-20" />
                <p>No spray applications recorded yet.</p>
              </div>
            ) : (
              <div className="rounded-md border">
                <table className="w-full text-sm text-left">
                  <thead className="bg-muted/50 text-muted-foreground">
                    <tr>
                      <th className="p-4 font-medium">Date</th>
                      <th className="p-4 font-medium">Product</th>
                      <th className="p-4 font-medium">Rate</th>
                      <th className="p-4 font-medium">Area</th>
                      <th className="p-4 font-medium">Applicator</th>
                      <th className="p-4 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredApplications.map((record) => (
                      <tr key={record.id} className="border-t hover:bg-muted/50 transition-colors">
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            {format(new Date(record.application_date), 'MMM d, yyyy')}
                          </div>
                        </td>
                        <td className="p-4 font-medium">
                          {record.product_name}
                          {record.product_type && <Badge variant="outline" className="ml-2 text-xs">{record.product_type}</Badge>}
                        </td>
                        <td className="p-4">{record.rate_per_ha ? `${record.rate_per_ha} ${record.rate_unit ?? ''}/ha` : '-'}</td>
                        <td className="p-4">{record.total_area_ha ? `${record.total_area_ha} ha` : '-'}</td>
                        <td className="p-4">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <User className="h-3 w-3" />
                            {record.applicator_name || 'N/A'}
                          </div>
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex justify-end gap-1">
                            <Button variant="ghost" size="icon" aria-label="View record" onClick={() => setSelectedRecord(record)}>
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" aria-label="Edit record" onClick={() => openEditDialog(record)}>
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label="Delete record"
                              onClick={() => {
                                if (window.confirm(`Delete ${record.product_name} application from ${formatDisplayDate(record.application_date)}?`)) {
                                  deleteMutation.mutate(record.id)
                                }
                              }}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Dialog open={selectedRecord !== null} onOpenChange={(open) => !open && setSelectedRecord(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedRecord?.product_name}</DialogTitle>
            <DialogDescription>{selectedRecord?.target_pest ?? 'Treatment record'}</DialogDescription>
          </DialogHeader>
          {selectedRecord && (
            <div className="grid gap-4 md:grid-cols-2 text-sm">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Application details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Date</span><span>{formatDisplayDate(selectedRecord.application_date)}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Rate</span><span>{selectedRecord.rate_per_ha ? `${selectedRecord.rate_per_ha} ${selectedRecord.rate_unit ?? ''}/ha` : '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Area</span><span>{selectedRecord.total_area_ha ? `${selectedRecord.total_area_ha} ha` : '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Water volume</span><span>{selectedRecord.water_volume_l_ha ? `${selectedRecord.water_volume_l_ha} L/ha` : '—'}</span></div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Compliance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Applicator</span><span>{selectedRecord.applicator_name ?? '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">Equipment</span><span>{selectedRecord.equipment_used ?? '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">PHI</span><span>{selectedRecord.pre_harvest_interval_days !== null ? `${selectedRecord.pre_harvest_interval_days} days` : '—'}</span></div>
                  <div className="flex items-center justify-between gap-4"><span className="text-muted-foreground">REI</span><span>{selectedRecord.re_entry_interval_hours !== null ? `${selectedRecord.re_entry_interval_hours} hours` : '—'}</span></div>
                </CardContent>
              </Card>
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">Operational notes</CardTitle>
                </CardHeader>
                <CardContent className="whitespace-pre-wrap text-muted-foreground">
                  {selectedRecord.notes ?? 'No notes captured for this application.'}
                </CardContent>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
