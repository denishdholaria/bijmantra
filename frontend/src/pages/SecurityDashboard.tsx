/**
 * Security Dashboard - ASHTA-STAMBHA Complete Security Framework
 * 
 * Unified dashboard for:
 * - CHAITANYA (Central Orchestrator) - System posture & coordination
 * - PRAHARI (Defense) - Security events, threats, responses
 * - RAKSHAKA (Self-Healing) - Health monitoring, anomalies, healing
 * 
 * Designed for mission-critical environments including space research.
 */
import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '@/components/ui/select'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger
} from '@/components/ui/dialog'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogTitle, AlertDialogTrigger
} from '@/components/ui/alert-dialog'
import { toast } from 'sonner'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Activity, AlertTriangle, AlertCircle, Ban, CheckCircle, Clock, Cpu, Database,
  Eye, HardDrive, Heart, Lock, RefreshCw, Server, Shield, ShieldAlert,
  ShieldCheck, ShieldOff, Target, Unlock, XCircle, Zap, Brain,
  Radio, Fingerprint, Globe, User, AlertOctagon, TrendingUp, TrendingDown
} from 'lucide-react'


// Types
interface SystemPosture {
  level: string
  health_score: number
  security_score: number
  overall_score: number
  active_threats: number
  active_anomalies: number
  blocked_ips: number
  last_incident: string | null
  recommendations: string[]
}

interface SecurityEvent {
  id: string
  timestamp: string
  layer: string
  event_type: string
  source_ip: string | null
  user_id: string | null
  endpoint: string | null
  severity: string
  details: Record<string, unknown>
}

interface ThreatAssessment {
  id: string
  event_id: string
  timestamp: string
  category: string
  confidence: string
  confidence_score: number
  severity: string
  indicators: string[]
  recommended_actions: string[]
}

interface BlockedItem {
  ip?: string
  user_id?: string
  expires_at: string
  remaining_seconds: number
}

interface ResponseRecord {
  id: string
  assessment_id: string
  action: string
  status: string
  started_at: string
  target: string | null
  result: string
}

interface HealthData {
  status: string
  uptime_human: string
  system: {
    cpu: { percent: number; status: string }
    memory: { percent: number; status: string }
    disk: { percent: number; status: string }
  }
  api: { avg_latency_ms: number; error_rate_percent: number }
}

