/**
 * Crop Health Dashboard
 * Overview of crop health status across trials and locations
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'

interface TrialHealth {
  id: string
  name: string
  location: string
  crop: string
  healthScore: number
  diseaseRisk: 'low' | 'medium' | 'high'
  stressLevel: number
  lastScan: string
  issues: string[]
  plotsScanned: number
  totalPlots: number
}

interface Alert {
  id: string
  type: 'disease' | 'stress' | 'pest' | 'weather'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  location: string
  timestamp: string
  acknowledged: boolean
}

const trialHealthData: TrialHealth[] = [
  { id: 't1', name: 'Yield Trial 2024-A', location: 'Punjab Station', crop: 'Rice', healthScore: 92, diseaseRisk: 'low', stressLevel: 15, lastScan: '2 hours ago', issues: [], plotsScanned: 48, totalPlots: 50 },
  { id: 't2', name: 'Disease Screening', location: 'Haryana Station', crop: 'Wheat', healthScore: 68, diseaseRisk: 'high', stressLevel: 45, lastScan: '1 day ago', issues: ['Rust detected', 'Nutrient deficiency'], plotsScanned: 30, totalPlots: 40 },
  { id: 't3', name: 'Drought Tolerance', location: 'Rajasthan Station', crop: 'Rice', healthScore: 75, diseaseRisk: 'medium', stressLevel: 60, lastScan: '6 hours ago', issues: ['Drought stress'], plotsScanned: 25, totalPlots: 30 },
  { id: 't4', name: 'Quality Trial', location: 'UP Station', crop: 'Wheat', healthScore: 88, diseaseRisk: 'low', stressLevel: 20, lastScan: '3 hours ago', issues: [], plotsScanned: 35, totalPlots: 35 },
  { id: 't5', name: 'Hybrid Evaluation', location: 'MP Station', crop: 'Maize', healthScore: 82, diseaseRisk: 'medium', stressLevel: 30, lastScan: '12 hours ago', issues: ['Minor leaf blight'], plotsScanned: 40, totalPlots: 45 },
]

const alerts: Alert[] = [
  { id: 'a1', type: 'disease', severity: 'high', message: 'Wheat rust outbreak detected in Haryana Station', location: 'Haryana Station', timestamp: '2 hours ago', acknowledged: false },
  { id: 'a2', type: 'stress', severity: 'medium', message: 'Drought stress increasing in Rajasthan trials', location: 'Rajasthan Station', timestamp: '6 hours ago', acknowledged: false },
  { id: 'a3', type: 'weather', severity: 'low', message: 'Heavy rain forecast for Punjab - monitor for waterlogging', location: 'Punjab Station', timestamp: '1 day ago', acknowledged: true },
  { id: 'a4', type: 'pest', severity: 'medium', message: 'Stem borer activity reported in MP maize trials', location: 'MP Station', timestamp: '1 day ago', acknowledged: true },
]

export function CropHealthDashboard() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedLocation, setSelectedLocation] = useState('all')
  const [timeRange, setTimeRange] = useState('7d')

  const avgHealthScore = Math.round(trialHealthData.reduce((sum, t) => sum + t.healthScore, 0) / trialHealthData.length)
  const highRiskTrials = trialHealthData.filter(t => t.diseaseRisk === 'high').length
  const activeAlerts = alerts.filter(a => !a.acknowledged).length

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getHealthBg = (score: number) => {
    if (score >= 80) return 'bg-green-50 border-green-200'
    if (score >= 60) return 'bg-yellow-50 border-yellow-200'
    return 'bg-red-50 border-red-200'
  }

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'high': return <Badge className="bg-red-100 text-red-700">High Risk</Badge>
      case 'medium': return <Badge className="bg-yellow-100 text-yellow-700">Medium Risk</Badge>
      case 'low': return <Badge className="bg-green-100 text-green-700">Low Risk</Badge>
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
      case 'critical': return 'border-red-500 bg-red-50'
      case 'high': return 'border-orange-500 bg-orange-50'
      case 'medium': return 'border-yellow-500 bg-yellow-50'
      case 'low': return 'border-blue-500 bg-blue-50'
      default: return 'border-gray-300'
    }
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
              <SelectItem value="punjab">Punjab</SelectItem>
              <SelectItem value="haryana">Haryana</SelectItem>
              <SelectItem value="rajasthan">Rajasthan</SelectItem>
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
            <p className={`text-4xl font-bold ${getHealthColor(avgHealthScore)}`}>{avgHealthScore}%</p>
            <p className="text-sm text-muted-foreground">Avg Health Score</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-4xl font-bold text-primary">{trialHealthData.length}</p>
            <p className="text-sm text-muted-foreground">Active Trials</p>
          </CardContent>
        </Card>
        <Card className={highRiskTrials > 0 ? 'bg-red-50 border-red-200' : ''}>
          <CardContent className="pt-4 text-center">
            <p className={`text-4xl font-bold ${highRiskTrials > 0 ? 'text-red-600' : 'text-green-600'}`}>{highRiskTrials}</p>
            <p className="text-sm text-muted-foreground">High Risk Trials</p>
          </CardContent>
        </Card>
        <Card className={activeAlerts > 0 ? 'bg-orange-50 border-orange-200' : ''}>
          <CardContent className="pt-4 text-center">
            <p className={`text-4xl font-bold ${activeAlerts > 0 ? 'text-orange-600' : 'text-green-600'}`}>{activeAlerts}</p>
            <p className="text-sm text-muted-foreground">Active Alerts</p>
          </CardContent>
        </Card>
      </div>

      {/* Active Alerts Banner */}
      {activeAlerts > 0 && (
        <Card className="border-orange-300 bg-orange-50">
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">⚠️</span>
                <span className="font-medium text-orange-800">{activeAlerts} active alert(s) require attention</span>
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {trialHealthData.map((trial) => (
              <Card key={trial.id} className={`${getHealthBg(trial.healthScore)} cursor-pointer hover:shadow-lg transition-shadow`}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{trial.name}</CardTitle>
                      <CardDescription>{trial.location} • {trial.crop}</CardDescription>
                    </div>
                    {getRiskBadge(trial.diseaseRisk)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Health Score</span>
                      <span className={`text-2xl font-bold ${getHealthColor(trial.healthScore)}`}>{trial.healthScore}%</span>
                    </div>
                    <Progress value={trial.healthScore} className="h-2" />
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Stress Level</span>
                      <span className={trial.stressLevel > 40 ? 'text-red-600' : 'text-green-600'}>{trial.stressLevel}%</span>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Plots Scanned</span>
                      <span>{trial.plotsScanned}/{trial.totalPlots}</span>
                    </div>

                    {trial.issues.length > 0 && (
                      <div className="pt-2 border-t">
                        <p className="text-xs text-muted-foreground mb-1">Issues:</p>
                        <div className="flex flex-wrap gap-1">
                          {trial.issues.map((issue, i) => (
                            <Badge key={i} variant="outline" className="text-xs bg-white">{issue}</Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <p className="text-xs text-muted-foreground">Last scan: {trial.lastScan}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="trials" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Trial Health Summary</CardTitle>
              <CardDescription>Detailed health metrics for all trials</CardDescription>
            </CardHeader>
            <CardContent>
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
                    {trialHealthData.map((trial) => (
                      <tr key={trial.id} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{trial.name}</td>
                        <td className="p-3">{trial.location}</td>
                        <td className="p-3">{trial.crop}</td>
                        <td className="p-3 text-center">
                          <span className={`font-bold ${getHealthColor(trial.healthScore)}`}>{trial.healthScore}%</span>
                        </td>
                        <td className="p-3 text-center">{getRiskBadge(trial.diseaseRisk)}</td>
                        <td className="p-3 text-center">{trial.stressLevel}%</td>
                        <td className="p-3 text-center">{Math.round((trial.plotsScanned / trial.totalPlots) * 100)}%</td>
                        <td className="p-3 text-muted-foreground">{trial.lastScan}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div key={alert.id} className={`p-4 border-l-4 rounded-r-lg ${getSeverityColor(alert.severity)} ${alert.acknowledged ? 'opacity-60' : ''}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{getAlertIcon(alert.type)}</span>
                        <div>
                          <p className="font-medium">{alert.message}</p>
                          <p className="text-sm text-muted-foreground">{alert.location} • {alert.timestamp}</p>
                        </div>
                      </div>
                      {!alert.acknowledged && (
                        <Button size="sm" variant="outline">Acknowledge</Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
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
                  <p className="text-xs text-muted-foreground">7-day moving average</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
