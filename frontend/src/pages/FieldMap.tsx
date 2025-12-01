import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Map, Layers, MapPin, Maximize2, Download, Filter, Eye } from 'lucide-react'

interface Field {
  id: string
  name: string
  location: string
  area: number
  plots: number
  status: 'active' | 'fallow' | 'harvested'
}

export function FieldMap() {
  const [selectedField, setSelectedField] = useState<string | null>(null)
  const [mapLayer, setMapLayer] = useState('satellite')

  const fields: Field[] = [
    { id: '1', name: 'Block A', location: 'Station 1', area: 2.5, plots: 150, status: 'active' },
    { id: '2', name: 'Block B', location: 'Station 1', area: 3.0, plots: 180, status: 'active' },
    { id: '3', name: 'Block C', location: 'Station 2', area: 1.8, plots: 100, status: 'harvested' },
    { id: '4', name: 'Nursery', location: 'Station 1', area: 0.5, plots: 50, status: 'active' },
  ]

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { active: 'bg-green-100 text-green-800', fallow: 'bg-yellow-100 text-yellow-800', harvested: 'bg-blue-100 text-blue-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Field Map</h1>
          <p className="text-muted-foreground">Interactive field and plot visualization</p>
        </div>
        <div className="flex gap-2">
          <Select value={mapLayer} onValueChange={setMapLayer}>
            <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="satellite">Satellite</SelectItem>
              <SelectItem value="terrain">Terrain</SelectItem>
              <SelectItem value="hybrid">Hybrid</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export</Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <Card className="md:col-span-3">
          <CardContent className="p-0">
            <div className="h-[500px] bg-accent/50 rounded-lg flex items-center justify-center relative">
              <div className="text-center text-muted-foreground">
                <Map className="h-16 w-16 mx-auto mb-4" />
                <p>Interactive map view</p>
                <p className="text-sm">GPS coordinates and plot boundaries</p>
              </div>
              <div className="absolute top-4 right-4 flex flex-col gap-2">
                <Button variant="secondary" size="icon"><Maximize2 className="h-4 w-4" /></Button>
                <Button variant="secondary" size="icon"><Layers className="h-4 w-4" /></Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-lg">Fields</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {fields.map((field) => (
                  <div key={field.id} className={`p-3 cursor-pointer hover:bg-accent ${selectedField === field.id ? 'bg-accent' : ''}`} onClick={() => setSelectedField(field.id)}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{field.name}</p>
                        <p className="text-xs text-muted-foreground">{field.area} ha • {field.plots} plots</p>
                      </div>
                      <Badge className={getStatusColor(field.status)}>{field.status}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-lg">Summary</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span>Total Area</span><span className="font-medium">{fields.reduce((s, f) => s + f.area, 0)} ha</span></div>
                <div className="flex justify-between"><span>Total Plots</span><span className="font-medium">{fields.reduce((s, f) => s + f.plots, 0)}</span></div>
                <div className="flex justify-between"><span>Active Fields</span><span className="font-medium">{fields.filter(f => f.status === 'active').length}</span></div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
