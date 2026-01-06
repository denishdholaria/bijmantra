/**
 * System Health Page - RAKSHAKA Self-Healing Dashboard
 * Part of ASHTA-STAMBHA (Eight Pillars) security framework
 */
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import {
  Activity, AlertTriangle, CheckCircle, Clock, Cpu, Database,
  HardDrive, Heart, RefreshCw, Server, Shield, Zap, XCircle
} from 'lucide-react'

interface HealthData {
  status: string
  timestamp: string
  uptime_seconds: number
  uptime_human: string
  system: {
    cpu: { percent: number; count: number; status: string }
    memory: { percent: number; used_gb: number; total_gb: number; status: string }
    disk: { percent: number; used_gb: number; total_gb: number; status: string }
  }
  api: { avg_latency_ms: number; requests_5min: number; errors_5min: number; error_rate_percent: number }
  database: { avg_latency_ms: number; queries_5min: number; status: string }
  summary: { healthy_components: number; degraded_components: number; critical_components: number }
}

interface Anomaly {
  id: string; type: string; severity: string; detected_at: string
  metric_name: string; current_value: number; baseline_value: number; description: string
  resolved: boolean
}

interface HealingAction {
  id: string; strategy: string; status: string; started_at: string
  completed_at: string | null; duration_ms: number | null; result: string
}

