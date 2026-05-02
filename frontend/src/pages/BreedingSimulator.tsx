/**
 * Breeding Simulator Page
 * Interactive 3D simulation of breeding populations
 */
import { useState, useEffect, Suspense } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Play, Dna, Target, TrendingUp, Users, Zap, Sprout, Loader2, Activity, ArrowRight, RotateCcw } from 'lucide-react'
import { IntegrityBanner } from '@/components/common/IntegrityBanner'
import { BreedingSimulator3D, SimulationState } from '@/components/three/BreedingSimulator3D'
import { apiClient } from '@/lib/api-client'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { SimulationResponse } from '@/lib/api/breeding/biosimulation'
import { useNavigate } from 'react-router-dom'
import { updateBreedingWorkflowState } from '@/lib/breeding-workflow'
import { useAuthStore } from '@/store/auth'

export function BreedingSimulator() {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const [state, setState] = useState<SimulationState>({
    generation: 0,
    population: [],
    selectionIntensity: 0.7,
    heritability: 0.5,
    isRunning: false,
  })
  
  const [showTrails, setShowTrails] = useState(true)
  const [stats, setStats] = useState({ meanFitness: 0, bestFitness: 0, geneticGain: 0 })

  // Biosimulation State
  const [simLocation, setSimLocation] = useState('loc001')
  const [simCropId, setSimCropId] = useState<string>('')
  const [cropModels, setCropModels] = useState<{id: number, name: string, crop_name: string}[]>([])
  const [isSimulating, setIsSimulating] = useState(false)
  const [simResult, setSimResult] = useState<SimulationResponse | null>(null)

  // Fetch models on mount
  useEffect(() => {
    async function fetchModels() {
      try {
        const models = await apiClient.biosimulationService.getCropModels()
        setCropModels(models)
        if (models.length > 0) {
          setSimCropId(models[0].id.toString())
        }
      } catch (e) {
        console.error("Failed to fetch crop models", e)
      }
    }
    fetchModels()
  }, [])

  // Add error state
  const [error, setError] = useState<string | null>(null)

  const runCropSimulation = async () => {
    setIsSimulating(true)
    setError(null)
    try {
      const weather = await apiClient.weatherService.getWeatherForecast(simLocation, 'Location', 120)
      const weatherData = weather.daily_forecast.map(d => ({
        date: d.date,
        t_max: d.temp_max,
        t_min: d.temp_min,
        par: d.solar_radiation || (d.uv_index * 10)
      }))
      
      // 2. Run simulation
      if (!simCropId) throw new Error("Please select a crop model")
      const result = await apiClient.biosimulationService.runSimulation({
        crop_model_id: parseInt(simCropId), 
        location_id: 1,   // Mock ID
        start_date: new Date().toISOString(),
        daily_weather_data: weatherData
      })
      setSimResult(result)
      const backendPopulation = Array.isArray((result as any).population) ? (result as any).population : []
      setState(prev => ({ ...prev, generation: 1, population: backendPopulation, isRunning: false }))
      updateBreedingWorkflowState({
        simulation: {
          provenance: {
            run_id: String(result.run_id),
            model_version: `biosim:${simCropId}`,
            seed: result.run_id,
            timestamp: new Date().toISOString(),
            organization_id: String(user?.organization_id || 'unknown'),
            inputs: { crop_model_id: simCropId, location_id: simLocation, weather_days: weatherData.length }
          },
          assumptions: ['Backend biosimulation API result only', 'No local fallback for weather or simulation'],
          summary: { predicted_yield: result.predicted_yield, predicted_maturity_date: result.predicted_maturity_date }
        }
      })
    } catch (error: any) {
      console.error("Simulation failed:", error)
      setError(error.message || "Simulation failed. Please try again.")
    } finally {
      setIsSimulating(false)
    }
  }

  // Calculate stats
  useEffect(() => {
    if (state.population.length > 0) {
      const fitnesses = state.population.map(i => i.fitness)
      const mean = fitnesses.reduce((a, b) => a + b, 0) / fitnesses.length
      const best = Math.min(...fitnesses)
      
      setStats(prev => ({
        meanFitness: mean,
        bestFitness: best,
        geneticGain: prev.meanFitness > 0 ? ((prev.meanFitness - mean) / prev.meanFitness) * 100 : 0
      }))
    }
  }, [state.population])

  const handleStart = () => runCropSimulation()
  
  const handleReset = () => {
    setState({
      generation: 0,
      population: [],
      selectionIntensity: 0.7,
      heritability: 0.5,
      isRunning: false,
    })
  }
  
  const handleStep = () => runCropSimulation()

  return (
    <div className="space-y-6 animate-fade-in">
      <IntegrityBanner type="fake-compute" />
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Dna className="h-7 w-7 text-primary" />
            3D Breeding Simulator
          </h1>
          <p className="text-muted-foreground mt-1">Watch genetic improvement unfold in 3D space</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleStart} className="bg-green-600 hover:bg-green-700" disabled={isSimulating}>
            <Play className="h-4 w-4 mr-2" />Run Simulation
          </Button>
          <Button onClick={handleStep} variant="outline" disabled={isSimulating}>
            <Play className="h-4 w-4 mr-2" />Re-run
          </Button>
          <Button onClick={handleReset} variant="outline">
            <RotateCcw className="h-4 w-4 mr-2" />Reset
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{state.population.length}</p>
                <p className="text-xs text-muted-foreground">Population Size</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Target className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.bestFitness.toFixed(2)}</p>
                <p className="text-xs text-muted-foreground">Best Fitness</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/10 rounded-lg">
                <TrendingUp className="h-5 w-5 text-amber-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.meanFitness.toFixed(2)}</p>
                <p className="text-xs text-muted-foreground">Mean Fitness</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Zap className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.geneticGain.toFixed(1)}%</p>
                <p className="text-xs text-muted-foreground">Genetic Gain</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* 3D Visualization */}
        <Card className="lg:col-span-3">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Dna className="h-5 w-5" />
                3D Genetic Space
              </span>
              <Badge variant={state.isRunning ? 'default' : 'secondary'}>
                Generation {state.generation}
              </Badge>
            </CardTitle>
            <CardDescription>
              Each point is an individual. Position = trait values. Color = fitness (green = better).
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-[500px]">
              <Suspense fallback={<Skeleton className="w-full h-full" />}>
                <BreedingSimulator3D
                  state={state}
                  showTrails={showTrails}
                />
              </Suspense>
            </div>
          </CardContent>
        </Card>

        {/* Controls Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Simulation Controls</CardTitle>
            <CardDescription>Adjust breeding parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Selection Intensity */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Selection Intensity</Label>
                <span className="text-sm text-muted-foreground">{(state.selectionIntensity * 100).toFixed(0)}%</span>
              </div>
              <Slider
                value={[state.selectionIntensity * 100]}
                onValueChange={([v]) => setState(prev => ({ ...prev, selectionIntensity: v / 100 }))}
                min={10}
                max={90}
                step={5}
                disabled={state.isRunning}
              />
              <p className="text-xs text-muted-foreground">
                Higher = fewer selected = faster gain but more inbreeding
              </p>
            </div>

            {/* Show Trails Toggle */}
            <div className="flex items-center justify-between">
              <Label>Show Evolution Trail</Label>
              <Button
                variant={showTrails ? 'default' : 'outline'}
                size="sm"
                onClick={() => setShowTrails(!showTrails)}
              >
                {showTrails ? 'On' : 'Off'}
              </Button>
            </div>

            {/* Info */}
            <div className="pt-4 border-t space-y-2">
              <p className="text-sm font-medium">How it works:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• 3 axes = 3 traits (Yield, Quality, Resistance)</li>
                <li>• 🎯 Yellow star = ideal genotype</li>
                <li>• Green points = high fitness (close to ideal)</li>
                <li>• Each generation: select best → cross → repeat</li>
                <li>• Watch population converge toward ideal!</li>
              </ul>
            </div>

            {/* Quick Actions */}
            <div className="pt-4 border-t space-y-2">
              <Button 
                variant="outline" 
                className="w-full" 
                onClick={() => runCropSimulation()}
                disabled={state.isRunning}
              >
                Double Population
              </Button>
              <Button variant="outline" className="w-full" onClick={() => navigate('/parent-selection')}>
                Continue to Parent Selection <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Crop Performance Prediction (Biosimulation) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sprout className="h-5 w-5 text-green-600" />
            Crop Performance Prediction
          </CardTitle>
          <CardDescription>
             Run physiological growth models to predict phenotype expression in specific environments.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Target Environment</Label>
                <Select value={simLocation} onValueChange={setSimLocation}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="loc001">IRRI Research Station</SelectItem>
                    <SelectItem value="loc002">CIMMYT Field Station</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Crop Model</Label>
                <Select value={simCropId} onValueChange={setSimCropId}>
                  <SelectTrigger><SelectValue placeholder="Select Crop Model" /></SelectTrigger>
                  <SelectContent>
                    {cropModels.map(model => (
                      <SelectItem key={model.id} value={model.id.toString()}>
                        {model.name}
                      </SelectItem>
                    ))}
                    {cropModels.length === 0 && (
                      <SelectItem value="loading" disabled>Loading models...</SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={runCropSimulation} disabled={isSimulating} className="w-full">
                {isSimulating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                Run Bio-Simulation
              </Button>
              {error && <p className="text-sm text-red-500">{error}</p>}
            </div>

            <div className="md:col-span-2 bg-muted/30 rounded-lg p-4 border">
              {simResult ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-lg">Simulation Results</h4>
                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                      ID: {simResult.run_id}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-background p-3 rounded shadow-sm">
                      <p className="text-sm text-muted-foreground">Predicted Yield</p>
                      <p className="text-2xl font-bold">{simResult.predicted_yield?.toFixed(2)} t/ha</p>
                    </div>
                    <div className="bg-background p-3 rounded shadow-sm">
                      <p className="text-sm text-muted-foreground">Maturity Date</p>
                      <p className="text-xl font-semibold">
                        {simResult.predicted_maturity_date ? new Date(simResult.predicted_maturity_date).toLocaleDateString() : 'N/A'}
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">Run provenance: seed={simResult.run_id} • model={simCropId || 'n/a'} • run_id={simResult.run_id} • organization={user?.organization_id || 'unknown'}</p>

                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden mt-4">
                     <div className="h-full bg-green-500 w-[85%]"></div> 
                  </div>
                  <p className="text-xs text-muted-foreground text-center">Development Progress (Simulated)</p>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground p-8">
                  <Activity className="h-12 w-12 mb-2 opacity-20" />
                  <p>Run simulation to view predicted phenotypes</p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Educational Note */}
      <Card className="bg-primary/5 border-primary/20">
        <CardContent className="pt-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Dna className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="font-medium">Understanding the Simulation</p>
              <p className="text-sm text-muted-foreground mt-1">
                This simulator demonstrates <strong>truncation selection</strong> in a multi-trait breeding program. 
                The population starts randomly distributed in 3D genetic space. Each generation, the best individuals 
                (closest to the ideal at coordinates 2,2,2) are selected as parents. Their offspring inherit a mix of 
                parental traits plus random variation. Over generations, the population mean shifts toward the breeding goal.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
