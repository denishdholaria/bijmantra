/**
 * Pedigree Viewer Page
 * Visualize germplasm ancestry and lineage - Connected to real API
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Loader2, RefreshCw } from 'lucide-react'
import { pedigreeAnalysisAPI, PedigreeNode } from '@/lib/api-client'
import { toast } from 'sonner'

export function PedigreeViewer() {
  const [selectedGermplasm, setSelectedGermplasm] = useState<string>('')
  const [generations, setGenerations] = useState(3)
  const [viewMode, setViewMode] = useState<'tree' | 'table'>('tree')
  const queryClient = useQueryClient()

  // Fetch germplasm list for dropdown
  const { data: germplasmListData } = useQuery({
    queryKey: ['pedigree-germplasm-list'],
    queryFn: async () => {
      // Use getIndividuals
      const response = await pedigreeAnalysisAPI.getIndividuals()
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
      if (!selectedGermplasm) return null
      const response = await pedigreeAnalysisAPI.getAncestors(selectedGermplasm, generations)
      return response.tree
    },
    enabled: !!selectedGermplasm,
  })

  const germplasmList = germplasmListData || []
  const pedigree = pedigreeData

  const loadPedigree = () => {
    if (!selectedGermplasm) {
      toast.error('Please select a germplasm')
      return
    }
    refetch()
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
            {node.parent1 && renderTreeNode(node.parent1, depth + 1)}
            {node.parent2 && renderTreeNode(node.parent2, depth + 1)}
          </div>
        )}
      </div>
    )
  }

  const flattenPedigree = (node: PedigreeNode, list: PedigreeNode[] = []): PedigreeNode[] => {
    list.push(node)
    if (node.parent1) flattenPedigree(node.parent1, list)
    if (node.parent2) flattenPedigree(node.parent2, list)
    return list
  }

  if (error) {
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
            <CardTitle>Search</CardTitle>
            <CardDescription>Find germplasm pedigree</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Germplasm</Label>
              <Select value={selectedGermplasm} onValueChange={setSelectedGermplasm}>
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

            <div className="space-y-2">
              <Label>Generations</Label>
              <Select value={generations.toString()} onValueChange={(v) => setGenerations(parseInt(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2">2 generations</SelectItem>
                  <SelectItem value="3">3 generations</SelectItem>
                  <SelectItem value="4">4 generations</SelectItem>
                  <SelectItem value="5">5 generations</SelectItem>
                </SelectContent>
              </Select>
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
              </div>
            </div>

            <Button onClick={loadPedigree} className="w-full" disabled={isLoading}>
              {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : '🔍'} Load Pedigree
            </Button>
          </CardContent>
        </Card>

        {/* Pedigree Display */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Pedigree {viewMode === 'tree' ? 'Tree' : 'Table'}</CardTitle>
            <CardDescription>
              {pedigree ? `Showing ancestry for ${pedigree.name}` : 'Select a germplasm to view pedigree'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
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
            ) : (
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
            )}
          </CardContent>
        </Card>
      </div>

      {/* Legend */}
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
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-100 border-2 border-blue-500 rounded"></div>
              <span className="text-sm">Generation 1 (Parents)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-100 border-2 border-purple-500 rounded"></div>
              <span className="text-sm">Generation 2 (Grandparents)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-100 border-2 border-orange-500 rounded"></div>
              <span className="text-sm">Generation 3+</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
