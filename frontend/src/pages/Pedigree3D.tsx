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
import { GitBranch, Maximize2, RotateCcw, Info, Dna, Calendar, Award, AlertCircle } from 'lucide-react'
import { PedigreeTree3D, PedigreeNode, PedigreeEdge } from '@/components/three/PedigreeTree3D'
import { apiClient } from '@/lib/api-client'
import { Alert, AlertDescription } from '@/components/ui/alert'

// Fetch pedigree data from API
async function fetchPedigreeData(germplasmId: string): Promise<{ nodes: PedigreeNode[], edges: PedigreeEdge[] }> {
  try {
    // Try to get pedigree from BrAPI germplasm endpoint
    const response = await apiClient.crossService.getPedigree(germplasmId)
    
    if (response?.result) {
      // Transform BrAPI pedigree response to nodes/edges
      const nodes: PedigreeNode[] = []
      const edges: PedigreeEdge[] = []
      const pedigree = response.result
      
      // Add the main germplasm
      nodes.push({
        id: pedigree.germplasmDbId || germplasmId,
        name: pedigree.germplasmName || germplasmId,
        generation: 0,
        type: 'offspring',
        traits: [],
      })
      
      // Add parents if available
      if (pedigree.parent1DbId) {
        nodes.push({
          id: pedigree.parent1DbId,
          name: pedigree.parent1Name || pedigree.parent1DbId,
          generation: 1,
          type: 'parent',
          traits: [],
        })
        edges.push({ from: pedigree.parent1DbId, to: pedigree.germplasmDbId || germplasmId })
      }
      
      if (pedigree.parent2DbId) {
        nodes.push({
          id: pedigree.parent2DbId,
          name: pedigree.parent2Name || pedigree.parent2DbId,
          generation: 1,
          type: 'parent',
          traits: [],
        })
        edges.push({ from: pedigree.parent2DbId, to: pedigree.germplasmDbId || germplasmId })
      }
      
      return { nodes, edges }
    }
    
    return { nodes: [], edges: [] }
  } catch {
    return { nodes: [], edges: [] }
  }
}

export function Pedigree3D() {
  const [selectedNode, setSelectedNode] = useState<PedigreeNode | null>(null)
  const [selectedGermplasm, setSelectedGermplasm] = useState('')
  const [isFullscreen, setIsFullscreen] = useState(false)

  // Fetch germplasm list for selection
  const { data: germplasmList, isLoading: germplasmLoading } = useQuery({
    queryKey: ['germplasm-list'],
    queryFn: async () => {
      const response = await apiClient.germplasmService.getGermplasm(0, 50)
      return response?.result?.data || []
    },
  })

  // Fetch pedigree data for selected germplasm
  const { data: pedigreeData, isLoading: pedigreeLoading } = useQuery({
    queryKey: ['pedigree-3d', selectedGermplasm],
    queryFn: () => fetchPedigreeData(selectedGermplasm),
    enabled: !!selectedGermplasm,
  })

  const nodes = pedigreeData?.nodes || []
  const edges = pedigreeData?.edges || []

  const handleNodeClick = (node: PedigreeNode) => {
    setSelectedNode(node)
  }

  const resetView = () => {
    setSelectedNode(null)
  }

  const hasData = nodes.length > 0

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
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select germplasm" />
            </SelectTrigger>
            <SelectContent>
              {germplasmLoading ? (
                <SelectItem value="__loading__" disabled>Loading...</SelectItem>
              ) : germplasmList && germplasmList.length > 0 ? (
                germplasmList.map((g: any) => (
                  <SelectItem key={g.germplasmDbId} value={g.germplasmDbId}>
                    {g.germplasmName || g.germplasmDbId}
                  </SelectItem>
                ))
              ) : (
                <SelectItem value="__empty__" disabled>No germplasm available</SelectItem>
              )}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={resetView} disabled={!hasData}>
            <RotateCcw className="h-4 w-4 mr-2" />Reset
          </Button>
          <Button variant="outline" onClick={() => setIsFullscreen(!isFullscreen)} disabled={!hasData}>
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
            <p className="text-3xl font-bold text-purple-600">{nodes.length > 0 ? Math.max(...nodes.map(n => n.generation)) : 0}</p>
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

      {/* Empty State */}
      {!selectedGermplasm && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Select a germplasm from the dropdown above to view its pedigree tree in 3D.
          </AlertDescription>
        </Alert>
      )}

      {selectedGermplasm && !hasData && !pedigreeLoading && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No pedigree data available for the selected germplasm. Pedigree information may not have been recorded.
          </AlertDescription>
        </Alert>
      )}

      {(hasData || pedigreeLoading) && (
        <div className={`grid ${selectedNode ? 'lg:grid-cols-3' : 'grid-cols-1'} gap-6`}>
          {/* 3D Visualization */}
          <Card className={`${selectedNode ? 'lg:col-span-2' : ''} ${isFullscreen ? 'fixed inset-4 z-50' : ''}`}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <Dna className="h-5 w-5" />
                Pedigree Tree {selectedGermplasm && `- ${germplasmList?.find((g: any) => g.germplasmDbId === selectedGermplasm)?.germplasmName || selectedGermplasm}`}
              </CardTitle>
              <CardDescription>Click and drag to rotate, scroll to zoom, click nodes for details</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className={`relative ${isFullscreen ? 'h-[calc(100vh-200px)]' : 'h-[500px]'}`}>
                {pedigreeLoading ? (
                  <Skeleton className="w-full h-full" />
                ) : hasData ? (
                  <Suspense fallback={<Skeleton className="w-full h-full" />}>
                    <PedigreeTree3D
                      nodes={nodes}
                      edges={edges}
                      onNodeClick={handleNodeClick}
                      selectedNodeId={selectedNode?.id}
                    />
                  </Suspense>
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-muted/50 rounded-lg">
                    <p className="text-muted-foreground">No pedigree data to display</p>
                  </div>
                )}
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
      )}
    </div>
  )
}
