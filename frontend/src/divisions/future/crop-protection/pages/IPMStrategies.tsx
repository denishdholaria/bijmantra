/**
 * IPM Strategies Page
 * Integrated Pest Management strategies with control methods and action thresholds
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
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { AlertCircle, Plus, Shield, RefreshCw, Trash2, Target, Leaf, Bug, Beaker } from 'lucide-react'

interface IPMStrategy {
  id: string
  strategy_name: string
  target_pest: string
  crop_id: string
  action_threshold: string | null
  control_methods: string[] | null
  monitoring_protocol: string | null
  economic_threshold: number | null
  status: string
  created_at: string
}

const CONTROL_METHOD_TYPES = [
  { value: 'cultural', label: 'Cultural', icon: Leaf, color: 'text-green-500' },
  { value: 'biological', label: 'Biological', icon: Bug, color: 'text-blue-500' },
  { value: 'mechanical', label: 'Mechanical', icon: Target, color: 'text-orange-500' },
  { value: 'chemical', label: 'Chemical', icon: Beaker, color: 'text-red-500' },
]

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Draft', color: 'bg-slate-500' },
  { value: 'active', label: 'Active', color: 'bg-green-500' },
  { value: 'archived', label: 'Archived', color: 'bg-gray-500' },
]

const getStatusInfo = (status: string) => STATUS_OPTIONS.find(s => s.value === status) || STATUS_OPTIONS[0]

export function IPMStrategies() {
  const [showCreate, setShowCreate] = useState(false)
  const [newStrategy, setNewStrategy] = useState({
    strategy_name: '',
    target_pest: '',
    crop_id: '',
    action_threshold: '',
    control_methods: [] as string[],
    monitoring_protocol: '',
    economic_threshold: 0,
    status: 'draft',
  })
  const [selectedMethods, setSelectedMethods] = useState<string[]>([])
  const queryClient = useQueryClient()

  const { data: strategies, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'ipm-strategies'],
    queryFn: () => apiClient.get('/api/v2/future/ipm-strategy/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newStrategy) => apiClient.post('/api/v2/future/ipm-strategy/', {
      ...data,
      control_methods: selectedMethods,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'ipm-strategies'] })
      toast.success('IPM strategy created')
      setShowCreate(false)
      setSelectedMethods([])
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create strategy'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v2/future/ipm-strategy/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'ipm-strategies'] })
      toast.success('Strategy deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  const toggleMethod = (method: string) => {
    setSelectedMethods(prev => 
      prev.includes(method) ? prev.filter(m => m !== method) : [...prev, method]
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Shield className="h-8 w-8 text-emerald-500" />
            IPM Strategies
          </h1>
          <p className="text-muted-foreground mt-1">
            Integrated Pest Management action thresholds and control methods
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Strategy</Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Create IPM Strategy</DialogTitle>
                <DialogDescription>Define integrated pest management approach</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
                <div className="space-y-2">
                  <Label>Strategy Name</Label>
                  <Input
                    value={newStrategy.strategy_name}
                    onChange={(e) => setNewStrategy((p) => ({ ...p, strategy_name: e.target.value }))}
                    placeholder="Aphid Management - Wheat"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Target Pest</Label>
                    <Input
                      value={newStrategy.target_pest}
                      onChange={(e) => setNewStrategy((p) => ({ ...p, target_pest: e.target.value }))}
                      placeholder="Aphid"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Crop ID</Label>
                    <Input
                      value={newStrategy.crop_id}
                      onChange={(e) => setNewStrategy((p) => ({ ...p, crop_id: e.target.value }))}
                      placeholder="CROP-001"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Action Threshold</Label>
                  <Input
                    value={newStrategy.action_threshold}
                    onChange={(e) => setNewStrategy((p) => ({ ...p, action_threshold: e.target.value }))}
                    placeholder="5 aphids per tiller"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Economic Threshold ($/ha)</Label>
                    <Input
                      type="number" min="0"
                      value={newStrategy.economic_threshold}
                      onChange={(e) => setNewStrategy((p) => ({ ...p, economic_threshold: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Status</Label>
                    <Select value={newStrategy.status}
                      onValueChange={(v) => setNewStrategy((p) => ({ ...p, status: v }))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {STATUS_OPTIONS.map((s) => (
                          <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Control Methods</Label>
                  <div className="flex flex-wrap gap-2">
                    {CONTROL_METHOD_TYPES.map((method) => (
                      <Button
                        key={method.value}
                        type="button"
                        variant={selectedMethods.includes(method.value) ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => toggleMethod(method.value)}
                        className="gap-1"
                      >
                        <method.icon className={`h-3 w-3 ${selectedMethods.includes(method.value) ? '' : method.color}`} />
                        {method.label}
                      </Button>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Monitoring Protocol</Label>
                  <Textarea
                    value={newStrategy.monitoring_protocol}
                    onChange={(e) => setNewStrategy((p) => ({ ...p, monitoring_protocol: e.target.value }))}
                    placeholder="Weekly scouting, 10 plants per plot..."
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newStrategy)}
                  disabled={!newStrategy.strategy_name || !newStrategy.target_pest || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Strategy'}
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
            Failed to load IPM strategies.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-64" />)}
        </div>
      )}

      {/* Strategy Cards */}
      {!isLoading && !error && (
        <>
          {Array.isArray(strategies) && strategies.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {strategies.map((strategy: IPMStrategy) => {
                const status = getStatusInfo(strategy.status)
                return (
                  <Card key={strategy.id} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <Badge className={`${status.color} text-white`}>{status.label}</Badge>
                        <Button variant="ghost" size="icon" aria-label="Delete strategy"
                          onClick={() => deleteMutation.mutate(strategy.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                      <CardTitle className="text-base mt-2">{strategy.strategy_name}</CardTitle>
                      <CardDescription>
                        <span className="flex items-center gap-1">
                          <Bug className="h-3 w-3" />
                          {strategy.target_pest} • {strategy.crop_id}
                        </span>
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {strategy.action_threshold && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground">Action Threshold</p>
                          <p className="text-sm">{strategy.action_threshold}</p>
                        </div>
                      )}
                      {strategy.economic_threshold !== null && strategy.economic_threshold > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground">Economic Threshold</p>
                          <p className="text-sm font-medium">${strategy.economic_threshold}/ha</p>
                        </div>
                      )}
                      {strategy.control_methods && strategy.control_methods.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">Control Methods</p>
                          <div className="flex flex-wrap gap-1">
                            {strategy.control_methods.map((method, i) => {
                              const methodInfo = CONTROL_METHOD_TYPES.find(m => m.value === method)
                              return (
                                <Badge key={i} variant="outline" className="text-xs gap-1">
                                  {methodInfo && <methodInfo.icon className={`h-3 w-3 ${methodInfo.color}`} />}
                                  {method}
                                </Badge>
                              )
                            })}
                          </div>
                        </div>
                      )}
                      {strategy.monitoring_protocol && (
                        <div className="pt-2 border-t">
                          <p className="text-xs font-medium text-muted-foreground">Monitoring</p>
                          <p className="text-xs text-muted-foreground line-clamp-2">{strategy.monitoring_protocol}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <Shield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No IPM strategies defined yet</p>
                <Button className="mt-4" onClick={() => setShowCreate(true)}>
                  <Plus className="h-4 w-4 mr-2" />Add First Strategy
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
