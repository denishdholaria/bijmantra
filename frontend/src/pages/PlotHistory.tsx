import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { History, Search, Calendar, Leaf, Droplets, Bug, TrendingUp } from 'lucide-react'

interface PlotEvent {
  id: string
  date: string
  type: 'planting' | 'observation' | 'treatment' | 'harvest'
  description: string
  value?: string
}

interface Plot {
  id: string
  name: string
  field: string
  currentCrop: string
  plantingDate: string
  events: PlotEvent[]
}

export function PlotHistory() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPlot, setSelectedPlot] = useState<Plot | null>(null)

  const plots: Plot[] = [
    { id: '1', name: 'A-001', field: 'Block A', currentCrop: 'Rice - BIJ-R-001', plantingDate: '2025-06-15', events: [
      { id: '1', date: '2025-06-15', type: 'planting', description: 'Transplanted BIJ-R-001' },
      { id: '2', date: '2025-07-01', type: 'observation', description: 'Plant height', value: '45 cm' },
      { id: '3', date: '2025-07-15', type: 'treatment', description: 'Fertilizer application' },
      { id: '4', date: '2025-08-01', type: 'observation', description: 'Tiller count', value: '12' },
    ]},
    { id: '2', name: 'A-002', field: 'Block A', currentCrop: 'Rice - BIJ-R-002', plantingDate: '2025-06-15', events: [] },
    { id: '3', name: 'B-001', field: 'Block B', currentCrop: 'Wheat - BIJ-W-001', plantingDate: '2025-11-01', events: [] },
  ]

  const getEventIcon = (type: string) => {
    const icons: Record<string, any> = { planting: Leaf, observation: TrendingUp, treatment: Droplets, harvest: Calendar }
    const Icon = icons[type] || History
    return <Icon className="h-4 w-4" />
  }

  const getEventColor = (type: string) => {
    const colors: Record<string, string> = { planting: 'bg-green-100 text-green-800', observation: 'bg-blue-100 text-blue-800', treatment: 'bg-orange-100 text-orange-800', harvest: 'bg-purple-100 text-purple-800' }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const filteredPlots = plots.filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Plot History</h1>
          <p className="text-muted-foreground">View historical data for each plot</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Plots</CardTitle>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search plots..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y max-h-[400px] overflow-auto">
              {filteredPlots.map((plot) => (
                <div key={plot.id} className={`p-3 cursor-pointer hover:bg-accent ${selectedPlot?.id === plot.id ? 'bg-accent' : ''}`} onClick={() => setSelectedPlot(plot)}>
                  <p className="font-medium">{plot.name}</p>
                  <p className="text-sm text-muted-foreground">{plot.field} • {plot.currentCrop}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>{selectedPlot ? `Plot ${selectedPlot.name} History` : 'Select a Plot'}</CardTitle>
            {selectedPlot && <CardDescription>{selectedPlot.currentCrop} • Planted {selectedPlot.plantingDate}</CardDescription>}
          </CardHeader>
          <CardContent>
            {selectedPlot ? (
              <div className="space-y-4">
                {selectedPlot.events.length > 0 ? selectedPlot.events.map((event) => (
                  <div key={event.id} className="flex items-start gap-4 p-4 border rounded-lg">
                    <div className={`p-2 rounded-lg ${getEventColor(event.type)}`}>{getEventIcon(event.type)}</div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium">{event.description}</p>
                        <Badge variant="outline">{event.date}</Badge>
                      </div>
                      {event.value && <p className="text-sm text-muted-foreground mt-1">Value: {event.value}</p>}
                    </div>
                  </div>
                )) : (
                  <p className="text-center text-muted-foreground py-8">No events recorded for this plot</p>
                )}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">Select a plot to view its history</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
