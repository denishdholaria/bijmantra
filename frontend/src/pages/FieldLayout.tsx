/**
 * Field Layout Designer Page
 * Visual plot layout and management for studies
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { apiClient, FieldPlot, FieldStudy } from '@/lib/api-client'

export function FieldLayout() {
  const [selectedStudy, setSelectedStudy] = useState<string>('')
  const [selectedPlot, setSelectedPlot] = useState<FieldPlot | null>(null)
  const [viewMode, setViewMode] = useState<'germplasm' | 'block' | 'replicate'>('germplasm')

  // Fetch studies list
  const { data: studiesData, isLoading: studiesLoading } = useQuery({
    queryKey: ['field-layout-studies'],
    queryFn: () => apiClient.fieldLayoutService.getStudies(),
  })

  const studies = studiesData?.data || []

  // Fetch layout for selected study
  const { data: layoutData, isLoading: layoutLoading } = useQuery({
    queryKey: ['field-layout', selectedStudy],
    queryFn: () => apiClient.fieldLayoutService.getLayout(selectedStudy),
    enabled: !!selectedStudy,
  })

  const study = layoutData?.study
  const plots = layoutData?.plots || []
  const summary = layoutData?.summary

  const getPlotColor = (plot: FieldPlot) => {
    if (viewMode === 'germplasm') {
      if (plot.entryType === 'CHECK') return 'bg-yellow-200 border-yellow-400'
      const colors = ['bg-green-200', 'bg-blue-200', 'bg-purple-200', 'bg-pink-200', 'bg-orange-200', 'bg-teal-200']
      const hash = plot.germplasmName?.charCodeAt(0) || 0
      return `${colors[hash % colors.length]} border-gray-300`
    }
    if (viewMode === 'block') {
      const blockColors = ['bg-red-100', 'bg-blue-100', 'bg-green-100', 'bg-yellow-100', 'bg-purple-100']
      return `${blockColors[(plot.blockNumber || 0) % blockColors.length]} border-gray-300`
    }
    if (viewMode === 'replicate') {
      return plot.replicate === 1 ? 'bg-blue-200 border-blue-400' : 'bg-green-200 border-green-400'
    }
    return 'bg-gray-100 border-gray-300'
  }

  const handleExport = async () => {
    if (!selectedStudy) return
    try {
      const result = await apiClient.fieldLayoutService.exportLayout(selectedStudy, 'csv')
      toast.success(result.message)
    } catch {
      toast.error('Export failed')
    }
  }

  if (studiesLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Field Layout</h1>
          <p className="text-muted-foreground mt-1">Visual plot layout designer</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport} disabled={!selectedStudy}>
            📥 Export
          </Button>
          <Button variant="outline" onClick={() => toast.success('Print layout')}>
            🖨️ Print
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Label>Select Study</Label>
              <Select value={selectedStudy} onValueChange={setSelectedStudy}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a study..." />
                </SelectTrigger>
                <SelectContent>
                  {studies.map((s: FieldStudy) => (
                    <SelectItem key={s.studyDbId} value={s.studyDbId}>{s.studyName}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>View Mode</Label>
              <Select value={viewMode} onValueChange={(v: any) => setViewMode(v)}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="germplasm">By Germplasm</SelectItem>
                  <SelectItem value="block">By Block</SelectItem>
                  <SelectItem value="replicate">By Replicate</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {!selectedStudy ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-4xl mb-4">🗺️</div>
            <p className="text-muted-foreground">Select a study to view its field layout</p>
          </CardContent>
        </Card>
      ) : layoutLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>{study?.studyName}</CardTitle>
                <CardDescription>
                  {study?.rows} rows × {study?.cols} columns = {plots.length} plots
                  {summary && (
                    <span className="ml-2">
                      ({summary.check_plots} checks, {summary.test_plots} tests, {summary.unique_germplasm} unique germplasm)
                    </span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <div className="inline-block min-w-full">
                    {/* Column headers */}
                    <div className="flex">
                      <div className="w-10 h-8"></div>
                      {Array.from({ length: study?.cols || 0 }, (_, i) => (
                        <div key={i} className="w-16 h-8 flex items-center justify-center text-xs font-medium text-muted-foreground">
                          C{i + 1}
                        </div>
                      ))}
                    </div>
                    {/* Rows */}
                    {Array.from({ length: study?.rows || 0 }, (_, rowIdx) => (
                      <div key={rowIdx} className="flex">
                        <div className="w-10 h-14 flex items-center justify-center text-xs font-medium text-muted-foreground">
                          R{rowIdx + 1}
                        </div>
                        {Array.from({ length: study?.cols || 0 }, (_, colIdx) => {
                          const plot = plots.find((p: FieldPlot) => p.row === rowIdx + 1 && p.col === colIdx + 1)
                          if (!plot) return <div key={colIdx} className="w-16 h-14" />
                          return (
                            <button
                              key={colIdx}
                              onClick={() => setSelectedPlot(plot)}
                              className={`w-16 h-14 m-0.5 rounded border-2 text-xs flex flex-col items-center justify-center transition-all hover:scale-105 ${getPlotColor(plot)} ${selectedPlot?.plotNumber === plot.plotNumber ? 'ring-2 ring-primary' : ''}`}
                            >
                              <span className="font-medium truncate w-full px-1">{plot.germplasmName?.slice(0, 6)}</span>
                              <span className="text-[10px] text-muted-foreground">{plot.plotNumber}</span>
                            </button>
                          )
                        })}
                      </div>
                    ))}
                  </div>
                </div>
                {/* Legend */}
                <div className="mt-4 flex flex-wrap gap-4 text-sm">
                  {viewMode === 'germplasm' && (
                    <>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-yellow-200 border border-yellow-400"></div>
                        <span>Check</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-green-200 border border-gray-300"></div>
                        <span>Test Entry</span>
                      </div>
                    </>
                  )}
                  {viewMode === 'replicate' && (
                    <>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-blue-200 border border-blue-400"></div>
                        <span>Rep 1</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-green-200 border border-green-400"></div>
                        <span>Rep 2</span>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Plot details panel */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Plot Details</CardTitle>
                <CardDescription>
                  {selectedPlot ? `Plot ${selectedPlot.plotNumber}` : 'Click a plot to view details'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selectedPlot ? (
                  <div className="space-y-4">
                    <div>
                      <Label className="text-muted-foreground">Plot Number</Label>
                      <p className="font-medium">{selectedPlot.plotNumber}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Position</Label>
                      <p className="font-medium">Row {selectedPlot.row}, Column {selectedPlot.col}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Germplasm</Label>
                      <p className="font-medium">{selectedPlot.germplasmName}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Block</Label>
                      <p className="font-medium">{selectedPlot.blockNumber}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Replicate</Label>
                      <p className="font-medium">{selectedPlot.replicate}</p>
                    </div>
                    <div>
                      <Label className="text-muted-foreground">Entry Type</Label>
                      <Badge variant={selectedPlot.entryType === 'CHECK' ? 'default' : 'secondary'}>
                        {selectedPlot.entryType}
                      </Badge>
                    </div>
                    <div className="pt-4 flex gap-2">
                      <Button size="sm" className="flex-1">📊 Collect Data</Button>
                      <Button size="sm" variant="outline" className="flex-1">📷 Add Image</Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>Select a plot to view its details</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
