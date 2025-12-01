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

interface MarkerPosition {
  markerPositionDbId: string
  markerDbId: string
  markerName: string
  mapDbId: string
  mapName: string
  linkageGroupName: string
  position: number
  unit: string
}

const mockMarkers: MarkerPosition[] = [
  { markerPositionDbId: 'mp001', markerDbId: 'mk001', markerName: 'RM1', mapDbId: 'map001', mapName: 'Rice_GBS_Map', linkageGroupName: 'Chr1', position: 0.0, unit: 'cM' },
  { markerPositionDbId: 'mp002', markerDbId: 'mk002', markerName: 'RM5', mapDbId: 'map001', mapName: 'Rice_GBS_Map', linkageGroupName: 'Chr1', position: 12.5, unit: 'cM' },
  { markerPositionDbId: 'mp003', markerDbId: 'mk003', markerName: 'RM10', mapDbId: 'map001', mapName: 'Rice_GBS_Map', linkageGroupName: 'Chr1', position: 28.3, unit: 'cM' },
  { markerPositionDbId: 'mp004', markerDbId: 'mk004', markerName: 'RM15', mapDbId: 'map001', mapName: 'Rice_GBS_Map', linkageGroupName: 'Chr2', position: 5.2, unit: 'cM' },
  { markerPositionDbId: 'mp005', markerDbId: 'mk005', markerName: 'RM20', mapDbId: 'map001', mapName: 'Rice_GBS_Map', linkageGroupName: 'Chr2', position: 18.7, unit: 'cM' },
  { markerPositionDbId: 'mp006', markerDbId: 'mk006', markerName: 'SNP_001', mapDbId: 'map002', mapName: 'Rice_Physical', linkageGroupName: 'Chr1', position: 1234567, unit: 'bp' },
]

export function MarkerPositions() {
  const [search, setSearch] = useState('')
  const [mapFilter, setMapFilter] = useState<string>('all')
  const [chrFilter, setChrFilter] = useState<string>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['markerPositions', search, mapFilter, chrFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockMarkers
      if (search) {
        filtered = filtered.filter(m => 
          m.markerName.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (mapFilter !== 'all') {
        filtered = filtered.filter(m => m.mapDbId === mapFilter)
      }
      if (chrFilter !== 'all') {
        filtered = filtered.filter(m => m.linkageGroupName === chrFilter)
      }
      return { result: { data: filtered } }
    },
  })

  const markers = data?.result?.data || []
  const maps = [...new Set(mockMarkers.map(m => ({ id: m.mapDbId, name: m.mapName })))]
  const chromosomes = [...new Set(mockMarkers.map(m => m.linkageGroupName))]

  // Group markers by chromosome for visualization
  const markersByChromosome = markers.reduce((acc, m) => {
    if (!acc[m.linkageGroupName]) acc[m.linkageGroupName] = []
    acc[m.linkageGroupName].push(m)
    return acc
  }, {} as Record<string, MarkerPosition[]>)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Marker Positions</h1>
          <p className="text-muted-foreground mt-1">Genetic marker locations on maps</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => toast.success('Export started (demo)')}>
            📥 Export
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search markers..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={mapFilter} onValueChange={setMapFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select map" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Maps</SelectItem>
                {maps.map(m => (
                  <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={chrFilter} onValueChange={setChrFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Chromosome" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Chromosomes</SelectItem>
                {chromosomes.map(chr => (
                  <SelectItem key={chr} value={chr}>{chr}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Chromosome visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Chromosome View</CardTitle>
          <CardDescription>Visual representation of marker positions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(markersByChromosome).map(([chr, chrMarkers]) => {
              const maxPos = Math.max(...chrMarkers.map(m => m.position))
              return (
                <div key={chr} className="flex items-center gap-4">
                  <div className="w-16 font-medium text-sm">{chr}</div>
                  <div className="flex-1 relative h-8 bg-gradient-to-r from-blue-100 to-blue-200 rounded-full">
                    {chrMarkers.map((marker) => {
                      const leftPercent = maxPos > 0 ? (marker.position / maxPos) * 100 : 0
                      return (
                        <div
                          key={marker.markerPositionDbId}
                          className="absolute top-0 w-1 h-full bg-red-500 rounded"
                          style={{ left: `${Math.min(leftPercent, 98)}%` }}
                          title={`${marker.markerName}: ${marker.position} ${marker.unit}`}
                        />
                      )
                    })}
                  </div>
                  <div className="w-20 text-sm text-muted-foreground">
                    {chrMarkers.length} markers
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Marker table */}
      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Marker List</CardTitle>
            <CardDescription>{markers.length} markers found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Marker Name</TableHead>
                  <TableHead>Map</TableHead>
                  <TableHead>Chromosome</TableHead>
                  <TableHead className="text-right">Position</TableHead>
                  <TableHead>Unit</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {markers.map((marker) => (
                  <TableRow key={marker.markerPositionDbId}>
                    <TableCell className="font-medium">{marker.markerName}</TableCell>
                    <TableCell>{marker.mapName}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{marker.linkageGroupName}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {marker.position.toLocaleString()}
                    </TableCell>
                    <TableCell>{marker.unit}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
