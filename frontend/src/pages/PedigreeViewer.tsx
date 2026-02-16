/**
 * Pedigree Viewer Page
 * Visualize germplasm ancestry and lineage - Connected to real API
 */
import { useState, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Loader2, RefreshCw, GitGraph, ArrowRight, ArrowDown } from 'lucide-react'
import { apiClient, PedigreeNode } from '@/lib/api-client'
import { toast } from 'sonner'
import { PedigreeGraph } from '@/components/pedigree/PedigreeGraph'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'

// Helper to generate mock data for testing graph
const generateMockPedigree = (depth: number, currentDepth = 0, idPrefix = 'G'): PedigreeNode => {
  const id = `${idPrefix}-${Math.floor(Math.random() * 10000)}`
  const node: PedigreeNode = {
    id,
    name: `Germplasm ${id}`,
    generation: currentDepth,
  }

  if (currentDepth < depth - 1) { // Depth is total generations, so index goes to depth - 1
    node.sire = generateMockPedigree(depth, currentDepth + 1, `${idPrefix}S`)
    node.dam = generateMockPedigree(depth, currentDepth + 1, `${idPrefix}D`)
  }

  return node
}

export function PedigreeViewer() {
  const [selectedGermplasm, setSelectedGermplasm] = useState<string>('')
  const [generations, setGenerations] = useState(3)
  const [viewMode, setViewMode] = useState<'tree' | 'table' | 'graph'>('tree')
  const [graphDirection, setGraphDirection] = useState<'TB' | 'LR'>('TB')
  const [useMockData, setUseMockData] = useState(false)

  const queryClient = useQueryClient()

  // Fetch germplasm list for dropdown
  const { data: germplasmListData } = useQuery({
    queryKey: ['pedigree-germplasm-list'],
    queryFn: async () => {
      // Use getIndividuals
      const response = await apiClient.pedigreeAnalysisService.getIndividuals()
      // Map to expected format {id, name}
      return response.individuals.map((i: any) => ({
        id: i.id,
        name: i.id // or i.germplasm_name if available
      }))
    },
  })

  // Fetch pedigree when germplasm is selected
  const { data: pedigreeData, isLoading, error, refetch } = useQuery({
    queryKey: ['pedigree-tree', selectedGermplasm, generations],
    queryFn: async () => {
      if (!selectedGermplasm) return null
      const response = await apiClient.pedigreeAnalysisService.getAncestors(selectedGermplasm, generations)
      return response.tree
    },
    enabled: !!selectedGermplasm,
  })

  const germplasmList = germplasmListData || []
  const realPedigree = pedigreeData

  const mockData = useMemo(() => {
    if (useMockData) {
      return generateMockPedigree(generations)
    }
    return null
  }, [generations, useMockData])

  const pedigree = useMockData ? mockData : realPedigree

  const loadPedigree = () => {
    if (!selectedGermplasm && !useMockData) {
      toast.error('Please select a germplasm')
      return
    }
    if (!useMockData) {
      refetch()
    }
    toast.success('Pedigree loaded')
  }

  const renderTreeNode = (node: PedigreeNode, depth: number = 0): JSX.Element => {
    const indent = depth * 40
    const colors = ['bg-green-100 border-green-500', 'bg-blue-100 border-blue-500', 'bg-purple-100 border-purple-500', 'bg-orange-100 border-orange-500']
    const colorClass = colors[depth % colors.length]
    
    return (
      <div key={node.id} className="relative">
        <div 
          className={`p-3 rounded-lg border-2 ${colorClass} mb-2 inline-block min-w-[180px]`}
          style={{ marginLeft: `${indent}px` }}
        >
          <p className="font-semibold text-sm">{node.name}</p>
          <p className="text-xs text-muted-foreground">{node.id}</p>
          <Badge variant="outline" className="mt-1 text-xs">Gen {node.generation}</Badge>
        </div>
        {depth < generations - 1 && (
          <div className="ml-4">
            {node.sire && renderTreeNode(node.sire, depth + 1)}
            {node.dam && renderTreeNode(node.dam, depth + 1)}
          </div>
        )}
      </div>
    )
  }

  const flattenPedigree = (node: PedigreeNode, list: PedigreeNode[] = []): PedigreeNode[] => {
    list.push(node)
    if (node.sire) flattenPedigree(node.sire, list)
    if (node.dam) flattenPedigree(node.dam, list)
    return list
  }

  if (error && !useMockData) {
    return (
      <div className="p-12 text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Pedigree</h3>
        <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
        <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['pedigree-tree'] })}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Pedigree Viewer</h1>
          <p className="text-muted-foreground mt-1">Visualize germplasm ancestry</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Controls */}
        <Card>
          <CardHeader>
            <CardTitle>Controls</CardTitle>
            <CardDescription>Configure visualization</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center space-x-2">
              <Switch id="mock-data" checked={useMockData} onCheckedChange={setUseMockData} />
              <Label htmlFor="mock-data">Use Mock Data</Label>
            </div>

            <div className="space-y-2">
              <Label>Germplasm</Label>
              <Select value={selectedGermplasm} onValueChange={setSelectedGermplasm} disabled={useMockData}>
                <SelectTrigger>
                  <SelectValue placeholder="Select germplasm" />
                </SelectTrigger>
                <SelectContent>
                  {germplasmList.map((g) => (
                    <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between">
                <Label>Generations: {generations}</Label>
              </div>
              <Slider
                value={[generations]}
                min={1}
                max={5}
                step={1}
                onValueChange={(vals) => setGenerations(vals[0])}
              />
            </div>

            <div className="space-y-2">
              <Label>View Mode</Label>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={viewMode === 'tree' ? 'default' : 'outline'}
                  onClick={() => setViewMode('tree')}
                  className="flex-1"
                >
                  🌳 Tree
                </Button>
                <Button
                  size="sm"
                  variant={viewMode === 'table' ? 'default' : 'outline'}
                  onClick={() => setViewMode('table')}
                  className="flex-1"
                >
                  📋 Table
                </Button>
                <Button
                  size="sm"
                  variant={viewMode === 'graph' ? 'default' : 'outline'}
                  onClick={() => {
                    setViewMode('graph')
                    if (!useMockData && !selectedGermplasm) {
                         // Optional: prompt to select germplasm
                    }
                  }}
                  className="flex-1"
                >
                  <GitGraph className="w-4 h-4 mr-1" /> Graph
                </Button>
              </div>
            </div>

            {viewMode === 'graph' && (
              <div className="space-y-2">
                 <Label>Graph Direction</Label>
                 <div className="flex gap-2">
                    <Button
                        size="sm"
                        variant={graphDirection === 'TB' ? 'default' : 'outline'}
                        onClick={() => setGraphDirection('TB')}
                        className="flex-1"
                    >
                        <ArrowDown className="w-4 h-4 mr-1" /> Top-Bottom
                    </Button>
                    <Button
                        size="sm"
                        variant={graphDirection === 'LR' ? 'default' : 'outline'}
                        onClick={() => setGraphDirection('LR')}
                        className="flex-1"
                    >
                        <ArrowRight className="w-4 h-4 mr-1" /> Left-Right
                    </Button>
                 </div>
              </div>
            )}

            <Button onClick={loadPedigree} className="w-full" disabled={isLoading && !useMockData}>
              {isLoading && !useMockData ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : '🔍'} Load Pedigree
            </Button>
          </CardContent>
        </Card>

        {/* Pedigree Display */}
        <Card className="lg:col-span-3 min-h-[500px]">
          <CardHeader>
            <CardTitle>Pedigree {viewMode === 'tree' ? 'Tree' : viewMode === 'table' ? 'Table' : 'Graph'}</CardTitle>
            <CardDescription>
              {pedigree ? `Showing ancestry for ${pedigree.name}` : 'Select a germplasm to view pedigree'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading && !useMockData ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : !pedigree ? (
              <div className="text-center py-12 text-muted-foreground">
                <span className="text-4xl">🌳</span>
                <p className="mt-2">Select a germplasm and click "Load Pedigree"</p>
              </div>
            ) : viewMode === 'tree' ? (
              <div className="overflow-x-auto p-4">
                {renderTreeNode(pedigree)}
              </div>
            ) : viewMode === 'table' ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">ID</th>
                      <th className="text-left p-2">Name</th>
                      <th className="text-left p-2">Generation</th>
                      <th className="text-left p-2">Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {flattenPedigree(pedigree).map((node) => (
                      <tr key={node.id} className="border-b hover:bg-muted/50">
                        <td className="p-2 font-mono text-xs">{node.id}</td>
                        <td className="p-2">{node.name}</td>
                        <td className="p-2">
                          <Badge variant="outline">Gen {node.generation}</Badge>
                        </td>
                        <td className="p-2 capitalize">{node.type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
                <div className="w-full h-full min-h-[600px]">
                    <PedigreeGraph
                        data={pedigree}
                        direction={graphDirection}
                        onNodeClick={(id) => toast.info(`Clicked node: ${id}`)}
                    />
                </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Legend - Only show for tree/graph */}
      {viewMode !== 'table' && (
      <Card>
        <CardHeader>
          <CardTitle>Legend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-100 border-2 border-green-500 rounded"></div>
              <span className="text-sm">Generation 0 (Target)</span>
            </div>
            {/* Add more specific legend items for Graph if needed */}
             <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-emerald-500 rounded"></div>
              <span className="text-sm">Graph Node</span>
            </div>
          </div>
        </CardContent>
      </Card>
      )}
    </div>
  )
}
