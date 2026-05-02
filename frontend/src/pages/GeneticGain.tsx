/**
 * Genetic Gain Page
 * Cycle-linked realized vs expected gain with provenance + uncertainty
 */
import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import { useAuthStore } from '@/store/auth'
import { updateBreedingWorkflowState } from '@/lib/breeding-workflow'

export function GeneticGain() {
  const [programId, setProgramId] = useState('')
  const [yearsAhead, setYearsAhead] = useState(10)
  const user = useAuthStore((s) => s.user)

  const { data: programsData } = useQuery({ queryKey: ['genetic-gain', 'programs'], queryFn: () => apiClient.geneticGainService.getPrograms() })
  const programs = programsData?.data || []

  const gainMutation = useMutation({
    mutationFn: async () => {
      if (!programId) throw new Error('Select a breeding program')
      const [gain, projection] = await Promise.all([
        apiClient.geneticGainService.calculateGain(programId, true),
        apiClient.geneticGainService.getProjection(programId, yearsAhead),
      ])
      return { gain: gain.data, projection: projection.data }
    },
    onSuccess: ({ gain, projection }) => {
      const cycleMeans = gain.cycles.map((c) => c.mean_value)
      const mean = cycleMeans.reduce((a, b) => a + b, 0) / Math.max(1, cycleMeans.length)
      const variance = cycleMeans.reduce((a, v) => a + (v - mean) ** 2, 0) / Math.max(1, cycleMeans.length)
      const sd = Math.sqrt(variance)
      const se = sd / Math.sqrt(Math.max(1, cycleMeans.length))
      const uncertainty95 = 1.96 * se

      updateBreedingWorkflowState({
        geneticGain: {
          provenance: {
            run_id: `${programId}-${Date.now()}`,
            model_version: 'genetic-gain:v2',
            seed: 0,
            timestamp: new Date().toISOString(),
            organization_id: String(user?.organization_id || 'unknown'),
            inputs: { program_id: programId, years_ahead: yearsAhead },
          },
          expected_gain: projection as unknown as Record<string, unknown>,
          realized_gain: gain as unknown as Record<string, unknown>,
          uncertainty: { sd, se, ci95_half_width: uncertainty95 },
        },
      })
      toast.success('Genetic gain run completed')
    },
    onError: (e: any) => toast.error(e?.message || 'Gain calculation failed'),
  })

  const result = gainMutation.data?.gain
  const projection = gainMutation.data?.projection

  const realizedVsExpected = useMemo(() => {
    if (!result || !projection) return null
    const realized = result.gain_per_year
    const expected = projection.projected_gain_per_year || projection.gain_per_year || 0
    return {
      realized,
      expected,
      delta: realized - expected,
    }
  }, [result, projection])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Genetic Gain</h1>
          <p className="text-muted-foreground mt-1">Track realized versus expected gain by breeding cycle with uncertainty</p>
        </div>
        <Button onClick={() => gainMutation.mutate()} disabled={gainMutation.isPending}>📈 {gainMutation.isPending ? 'Computing...' : 'Calculate Gain'}</Button>
      </div>

      <Card>
        <CardHeader><CardTitle>Program Scope</CardTitle><CardDescription>Traceable metadata sourced from program records</CardDescription></CardHeader>
        <CardContent className="grid md:grid-cols-3 gap-4">
          <div>
            <Label>Program</Label>
            <Select value={programId} onValueChange={setProgramId}>
              <SelectTrigger><SelectValue placeholder="Select breeding program" /></SelectTrigger>
              <SelectContent>
                {programs.map((p: any) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Projection Horizon (years)</Label>
            <Input type="number" value={yearsAhead} onChange={(e) => setYearsAhead(Number(e.target.value) || 10)} />
          </div>
          <div className="text-sm text-muted-foreground flex items-end">Outputs include lineage and uncertainty (95% CI from cycle variance).</div>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader><CardTitle>Realized vs Expected Genetic Gain</CardTitle><CardDescription>Cycle-linked estimate and recalibration signal</CardDescription></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 bg-green-50 rounded-lg text-center"><p className="text-2xl font-bold text-green-700">{result.gain_per_year.toFixed(3)}</p><p className="text-sm text-green-600">Realized Gain/Year</p></div>
              <div className="p-4 bg-blue-50 rounded-lg text-center"><p className="text-2xl font-bold text-blue-700">{(realizedVsExpected?.expected || 0).toFixed(3)}</p><p className="text-sm text-blue-600">Expected Gain/Year</p></div>
              <div className="p-4 bg-purple-50 rounded-lg text-center"><p className="text-2xl font-bold text-purple-700">{(realizedVsExpected?.delta || 0).toFixed(3)}</p><p className="text-sm text-purple-600">Recalibration Delta</p></div>
              <div className="p-4 bg-orange-50 rounded-lg text-center"><p className="text-2xl font-bold text-orange-700">±{(((gainMutation.data as any)?.gain?.cycles || []).length ? (1.96 * Math.sqrt((((gainMutation.data as any).gain.cycles.map((c:any)=>c.mean_value).reduce((a:number,v:number)=>a+v,0)/(gainMutation.data as any).gain.cycles.length) || 0))) : 0).toFixed(3)}</p><p className="text-sm text-orange-600">95% CI (approx.)</p></div>
            </div>
            <pre className="bg-muted p-3 rounded overflow-auto text-xs">{JSON.stringify({ gain: result, projection, uncertainty: (gainMutation.data as any)?.gain ? 'Persisted in workflow.geneticGain.uncertainty' : null }, null, 2)}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
