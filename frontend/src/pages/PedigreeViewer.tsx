/**
 * Pedigree Viewer Page
 * Visualize germplasm ancestry and lineage
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'

interface PedigreeNode {
  id: string
  name: string
  type: 'germplasm' | 'cross' | 'unknown'
  generation: number
  parent1?: PedigreeNode
  parent2?: PedigreeNode
  children?: PedigreeNode[]
}

// Sample pedigree data
const samplePedigrees: Record<string, PedigreeNode> = {
  'VARIETY-001': {
    id: 'VARIETY-001',
    name: 'Elite Variety 2024',
    type: 'germplasm',
    generation: 0,
    parent1: {
      id: 'LINE-A',
      name: 'High Yield Line A',
      type: 'germplasm',
      generation: 1,
      parent1: {
        id: 'DONOR-1',
        name: 'Donor Parent 1',
        type: 'germplasm',
        generation: 2,
      },
      parent2: {
        id: 'RECURRENT-1',
        name: 'Recurrent Parent 1',
        type: 'germplasm',
        generation: 2,
      },
    },
    parent2: {
      id: 'LINE-B',
      name: 'Disease Resistant B',
      type: 'germplasm',
      generation: 1,
      parent1: {
        id: 'WILD-1',
        name: 'Wild Relative',
        type: 'germplasm',
        generation: 2,
      },
      parent2: {
        id: 'ELITE-OLD',
        name: 'Old Elite Variety',
        type: 'germplasm',
        generation: 2,
      },
    },
  },
  'HYBRID-X': {
    id: 'HYBRID-X',
    name: 'Hybrid X',
    type: 'germplasm',
    generation: 0,
    parent1: {
      id: 'INBRED-A',
      name: 'Inbred Line A',
      type: 'germplasm',
      generation: 1,
    },
    parent2: {
      id: 'INBRED-B',
      name: 'Inbred Line B',
      type: 'germplasm',
      generation: 1,
    },
  },
}

export function PedigreeViewer() {
  const [selectedGermplasm, setSelectedGermplasm] = useState<string>('')
  const [pedigree, setPedigree] = useState<PedigreeNode | null>(null)
  const [generations, setGenerations] = useState(3)
  const [viewMode, setViewMode] = useState<'tree' | 'table'>('tree')

  const loadPedigree = () => {
    if (!selectedGermplasm) {
      toast.error('Please select a germplasm')
      return
    }
    const data = samplePedigrees[selectedGermplasm]
    if (data) {
      setPedigree(data)
      toast.success('Pedigree loaded')
    } else {
      toast.error('Pedigree not found')
    }
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
                  <SelectItem value="VARIETY-001">Elite Variety 2024</SelectItem>
                  <SelectItem value="HYBRID-X">Hybrid X</SelectItem>
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

            <Button onClick={loadPedigree} className="w-full">
              🔍 Load Pedigree
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
            {!pedigree ? (
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
