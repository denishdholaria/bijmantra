import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Plane, Camera, MapPin, Battery, Wifi, Clock,
  Play, Pause, Square, Upload, Download, Settings
} from 'lucide-react'

interface DroneStatus {
  id: string
  name: string
  status: 'idle' | 'flying' | 'charging' | 'offline'
  battery: number
  location: string
  lastFlight: string
  totalFlights: number
}

interface FlightMission {
  id: string
  name: string
  field: string
  status: 'scheduled' | 'in-progress' | 'completed' | 'failed'
  progress: number
  images: number
  startTime: string
  duration: string
}

export function DroneIntegration() {
  const [activeTab, setActiveTab] = useState('fleet')

  const drones: DroneStatus[] = [
    { id: '1', name: 'DJI Phantom 4 RTK', status: 'idle', battery: 95, location: 'Hangar A', lastFlight: '2 hours ago', totalFlights: 156 },
    { id: '2', name: 'DJI Matrice 300', status: 'flying', battery: 68, location: 'Block A', lastFlight: 'Now', totalFlights: 89 },
    { id: '3', name: 'senseFly eBee X', status: 'charging', battery: 45, location: 'Hangar A', lastFlight: '1 day ago', totalFlights: 234 },
    { id: '4', name: 'Parrot Bluegrass', status: 'offline', battery: 0, location: 'Unknown', lastFlight: '1 week ago', totalFlights: 67 },
  ]

  const missions: FlightMission[] = [
    { id: '1', name: 'Block A Survey', field: 'Block A', status: 'in-progress', progress: 65, images: 245, startTime: '10:30 AM', duration: '25 min' },
    { id: '2', name: 'Nursery Monitoring', field: 'Nursery', status: 'scheduled', progress: 0, images: 0, startTime: '2:00 PM', duration: 'Est. 15 min' },
    { id: '3', name: 'Block B NDVI', field: 'Block B', status: 'completed', progress: 100, images: 512, startTime: 'Yesterday', duration: '45 min' },
    { id: '4', name: 'Disease Hotspot', field: 'Block C', status: 'failed', progress: 30, images: 89, startTime: '2 days ago', duration: '12 min' },
  ]

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { idle: 'bg-green-100 text-green-800', flying: 'bg-blue-100 text-blue-800', charging: 'bg-yellow-100 text-yellow-800', offline: 'bg-gray-100 text-gray-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getMissionStatusColor = (status: string) => {
    const colors: Record<string, string> = { scheduled: 'bg-blue-100 text-blue-800', 'in-progress': 'bg-yellow-100 text-yellow-800', completed: 'bg-green-100 text-green-800', failed: 'bg-red-100 text-red-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getBatteryColor = (battery: number) => {
    if (battery > 60) return 'text-green-500'
    if (battery > 30) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Drone Integration</h1>
          <p className="text-muted-foreground">Manage drone fleet and flight missions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Settings className="mr-2 h-4 w-4" />Settings</Button>
          <Button><Plane className="mr-2 h-4 w-4" />New Mission</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Plane className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{drones.length}</p><p className="text-xs text-muted-foreground">Total Drones</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Wifi className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{drones.filter(d => d.status !== 'offline').length}</p><p className="text-xs text-muted-foreground">Online</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Camera className="h-8 w-8 text-purple-500" /><div><p className="text-2xl font-bold">{missions.filter(m => m.status === 'completed').reduce((s, m) => s + m.images, 0)}</p><p className="text-xs text-muted-foreground">Images Captured</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Clock className="h-8 w-8 text-orange-500" /><div><p className="text-2xl font-bold">{drones.reduce((s, d) => s + d.totalFlights, 0)}</p><p className="text-xs text-muted-foreground">Total Flights</p></div></div></CardContent></Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="fleet"><Plane className="mr-2 h-4 w-4" />Fleet</TabsTrigger>
          <TabsTrigger value="missions"><MapPin className="mr-2 h-4 w-4" />Missions</TabsTrigger>
          <TabsTrigger value="imagery"><Camera className="mr-2 h-4 w-4" />Imagery</TabsTrigger>
        </TabsList>

        <TabsContent value="fleet" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {drones.map((drone) => (
              <Card key={drone.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{drone.name}</CardTitle>
                    <Badge className={getStatusColor(drone.status)}>{drone.status}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2"><Battery className={`h-4 w-4 ${getBatteryColor(drone.battery)}`} />Battery</span>
                      <span className="font-medium">{drone.battery}%</span>
                    </div>
                    <Progress value={drone.battery} className="h-2" />
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1 text-muted-foreground"><MapPin className="h-3 w-3" />{drone.location}</span>
                      <span className="text-muted-foreground">{drone.totalFlights} flights</span>
                    </div>
                    <div className="flex gap-2 pt-2">
                      {drone.status === 'idle' && <Button size="sm" className="flex-1"><Play className="mr-1 h-3 w-3" />Start Mission</Button>}
                      {drone.status === 'flying' && <><Button size="sm" variant="outline" className="flex-1"><Pause className="mr-1 h-3 w-3" />Pause</Button><Button size="sm" variant="destructive" className="flex-1"><Square className="mr-1 h-3 w-3" />Stop</Button></>}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="missions" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Flight Missions</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {missions.map((mission) => (
                  <div key={mission.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <MapPin className={`h-8 w-8 ${mission.status === 'in-progress' ? 'text-blue-500 animate-pulse' : 'text-muted-foreground'}`} />
                      <div>
                        <p className="font-medium">{mission.name}</p>
                        <p className="text-sm text-muted-foreground">{mission.field} • {mission.startTime}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {mission.status === 'in-progress' && <div className="w-24"><Progress value={mission.progress} /><p className="text-xs text-center mt-1">{mission.progress}%</p></div>}
                      <div className="text-right text-sm"><p>{mission.images} images</p><p className="text-muted-foreground">{mission.duration}</p></div>
                      <Badge className={getMissionStatusColor(mission.status)}>{mission.status}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="imagery"><Card><CardContent className="pt-6"><p className="text-muted-foreground text-center py-8">Drone imagery gallery and processing</p></CardContent></Card></TabsContent>
      </Tabs>
    </div>
  )
}
