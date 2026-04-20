import { useState, useEffect, useMemo } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { useDebounce } from '@/hooks/useDebounce'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Calculator, TrendingUp, Target, Clock, Dna, Download, RefreshCw } from 'lucide-react'
import { updateBreedingWorkflowState } from '@/lib/breeding-workflow'
import { useAuthStore } from '@/store/auth'

interface BreederEquationParams {
  selectionIntensity: number
  heritability: number
  phenotypicSD: number
  generationInterval: number
  accuracy: number
}

export function GeneticGainCalculator() {
  const [params, setParams] = useState<BreederEquationParams>({ selectionIntensity: 1.76, heritability: 0.35, phenotypicSD: 12.5, generationInterval: 4, accuracy: 0.7 })
  const [method, setMethod] = useState('phenotypic')
  const [programId, setProgramId] = useState('')
  const debouncedParams = useDebounce(params, 500)
  const user = useAuthStore((s) => s.user)

  const { data: programsData } = useQuery({ queryKey: ['genetic-gain-calc', 'programs'], queryFn: () => apiClient.geneticGainService.getPrograms() })
  const programs = programsData?.data || []

  const expectedMutation = useMutation({
    mutationFn: async (data: typeof params) => {
      const response = await apiClient.selectionIndexService.predictSelectionResponse({
        selection_intensity: data.selectionIntensity,
        heritability: data.heritability,
        phenotypic_std: data.phenotypicSD,
        generation_interval: data.generationInterval,
        accuracy: method === 'genomic' ? data.accuracy : undefined,
      })
      return response.data
    },
    onError: (err: Error) => toast.error(`Calculation failed: ${err.message}`),
  })

  const realizedMutation = useMutation({
    mutationFn: async () => {
      if (!programId) throw new Error('Select a program to compare realized gain')
      const response = await apiClient.geneticGainService.calculateGain(programId, true)
      return response.data
    },
    onError: (err: any) => toast.error(err?.message || 'Realized gain fetch failed'),
  })

  useEffect(() => {
    expectedMutation.mutate(debouncedParams)
  }, [debouncedParams, method])

  const compare = () => realizedMutation.mutate()

  const expected = expectedMutation.data?.data
  const realized = realizedMutation.data
  const annualExpected = expected?.annual_response || 0
  const annualRealized = realized?.gain_per_year || 0
  const delta = annualRealized - annualExpected

  const uncertainty = useMemo(() => {
    const cycles = realized?.cycles || []
    if (!cycles.length) return null
    const vals = cycles.map((c: any) => c.mean_value)
    const mean = vals.reduce((a: number, b: number) => a + b, 0) / vals.length
    const variance = vals.reduce((a: number, v: number) => a + (v - mean) ** 2, 0) / vals.length
    const sd = Math.sqrt(variance)
    const se = sd / Math.sqrt(vals.length)
    return { sd, se, ci95: 1.96 * se }
  }, [realized])

  useEffect(() => {
    if (!expected) return
    updateBreedingWorkflowState({
      geneticGain: {
        provenance: {
          run_id: `${programId || 'no-program'}-${Date.now()}`,
          model_version: 'breeders-equation:v2',
          seed: 0,
          timestamp: new Date().toISOString(),
          organization_id: String(user?.organization_id || 'unknown'),
          inputs: { method, params: debouncedParams, program_id: programId || null },
        },
          expected_gain: expected as unknown as Record<string, unknown>,
          realized_gain: realized ? (realized as unknown as Record<string, unknown>) : undefined,
          uncertainty: uncertainty || undefined,
      },
    })
  }, [expected, realized, uncertainty, programId, method, debouncedParams, user?.organization_id])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2"><Calculator className="h-8 w-8 text-primary" />Genetic Gain Calculator</h1>
          <p className="text-muted-foreground mt-1">Expected vs realized genetic gain with recalibration and uncertainty</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setParams({ selectionIntensity: 1.76, heritability: 0.35, phenotypicSD: 12.5, generationInterval: 4, accuracy: 0.7 })}><RefreshCw className="h-4 w-4 mr-2" />Reset</Button>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-primary text-primary-foreground"><CardContent className="p-4"><div className="flex items-center gap-3"><TrendingUp className="h-8 w-8" /><div><div className="text-3xl font-bold">{annualExpected.toFixed(2)}</div><div className="text-sm opacity-90">Expected Annual Gain</div></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><Target className="h-5 w-5 text-green-600" /><div><div className="text-2xl font-bold">{annualRealized.toFixed(2)}</div><div className="text-sm text-muted-foreground">Realized Annual Gain</div></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><Clock className="h-5 w-5 text-blue-600" /><div><div className="text-2xl font-bold">{delta.toFixed(2)}</div><div className="text-sm text-muted-foreground">Recalibration Delta</div></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><Dna className="h-5 w-5 text-purple-600" /><div><div className="text-2xl font-bold">{uncertainty ? `±${uncertainty.ci95.toFixed(2)}` : '—'}</div><div className="text-sm text-muted-foreground">95% CI</div></div></div></CardContent></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Breeder's Equation Parameters</CardTitle><CardDescription>ΔG = (i × h² × σp) / L with cycle-linked comparison</CardDescription></CardHeader>
          <CardContent className="space-y-6">
            <div className="grid md:grid-cols-2 gap-4">
              <div><Label>Comparison Program</Label><Select value={programId} onValueChange={setProgramId}><SelectTrigger><SelectValue placeholder="Select program" /></SelectTrigger><SelectContent>{programs.map((p: any) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent></Select></div>
              <div className="flex items-end"><Button className="w-full" onClick={compare} disabled={realizedMutation.isPending || !programId}>{realizedMutation.isPending ? 'Loading realized...' : 'Load Realized Gain'}</Button></div>
            </div>

            <div className="flex gap-4 mb-2">
              <Button variant={method === 'phenotypic' ? 'default' : 'outline'} onClick={() => setMethod('phenotypic')}>Phenotypic Selection</Button>
              <Button variant={method === 'genomic' ? 'default' : 'outline'} onClick={() => setMethod('genomic')}>Genomic Selection</Button>
            </div>

            <div className="space-y-4">
              <div><div className="flex items-center justify-between"><Label>Selection Intensity (i)</Label><span className="font-mono text-sm">{params.selectionIntensity.toFixed(2)}</span></div><Slider value={[params.selectionIntensity]} onValueChange={([v]) => setParams({ ...params, selectionIntensity: v })} min={0.5} max={3} step={0.01} /></div>
              <div><div className="flex items-center justify-between"><Label>Heritability (h²)</Label><span className="font-mono text-sm">{params.heritability.toFixed(2)}</span></div><Slider value={[params.heritability]} onValueChange={([v]) => setParams({ ...params, heritability: v })} min={0.05} max={0.95} step={0.01} /></div>
              <div><div className="flex items-center justify-between"><Label>Phenotypic SD (σp)</Label><span className="font-mono text-sm">{params.phenotypicSD.toFixed(1)}</span></div><Slider value={[params.phenotypicSD]} onValueChange={([v]) => setParams({ ...params, phenotypicSD: v })} min={1} max={50} step={0.5} /></div>
              <div><div className="flex items-center justify-between"><Label>Generation Interval (L)</Label><span className="font-mono text-sm">{params.generationInterval}</span></div><Slider value={[params.generationInterval]} onValueChange={([v]) => setParams({ ...params, generationInterval: v })} min={1} max={10} step={0.5} /></div>
              {method === 'genomic' && <div><div className="flex items-center justify-between"><Label>Prediction Accuracy (r)</Label><span className="font-mono text-sm">{params.accuracy.toFixed(2)}</span></div><Slider value={[params.accuracy]} onValueChange={([v]) => setParams({ ...params, accuracy: v })} min={0.1} max={0.95} step={0.01} /></div>}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Lineage & Uncertainty</CardTitle><CardDescription>Run provenance and parameter sourcing</CardDescription></CardHeader>
          <CardContent className="text-xs space-y-2">
            <p>Method: <strong>{method}</strong></p>
            <p>Program linked: <strong>{programId || 'none'}</strong></p>
            <p>Expected formula: <strong>{expected?.formula || 'n/a'}</strong></p>
            <p>Uncertainty: <strong>{uncertainty ? `SD=${uncertainty.sd.toFixed(3)}, CI95=±${uncertainty.ci95.toFixed(3)}` : 'not available (needs cycle data)'}</strong></p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