interface ChaitanyaConfig {
  auto_response_enabled: boolean
  current_posture: string
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Posture level colors and icons
const POSTURE_CONFIG: Record<string, { color: string; bg: string; icon: typeof Shield }> = {
  normal: { color: 'text-green-600', bg: 'bg-green-100', icon: ShieldCheck },
  elevated: { color: 'text-blue-600', bg: 'bg-blue-100', icon: Shield },
  high: { color: 'text-yellow-600', bg: 'bg-yellow-100', icon: ShieldAlert },
  severe: { color: 'text-orange-600', bg: 'bg-orange-100', icon: AlertOctagon },
  lockdown: { color: 'text-red-600', bg: 'bg-red-100', icon: Lock },
}

const SEVERITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

export function SecurityDashboard() {
  // State
  const [posture, setPosture] = useState<SystemPosture | null>(null)
  const [config, setConfig] = useState<ChaitanyaConfig | null>(null)
  const [events, setEvents] = useState<SecurityEvent[]>([])
  const [threats, setThreats] = useState<ThreatAssessment[]>([])
  const [blockedIps, setBlockedIps] = useState<BlockedItem[]>([])
  const [blockedUsers, setBlockedUsers] = useState<BlockedItem[]>([])
  const [responses, setResponses] = useState<ResponseRecord[]>([])
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  
  // Block dialog state
  const [blockDialogOpen, setBlockDialogOpen] = useState(false)
  const [blockType, setBlockType] = useState<'ip' | 'user'>('ip')
  const [blockTargetValue, setBlockTargetValue] = useState('')
  const [blockDuration, setBlockDuration] = useState(3600)


  // Fetch all data
  const fetchData = useCallback(async () => {
    setError(null)
    try {
      const [postureRes, configRes, eventsRes, threatsRes, blockedRes, responsesRes, healthRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/chaitanya/posture`),
        fetch(`${API_BASE}/api/v2/chaitanya/config`),
        fetch(`${API_BASE}/api/v2/prahari/events?limit=50`),
        fetch(`${API_BASE}/api/v2/prahari/threats?limit=50`),
        fetch(`${API_BASE}/api/v2/prahari/blocked`),
        fetch(`${API_BASE}/api/v2/prahari/responses?limit=50`),
        fetch(`${API_BASE}/api/v2/rakshaka/health`),
      ])
      
      if (postureRes.ok) setPosture(await postureRes.json())
      if (configRes.ok) setConfig(await configRes.json())
      if (eventsRes.ok) {
        const data = await eventsRes.json()
        setEvents(data.events || [])
      }
      if (threatsRes.ok) {
        const data = await threatsRes.json()
        setThreats(data.assessments || [])
      }
      if (blockedRes.ok) {
        const data = await blockedRes.json()
        setBlockedIps(data.blocked_ips || [])
        setBlockedUsers(data.blocked_users || [])
      }
      if (responsesRes.ok) {
        const data = await responsesRes.json()
        setResponses(data.responses || [])
      }
      if (healthRes.ok) setHealth(await healthRes.json())
    } catch (error) {
      console.error('Failed to fetch security data:', error)
      setError('Failed to load security data. Please check your connection.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    if (autoRefresh) {
      const interval = setInterval(fetchData, 5000)
      return () => clearInterval(interval)
    }
  }, [fetchData, autoRefresh])

  // Actions
  const setPostureLevel = async (level: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/chaitanya/posture`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level, reason: 'Manual override from Security Dashboard' })
      })
      if (res.ok) {
        toast.success(`Posture set to ${level.toUpperCase()}`)
        fetchData()
      } else {
        toast.error('Failed to set posture')
      }
    } catch {
      toast.error('Connection error')
    }
  }

  const toggleAutoResponse = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/chaitanya/auto-response`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !config?.auto_response_enabled })
      })
      if (res.ok) {
        toast.success(`Auto-response ${!config?.auto_response_enabled ? 'enabled' : 'disabled'}`)
        fetchData()
      }
    } catch {
      toast.error('Connection error')
    }
  }

  const handleBlockTarget = async () => {
    if (!blockTargetValue.trim()) return
    try {
      const res = await fetch(`${API_BASE}/api/v2/prahari/block`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_type: blockType,
          target: blockTargetValue.trim(),
          duration_seconds: blockDuration
        })
      })
      if (res.ok) {
        toast.success(`${blockType === 'ip' ? 'IP' : 'User'} blocked successfully`)
        setBlockDialogOpen(false)
        setBlockTargetValue('')
        fetchData()
      } else {
        toast.error('Failed to block target')
      }
    } catch {
      toast.error('Connection error')
    }
  }

  const unblockIp = async (ip: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/prahari/block/ip/${encodeURIComponent(ip)}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        toast.success(`IP ${ip} unblocked`)
        fetchData()
      }
    } catch {
      toast.error('Connection error')
    }
  }

  const unblockUser = async (userId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/prahari/block/user/${encodeURIComponent(userId)}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        toast.success(`User ${userId} unblocked`)
        fetchData()
      }
    } catch {
      toast.error('Connection error')
    }
  }


  // Render helpers
  const PostureIcon = POSTURE_CONFIG[posture?.level || 'normal']?.icon || Shield
  const postureConfig = POSTURE_CONFIG[posture?.level || 'normal'] || POSTURE_CONFIG.normal

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="w-6 h-6" /> Security Command Center
          </h1>
          <p className="text-muted-foreground">ASHTA-STAMBHA Framework • CHAITANYA Orchestrator</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
            <span className="text-sm">Auto-refresh</span>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      {/* Posture Banner */}
      <Card className={`border-2 ${posture?.level === 'lockdown' ? 'border-red-500 bg-red-50' : posture?.level === 'severe' ? 'border-orange-500 bg-orange-50' : ''}`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-4 rounded-full ${postureConfig.bg}`}>
                <PostureIcon className={`w-8 h-8 ${postureConfig.color}`} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-2xl font-bold capitalize">{posture?.level || 'Unknown'} Posture</h2>
                  {config?.auto_response_enabled && (
                    <Badge variant="outline" className="bg-green-50">
                      <Zap className="w-3 h-3 mr-1" /> Auto-Response Active
                    </Badge>
                  )}
                </div>
                <p className="text-muted-foreground">
                  Overall Score: {posture?.overall_score?.toFixed(0) || 0}/100 • 
                  Health: {posture?.health_score?.toFixed(0) || 0} • 
                  Security: {posture?.security_score?.toFixed(0) || 0}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Select value={posture?.level || 'normal'} onValueChange={setPostureLevel}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="normal">Normal</SelectItem>
                  <SelectItem value="elevated">Elevated</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="severe">Severe</SelectItem>
                  <SelectItem value="lockdown">Lockdown</SelectItem>
                </SelectContent>
              </Select>
              <Button variant={config?.auto_response_enabled ? 'default' : 'outline'} onClick={toggleAutoResponse}>
                {config?.auto_response_enabled ? <ShieldCheck className="w-4 h-4 mr-2" /> : <ShieldOff className="w-4 h-4 mr-2" />}
                Auto-Response
              </Button>
            </div>
          </div>
          
          {/* Recommendations */}
          {posture?.recommendations && posture.recommendations.length > 0 && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm font-medium text-yellow-800 mb-1">Recommendations:</p>
              <ul className="text-sm text-yellow-700 space-y-1">
                {posture.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-6 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <Eye className="w-6 h-6 mx-auto mb-2 text-blue-500" />
            <p className="text-2xl font-bold">{events.length}</p>
            <p className="text-xs text-muted-foreground">Security Events</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Target className="w-6 h-6 mx-auto mb-2 text-orange-500" />
            <p className="text-2xl font-bold">{posture?.active_threats || 0}</p>
            <p className="text-xs text-muted-foreground">Active Threats</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2 text-yellow-500" />
            <p className="text-2xl font-bold">{posture?.active_anomalies || 0}</p>
            <p className="text-xs text-muted-foreground">Anomalies</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Ban className="w-6 h-6 mx-auto mb-2 text-red-500" />
            <p className="text-2xl font-bold">{blockedIps.length + blockedUsers.length}</p>
            <p className="text-xs text-muted-foreground">Blocked</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Zap className="w-6 h-6 mx-auto mb-2 text-purple-500" />
            <p className="text-2xl font-bold">{responses.length}</p>
            <p className="text-xs text-muted-foreground">Responses</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Activity className="w-6 h-6 mx-auto mb-2 text-green-500" />
            <p className="text-2xl font-bold">{health?.uptime_human || '0s'}</p>
            <p className="text-xs text-muted-foreground">Uptime</p>
          </CardContent>
        </Card>
      </div>


      {/* Main Tabs */}
      <Tabs defaultValue="events">
        <TabsList className="grid grid-cols-5 w-full max-w-2xl">
          <TabsTrigger value="events"><Eye className="w-4 h-4 mr-2" />Events</TabsTrigger>
          <TabsTrigger value="threats"><Target className="w-4 h-4 mr-2" />Threats</TabsTrigger>
          <TabsTrigger value="blocked"><Ban className="w-4 h-4 mr-2" />Blocked</TabsTrigger>
          <TabsTrigger value="responses"><Zap className="w-4 h-4 mr-2" />Responses</TabsTrigger>
          <TabsTrigger value="health"><Heart className="w-4 h-4 mr-2" />Health</TabsTrigger>
        </TabsList>

        {/* Security Events Tab */}
        <TabsContent value="events" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5" /> Security Events
              </CardTitle>
              <CardDescription>DRISHTI (दृष्टि) - Multi-layer observation</CardDescription>
            </CardHeader>
            <CardContent>
              {events.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
                  <p>No security events recorded</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {events.map((event) => (
                    <div key={event.id} className="p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge className={SEVERITY_COLORS[event.severity] || 'bg-gray-100'}>
                            {event.severity}
                          </Badge>
                          <Badge variant="outline">{event.layer}</Badge>
                          <span className="font-medium">{event.event_type.replace(/_/g, ' ')}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(event.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
                        {event.source_ip && (
                          <span className="flex items-center gap-1">
                            <Globe className="w-3 h-3" /> {event.source_ip}
                          </span>
                        )}
                        {event.user_id && (
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" /> {event.user_id}
                          </span>
                        )}
                        {event.endpoint && (
                          <span className="flex items-center gap-1">
                            <Radio className="w-3 h-3" /> {event.endpoint}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Threats Tab */}
        <TabsContent value="threats" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" /> Threat Assessments
              </CardTitle>
              <CardDescription>VIVEK (विवेक) - Threat analysis & classification</CardDescription>
            </CardHeader>
            <CardContent>
              {threats.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <ShieldCheck className="w-12 h-12 mx-auto mb-2 text-green-500" />
                  <p>No threats detected</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {threats.map((threat) => (
                    <div key={threat.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge className={SEVERITY_COLORS[threat.severity] || 'bg-gray-100'}>
                            {threat.severity}
                          </Badge>
                          <Badge variant="outline">{threat.category.replace(/_/g, ' ')}</Badge>
                          <span className="font-medium">
                            Confidence: {threat.confidence} ({threat.confidence_score.toFixed(0)}%)
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(threat.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="mt-2">
                        <p className="text-sm font-medium">Indicators:</p>
                        <ul className="text-sm text-muted-foreground list-disc list-inside">
                          {threat.indicators.slice(0, 3).map((ind, i) => (
                            <li key={i}>{ind}</li>
                          ))}
                        </ul>
                      </div>
                      {threat.recommended_actions.length > 0 && (
                        <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
                          <p className="font-medium text-blue-800">Recommended:</p>
                          <ul className="text-blue-700 list-disc list-inside">
                            {threat.recommended_actions.slice(0, 2).map((action, i) => (
                              <li key={i}>{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>


        {/* Blocked Tab */}
        <TabsContent value="blocked" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Ban className="w-5 h-5" /> Blocked IPs & Users
                </CardTitle>
                <CardDescription>SHAKTI (शक्ति) - Active countermeasures</CardDescription>
              </div>
              <Dialog open={blockDialogOpen} onOpenChange={setBlockDialogOpen}>
                <DialogTrigger asChild>
                  <Button><Ban className="w-4 h-4 mr-2" /> Block New</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Block IP or User</DialogTitle>
                    <DialogDescription>
                      Manually block an IP address or user account
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label>Type</Label>
                      <Select value={blockType} onValueChange={(v) => setBlockType(v as 'ip' | 'user')}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ip">IP Address</SelectItem>
                          <SelectItem value="user">User ID</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>{blockType === 'ip' ? 'IP Address' : 'User ID'}</Label>
                      <Input
                        placeholder={blockType === 'ip' ? '192.168.1.1' : 'user@example.com'}
                        value={blockTargetValue}
                        onChange={(e) => setBlockTargetValue(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Duration</Label>
                      <Select value={blockDuration.toString()} onValueChange={(v) => setBlockDuration(parseInt(v))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="300">5 minutes</SelectItem>
                          <SelectItem value="900">15 minutes</SelectItem>
                          <SelectItem value="3600">1 hour</SelectItem>
                          <SelectItem value="86400">24 hours</SelectItem>
                          <SelectItem value="604800">7 days</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setBlockDialogOpen(false)}>Cancel</Button>
                    <Button variant="destructive" onClick={handleBlockTarget}>Block</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                {/* Blocked IPs */}
                <div>
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <Globe className="w-4 h-4" /> Blocked IPs ({blockedIps.length})
                  </h3>
                  {blockedIps.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No blocked IPs</p>
                  ) : (
                    <div className="space-y-2">
                      {blockedIps.map((item) => (
                        <div key={item.ip} className="flex items-center justify-between p-2 border rounded">
                          <div>
                            <p className="font-mono text-sm">{item.ip}</p>
                            <p className="text-xs text-muted-foreground">
                              Expires in {Math.floor(item.remaining_seconds / 60)}m
                            </p>
                          </div>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button size="sm" variant="ghost"><Unlock className="w-4 h-4" /></Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Unblock IP?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to unblock {item.ip}?
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => unblockIp(item.ip!)}>Unblock</AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Blocked Users */}
                <div>
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <User className="w-4 h-4" /> Blocked Users ({blockedUsers.length})
                  </h3>
                  {blockedUsers.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No blocked users</p>
                  ) : (
                    <div className="space-y-2">
                      {blockedUsers.map((item) => (
                        <div key={item.user_id} className="flex items-center justify-between p-2 border rounded">
                          <div>
                            <p className="font-medium text-sm">{item.user_id}</p>
                            <p className="text-xs text-muted-foreground">
                              Expires in {Math.floor(item.remaining_seconds / 60)}m
                            </p>
                          </div>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button size="sm" variant="ghost"><Unlock className="w-4 h-4" /></Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Unblock User?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to unblock {item.user_id}?
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => unblockUser(item.user_id!)}>Unblock</AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>


        {/* Responses Tab */}
        <TabsContent value="responses" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" /> Response Actions
              </CardTitle>
              <CardDescription>Automated and manual security responses</CardDescription>
            </CardHeader>
            <CardContent>
              {responses.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Zap className="w-12 h-12 mx-auto mb-2" />
                  <p>No response actions recorded</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {responses.map((response) => (
                    <div key={response.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant={response.status === 'success' ? 'default' : response.status === 'failed' ? 'destructive' : 'secondary'}>
                            {response.status}
                          </Badge>
                          <span className="font-medium">{response.action.replace(/_/g, ' ')}</span>
                          {response.target && (
                            <span className="text-sm text-muted-foreground">→ {response.target}</span>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(response.started_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{response.result}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Health Tab */}
        <TabsContent value="health" className="mt-4">
          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Heart className="w-5 h-5" /> System Health
                </CardTitle>
                <CardDescription>RAKSHAKA (रक्षक) - Self-healing system</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-2"><Cpu className="w-4 h-4" /> CPU</span>
                      <span>{health?.system.cpu.percent.toFixed(1)}%</span>
                    </div>
                    <Progress value={health?.system.cpu.percent || 0} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-2"><Server className="w-4 h-4" /> Memory</span>
                      <span>{health?.system.memory.percent.toFixed(1)}%</span>
                    </div>
                    <Progress value={health?.system.memory.percent || 0} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="flex items-center gap-2"><HardDrive className="w-4 h-4" /> Disk</span>
                      <span>{health?.system.disk.percent.toFixed(1)}%</span>
                    </div>
                    <Progress value={health?.system.disk.percent || 0} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5" /> API Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-muted rounded-lg">
                    <p className="text-3xl font-bold">{health?.api.avg_latency_ms.toFixed(0) || 0}ms</p>
                    <p className="text-sm text-muted-foreground">Avg Latency</p>
                  </div>
                  <div className="text-center p-4 bg-muted rounded-lg">
                    <p className="text-3xl font-bold">{health?.api.error_rate_percent.toFixed(2) || 0}%</p>
                    <p className="text-sm text-muted-foreground">Error Rate</p>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="font-medium text-green-800">System Status: {health?.status || 'Unknown'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* ASHTA-STAMBHA Framework Reference */}
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Fingerprint className="w-5 h-5" /> ASHTA-STAMBHA Framework
          </CardTitle>
          <CardDescription>Eight Pillars of Security + Central Orchestrator</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-purple-700 mb-2">PRAHARI (Defense)</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>1. DRISHTI - Vision/Observation</li>
                <li>2. SMRITI - Memory/Intelligence</li>
                <li>3. VIVEK - Discrimination/Analysis</li>
                <li>4. KAVACH - Shield/Protection</li>
                <li>5. SHAKTI - Power/Response</li>
                <li>6. MAYA - Illusion/Deception</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-green-700 mb-2">RAKSHAKA (Healing)</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>7. SANJEEVANI - Recovery</li>
                <li>8. VIKASA - Evolution/Adaptation</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-blue-700 mb-2">CHAITANYA (Orchestrator)</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>⊕ Central Consciousness</li>
                <li>• Unified Posture Assessment</li>
                <li>• Cross-System Coordination</li>
                <li>• Adaptive Response</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
