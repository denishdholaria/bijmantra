
import React, { useState, useEffect } from 'react'
import ReactECharts from 'echarts-for-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Loader2, Play, RefreshCw, TrendingUp } from 'lucide-react'
import { simulationApi } from '@/api/simulation'
import { toast } from 'sonner'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface Ind {
  id: string
  genotype: number[]
  g_val: number // True Breeding Value (sum of alleles)
  p_val: number // Phenotype (G + E)
}

interface HistoryPoint {
  generation: number
  mean_g: number
  mean_p: number
}

export default function BreedingSimulator() {
  const [loading, setLoading] = useState(false)
  const [population, setPopulation] = useState<Ind[]>([])
  const [history, setHistory] = useState<HistoryPoint[]>([])
  const [generation, setGeneration] = useState(0)
  
  // Parameters
  const [popSize, setPopSize] = useState([50]) // Array for slider
  const [nLoci, setNLoci] = useState(100)
  const [h2, setH2] = useState([0.5])
  const [selectionIntensity, setSelectionIntensity] = useState([20]) // Top 20%
  const [crossingScheme, setCrossingScheme] = useState('random')

  // Initialize
  const initPopulation = () => {
    const size = popSize[0]
    const loci = nLoci
    const newPop: Ind[] = []
    
    for (let i = 0; i < size; i++) {
      // Random genotypes (0, 1, 2)
      // Assuming p=0.5 for simplicity
      const genotype = Array.from({ length: loci }, () => {
          const rand = Math.random()
          return rand < 0.25 ? 0 : rand < 0.75 ? 1 : 2
      })
      const g_val = genotype.reduce((a, b) => a + b, 0)
      newPop.push({
          id: `Gen0_Ind${i}`,
          genotype,
          g_val,
          p_val: g_val // Initial phenotype before environment noise added in loop? 
                       // Wait, G is fixed. P changes if we simulate E.
      })
    }
    
    // Calculate P with initial h2
    const popWithP = applyEnvironment(newPop, h2[0])
    
    setPopulation(popWithP)
    setGeneration(0)
    setHistory([{ 
        generation: 0, 
        mean_g: calculateMean(popWithP, 'g_val'),
        mean_p: calculateMean(popWithP, 'p_val')
    }])
    toast.success(`Initialized population of ${size}`)
  }

  // Helper: Apply Environment Noise
  const applyEnvironment = (inds: Ind[], heritability: number) => {
     // Var(P) = Var(G) + Var(E)
     // h2 = Var(G) / Var(P)
     // Var(E) = Var(G) * (1 - h2) / h2
     
     const g_values = inds.map(i => i.g_val)
     const var_g = calculateVariance(g_values)
     
     if (heritability >= 1) return inds.map(i => ({ ...i, p_val: i.g_val }))
     if (heritability <= 0) return inds.map(i => ({ ...i, p_val: Math.random() })) // Pure noise?
     
     const var_e = var_g * (1 - heritability) / heritability
     const std_e = Math.sqrt(var_e)
     
     return inds.map(i => {
         // Gaussian noise using Box-Muller transform
         const u1 = Math.random()
         const u2 = Math.random()
         const z = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2)
         const env_effect = z * std_e
         return { ...i, p_val: i.g_val + env_effect }
     })
  }

  const calculateMean = (inds: Ind[], key: 'g_val' | 'p_val') => {
      const sum = inds.reduce((acc, curr) => acc + curr[key], 0)
      return sum / inds.length
  }
  
  const calculateVariance = (values: number[]) => {
      const mean = values.reduce((a, b) => a + b, 0) / values.length
      return values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length
  }

  const runGeneration = async () => {
    if (population.length === 0) {
        toast.error("Initialize population first")
        return
    }
    setLoading(true)
    
    try {
        // 1. Selection
        // Sort by Phenotype (High is better)
        const sorted = [...population].sort((a, b) => b.p_val - a.p_val)
        
        // Select Top X%
        const n_select = Math.max(2, Math.floor(sorted.length * (selectionIntensity[0] / 100)))
        const parents = sorted.slice(0, n_select)
        
        // 2. Simulate Mating (Backend)
        const parentDosages = parents.map(p => p.genotype)
        
        // We want constant population size? Or growth? Let's keep constant.
        const targetSize = popSize[0]
        
        const result = await simulationApi.simulateGeneration({
            population_dosages: parentDosages,
            n_offspring: targetSize,
            crossing_scheme: crossingScheme as any
        })
        
        // 3. Process Offspring
        const newInds: Ind[] = result.offspring_dosages.map((gt, idx) => ({
            id: `Gen${generation + 1}_Ind${idx}`,
            genotype: gt,
            g_val: gt.reduce((a, b) => a + b, 0),
            p_val: 0 // Placeholder
        }))
        
        // 4. Update Environment on New Generation
        const nextPop = applyEnvironment(newInds, h2[0])
        
        setPopulation(nextPop)
        setGeneration(g => g + 1)
        
        // 5. Update History
        setHistory(prev => [
            ...prev, 
            {
                generation: generation + 1,
                mean_g: calculateMean(nextPop, 'g_val'),
                mean_p: calculateMean(nextPop, 'p_val')
            }
        ])
        
        toast.success(`Generation ${generation + 1} Complete`)
        
    } catch (error: any) {
        console.error(error)
        toast.error("Simulation Failed")
    } finally {
        setLoading(false)
    }
  }

  // ECharts Option
  const getChartOption = () => {
      return {
          title: { text: 'Genetic Gain (Response to Selection)' },
          tooltip: { trigger: 'axis' },
          legend: { data: ['Mean BV (G)', 'Mean Phenotype (P)'] },
          xAxis: { 
              type: 'category', 
              name: 'Generation',
              data: history.map(h => h.generation.toString()) 
          },
          yAxis: { type: 'value', name: 'Value', scale: true },
          series: [
              {
                  name: 'Mean BV (G)',
                  type: 'line',
                  data: history.map(h => h.mean_g.toFixed(2)),
                  smooth: true,
                  lineStyle: { width: 3, color: '#16a34a' } // Green
              },
              {
                  name: 'Mean Phenotype (P)',
                  type: 'line',
                  data: history.map(h => h.mean_p.toFixed(2)),
                  smooth: true,
                  lineStyle: { width: 2, type: 'dashed', color: '#2563eb' } // Blue
              }
          ]
      }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Breeding Simulator</h1>
          <p className="text-muted-foreground">Real-time genetic algorithm simulation with selection response</p>
        </div>
        <div className="flex space-x-2">
            <Button variant="outline" onClick={initPopulation}>
                <RefreshCw className="mr-2 h-4 w-4" /> Reset
            </Button>
            <Button onClick={runGeneration} disabled={loading || population.length === 0}>
                {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                Next Generation
            </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
         {/* Controls Sidebar */}
         <Card className="col-span-1">
            <CardHeader>
               <CardTitle>Parameters</CardTitle>
               <CardDescription>Configure simulation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
               <div className="space-y-2">
                  <Label>Population Size: {popSize[0]}</Label>
                  <Slider 
                    value={popSize} 
                    onValueChange={setPopSize} 
                    min={10} max={500} step={10} 
                  />
               </div>
               
               <div className="space-y-2">
                  <Label>Heritability (h²): {h2[0]}</Label>
                  <Slider 
                    value={h2} 
                    onValueChange={setH2} 
                    min={0.1} max={1.0} step={0.1} 
                  />
                  <p className="text-xs text-muted-foreground">High h² means phenotype predicts genotype well.</p>
               </div>
               
               <div className="space-y-2">
                  <Label>Selection Intensity (Top {selectionIntensity[0]}%)</Label>
                  <Slider 
                    value={selectionIntensity} 
                    onValueChange={setSelectionIntensity} 
                    min={1} max={50} step={1} 
                  />
               </div>
               
               <div className="space-y-2">
                  <Label>Crossing Scheme</Label>
                  <Select value={crossingScheme} onValueChange={setCrossingScheme}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="random">Random Mating</SelectItem>
                      <SelectItem value="selfing">Selfing</SelectItem>
                    </SelectContent>
                  </Select>
               </div>
               
               <div className="pt-4 border-t">
                  <h4 className="font-semibold mb-2">Current State</h4>
                  <ul className="text-sm space-y-1">
                     <li>Gen: {generation}</li>
                     <li>Pop: {population.length}</li>
                     <li>Mean G: {history.length > 0 ? history[history.length-1].mean_g.toFixed(2) : '-'}</li>
                  </ul>
               </div>
            </CardContent>
         </Card>

         {/* Main Visualization */}
         <Card className="col-span-3">
            <CardHeader>
               <CardTitle>Genetic Progress</CardTitle>
            </CardHeader>
            <CardContent>
               {history.length > 0 ? (
                  <ReactECharts option={getChartOption()} style={{ height: '500px' }} />
               ) : (
                  <div className="h-[500px] flex items-center justify-center border-2 border-dashed rounded-lg text-muted-foreground">
                     Initialize population to start simulation
                  </div>
               )}
            </CardContent>
         </Card>
      </div>
    </div>
  )
}
