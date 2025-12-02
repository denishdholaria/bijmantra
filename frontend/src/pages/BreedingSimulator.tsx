import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Progress } from '@/components/ui/progress'
import {
  Play,
  Pause,
  RotateCcw,
  Settings,
  TrendingUp,
  Target,
  Dna,
  Clock,
  BarChart3,
  Download,
  Zap,
  Layers
} from 'lucide-react'

interface SimulationParams {
  generations: number
  populationSize: number
  selectionIntensity: number
  heritability: number
  numTraits: number
  crossingScheme: string
}

interface GenerationResult {
  generation: number
  meanGEBV: number
  geneticVariance: number
  inbreeding: number
  topPerformer: number
}

export function BreedingSimulator() {
  const [params, setParams] = useState<SimulationParams>({
    generations: 10,
    populationSize: 200,
    selectionIntensity: 10,
    heritability: 0.4,
    numTraits: 3,
    crossingScheme: 'random'
  })
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState<GenerationResult[]>([])

  const runSimulation = () => {
    setIsRunning(true)
    setProgress(0)
    setResults([])
    
    const simulatedResults: GenerationResult[] = []
    let currentMean = 0
    let currentVariance = 1
    let inbreeding = 0
    
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + (100 / params.generations)
        if (newProgress >= 100) {
          clearInterval(interval)
          setIsRunning(false)
          return 100
        }
        
        // Simulate genetic gain
        const gain = (params.selectionIntensity / 100) * Math.sqrt(params.heritability) * Math.sqrt(currentVariance) * 0.5
        currentMean += gain
        currentVariance *= 0.98 // Variance reduction
        inbreeding += 1 / (2 * params.populationSize)
        
        const gen = Math.floor(newProgress / (100 / params.generations))
        simulatedResults.push({
          generation: gen,
          meanGEBV: currentMean,
          geneticVariance: currentVariance,
          inbreeding: inbreeding,
          topPerformer: currentMean + 2 * Math.sqrt(currentVariance)
        })
        setResults([...simulatedResults])
        
        return newProgress
      })
    }, 500)
  }

  const resetSimulation = () => {
    setIsRunning(false)
    setProgress(0)
    setResults([])
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Zap className="h-8 w-8 text-primary" />
            Breeding Simulator
          </h1>
          <p className="text-muted-foreground mt-1">Simulate breeding strategies and predict outcomes</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={resetSimulation} disabled={isRunning}><RotateCcw className="h-4 w-4 mr-2" />Reset</Button>
          <Button onClick={runSimulation} disabled={isRunning}>
            {isRunning ? <><Pause className="h-4 w-4 mr-2" />Running...</> : <><Play className="h-4 w-4 mr-2" />Run Simulation</>}
          </Button>
        </div>
      </div>

      {/* Progress */}
      {(isRunning || progress > 0) && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <Zap className={`h-5 w-5 ${isRunning ? 'text-primary animate-pulse' : 'text-green-500'}`} />
              <div className="flex-1">
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">{isRunning ? 'Simulating...' : 'Simulation Complete'}</span>
                  <span className="text-sm text-muted-foreground">{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Parameters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Settings className="h-5 w-5" />Simulation Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between"><Label>Generations</Label><span className="text-sm font-mono">{params.generations}</span></div>
              <Slider value={[params.generations]} onValueChange={([v]) => setParams({...params, generations: v})} min={5} max={30} step={1} disabled={isRunning} />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between"><Label>Population Size</Label><span className="text-sm font-mono">{params.populationSize}</span></div>
              <Slider value={[params.populationSize]} onValueChange={([v]) => setParams({...params, populationSize: v})} min={50} max={1000} step={50} disabled={isRunning} />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between"><Label>Selection Intensity (%)</Label><span className="text-sm font-mono">{params.selectionIntensity}%</span></div>
              <Slider value={[params.selectionIntensity]} onValueChange={([v]) => setParams({...params, selectionIntensity: v})} min={1} max={50} step={1} disabled={isRunning} />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between"><Label>Heritability</Label><span className="text-sm font-mono">{params.heritability.toFixed(2)}</span></div>
              <Slider value={[params.heritability]} onValueChange={([v]) => setParams({...params, heritability: v})} min={0.1} max={0.9} step={0.05} disabled={isRunning} />
            </div>
            <div className="space-y-2">
              <Label>Crossing Scheme</Label>
              <Select value={params.crossingScheme} onValueChange={(v) => setParams({...params, crossingScheme: v})} disabled={isRunning}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="random">Random Mating</SelectItem>
                  <SelectItem value="assortative">Assortative Mating</SelectItem>
                  <SelectItem value="optimal">Optimal Contribution</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5" />Simulation Results</CardTitle>
            <CardDescription>Genetic progress over generations</CardDescription>
          </CardHeader>
          <CardContent>
            {results.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Layers className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Run simulation to see results</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Chart visualization */}
                <div className="h-48 flex items-end justify-between gap-1 border-b border-l p-4">
                  {results.map((r, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full bg-primary rounded-t transition-all" style={{ height: `${Math.max(10, r.meanGEBV * 30)}px` }} />
                      <span className="text-xs">{r.generation}</span>
                    </div>
                  ))}
                </div>
                
                {/* Summary stats */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <div className="text-xl font-bold text-primary">{results[results.length - 1]?.meanGEBV.toFixed(2) || '0'}</div>
                    <div className="text-xs text-muted-foreground">Final Mean GEBV</div>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <div className="text-xl font-bold text-green-600">{results[results.length - 1]?.topPerformer.toFixed(2) || '0'}</div>
                    <div className="text-xs text-muted-foreground">Top Performer</div>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <div className="text-xl font-bold text-blue-600">{((results[results.length - 1]?.geneticVariance || 1) * 100).toFixed(0)}%</div>
                    <div className="text-xs text-muted-foreground">Variance Retained</div>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <div className="text-xl font-bold text-orange-600">{((results[results.length - 1]?.inbreeding || 0) * 100).toFixed(1)}%</div>
                    <div className="text-xs text-muted-foreground">Inbreeding</div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Generation Details */}
      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Generation Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Generation</th>
                    <th className="text-right p-2">Mean GEBV</th>
                    <th className="text-right p-2">Genetic Variance</th>
                    <th className="text-right p-2">Inbreeding (F)</th>
                    <th className="text-right p-2">Top Performer</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => (
                    <tr key={i} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-medium">Gen {r.generation}</td>
                      <td className="p-2 text-right">{r.meanGEBV.toFixed(3)}</td>
                      <td className="p-2 text-right">{r.geneticVariance.toFixed(3)}</td>
                      <td className="p-2 text-right">{(r.inbreeding * 100).toFixed(2)}%</td>
                      <td className="p-2 text-right text-green-600 font-medium">{r.topPerformer.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
