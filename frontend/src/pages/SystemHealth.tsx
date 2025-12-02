import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Activity,
  Server,
  Database,
  HardDrive,
  Cpu,
  MemoryStick,
  Wifi,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Download
} from 'lucide-react'

interface ServiceStatus {
  name: string
  status: 'healthy' | 'warning' | 'error'
  uptime: string
  responseTime: number
  lastCheck: string
}

interface SystemMetric {
  name: string
  value: number
  max: number
  unit: string
  status: 'good' | 'warning' | 'critical'
}

export function SystemHealth() {
  const [isRefreshing, setIsRefreshing] = useState(false)

  const services: ServiceStatus[] = [
    { name: 'API Server', status: 'healthy', uptime: '99.9%', responseTime: 45, lastCheck: '30 seconds ago' },
    { name: 'Database', status: 'healthy', uptime: '99.8%', responseTime: 12, lastCheck: '30 seconds ago' },
    { name: 'File Storage', status: 'healthy', uptime: '99.9%', responseTime: 89, lastCheck: '30 seconds ago' },
    { name: 'Cache Server', status: 'warning', uptime: '98.5%', responseTime: 156, lastCheck: '30 seconds ago' },
    { name: 'Background Jobs', status: 'healthy', uptime: '99.7%', responseTime: 23, lastCheck: '30 seconds ago' }
  ]

  const metrics: SystemMetric[] = [
    { name: 'CPU Usage', value: 42, max: 100, unit: '%', status: 'good' },
    { name: 'Memory', value: 6.2, max: 16, unit: 'GB', status: 'good' },
    { name: 'Disk Space', value: 234, max: 500, unit: 'GB', status: 'good' },
    { name: 'Network I/O', value: 125, max: 1000, unit: 'Mbps', status: 'good' }
  ]

  const recentEvents = [
    { time: '10:45 AM', event: 'Database backup completed', type: 'success' },
    { time: '10:30 AM', event: 'Cache server high latency detected', type: 'warning' },
    { time: '10:15 AM', event: 'API server restarted', type: 'info' },
    { time: '09:00 AM', event: 'Scheduled maintenance completed', type: 'success' }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': case 'good': return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'warning': return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'error': case 'critical': return <XCircle className="h-5 w-5 text-red-500" />
      default: return <Activity className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': case 'good': return 'bg-green-500'
      case 'warning': return 'bg-yellow-500'
      case 'error': case 'critical': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => setIsRefreshing(false), 1500)
  }

  const overallHealth = services.every(s => s.status === 'healthy') ? 'healthy' : services.some(s => s.status === 'error') ? 'error' : 'warning'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Activity className="h-8 w-8 text-primary" />
            System Health
          </h1>
          <p className="text-muted-foreground mt-1">Monitor system performance and service status</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Report</Button>
        </div>
      </div>

      {/* Overall Status */}
      <Card className={`border-2 ${overallHealth === 'healthy' ? 'border-green-500 bg-green-50' : overallHealth === 'warning' ? 'border-yellow-500 bg-yellow-50' : 'border-red-500 bg-red-50'}`}>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            {getStatusIcon(overallHealth)}
            <div>
              <h2 className="text-xl font-bold capitalize">System {overallHealth}</h2>
              <p className="text-muted-foreground">All critical services are operational</p>
            </div>
            <div className="ml-auto text-right">
              <div className="text-sm text-muted-foreground">Last updated</div>
              <div className="font-medium">30 seconds ago</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {metrics.map((metric, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">{metric.name}</span>
                {getStatusIcon(metric.status)}
              </div>
              <div className="text-2xl font-bold">{metric.value} {metric.unit}</div>
              <Progress value={(metric.value / metric.max) * 100} className="mt-2" />
              <div className="text-xs text-muted-foreground mt-1">of {metric.max} {metric.unit}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="services" className="space-y-4">
        <TabsList>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="events">Recent Events</TabsTrigger>
        </TabsList>

        <TabsContent value="services" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Server className="h-5 w-5" />Service Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {services.map((service, i) => (
                  <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className={`w-3 h-3 rounded-full ${getStatusColor(service.status)}`} />
                      <div>
                        <div className="font-medium">{service.name}</div>
                        <div className="text-sm text-muted-foreground">Uptime: {service.uptime}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className="text-sm font-medium">{service.responseTime}ms</div>
                        <div className="text-xs text-muted-foreground">Response time</div>
                      </div>
                      <Badge variant={service.status === 'healthy' ? 'default' : service.status === 'warning' ? 'secondary' : 'destructive'} className="capitalize">{service.status}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Clock className="h-5 w-5" />Recent Events</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentEvents.map((event, i) => (
                  <div key={i} className="flex items-center gap-4 p-3 border rounded-lg">
                    <div className={`w-2 h-2 rounded-full ${event.type === 'success' ? 'bg-green-500' : event.type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'}`} />
                    <div className="flex-1">
                      <div className="font-medium">{event.event}</div>
                    </div>
                    <div className="text-sm text-muted-foreground">{event.time}</div>
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