export function SystemHealth() {
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const [health, setHealth] = useState<HealthData | null>(null)
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [incidents, setIncidents] = useState<HealingAction[]>([])
  const [strategies, setStrategies] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [healing, setHealing] = useState(false)

  const fetchData = async () => {
    try {
      const [healthRes, anomaliesRes, incidentsRes, strategiesRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/rakshaka/health`),
        fetch(`${API_BASE}/api/v2/rakshaka/anomalies?active_only=false&limit=20`),
        fetch(`${API_BASE}/api/v2/rakshaka/incidents?limit=20`),
        fetch(`${API_BASE}/api/v2/rakshaka/strategies`),
      ])
      if (healthRes.ok) setHealth(await healthRes.json())
      if (anomaliesRes.ok) {
        const data = await anomaliesRes.json()
        setAnomalies(data.anomalies || [])
      }
      if (incidentsRes.ok) {
        const data = await incidentsRes.json()
        setIncidents(data.incidents || [])
      }
      if (strategiesRes.ok) {
        const data = await strategiesRes.json()
        setStrategies(data.strategies || [])
      }
    } catch (error) {
      console.error('Failed to fetch health data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const triggerHealing = async (strategy: string) => {
    setHealing(true)
    try {
      const res = await fetch(`${API_BASE}/api/v2/rakshaka/heal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy })
      })
      if (res.ok) {
        toast.success(`Healing action triggered: ${strategy}`)
        fetchData()
      } else {
        toast.error('Failed to trigger healing')
      }
    } catch {
      toast.error('Failed to connect to server')
    } finally {
      setHealing(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500'
      case 'degraded': return 'bg-yellow-500'
      case 'critical': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy': return <Badge className="bg-green-100 text-green-700"><CheckCircle className="w-3 h-3 mr-1" />Healthy</Badge>
      case 'degraded': return <Badge className="bg-yellow-100 text-yellow-700"><AlertTriangle className="w-3 h-3 mr-1" />Degraded</Badge>
      case 'critical': return <Badge className="bg-red-100 text-red-700"><XCircle className="w-3 h-3 mr-1" />Critical</Badge>
      default: return <Badge variant="secondary">Unknown</Badge>
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="w-6 h-6" /> System Health
          </h1>
          <p className="text-muted-foreground">RAKSHAKA Self-Healing Dashboard</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(health?.status || 'unknown')} animate-pulse`} />
            <span className="text-sm font-medium capitalize">{health?.status || 'Unknown'}</span>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><CheckCircle className="w-5 h-5 text-green-600" /></div>
              <div>
                <p className="text-2xl font-bold">{health?.summary.healthy_components || 0}</p>
                <p className="text-xs text-muted-foreground">Healthy</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><AlertTriangle className="w-5 h-5 text-yellow-600" /></div>
              <div>
                <p className="text-2xl font-bold">{health?.summary.degraded_components || 0}</p>
                <p className="text-xs text-muted-foreground">Degraded</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Clock className="w-5 h-5 text-blue-600" /></div>
              <div>
                <p className="text-2xl font-bold">{health?.uptime_human || '0s'}</p>
                <p className="text-xs text-muted-foreground">Uptime</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><Zap className="w-5 h-5 text-purple-600" /></div>
              <div>
                <p className="text-2xl font-bold">{incidents.length}</p>
                <p className="text-xs text-muted-foreground">Healing Actions</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
          <TabsTrigger value="healing">Healing</TabsTrigger>
          <TabsTrigger value="strategies">Strategies</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4 mt-4">
          <div className="grid md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><Cpu className="w-4 h-4" /> CPU</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{health?.system.cpu.percent.toFixed(1)}%</span>
                    {getStatusBadge(health?.system.cpu.status || 'unknown')}
                  </div>
                  <Progress value={health?.system.cpu.percent || 0} className="h-2" />
                  <p className="text-xs text-muted-foreground">{health?.system.cpu.count} cores</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><Server className="w-4 h-4" /> Memory</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{health?.system.memory.percent.toFixed(1)}%</span>
                    {getStatusBadge(health?.system.memory.status || 'unknown')}
                  </div>
                  <Progress value={health?.system.memory.percent || 0} className="h-2" />
                  <p className="text-xs text-muted-foreground">{health?.system.memory.used_gb.toFixed(1)} / {health?.system.memory.total_gb.toFixed(1)} GB</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><HardDrive className="w-4 h-4" /> Disk</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{health?.system.disk.percent.toFixed(1)}%</span>
                    {getStatusBadge(health?.system.disk.status || 'unknown')}
                  </div>
                  <Progress value={health?.system.disk.percent || 0} className="h-2" />
                  <p className="text-xs text-muted-foreground">{health?.system.disk.used_gb.toFixed(1)} / {health?.system.disk.total_gb.toFixed(1)} GB</p>
                </div>
              </CardContent>
            </Card>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><Activity className="w-4 h-4" /> API Performance</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-2xl font-bold">{health?.api.avg_latency_ms.toFixed(0)}ms</p><p className="text-xs text-muted-foreground">Avg Latency</p></div>
                  <div><p className="text-2xl font-bold">{health?.api.requests_5min || 0}</p><p className="text-xs text-muted-foreground">Requests (5min)</p></div>
                  <div><p className="text-2xl font-bold">{health?.api.errors_5min || 0}</p><p className="text-xs text-muted-foreground">Errors (5min)</p></div>
                  <div><p className="text-2xl font-bold">{health?.api.error_rate_percent.toFixed(2)}%</p><p className="text-xs text-muted-foreground">Error Rate</p></div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><Database className="w-4 h-4" /> Database</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-2xl font-bold">{health?.database.avg_latency_ms.toFixed(0)}ms</p><p className="text-xs text-muted-foreground">Avg Query Time</p></div>
                  <div><p className="text-2xl font-bold">{health?.database.queries_5min || 0}</p><p className="text-xs text-muted-foreground">Queries (5min)</p></div>
                  <div className="col-span-2">{getStatusBadge(health?.database.status || 'unknown')}</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="anomalies" className="mt-4">
          <Card>
            <CardHeader><CardTitle>Detected Anomalies</CardTitle><CardDescription>Statistical deviations from baseline behavior</CardDescription></CardHeader>
            <CardContent>
              {anomalies.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground"><CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" /><p>No anomalies detected</p></div>
              ) : (
                <div className="space-y-3">
                  {anomalies.map((anomaly) => (
                    <div key={anomaly.id} className={`p-3 border rounded-lg ${anomaly.resolved ? 'opacity-50' : ''}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant={anomaly.severity === 'critical' ? 'destructive' : anomaly.severity === 'high' ? 'default' : 'secondary'}>{anomaly.severity}</Badge>
                          <span className="font-medium">{anomaly.type.replace('_', ' ')}</span>
                          {anomaly.resolved && <Badge variant="outline">Resolved</Badge>}
                        </div>
                        <span className="text-xs text-muted-foreground">{new Date(anomaly.detected_at).toLocaleString()}</span>
                      </div>
                      <p className="text-sm mt-1">{anomaly.description}</p>
                      <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                        <span>Current: {anomaly.current_value.toFixed(1)}</span>
                        <span>Baseline: {anomaly.baseline_value.toFixed(1)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="healing" className="mt-4">
          <Card>
            <CardHeader><CardTitle>Healing History</CardTitle><CardDescription>Self-healing actions taken by RAKSHAKA</CardDescription></CardHeader>
            <CardContent>
              {incidents.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground"><Heart className="w-12 h-12 mx-auto mb-2" /><p>No healing actions yet</p></div>
              ) : (
                <div className="space-y-3">
                  {incidents.map((action) => (
                    <div key={action.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant={action.status === 'success' ? 'default' : action.status === 'failed' ? 'destructive' : 'secondary'}>{action.status}</Badge>
                          <span className="font-medium">{action.strategy.replace('_', ' ')}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">{new Date(action.started_at).toLocaleString()}</span>
                      </div>
                      <p className="text-sm mt-1 text-muted-foreground">{action.result}</p>
                      {action.duration_ms && <p className="text-xs text-muted-foreground mt-1">Duration: {action.duration_ms}ms</p>}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="strategies" className="mt-4">
          <Card>
            <CardHeader><CardTitle>Healing Strategies</CardTitle><CardDescription>Available self-healing strategies</CardDescription></CardHeader>
            <CardContent>
              <div className="space-y-3">
                {strategies.map((strategy) => (
                  <div key={strategy.id} className="p-3 border rounded-lg flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{strategy.name}</span>
                        <Badge variant={strategy.enabled ? 'default' : 'secondary'}>{strategy.enabled ? 'Enabled' : 'Disabled'}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{strategy.description}</p>
                    </div>
                    <Button size="sm" variant="outline" disabled={healing || !strategy.enabled} onClick={() => triggerHealing(strategy.id)}>
                      <Zap className="w-3 h-3 mr-1" /> Execute
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
