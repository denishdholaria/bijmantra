import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Cpu, Thermometer, Droplets, Wind, Sun, 
  Wifi, WifiOff, Battery, AlertTriangle, Settings, Plus
} from 'lucide-react'

interface Sensor {
  id: string
  name: string
  type: 'weather' | 'soil' | 'plant' | 'water'
  location: string
  status: 'online' | 'offline' | 'warning'
  battery: number
  lastReading: string
  readings: { label: string; value: string; unit: string }[]
}

export function IoTSensors() {
  const [activeTab, setActiveTab] = useState('all')

  const sensors: Sensor[] = [
    { id: '1', name: 'Weather Station A1', type: 'weather', location: 'Block A', status: 'online', battery: 85, lastReading: '2 min ago', readings: [{ label: 'Temperature', value: '28.5', unit: '°C' }, { label: 'Humidity', value: '65', unit: '%' }, { label: 'Wind', value: '12', unit: 'km/h' }] },
    { id: '2', name: 'Soil Sensor B1', type: 'soil', location: 'Block B', status: 'online', battery: 72, lastReading: '5 min ago', readings: [{ label: 'Moisture', value: '42', unit: '%' }, { label: 'Temperature', value: '24', unit: '°C' }, { label: 'EC', value: '1.2', unit: 'mS/cm' }] },
    { id: '3', name: 'Plant Sensor C1', type: 'plant', location: 'Greenhouse', status: 'warning', battery: 15, lastReading: '1 hour ago', readings: [{ label: 'Leaf Wetness', value: '45', unit: '%' }, { label: 'Canopy Temp', value: '32', unit: '°C' }] },
    { id: '4', name: 'Water Level W1', type: 'water', location: 'Reservoir', status: 'online', battery: 90, lastReading: '10 min ago', readings: [{ label: 'Level', value: '78', unit: '%' }, { label: 'pH', value: '6.8', unit: '' }, { label: 'TDS', value: '450', unit: 'ppm' }] },
    { id: '5', name: 'Soil Sensor A2', type: 'soil', location: 'Block A', status: 'offline', battery: 0, lastReading: '2 days ago', readings: [] },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <Wifi className="h-4 w-4 text-green-500" />
      case 'offline': return <WifiOff className="h-4 w-4 text-red-500" />
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      default: return null
    }
  }

  const getTypeIcon = (type: string) => {
    const icons: Record<string, any> = { weather: Sun, soil: Droplets, plant: Thermometer, water: Droplets }
    const Icon = icons[type] || Cpu
    return <Icon className="h-5 w-5" />
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { online: 'bg-green-100 text-green-800', offline: 'bg-red-100 text-red-800', warning: 'bg-yellow-100 text-yellow-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const filteredSensors = sensors.filter(s => activeTab === 'all' || s.type === activeTab)
  const stats = { total: sensors.length, online: sensors.filter(s => s.status === 'online').length, warning: sensors.filter(s => s.status === 'warning').length, offline: sensors.filter(s => s.status === 'offline').length }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">IoT Sensors</h1>
          <p className="text-muted-foreground">Monitor field sensors and devices</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Settings className="mr-2 h-4 w-4" />Configure</Button>
          <Button><Plus className="mr-2 h-4 w-4" />Add Sensor</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Cpu className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total Sensors</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Wifi className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{stats.online}</p><p className="text-xs text-muted-foreground">Online</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><AlertTriangle className="h-8 w-8 text-yellow-500" /><div><p className="text-2xl font-bold">{stats.warning}</p><p className="text-xs text-muted-foreground">Warning</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><WifiOff className="h-8 w-8 text-red-500" /><div><p className="text-2xl font-bold">{stats.offline}</p><p className="text-xs text-muted-foreground">Offline</p></div></div></CardContent></Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All ({sensors.length})</TabsTrigger>
          <TabsTrigger value="weather">Weather</TabsTrigger>
          <TabsTrigger value="soil">Soil</TabsTrigger>
          <TabsTrigger value="plant">Plant</TabsTrigger>
          <TabsTrigger value="water">Water</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredSensors.map((sensor) => (
              <Card key={sensor.id} className={sensor.status === 'offline' ? 'opacity-60' : ''}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getTypeIcon(sensor.type)}
                      <CardTitle className="text-lg">{sensor.name}</CardTitle>
                    </div>
                    {getStatusIcon(sensor.status)}
                  </div>
                  <CardDescription>{sensor.location}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {sensor.readings.length > 0 ? (
                      <div className="grid grid-cols-3 gap-2">
                        {sensor.readings.map((r, i) => (
                          <div key={i} className="text-center p-2 bg-accent rounded-lg">
                            <p className="text-lg font-bold">{r.value}<span className="text-xs text-muted-foreground">{r.unit}</span></p>
                            <p className="text-xs text-muted-foreground">{r.label}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-center text-muted-foreground py-4">No data available</p>
                    )}
                    <div className="flex items-center justify-between pt-2 border-t">
                      <div className="flex items-center gap-2">
                        <Battery className={`h-4 w-4 ${sensor.battery > 30 ? 'text-green-500' : 'text-red-500'}`} />
                        <span className="text-sm">{sensor.battery}%</span>
                      </div>
                      <span className="text-xs text-muted-foreground">{sensor.lastReading}</span>
                      <Badge className={getStatusColor(sensor.status)}>{sensor.status}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
