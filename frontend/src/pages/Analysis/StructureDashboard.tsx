
import React, { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, Play } from 'lucide-react'
import { structureApi, PCAResponse } from '@/api/structure'
import { toast } from 'sonner'

export default function StructureDashboard() {
  const [loading, setLoading] = useState(false)
  const [pcaResult, setPcaResult] = useState<PCAResponse | null>(null)

  const runDemoAnalysis = async () => {
    setLoading(true)
    try {
      // Generate random genotype matrix (20 samples, 50 markers)
      // 0, 1, 2 coding
      const matrix = Array.from({ length: 50 }, () => 
        Array.from({ length: 100 }, () => Math.floor(Math.random() * 3))
      )
      
      const result = await structureApi.pcaAnalysis({
        matrix,
        components: 3
      })
      
      setPcaResult(result)
      toast.success("PCA Analysis Complete")
    } catch (error) {
      console.error(error)
      toast.error("Analysis Failed")
    } finally {
      setLoading(false)
    }
  }

  const getOption = () => {
    if (!pcaResult) return {}
    
    // coords is [PC1, PC2, ...] for each sample ?? 
    // Wait, backend returns:
    // "coords": project.tolist() -> (n_samples, n_components)
    // So coords[i] is [pc1, pc2, pc3] for sample i
    
    const data = pcaResult.coords.map((row, idx) => {
        return [row[0], row[1], `Sample ${idx + 1}`] // x, y, name
    })

    return {
      title: { text: 'PCA Plot (PC1 vs PC2)' },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
           return `${params.data[2]}<br/>PC1: ${params.data[0].toFixed(2)}<br/>PC2: ${params.data[1].toFixed(2)}`
        }
      },
      xAxis: { name: `PC1 (${(pcaResult.explained_variance[0] * 100).toFixed(1)}%)` },
      yAxis: { name: `PC2 (${(pcaResult.explained_variance[1] * 100).toFixed(1)}%)` },
      series: [
        {
          symbolSize: 10,
          data: data,
          type: 'scatter',
          itemStyle: { color: '#3b82f6' }
        }
      ]
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Structure Analysis</h1>
          <p className="text-muted-foreground">Population structure and principal component analysis</p>
        </div>
        <Button onClick={runDemoAnalysis} disabled={loading}>
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
          Run Demo PCA
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
         <Card className="col-span-2">
            <CardHeader>
              <CardTitle>Principal Component Analysis</CardTitle>
              <CardDescription>2D projection of genetic markers</CardDescription>
            </CardHeader>
            <CardContent>
              {pcaResult ? (
                 <ReactECharts option={getOption()} style={{ height: '500px' }} />
              ) : (
                <div className="h-[400px] flex items-center justify-center border-2 border-dashed rounded-lg text-muted-foreground">
                   Run analysis to view plot
                </div>
              )}
            </CardContent>
         </Card>
         
         {pcaResult && (
             <Card>
                <CardHeader>
                   <CardTitle>Explained Variance</CardTitle>
                </CardHeader>
                <CardContent>
                   <ul className="space-y-2">
                      {pcaResult.explained_variance.map((v, i) => (
                          <li key={i} className="flex justify-between">
                             <span>PC{i+1}</span>
                             <span className="font-mono">{(v * 100).toFixed(2)}%</span>
                          </li>
                      ))}
                   </ul>
                </CardContent>
             </Card>
         )}
      </div>
    </div>
  )
}
