import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Map,
  Grid3X3,
  Calendar,
  Leaf,
  Plus,
  Settings,
  Download,
  Eye,
  Maximize2,
  RotateCcw,
  Layers
} from 'lucide-react'

interface PlotInfo {
  id: string
  row: number
  col: number
  germplasm?: string
  treatment?: string
  status: 'empty' | 'planted' | 'harvested'
}

export function FieldPlanning() {
  const [selectedSeason, setSelectedSeason] = useState('2024-25')
  const [selectedField, setSelectedField] = useState('field-a')
  const [gridRows, setGridRows] = useState(8)
  const [gridCols, setGridCols] = useState(12)
  const [selectedPlot, setSelectedPlot] = useState<string | null>(null)

  const generatePlots = (): PlotInfo[] => {
    const plots: PlotInfo[] = []
    for (let r = 1; r <= gridRows; r++) {
      for (let c = 1; c <= gridCols; c++) {
        const status = Math.random() > 0.3 ? 'planted' : Math.random() > 0.5 ? 'harvested' : 'empty'
        plots.push({
          id: `${r}-${c}`,
          row: r,
          col: c,
          germplasm: status !== 'empty' ? `GERM-${Math.floor(Math.random() * 100)}` : undefined,
          treatment: status !== 'empty' ? ['Control', 'T1', 'T2'][Math.floor(Math.random() * 3)] : undefined,
          status
        })
      }
    }
    return plots
  }

  const [plots] = useState<PlotInfo[]>(generatePlots())

  const getPlotColor = (status: string) => {
    switch (status) {
      case 'planted': return 'bg-green-500'
      case 'harvested': return 'bg-yellow-500'
      default: return 'bg-gray-200'
    }
  }

  const stats = {
    total: plots.length,
    planted: plots.filter(p => p.status === 'planted').length,
    harvested: plots.filter(p => p.status === 'harvested').length,
    empty: plots.filter(p => p.status === 'empty').length
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Map className="h-8 w-8 text-primary" />
            Field Planning
          </h1>
          <p className="text-muted-foreground mt-1">Design and manage field layouts for trials</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedField} onValueChange={setSelectedField}>
            <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="field-a">Field A - Main</SelectItem>
              <SelectItem value="field-b">Field B - North</SelectItem>
              <SelectItem value="field-c">Field C - South</SelectItem>
            </SelectContent>
          </Select>
          <Select value={selectedSeason} onValueChange={setSelectedSeason}>
            <SelectTrigger className="w-[140px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="2024-25">2024-25</SelectItem>
              <SelectItem value="2023-24">2023-24</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
          <Button><Plus className="h-4 w-4 mr-2" />New Layout</Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Grid3X3 className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.total}</div>
                <div className="text-sm text-muted-foreground">Total Plots</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><Leaf className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.planted}</div>
                <div className="text-sm text-muted-foreground">Planted</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><Calendar className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.harvested}</div>
                <div className="text-sm text-muted-foreground">Harvested</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-100 rounded-lg"><Layers className="h-5 w-5 text-gray-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.empty}</div>
                <div className="text-sm text-muted-foreground">Empty</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Field Grid */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Field Layout</CardTitle>
                <CardDescription>{gridRows} rows × {gridCols} columns</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="icon"><RotateCcw className="h-4 w-4" /></Button>
                <Button variant="outline" size="icon"><Maximize2 className="h-4 w-4" /></Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto">
              <div className="inline-grid gap-1" style={{ gridTemplateColumns: `repeat(${gridCols}, minmax(40px, 1fr))` }}>
                {plots.map((plot) => (
                  <div key={plot.id} className={`w-10 h-10 rounded cursor-pointer transition-all hover:ring-2 hover:ring-primary ${getPlotColor(plot.status)} ${selectedPlot === plot.id ? 'ring-2 ring-primary' : ''}`} onClick={() => setSelectedPlot(plot.id)} title={`Row ${plot.row}, Col ${plot.col}`} />
                ))}
              </div>
            </div>
            <div className="flex items-center gap-6 mt-4 pt-4 border-t">
              <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-green-500" /><span className="text-sm">Planted</span></div>
              <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-yellow-500" /><span className="text-sm">Harvested</span></div>
              <div className="flex items-center gap-2"><div className="w-4 h-4 rounded bg-gray-200" /><span className="text-sm">Empty</span></div>
            </div>
          </CardContent>
        </Card>

        {/* Plot Details */}
        <Card>
          <CardHeader>
            <CardTitle>Plot Details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedPlot ? (
              <div className="space-y-4">
                {(() => {
                  const plot = plots.find(p => p.id === selectedPlot)
                  if (!plot) return null
                  return (
                    <>
                      <div className="p-4 bg-muted rounded-lg text-center">
                        <div className="text-2xl font-bold">R{plot.row} C{plot.col}</div>
                        <Badge variant={plot.status === 'planted' ? 'default' : plot.status === 'harvested' ? 'secondary' : 'outline'} className="mt-2 capitalize">{plot.status}</Badge>
                      </div>
                      {plot.germplasm && (
                        <div>
                          <div className="text-sm text-muted-foreground">Germplasm</div>
                          <div className="font-medium">{plot.germplasm}</div>
                        </div>
                      )}
                      {plot.treatment && (
                        <div>
                          <div className="text-sm text-muted-foreground">Treatment</div>
                          <div className="font-medium">{plot.treatment}</div>
                        </div>
                      )}
                      <div className="space-y-2">
                        <Button className="w-full" variant="outline"><Eye className="h-4 w-4 mr-2" />View Details</Button>
                        <Button className="w-full" variant="outline"><Settings className="h-4 w-4 mr-2" />Edit Plot</Button>
                      </div>
                    </>
                  )
                })()}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Grid3X3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Select a plot to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
