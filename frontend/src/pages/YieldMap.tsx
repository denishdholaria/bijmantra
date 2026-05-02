/**
 * Yield Map Page
 * Visualize yield data spatially across field - Connected to real API
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, Map, Grid3X3, Layers } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface PlotData {
  row: number
  col: number
  plotId: string
  germplasm: string
  yield: number
  rep: string
}

interface Study {
  id: string;
  name: string;
}

interface ObservationUnit {
  coordinates?: {
    positionCoordinateX?: string;
    positionCoordinateY?: string;
  };
  plot_name?: string;
  plot_id?: string;
  value?: string | number;
  observations?: Array<{
    observationVariableName: string;
    value: string;
  }>;
}

export function YieldMap() {
  const [selectedStudy, setSelectedStudy] = useState<string>('')
  const [selectedTrait, setSelectedTrait] = useState('yield')
  const [selectedPlot, setSelectedPlot] = useState<PlotData | null>(null)
  const [showHeatmap, setShowHeatmap] = useState(false)

  // Fetch studies from API
  const { data: studiesData, isLoading: loadingStudies } = useQuery({
    queryKey: ['yield-map-studies'],
    queryFn: () => apiClient.yieldMapService.getStudies({ limit: 50 }),
  })

  // Fetch plot data for selected study
  const { data: plotsData, isLoading: loadingPlots } = useQuery({
    queryKey: ['yield-map-plots', selectedStudy, selectedTrait],
    queryFn: async () => {
      const studyId = selectedStudy || 'study-001'
      const response = await apiClient.yieldMapService.getFieldPlotData({ study_id: studyId, trait: selectedTrait })
      return (response.result.data as ObservationUnit[]).map((unit) => {
        const yieldObs = unit.observations?.find((o) => 
          o.observationVariableName.toLowerCase().includes('yield')
        )
        return {
          row: parseInt(unit.coordinates?.positionCoordinateY || '1'),
          col: parseInt(unit.coordinates?.positionCoordinateX || '1'),
          plotId: String(unit.plot_name || unit.plot_id || 'Unknown'),
          germplasm: 'Unknown', // Germplasm name is not in YieldMapPlot currently
          yield: parseFloat(yieldObs?.value || unit.value?.toString() || '0'),
          rep: `R${Math.ceil(parseInt(unit.coordinates?.positionCoordinateY || '1') / 2)}`,
        }
      })
    },
  })

  const studies: Study[] = studiesData?.result?.data || []
  const plotData: PlotData[] = plotsData || []

  // Fetch interpolated data
  const { data: interpolatedData, isLoading: loadingHeatmap } = useQuery({
    queryKey: ['yield-map-interpolation', selectedStudy, selectedTrait],
    queryFn: async () => {
      if (!plotData.length) return null;
      const points = plotData.map(p => ({ x: p.col, y: p.row, value: p.yield }));
      return apiClient.calculatorService.interpolateYield({ points, resolution: 50 });
    },
    enabled: showHeatmap && plotData.length > 0
  })

  const minYield = plotData.length > 0 ? Math.min(...plotData.map(d => d.yield)) : 0
  const maxYield = plotData.length > 0 ? Math.max(...plotData.map(d => d.yield)) : 0
  const avgYield = plotData.length > 0 ? plotData.reduce((sum, d) => sum + d.yield, 0) / plotData.length : 0

  const getColor = (value: number, min: number = minYield, max: number = maxYield) => {
    if (max === min) return 'bg-lime-400'
    const normalized = (value - min) / (max - min)
    if (normalized < 0.25) return 'bg-red-400'
    if (normalized < 0.5) return 'bg-yellow-400'
    if (normalized < 0.75) return 'bg-lime-400'
    return 'bg-green-500'
  }

  // For heatmap (color only, no class)
  const getHexColor = (value: number, min: number, max: number) => {
     if (isNaN(value)) return '#f0f0f0'; // transparent/grey
     const normalized = (value - min) / (max - min);
     // Simple Red to Green gradient
     const r = Math.round(255 * (1 - normalized));
     const g = Math.round(255 * normalized);
     return `rgb(${r},${g},0)`;
  }

  const rows = [...new Set(plotData.map(d => d.row))].sort((a, b) => a - b)
  const cols = [...new Set(plotData.map(d => d.col))].sort((a, b) => a - b)

  const isLoading = loadingStudies || loadingPlots

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Yield Map</h1>
          <p className="text-muted-foreground mt-1">Spatial visualization of field data</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={showHeatmap ? "default" : "outline"}
            onClick={() => setShowHeatmap(!showHeatmap)}
            title="Toggle Interpolated Heatmap"
          >
            <Layers className="h-4 w-4 mr-2" />
            Heatmap
          </Button>
          <Select value={selectedStudy} onValueChange={setSelectedStudy}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select study..." />
            </SelectTrigger>
            <SelectContent>
              {studies.map(s => (
                <SelectItem key={s.id} value={s.id}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedTrait} onValueChange={setSelectedTrait}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="yield">Yield</SelectItem>
              <SelectItem value="height">Height</SelectItem>
              <SelectItem value="disease">Disease</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold">{plotData.length}</p>
            <p className="text-xs text-muted-foreground">Total Plots</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-green-600">{maxYield.toFixed(1)}</p>
            <p className="text-xs text-muted-foreground">Max Yield</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{avgYield.toFixed(1)}</p>
            <p className="text-xs text-muted-foreground">Avg Yield</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-red-600">{minYield.toFixed(1)}</p>
            <p className="text-xs text-muted-foreground">Min Yield</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Field Map */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Grid3X3 className="w-5 h-5" />
              Field Layout
            </CardTitle>
            <CardDescription>Click on a plot to see details</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : plotData.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Map className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No plot data available</p>
              </div>
            ) : showHeatmap && interpolatedData ? (
               <div className="relative w-full aspect-video border rounded overflow-hidden">
                 {/* Simple heatmap rendering using canvas or lots of divs. Divs for simplicity in this context. */}
                 {loadingHeatmap && <div className="absolute inset-0 flex items-center justify-center bg-white/50"><Loader2 className="w-8 h-8 animate-spin" /></div>}
                 <div style={{
                    display: 'grid',
                    gridTemplateColumns: `repeat(${interpolatedData.grid_z.length}, 1fr)`,
                    width: '100%',
                    height: '100%'
                 }}>
                   {interpolatedData.grid_z.map((row, i) => (
                      row.map((val, j) => (
                        <div
                          key={`${i}-${j}`}
                          style={{ backgroundColor: getHexColor(val, interpolatedData.min_val, interpolatedData.max_val) }}
                          title={`Interpolated: ${val?.toFixed(2) || 'N/A'}`}
                        />
                      ))
                   ))}
                 </div>
               </div>
            ) : (
              <div className="overflow-x-auto">
                <div className="inline-block">
                  {/* Column headers */}
                  <div className="flex gap-1 mb-1">
                    <div className="w-8"></div>
                    {cols.map(col => (
                      <div key={col} className="w-16 text-center text-xs text-muted-foreground">
                        Col {col}
                      </div>
                    ))}
                  </div>
                  {/* Rows */}
                  {rows.map(row => (
                    <div key={row} className="flex gap-1 mb-1">
                      <div className="w-8 flex items-center justify-center text-xs text-muted-foreground">
                        R{row}
                      </div>
                      {cols.map(col => {
                        const plot = plotData.find(d => d.row === row && d.col === col)
                        if (!plot) return <div key={col} className="w-16 h-12"></div>
                        return (
                          <div
                            key={col}
                            className={`w-16 h-12 rounded cursor-pointer flex items-center justify-center text-xs font-bold text-white transition-transform hover:scale-105 ${getColor(plot.yield)} ${selectedPlot?.plotId === plot.plotId ? 'ring-2 ring-black' : ''}`}
                            onClick={() => setSelectedPlot(plot)}
                            title={`${plot.germplasm}: ${plot.yield.toFixed(2)} t/ha`}
                          >
                            {plot.yield.toFixed(1)}
                          </div>
                        )
                      })}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Legend */}
            <div className="flex items-center gap-4 mt-4 text-sm">
              <span>Legend:</span>
              <div className="flex items-center gap-1"><div className="w-4 h-4 bg-red-400 rounded"></div><span>Low</span></div>
              <div className="flex items-center gap-1"><div className="w-4 h-4 bg-yellow-400 rounded"></div><span>Below Avg</span></div>
              <div className="flex items-center gap-1"><div className="w-4 h-4 bg-lime-400 rounded"></div><span>Above Avg</span></div>
              <div className="flex items-center gap-1"><div className="w-4 h-4 bg-green-500 rounded"></div><span>High</span></div>
            </div>
          </CardContent>
        </Card>

        {/* Plot Details */}
        <Card>
          <CardHeader>
            <CardTitle>Plot Details</CardTitle>
            <CardDescription>{selectedPlot ? selectedPlot.plotId : 'Select a plot'}</CardDescription>
          </CardHeader>
          <CardContent>
            {!selectedPlot ? (
              <div className="text-center py-8 text-muted-foreground">
                <Map className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="mt-2">Click on a plot to see details</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-muted rounded-lg">
                  <p className="font-bold text-lg">{selectedPlot.germplasm}</p>
                  <p className="text-sm text-muted-foreground">{selectedPlot.plotId}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-green-50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-green-700">{selectedPlot.yield.toFixed(2)}</p>
                    <p className="text-xs text-green-600">Yield (t/ha)</p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-blue-700">{selectedPlot.rep}</p>
                    <p className="text-xs text-blue-600">Replication</p>
                  </div>
                </div>
                <div className="text-sm space-y-1">
                  <div className="flex justify-between"><span>Row:</span><span className="font-mono">{selectedPlot.row}</span></div>
                  <div className="flex justify-between"><span>Column:</span><span className="font-mono">{selectedPlot.col}</span></div>
                  <div className="flex justify-between"><span>vs Average:</span>
                    <span className={selectedPlot.yield > avgYield ? 'text-green-600' : 'text-red-600'}>
                      {((selectedPlot.yield - avgYield) / avgYield * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
