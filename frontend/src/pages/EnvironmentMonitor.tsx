import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Thermometer, Droplets, Wind, Sun, CloudRain,
  AlertTriangle, TrendingUp, TrendingDown, Minus,
  MapPin, RefreshCw, Settings, Bell
} from 'lucide-react'

interface SensorData {
  id: string
  name: string
  location: string
  temperature: number
  humidity: number
  soilMoisture: number
  lightIntensity: number
  windSpeed: number
  lastUpdate: string
  status: 'online' | 'offline' | 'warning'
}

interface Alert {
  id: string
  type: 'temperature' | 'humidity' | 'moisture' | 'wind'
  message: string
  severity: 'low' | 'medium' | 'high'
  timestamp: string
  location: string
}

export function EnvironmentMonitor() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedLocation, setSelectedLocation] = useState('all')
  const [refreshing, setRefreshing] = useState(false)

  const sensors: SensorData[] = [
    { id: '1', name: 'Station Alpha', location: 'Field Block A', temperature: 28.5, humidity: 65, soilMoisture: 42, lightIntensity: 850, windSpeed: 12, lastUpdate: '2 min ago', status: 'online' },
    { id: '2', name: 'Station Beta', location: 'Field Block B', temperature: 29.2, humidity: 62, soilMoisture: 38, lightIntensity: 920, windSpeed: 15, lastUpdate: '2 min ago', status: 'online' },
    { id: '3', name: 'Station Gamma', location: 'Greenhouse 1', temperature: 32.1, humidity: 78, soilMoisture: 55, lightIntensity: 650, windSpeed: 0, lastUpdate: '5 min ago', status: 'warning' },
    { id: '4', name: 'Station Delta', location: 'Nursery', temperature: 26.8, humidity: 70, soilMoisture: 48, lightIntensity: 780, windSpeed: 8, lastUpdate: '2 min ago', status: 'online' },
    { id: '5', name: 'Station Epsilon', location: 'Field Block C', temperature: 27.9, humidity: 68, soilMoisture: 35, lightIntensity: 890, windSpeed: 18, lastUpdate: '15 min ago', status: 'offline' },
  ]

  const alerts: Alert[] = [
    { id: '1', type: 'temperature', message: 'High temperature detected in Greenhouse 1', severity: 'high', timestamp: '10 min ago', location: 'Greenhouse 1' },
    { id: '2', type: 'moisture', message: 'Low soil moisture in Field Block C', severity: 'medium', timestamp: '30 min ago', location: 'Field Block C' },
    { id: '3', type: 'wind', message: 'Strong winds expected this afternoon', severity: 'low', timestamp: '1 hour ago', location: 'All locations' },
  ]

  const avgTemp = (sensors.reduce((sum, s) => sum + s.temperature, 0) / sensors.length).toFixed(1)
  const avgHumidity = Math.round(sensors.reduce((sum, s) => sum + s.humidity, 0) / sensors.length)
  const avgMoisture = Math.round(sensors.reduce((sum, s) => sum + s.soilMoisture, 0) / sensors.length)
  const onlineSensors = sensors.filter(s => s.status === 'online').length

  const handleRefresh = async () => {
    setRefreshing(true)
    await new Promise(r => setTimeout(r, 1000))
    setRefreshing(false)
  }

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = { low: 'bg-yellow-100 text-yellow-800', medium: 'bg-orange-100 text-orange-800', high: 'bg-red-100 text-red-800' }
    return colors[severity] || 'bg-gray-100 text-gray-800'
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { online: 'bg-green-500', offline: 'bg-red-500', warning: 'bg-yellow-500' }
    return colors[status] || 'bg-gray-500'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Environment Monitor</h1>
          <p className="text-muted-foreground">Real-time environmental data from field sensors</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />Refresh
          </Button>
          <Button variant="outline"><Bell className="mr-2 h-4 w-4" />Alerts</Button>
          <Button><Settings className="mr-2 h-4 w-4" />Configure</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Temperature</CardTitle>
            <Thermometer className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgTemp}°C</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1"><TrendingUp className="h-3 w-3 text-red-500" />+2.1° from yesterday</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Humidity</CardTitle>
            <Droplets className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgHumidity}%</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1"><Minus className="h-3 w-3" />Stable</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Soil Moisture</CardTitle>
            <CloudRain className="h-4 w-4 text-cyan-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgMoisture}%</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1"><TrendingDown className="h-3 w-3 text-yellow-500" />-5% this week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Light</CardTitle>
            <Sun className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">820 lux</div>
            <p className="text-xs text-muted-foreground">Optimal range</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sensors</CardTitle>
            <Wind className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{onlineSensors}/{sensors.length}</div>
            <p className="text-xs text-muted-foreground">Online</p>
          </CardContent>
        </Card>
      </div>

      {alerts.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <CardTitle className="text-lg">Active Alerts</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-3 bg-white rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge className={getSeverityColor(alert.severity)}>{alert.severity}</Badge>
                    <div>
                      <p className="font-medium text-sm">{alert.message}</p>
                      <p className="text-xs text-muted-foreground">{alert.location} • {alert.timestamp}</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">Dismiss</Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sensors">Sensors</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="flex gap-4">
            <Select value={selectedLocation} onValueChange={setSelectedLocation}>
              <SelectTrigger className="w-[200px]"><SelectValue placeholder="Location" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Locations</SelectItem>
                {sensors.map(s => (<SelectItem key={s.id} value={s.location}>{s.location}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sensors.map((sensor) => (
              <Card key={sensor.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`h-2 w-2 rounded-full ${getStatusColor(sensor.status)}`} />
                      <CardTitle className="text-lg">{sensor.name}</CardTitle>
                    </div>
                    <Badge variant="outline">{sensor.status}</Badge>
                  </div>
                  <CardDescription className="flex items-center gap-1"><MapPin className="h-3 w-3" />{sensor.location}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-2"><Thermometer className="h-4 w-4 text-orange-500" /><span className="text-sm">{sensor.temperature}°C</span></div>
                    <div className="flex items-center gap-2"><Droplets className="h-4 w-4 text-blue-500" /><span className="text-sm">{sensor.humidity}%</span></div>
                    <div className="flex items-center gap-2"><CloudRain className="h-4 w-4 text-cyan-500" /><span className="text-sm">{sensor.soilMoisture}%</span></div>
                    <div className="flex items-center gap-2"><Wind className="h-4 w-4 text-gray-500" /><span className="text-sm">{sensor.windSpeed} km/h</span></div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-3">Updated {sensor.lastUpdate}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="sensors"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Sensor configuration and management</p></CardContent></Card></TabsContent>
        <TabsContent value="history"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Historical data and trends</p></CardContent></Card></TabsContent>
      </Tabs>
    </div>
  )
}
