/**
 * Marker Positions Page - BrAPI Genotyping Module
 * Genetic marker positions on maps
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface MarkerPosition {
  markerPositionDbId: string
  markerDbId: string
  markerName: string
  mapDbId: string
  mapName: string
  linkageGroupName: string
  position: number
  positionUnit: string
}

export function MarkerPositions() {
  const [search, setSearch] = useState('')
  const [chrFilter, setChrFilter] = useState<string>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['markerPositions', chrFilter],
    queryFn: () => apiClient.getMarkerPositions({
      linkageGroupName: chrFilter !== 'all' ? chrFilter : undefined,
      pageSize: 500,
    }),
  })

  const markers: MarkerPosition[] = data?.result?.data || []
  const chromosomes = [...new Set(markers.map(m => m.linkageGroupName))].sort()

  const filteredMarkers = search
    ? markers.filter(m => m.markerName.toLowerCase().includes(search.toLowerCase()))
    : markers

  const markersByChromosome = filteredMarkers.reduce((acc, m) => {
    if (!acc[m.linkageGroupName]) acc[m.linkageGroupName] = []
    acc[m.linkageGroupName].push(m)
    return acc
  }, {} as Record<string, MarkerPosition[]>)

  const handleExport = () => {
    const header = 'Marker\tChromosome\tPosition\tUnit\n'
    const rows = filteredMarkers.map(m => `${m.markerName}\t${m.linkageGroupName}\t${m.position}\t${m.positionUnit}`).join('\n')
    const blob = new Blob([header + rows], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'marker_positions.tsv'
    a.click()
    toast.success('Exported marker positions')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Marker Positions</h1>
          <p className="text-muted-foreground mt-1">Genetic marker locations on maps</p>
        </div>
        <Button variant="outline" onClick={handleExport}>📥 Export</Button>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input placeholder="Search markers..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1" />
            <Select value={chrFilter} onValueChange={setChrFilter}>
              <SelectTrigger className="w-[150px]"><SelectValue placeholder="Chromosome" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Chromosomes</SelectItem>
                {chromosomes.map(chr => <SelectItem key={chr} value={chr}>{chr}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{filteredMarkers.length}</div><p className="text-sm text-muted-foreground">Markers</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{Object.keys(markersByChromosome).length}</div><p className="text-sm text-muted-foreground">Chromosomes</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{new Set(filteredMarkers.map(m => m.mapName)).size}</div><p className="text-sm text-muted-foreground">Maps</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{Math.max(...filteredMarkers.map(m => m.position), 0).toFixed(1)}</div><p className="text-sm text-muted-foreground">Max Position (cM)</p></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Chromosome View</CardTitle><CardDescription>Visual representation of marker positions</CardDescription></CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(markersByChromosome).sort().map(([chr, chrMarkers]) => {
              const maxPos = Math.max(...chrMarkers.map(m => m.position), 1)
              return (
                <div key={chr} className="flex items-center gap-4">
                  <div className="w-16 font-medium text-sm">{chr}</div>
                  <div className="flex-1 relative h-8 bg-gradient-to-r from-blue-100 to-blue-200 rounded-full overflow-hidden">
                    {chrMarkers.map((marker) => {
                      const leftPercent = (marker.position / maxPos) * 100
                      return <div key={marker.markerPositionDbId} className="absolute top-0 w-0.5 h-full bg-red-500" style={{ left: `${Math.min(leftPercent, 99)}%` }} title={`${marker.markerName}: ${marker.position} ${marker.positionUnit}`} />
                    })}
                  </div>
                  <div className="w-24 text-sm text-muted-foreground">{chrMarkers.length} markers</div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {isLoading ? <Skeleton className="h-64 w-full" /> : (
        <Card>
          <CardHeader><CardTitle>Marker List</CardTitle><CardDescription>{filteredMarkers.length} markers</CardDescription></CardHeader>
          <CardContent>
            <Table>
              <TableHeader><TableRow><TableHead>Marker Name</TableHead><TableHead>Map</TableHead><TableHead>Chromosome</TableHead><TableHead className="text-right">Position</TableHead><TableHead>Unit</TableHead></TableRow></TableHeader>
              <TableBody>
                {filteredMarkers.slice(0, 100).map((marker) => (
                  <TableRow key={marker.markerPositionDbId}>
                    <TableCell className="font-medium">{marker.markerName}</TableCell>
                    <TableCell>{marker.mapName}</TableCell>
                    <TableCell><Badge variant="outline">{marker.linkageGroupName}</Badge></TableCell>
                    <TableCell className="text-right font-mono">{marker.position.toLocaleString()}</TableCell>
                    <TableCell>{marker.positionUnit}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {filteredMarkers.length > 100 && <p className="text-sm text-muted-foreground mt-4 text-center">Showing first 100 of {filteredMarkers.length}</p>}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
