import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Droplets, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

interface IrrigationZone {
  id: string
  name: string
  field: string
  soilMoisture: number
  lastIrrigation: string
  nextScheduled: string
  status: 'optimal' | 'needs-water' | 'scheduled'
}

export function IrrigationPlanner() {
  const zones: IrrigationZone[] = [
    { id: '1', name: 'Zone A1', field: 'Block A', soilMoisture: 45, lastIrrigation: '2 days ago', nextScheduled: 'Tomorrow', status: 'optimal' },
    { id: '2', name: 'Zone A2', field: 'Block A', soilMoisture: 28, lastIrrigation: '4 days ago', nextScheduled: 'Today', status: 'needs-water' },
    { id: '3', name: 'Zone B1', field: 'Block B', soilMoisture: 52, lastIrrigation: '1 day ago', nextScheduled: 'In 3 days', status: 'optimal' },
    { id: '4', name: 'Zone B2', field: 'Block B', soilMoisture: 35, lastIrrigation: '3 days ago', nextScheduled: 'Tomorrow', status: 'scheduled' },
  ]

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { optimal: 'bg-green-100 text-green-800', 'needs-water': 'bg-red-100 text-red-800', scheduled: 'bg-blue-100 text-blue-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getMoistureColor = (moisture: number) => {
    if (moisture < 30) return 'bg-red-500'
    if (moisture < 40) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Irrigation Planner</h1>
          <p className="text-muted-foreground">Schedule and monitor irrigation</p>
        </div>
        <Button><Droplets className="mr-2 h-4 w-4" />Schedule Irrigation</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Droplets className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{zones.length}</p><p className="text-xs text-muted-foreground">Total Zones</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><AlertTriangle className="h-8 w-8 text-red-500" /><div><p className="text-2xl font-bold">{zones.filter(z => z.status === 'needs-water').length}</p><p className="text-xs text-muted-foreground">Need Water</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Clock className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{zones.filter(z => z.status === 'scheduled').length}</p><p className="text-xs text-muted-foreground">Scheduled</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><CheckCircle className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{zones.filter(z => z.status === 'optimal').length}</p><p className="text-xs text-muted-foreground">Optimal</p></div></div></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Irrigation Zones</CardTitle><CardDescription>Monitor soil moisture and schedule irrigation</CardDescription></CardHeader>
        <CardContent>
          <div className="space-y-4">
            {zones.map((zone) => (
              <div key={zone.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <Droplets className={`h-8 w-8 ${zone.soilMoisture < 30 ? 'text-red-500' : zone.soilMoisture < 40 ? 'text-yellow-500' : 'text-blue-500'}`} />
                  <div>
                    <p className="font-medium">{zone.name}</p>
                    <p className="text-sm text-muted-foreground">{zone.field}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="w-32">
                    <div className="flex justify-between text-xs mb-1"><span>Moisture</span><span>{zone.soilMoisture}%</span></div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden"><div className={`h-full ${getMoistureColor(zone.soilMoisture)} rounded-full`} style={{ width: `${zone.soilMoisture}%` }} /></div>
                  </div>
                  <div className="text-right text-sm">
                    <p>Last: {zone.lastIrrigation}</p>
                    <p className="text-muted-foreground">Next: {zone.nextScheduled}</p>
                  </div>
                  <Badge className={getStatusColor(zone.status)}>{zone.status}</Badge>
                  <Button variant="outline" size="sm">Irrigate Now</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
