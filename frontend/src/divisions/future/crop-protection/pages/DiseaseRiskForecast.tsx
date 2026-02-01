/**
 * Disease Risk Forecast Page
 * Weather-based disease prediction models with risk levels and alerts
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
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { AlertCircle, Plus, AlertTriangle, RefreshCw, Trash2, Thermometer, Droplets } from 'lucide-react'

interface DiseaseRiskForecast {
  id: string
  disease_name: string
  crop_id: string
  location_id: string
  forecast_date: string
  risk_level: string
  probability: number | null
  weather_factors: Record<string, unknown> | null
  recommendations: string[] | null
  created_at: string
}

const RISK_LEVELS = [
  { value: 'low', label: 'Low', color: 'bg-green-500', textColor: 'text-green-700 dark:text-green-400' },
  { value: 'moderate', label: 'Moderate', color: 'bg-yellow-500', textColor: 'text-yellow-700 dark:text-yellow-400' },
  { value: 'high', label: 'High', color: 'bg-orange-500', textColor: 'text-orange-700 dark:text-orange-400' },
  { value: 'critical', label: 'Critical', color: 'bg-red-500', textColor: 'text-red-700 dark:text-red-400' },
]

const getRiskInfo = (level: string) => RISK_LEVELS.find(r => r.value === level) || RISK_LEVELS[0]

export function DiseaseRiskForecastPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [newForecast, setNewForecast] = useState({
    disease_name: '',
    crop_id: '',
    location_id: '',
    forecast_date: new Date().toISOString().split('T')[0],
    risk_level: 'low',
    probability: 25,
    weather_factors: {},
    recommendations: [] as string[],
  })
  const queryClient = useQueryClient()

  const { data: forecasts, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'disease-risk-forecast'],
    queryFn: () => apiClient.get('/api/v2/future/disease-risk-forecasts/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newForecast) => apiClient.post('/api/v2/future/disease-risk-forecast/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'disease-risk-forecast'] })
      toast.success('Disease risk forecast created')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create forecast'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v2/future/disease-risk-forecast/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'disease-risk-forecast'] })
      toast.success('Forecast deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  }

  // Count by risk level for summary
  const riskCounts = RISK_LEVELS.map(level => ({
    ...level,
    count: Array.isArray(forecasts) ? forecasts.filter((f: DiseaseRiskForecast) => f.risk_level === level.value).length : 0
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            Disease Risk Forecast
          </h1>
          <p className="text-muted-foreground mt-1">
            Weather-based disease prediction models and alerts
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Forecast</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Disease Risk Forecast</DialogTitle>
                <DialogDescription>Add a new disease risk prediction</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Disease Name</Label>
                  <Input
                    value={newForecast.disease_name}
                    onChange={(e) => setNewForecast((p) => ({ ...p, disease_name: e.target.value }))}
                    placeholder="Late Blight, Powdery Mildew, etc."
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Crop ID</Label>
                    <Input
                      value={newForecast.crop_id}
                      onChange={(e) => setNewForecast((p) => ({ ...p, crop_id: e.target.value }))}
                      placeholder="CROP-001"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Location ID</Label>
                    <Input
                      value={newForecast.location_id}
                      onChange={(e) => setNewForecast((p) => ({ ...p, location_id: e.target.value }))}
                      placeholder="LOC-001"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Forecast Date</Label>
                    <Input
                      type="date"
                      value={newForecast.forecast_date}
                      onChange={(e) => setNewForecast((p) => ({ ...p, forecast_date: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Probability (%)</Label>
                    <Input
                      type="number" min="0" max="100"
                      value={newForecast.probability}
                      onChange={(e) => setNewForecast((p) => ({ ...p, probability: Number(e.target.value) }))}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Risk Level</Label>
                  <Select
                    value={newForecast.risk_level}
                    onValueChange={(v) => setNewForecast((p) => ({ ...p, risk_level: v }))}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {RISK_LEVELS.map((r) => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newForecast)}
                  disabled={!newForecast.disease_name || !newForecast.crop_id || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Forecast'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Risk Summary */}
      {!isLoading && !error && Array.isArray(forecasts) && forecasts.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {riskCounts.map((risk) => (
            <Card key={risk.value} className={`border-l-4 ${risk.color.replace('bg-', 'border-')}`}>
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">{risk.label} Risk</p>
                <p className="text-2xl font-bold">{risk.count}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load disease forecasts.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-48" />)}
        </div>
      )}

      {/* Forecast Cards */}
      {!isLoading && !error && (
        <>
          {Array.isArray(forecasts) && forecasts.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {forecasts.map((forecast: DiseaseRiskForecast) => {
                const risk = getRiskInfo(forecast.risk_level)
                return (
                  <Card key={forecast.id} className={`hover:shadow-md transition-shadow border-l-4 ${risk.color.replace('bg-', 'border-')}`}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <Badge className={`${risk.color} text-white`}>{risk.label}</Badge>
                        <Button variant="ghost" size="icon" aria-label="Delete forecast"
                          onClick={() => deleteMutation.mutate(forecast.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                      <CardTitle className="text-base mt-2">{forecast.disease_name}</CardTitle>
                      <CardDescription>{forecast.crop_id} • {forecast.location_id}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Forecast Date</span>
                        <span className="font-medium">{formatDate(forecast.forecast_date)}</span>
                      </div>
                      {forecast.probability !== null && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Probability</span>
                          <span className={`font-bold ${risk.textColor}`}>{forecast.probability}%</span>
                        </div>
                      )}
                      {forecast.recommendations && forecast.recommendations.length > 0 && (
                        <div className="pt-2 border-t">
                          <p className="text-xs font-medium text-muted-foreground mb-1">Recommendations</p>
                          <ul className="text-xs space-y-1">
                            {forecast.recommendations.slice(0, 2).map((rec, i) => (
                              <li key={i} className="text-muted-foreground">• {rec}</li>
                            ))}
                          </ul>
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
                <AlertTriangle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No disease risk forecasts recorded yet</p>
                <Button className="mt-4" onClick={() => setShowCreate(true)}>
                  <Plus className="h-4 w-4 mr-2" />Add First Forecast
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
