/**
 * Crop Health Dashboard
 * Overview of crop health status across trials and locations
 * Connected to /api/v2/crop-health/* API
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface TrialHealth {
  id: string
  name: string
  location: string
  crop: string
  health_score: number
  disease_risk: 'low' | 'medium' | 'high'
  stress_level: number
  last_scan: string
  issues: string[]
  plots_scanned: number
  total_plots: number
}

interface Alert {
  id: string
  type: 'disease' | 'stress' | 'pest' | 'weather'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  location: string
  timestamp: string
  acknowledged: boolean
  trial_id?: string
}

interface HealthSummary {
  avg_health_score: number
  total_trials: number
  high_risk_trials: number
  active_alerts: number
  by_crop: Record<string, { count: number; avg_health: number }>
  by_location: Record<string, { count: number; avg_health: number }>
}

// API functions
async function fetchTrialHealth(location?: string, crop?: string): Promise<TrialHealth[]> {
  try {
    const response = await apiClient.cropHealthService.getTrials({
      location: location !== 'all' ? location : undefined,
      crop: crop !== 'all' ? crop : undefined,
    });
    return response.data || [];
  } catch {
    return [];
  }
}

async function fetchAlerts(acknowledged?: boolean): Promise<Alert[]> {
  try {
    const response = await apiClient.cropHealthService.getAlerts({ acknowledged });
    return response.data || [];
  } catch {
    return [];
  }
}

async function fetchHealthSummary(): Promise<HealthSummary> {
  try {
    const response = await apiClient.cropHealthService.getSummary();
    return response.data || {
      avg_health_score: 0,
      total_trials: 0,
      high_risk_trials: 0,
      active_alerts: 0,
      by_crop: {},
      by_location: {},
    };
  } catch {
    return {
      avg_health_score: 0,
      total_trials: 0,
      high_risk_trials: 0,
      active_alerts: 0,
      by_crop: {},
      by_location: {},
    };
  }
}

async function fetchLocations(): Promise<string[]> {
  try {
    const response = await apiClient.cropHealthService.getLocations();
    return response.data || [];
  } catch {
    return [];
  }
}

async function acknowledgeAlert(alertId: string): Promise<void> {
  await apiClient.cropHealthService.acknowledgeAlert(alertId);
}

export function CropHealthDashboard() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedLocation, setSelectedLocation] = useState('all')
  const [timeRange, setTimeRange] = useState('7d')
  const queryClient = useQueryClient()

  // Fetch data
  const { data: trials = [], isLoading: trialsLoading } = useQuery({
    queryKey: ['crop-health-trials', selectedLocation],
    queryFn: () => fetchTrialHealth(selectedLocation),
    staleTime: 1000 * 60 * 2, // 2 minutes
  })

  const { data: alerts = [], isLoading: alertsLoading } = useQuery({
    queryKey: ['crop-health-alerts'],
    queryFn: () => fetchAlerts(),
    staleTime: 1000 * 60, // 1 minute
  })

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['crop-health-summary'],
    queryFn: fetchHealthSummary,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  const { data: locations = [] } = useQuery({
    queryKey: ['crop-health-locations'],
    queryFn: fetchLocations,
    staleTime: 1000 * 60 * 30, // 30 minutes
  })

  // Acknowledge alert mutation
  const acknowledgeMutation = useMutation({
    mutationFn: acknowledgeAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crop-health-alerts'] })
      queryClient.invalidateQueries({ queryKey: ['crop-health-summary'] })
    },
  })

  const avgHealthScore = summary?.avg_health_score || 0
  const highRiskTrials = summary?.high_risk_trials || 0
  const activeAlerts = alerts.filter(a => !a.acknowledged).length

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getHealthBg = (score: number) => {
    if (score >= 80) return 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800'
    if (score >= 60) return 'bg-yellow-50 border-yellow-200 dark:bg-yellow-950 dark:border-yellow-800'
    return 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800'
  }

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'high': return <Badge className="bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300">High Risk</Badge>
      case 'medium': return <Badge className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300">Medium Risk</Badge>
      case 'low': return <Badge className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">Low Risk</Badge>
      default: return <Badge variant="secondary">{risk}</Badge>
    }
  }

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'disease': return '🦠'
      case 'stress': return '⚠️'
      case 'pest': return '🐛'
      case 'weather': return '🌧️'
      default: return '📢'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50 dark:bg-red-950'
      case 'high': return 'border-orange-500 bg-orange-50 dark:bg-orange-950'
      case 'medium': return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950'
      case 'low': return 'border-blue-500 bg-blue-50 dark:bg-blue-950'
      default: return 'border-gray-300'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffHours < 1) return 'Just now'
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">🌾 Crop Health Dashboard</h1>
          <p className="text-muted-foreground mt-1">Monitor crop health across all trials</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedLocation} onValueChange={setSelectedLocation}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Location" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Locations</SelectItem>
              {locations.map(loc => (
                <SelectItem key={loc} value={loc}>{loc}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-28">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">24 Hours</SelectItem>
              <SelectItem value="7d">7 Days</SelectItem>
              <SelectItem value="30d">30 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className={getHealthBg(avgHealthScore)}>
          <CardContent className="pt-4 text-center">
            {summaryLoading ? (
              <Loader2 className="h-8 w-8 animate-spin mx-auto" />
            ) : (
              <p className={`text-4xl font-bold ${getHealthColor(avgHealthScore)}`}>{avgHealthScore}%</p>
            )}
            <p className="text-sm text-muted-foreground">Avg Health Score</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            {summaryLoading ? (
              <Loader2 className="h-8 w-8 animate-spin mx-auto" />
            ) : (
              <p className="text-4xl font-bold text-primary">{summary?.total_trials || trials.length}</p>
            )}
            <p className="text-sm text-muted-foreground">Active Trials</p>
          </CardContent>
        </Card>
        <Card className={highRiskTrials > 0 ? 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800' : ''}>
          <CardContent className="pt-4 text-center">
            {summaryLoading ? (
              <Loader2 className="h-8 w-8 animate-spin mx-auto" />
            ) : (
              <p className={`text-4xl font-bold ${highRiskTrials > 0 ? 'text-red-600' : 'text-green-600'}`}>{highRiskTrials}</p>
            )}
            <p className="text-sm text-muted-foreground">High Risk Trials</p>
          </CardContent>
        </Card>
        <Card className={activeAlerts > 0 ? 'bg-orange-50 border-orange-200 dark:bg-orange-950 dark:border-orange-800' : ''}>
          <CardContent className="pt-4 text-center">
            {alertsLoading ? (
              <Loader2 className="h-8 w-8 animate-spin mx-auto" />
            ) : (
              <p className={`text-4xl font-bold ${activeAlerts > 0 ? 'text-orange-600' : 'text-green-600'}`}>{activeAlerts}</p>
            )}
            <p className="text-sm text-muted-foreground">Active Alerts</p>
          </CardContent>
        </Card>
      </div>

      {/* Active Alerts Banner */}
      {activeAlerts > 0 && (
        <Card className="border-orange-300 bg-orange-50 dark:bg-orange-950 dark:border-orange-700">
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">⚠️</span>
                <span className="font-medium text-orange-800 dark:text-orange-300">{activeAlerts} active alert(s) require attention</span>
              </div>
              <Button size="sm" variant="outline" onClick={() => setActiveTab('alerts')}>View Alerts</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">📊 Overview</TabsTrigger>
          <TabsTrigger value="trials">🧪 Trials</TabsTrigger>
          <TabsTrigger value="alerts">🔔 Alerts ({activeAlerts})</TabsTrigger>
          <TabsTrigger value="trends">📈 Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-4">
          {/* Trial Health Cards */}
          {trialsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {trials.map((trial) => (
                <Card key={trial.id} className={`${getHealthBg(trial.health_score)} cursor-pointer hover:shadow-lg transition-shadow`}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{trial.name}</CardTitle>
                        <CardDescription>{trial.location} • {trial.crop}</CardDescription>
                      </div>
                      {getRiskBadge(trial.disease_risk)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Health Score</span>
                        <span className={`text-2xl font-bold ${getHealthColor(trial.health_score)}`}>{trial.health_score}%</span>
                      </div>
                      <Progress value={trial.health_score} className="h-2" />
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Stress Level</span>
                        <span className={trial.stress_level > 40 ? 'text-red-600' : 'text-green-600'}>{trial.stress_level}%</span>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Plots Scanned</span>
                        <span>{trial.plots_scanned}/{trial.total_plots}</span>
                      </div>

                      {trial.issues.length > 0 && (
                        <div className="pt-2 border-t">
                          <p className="text-xs text-muted-foreground mb-1">Issues:</p>
                          <div className="flex flex-wrap gap-1">
                            {trial.issues.map((issue, i) => (
                              <Badge key={i} variant="outline" className="text-xs bg-white dark:bg-gray-800">{issue}</Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      <p className="text-xs text-muted-foreground">Last scan: {trial.last_scan}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {!trialsLoading && trials.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">No trials found for the selected filters</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="trials" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Trial Health Summary</CardTitle>
              <CardDescription>Detailed health metrics for all trials</CardDescription>
            </CardHeader>
            <CardContent>
              {trialsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Trial</th>
                        <th className="text-left p-3">Location</th>
                        <th className="text-left p-3">Crop</th>
                        <th className="text-center p-3">Health</th>
                        <th className="text-center p-3">Risk</th>
                        <th className="text-center p-3">Stress</th>
                        <th className="text-center p-3">Coverage</th>
                        <th className="text-left p-3">Last Scan</th>
                      </tr>
                    </thead>
                    <tbody>
                      {trials.map((trial) => (
                        <tr key={trial.id} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{trial.name}</td>
                          <td className="p-3">{trial.location}</td>
                          <td className="p-3">{trial.crop}</td>
                          <td className="p-3 text-center">
                            <span className={`font-bold ${getHealthColor(trial.health_score)}`}>{trial.health_score}%</span>
                          </td>
                          <td className="p-3 text-center">{getRiskBadge(trial.disease_risk)}</td>
                          <td className="p-3 text-center">{trial.stress_level}%</td>
                          <td className="p-3 text-center">{Math.round((trial.plots_scanned / trial.total_plots) * 100)}%</td>
                          <td className="p-3 text-muted-foreground">{trial.last_scan}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Health Alerts</CardTitle>
              <CardDescription>Issues requiring attention</CardDescription>
            </CardHeader>
            <CardContent>
              {alertsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : alerts.length === 0 ? (
                <div className="py-8 text-center text-muted-foreground">
                  <p>No alerts at this time</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert) => (
                    <div key={alert.id} className={`p-4 border-l-4 rounded-r-lg ${getSeverityColor(alert.severity)} ${alert.acknowledged ? 'opacity-60' : ''}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <span className="text-2xl">{getAlertIcon(alert.type)}</span>
                          <div>
                            <p className="font-medium">{alert.message}</p>
                            <p className="text-sm text-muted-foreground">{alert.location} • {formatTimestamp(alert.timestamp)}</p>
                          </div>
                        </div>
                        {!alert.acknowledged && (
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => acknowledgeMutation.mutate(alert.id)}
                            disabled={acknowledgeMutation.isPending}
                          >
                            {acknowledgeMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Acknowledge'}
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Health Trends</CardTitle>
              <CardDescription>Health score trends over time</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">📈</span>
                  <p className="mt-2 text-muted-foreground">Health Trend Chart</p>
                  <p className="text-xs text-muted-foreground">{timeRange === '7d' ? '7-day' : timeRange === '24h' ? '24-hour' : '30-day'} moving average</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
