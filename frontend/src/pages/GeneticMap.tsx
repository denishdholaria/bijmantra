import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Map,
  Dna,
  Target,
  ZoomIn,
  ZoomOut,
  Download,
  Filter,
  Info
} from 'lucide-react'

interface Marker {
  id: string
  name: string
  position: number
  type: 'SNP' | 'SSR' | 'InDel'
  trait?: string
}

interface Chromosome {
  id: string
  name: string
  length: number
  markers: Marker[]
}

export function GeneticMap() {
  const [selectedChromosome, setSelectedChromosome] = useState('chr1')
  const [zoom, setZoom] = useState(1)

  const chromosomes: Chromosome[] = [
    { id: 'chr1', name: 'Chromosome 1', length: 43.3, markers: [
      { id: 'm1', name: 'RM1', position: 5.2, type: 'SSR', trait: 'Yield QTL' },
      { id: 'm2', name: 'SNP_1_12', position: 12.4, type: 'SNP' },
      { id: 'm3', name: 'Sub1A', position: 25.8, type: 'SNP', trait: 'Submergence tolerance' },
      { id: 'm4', name: 'RM259', position: 38.1, type: 'SSR' }
    ]},
    { id: 'chr2', name: 'Chromosome 2', length: 35.9, markers: [
      { id: 'm5', name: 'RM154', position: 8.3, type: 'SSR' },
      { id: 'm6', name: 'Saltol', position: 18.5, type: 'SNP', trait: 'Salt tolerance' },
      { id: 'm7', name: 'RM263', position: 28.7, type: 'SSR' }
    ]},
    { id: 'chr3', name: 'Chromosome 3', length: 36.4, markers: [
      { id: 'm8', name: 'RM16', position: 10.2, type: 'SSR' },
      { id: 'm9', name: 'qDTY3.1', position: 22.4, type: 'SNP', trait: 'Drought tolerance' }
    ]}
  ]

  const currentChromosome = chromosomes.find(c => c.id === selectedChromosome)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Map className="h-8 w-8 text-primary" />
            Genetic Map
          </h1>
          <p className="text-muted-foreground mt-1">Visualize marker positions and QTL regions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={() => setZoom(z => Math.max(0.5, z - 0.25))} aria-label="Zoom out"><ZoomOut className="h-4 w-4" /></Button>
          <Button variant="outline" size="icon" onClick={() => setZoom(z => Math.min(2, z + 0.25))} aria-label="Zoom in"><ZoomIn className="h-4 w-4" /></Button>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Dna className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{chromosomes.length}</div>
                <div className="text-sm text-muted-foreground">Chromosomes</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><Target className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{chromosomes.reduce((sum, c) => sum + c.markers.length, 0)}</div>
                <div className="text-sm text-muted-foreground">Markers</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><Map className="h-5 w-5 text-purple-600" /></div>
              <div>
                <div className="text-2xl font-bold">{chromosomes.reduce((sum, c) => sum + c.length, 0).toFixed(1)} cM</div>
                <div className="text-sm text-muted-foreground">Total Length</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><Info className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">{chromosomes.reduce((sum, c) => sum + c.markers.filter(m => m.trait).length, 0)}</div>
                <div className="text-sm text-muted-foreground">QTL Markers</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chromosome List */}
        <Card>
          <CardHeader>
            <CardTitle>Chromosomes</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[400px]">
              <div className="space-y-1 p-2">
                {chromosomes.map(chr => (
                  <div key={chr.id} className={`p-3 rounded-lg cursor-pointer transition-colors ${selectedChromosome === chr.id ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`} onClick={() => setSelectedChromosome(chr.id)}>
                    <div className="font-medium">{chr.name}</div>
                    <div className="text-sm opacity-80">{chr.length} cM • {chr.markers.length} markers</div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Map Visualization */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>{currentChromosome?.name}</CardTitle>
            <CardDescription>{currentChromosome?.length} cM • {currentChromosome?.markers.length} markers</CardDescription>
          </CardHeader>
          <CardContent>
            {currentChromosome && (
              <div className="relative" style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}>
                {/* Chromosome bar */}
                <div className="relative h-16 bg-gradient-to-r from-blue-200 via-blue-300 to-blue-200 rounded-full mx-8">
                  {/* Centromere */}
                  <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-4 bg-blue-400 rounded-full" />
                  
                  {/* Markers */}
                  {currentChromosome.markers.map(marker => (
                    <div key={marker.id} className="absolute top-full mt-2" style={{ left: `${(marker.position / currentChromosome.length) * 100}%` }}>
                      <div className={`w-0.5 h-4 ${marker.trait ? 'bg-red-500' : 'bg-gray-400'}`} />
                      <div className="text-xs mt-1 -rotate-45 origin-top-left whitespace-nowrap">
                        {marker.name}
                        {marker.trait && <Badge variant="destructive" className="ml-1 text-[10px]">QTL</Badge>}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Scale */}
                <div className="flex justify-between mt-16 mx-8 text-xs text-muted-foreground">
                  <span>0 cM</span>
                  <span>{(currentChromosome.length / 2).toFixed(1)} cM</span>
                  <span>{currentChromosome.length} cM</span>
                </div>
              </div>
            )}

            {/* Marker List */}
            <div className="mt-8 pt-4 border-t">
              <h4 className="font-medium mb-3">Markers on {currentChromosome?.name}</h4>
              <div className="grid grid-cols-2 gap-2">
                {currentChromosome?.markers.map(marker => (
                  <div key={marker.id} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <span className="font-medium">{marker.name}</span>
                      <span className="text-sm text-muted-foreground ml-2">{marker.position} cM</span>
                    </div>
                    <div className="flex gap-1">
                      <Badge variant="outline">{marker.type}</Badge>
                      {marker.trait && <Badge variant="destructive">{marker.trait}</Badge>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
