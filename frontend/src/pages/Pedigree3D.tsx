/**
 * 3D Pedigree Visualization Page
 * Interactive 3D exploration of germplasm lineage
 */
import { useState, Suspense } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { GitBranch, Maximize2, RotateCcw, Info, Dna, Calendar, Award } from 'lucide-react'
import { PedigreeTree3D, PedigreeNode, PedigreeEdge } from '@/components/three/PedigreeTree3D'
import { apiClient } from '@/lib/api-client'

// Demo pedigree data - IR64 lineage
const demoPedigreeNodes: PedigreeNode[] = [
  // Founders (Generation 0)
  { id: 'ir8', name: 'IR8', generation: 0, type: 'root', year: 1966, traits: ['Semi-dwarf', 'High yield'] },
  { id: 'peta', name: 'Peta', generation: 0, type: 'root', year: 1960, traits: ['Tall', 'Traditional'] },
  { id: 'dgwg', name: 'Dee-geo-woo-gen', generation: 0, type: 'root', year: 1950, traits: ['Semi-dwarf gene'] },
  
  // F1 Generation
  { id: 'ir5', name: 'IR5', generation: 1, type: 'parent', year: 1967, traits: ['Improved yield'] },
  { id: 'ir20', name: 'IR20', generation: 1, type: 'parent', year: 1969, traits: ['Disease resistant'] },
  { id: 'ir22', name: 'IR22', generation: 1, type: 'parent', year: 1969, traits: ['Good grain'] },
  
  // F2-F3 Generation
  { id: 'ir24', name: 'IR24', generation: 2, type: 'parent', year: 1971, traits: ['High yield', 'Short duration'] },
  { id: 'ir26', name: 'IR26', generation: 2, type: 'parent', year: 1973, traits: ['BPH resistant'] },
  { id: 'ir36', name: 'IR36', generation: 2, type: 'parent', year: 1976, traits: ['Multiple resistance'] },
  
  // F4+ Generation
  { id: 'ir42', name: 'IR42', generation: 3, type: 'parent', year: 1977, traits: ['Improved quality'] },
  { id: 'ir50', name: 'IR50', generation: 3, type: 'parent', year: 1978, traits: ['Early maturity'] },
  { id: 'ir58', name: 'IR58', generation: 3, type: 'parent', year: 1980, traits: ['Blast resistant'] },
  
  // Target variety
  { id: 'ir64', name: 'IR64', generation: 4, type: 'offspring', year: 1985, traits: ['High yield', 'Good quality', 'Wide adaptation'] },
  { id: 'ir72', name: 'IR72', generation: 4, type: 'offspring', year: 1988, traits: ['Super high yield'] },
]

const demoPedigreeEdges: PedigreeEdge[] = [
  // Founders to F1
  { from: 'ir8', to: 'ir5' },
  { from: 'peta', to: 'ir5' },
  { from: 'dgwg', to: 'ir20' },
  { from: 'ir8', to: 'ir22' },
  
  // F1 to F2
  { from: 'ir5', to: 'ir24' },
  { from: 'ir20', to: 'ir26' },
  { from: 'ir22', to: 'ir36' },
  { from: 'ir5', to: 'ir36' },
  
  // F2 to F3
  { from: 'ir24', to: 'ir42' },
  { from: 'ir26', to: 'ir50' },
  { from: 'ir36', to: 'ir58' },
  { from: 'ir36', to: 'ir42' },
  
  // F3 to F4
  { from: 'ir42', to: 'ir64' },
  { from: 'ir58', to: 'ir64' },
  { from: 'ir50', to: 'ir72' },
  { from: 'ir42', to: 'ir72' },
]

export function Pedigree3D() {
  const [selectedNode, setSelectedNode] = useState<PedigreeNode | null>(null)
  const [selectedGermplasm, setSelectedGermplasm] = useState('ir64')
  const [isFullscreen, setIsFullscreen] = useState(false)

  // In production, fetch from API
  const nodes = demoPedigreeNodes
  const edges = demoPedigreeEdges

  const handleNodeClick = (node: PedigreeNode) => {
    setSelectedNode(node)
  }

  const resetView = () => {
    setSelectedNode(null)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <GitBranch className="h-7 w-7 text-primary" />
            3D Pedigree Explorer
          </h1>
          <p className="text-muted-foreground mt-1">Interactive 3D visualization of germplasm lineage</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedGermplasm} onValueChange={setSelectedGermplasm}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select germplasm" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ir64">IR64 Lineage</SelectItem>
              <SelectItem value="swarna">Swarna Lineage</SelectItem>
              <SelectItem value="nipponbare">Nipponbare Lineage</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={resetView}>
            <RotateCcw className="h-4 w-4 mr-2" />Reset
          </Button>
          <Button variant="outline" onClick={() => setIsFullscreen(!isFullscreen)}>
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{nodes.length}</p>
            <p className="text-sm text-muted-foreground">Total Entries</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{nodes.filter(n => n.type === 'root').length}</p>
            <p className="text-sm text-muted-foreground">Founders</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">{Math.max(...nodes.map(n => n.generation))}</p>
            <p className="text-sm text-muted-foreground">Generations</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">{edges.length}</p>
            <p className="text-sm text-muted-foreground">Connections</p>
          </CardContent>
        </Card>
      </div>

      <div className={`grid ${selectedNode ? 'lg:grid-cols-3' : 'grid-cols-1'} gap-6`}>
        {/* 3D Visualization */}
        <Card className={`${selectedNode ? 'lg:col-span-2' : ''} ${isFullscreen ? 'fixed inset-4 z-50' : ''}`}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2">
              <Dna className="h-5 w-5" />
              Pedigree Tree - {selectedGermplasm.toUpperCase()}
            </CardTitle>
            <CardDescription>Click and drag to rotate, scroll to zoom, click nodes for details</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className={`relative ${isFullscreen ? 'h-[calc(100vh-200px)]' : 'h-[500px]'}`}>
              <Suspense fallback={<Skeleton className="w-full h-full" />}>
                <PedigreeTree3D
                  nodes={nodes}
                  edges={edges}
                  onNodeClick={handleNodeClick}
                  selectedNodeId={selectedNode?.id}
                />
              </Suspense>
            </div>
          </CardContent>
        </Card>

        {/* Selected Node Details */}
        {selectedNode && (
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                {selectedNode.name}
              </CardTitle>
              <CardDescription>
                {selectedNode.type === 'root' ? 'Founder/Root' : `Generation F${selectedNode.generation}`}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedNode.year && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Released: {selectedNode.year}</span>
                </div>
              )}
              
              {selectedNode.traits && selectedNode.traits.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Award className="h-4 w-4" />Key Traits
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedNode.traits.map((trait, i) => (
                      <Badge key={i} variant="secondary">{trait}</Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-4 border-t">
                <p className="text-sm font-medium mb-2">Lineage</p>
                <div className="space-y-2 text-sm">
                  <p className="text-muted-foreground">
                    Parents: {edges.filter(e => e.to === selectedNode.id).length}
                  </p>
                  <p className="text-muted-foreground">
                    Offspring: {edges.filter(e => e.from === selectedNode.id).length}
                  </p>
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                <Button variant="outline" size="sm" className="flex-1">View Full Profile</Button>
                <Button variant="outline" size="sm" className="flex-1">Show Descendants</Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
