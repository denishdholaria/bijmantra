
import React, { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, Search, Network } from 'lucide-react'
import { pedigreeApi, CytoscapeGraph } from '@/api/pedigree'
import { toast } from 'sonner'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export default function PedigreeViewer() {
  const [loading, setLoading] = useState(false)
  const [germplasmId, setGermplasmId] = useState('')
  const [depth, setDepth] = useState('3')
  const [graphData, setGraphData] = useState<CytoscapeGraph | null>(null)

  const fetchGraph = async () => {
    if (!germplasmId) {
        toast.error("Please enter a Germplasm ID")
        return
    }
    
    setLoading(true)
    try {
      const data = await pedigreeApi.getVisualization(germplasmId, parseInt(depth), 'ancestors')
      setGraphData(data)
      
      if (data.nodes.length === 0) {
        toast.warning("No pedigree data found for this ID")
      } else {
        toast.success(`Loaded ${data.nodes.length} nodes`)
      }
    } catch (error: any) {
      console.error(error)
      toast.error("Fetch Failed: " + error.message)
    } finally {
      setLoading(false)
    }
  }

  const getOption = () => {
    if (!graphData) return {}
    
    // Adapt Cytoscape JSON to ECharts
    const echartsNodes = graphData.nodes.map(n => ({
        id: n.data.id,
        name: n.data.label || n.data.id,
        value: n.data.type,
        // Visuals
        itemStyle: n.data.id === germplasmId ? { color: '#ef4444' } : { color: '#3b82f6' },
        symbolSize: n.data.id === germplasmId ? 30 : 20,
        label: { show: true, position: 'right' }
    }))
    
    const echartsLinks = graphData.edges.map(e => ({
        source: e.data.source,
        target: e.data.target,
        // Arrow for parent->child (ancestry flow)
        // ECharts edgeSymbol: ['none', 'arrow']
    }))

    return {
      title: { text: 'Pedigree Tree (Ancestry)' },
      tooltip: {},
      animationDurationUpdate: 1500,
      animationEasingUpdate: 'quinticInOut',
      series: [
        {
          type: 'graph',
          layout: 'force', // or 'tree' if structured properly, but force is safer for DAGs
          data: echartsNodes,
          links: echartsLinks,
          roam: true,
          label: {
            position: 'right',
            formatter: '{b}'
          },
          force: {
            repulsion: 1000,
            edgeLength: 50
          },
          edgeSymbol: ['none', 'arrow'],
          edgeSymbolSize: 10,
          lineStyle: {
            color: 'source',
            curveness: 0.2
          }
        }
      ]
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Pedigree Visualization</h1>
          <p className="text-muted-foreground">Interactive ancestry and relationship explorer</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Search</CardTitle>
            <CardDescription>Find Germplasm</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Germplasm ID</Label>
              <div className="flex space-x-2">
                  <Input 
                    value={germplasmId} 
                    onChange={(e) => setGermplasmId(e.target.value)} 
                    placeholder="e.g. 1042"
                  />
              </div>
            </div>
            
            <div className="space-y-2">
               <Label>Generations (Depth)</Label>
               <Select value={depth} onValueChange={setDepth}>
                 <SelectTrigger>
                   <SelectValue />
                 </SelectTrigger>
                 <SelectContent>
                   <SelectItem value="1">1 (Parents)</SelectItem>
                   <SelectItem value="3">3 (Great-Grandparents)</SelectItem>
                   <SelectItem value="5">5 (Deep Pedigree)</SelectItem>
                 </SelectContent>
               </Select>
            </div>
            
            <Button onClick={fetchGraph} disabled={loading} className="w-full">
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
              Visualize
            </Button>
            
            <div className="pt-4 text-xs text-muted-foreground">
               <p>Tip: Red node indicates the focal individual.</p>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
           <CardHeader>
              <CardTitle>Network Graph</CardTitle>
           </CardHeader>
           <CardContent>
              {graphData ? (
                 <ReactECharts option={getOption()} style={{ height: '600px' }} />
              ) : (
                <div className="h-[600px] flex flex-col items-center justify-center border-2 border-dashed rounded-lg text-muted-foreground">
                   <Network className="h-16 w-16 mb-4 opacity-20" />
                   <p>Enter an ID to view pedigree tree</p>
                </div>
              )}
           </CardContent>
        </Card>
      </div>
    </div>
  )
}
