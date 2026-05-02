/**
 * G×E Interaction Analysis Page
 * Dataset-driven MET analysis with persisted artifacts and provenance
 */
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { apiClient, type GxEResult } from '@/lib/api-client'
import { GxEFromDbRequest } from '@/lib/api/breeding/gxe-analysis'
import { updateBreedingWorkflowState } from '@/lib/breeding-workflow'
import { useAuthStore } from '@/store/auth'

export function GxEInteraction() {
  const [activeTab, setActiveTab] = useState('anova')
  const [selectedTrait, setSelectedTrait] = useState('')
  const [selectedStudyIds, setSelectedStudyIds] = useState<string[]>([])
  const [analysisResult, setAnalysisResult] = useState<GxEResult | null>(null)
  const [runError, setRunError] = useState<string | null>(null)
  const [method, setMethod] = useState<'ammi' | 'gge'>('ammi')
  const user = useAuthStore((state) => state.user)

  const { data: methodsData } = useQuery({ queryKey: ['gxe-methods'], queryFn: () => apiClient.gxeAnalysisService.getMethods(), staleTime: 1000 * 60 * 60 })
  const { data: studiesData } = useQuery({ queryKey: ['studies'], queryFn: () => apiClient.studyService.getStudies(0, 50), staleTime: 1000 * 60 * 5 })
  const { data: traitsData } = useQuery({ queryKey: ['traits'], queryFn: () => apiClient.observationService.getObservationVariables(0, 50), staleTime: 1000 * 60 * 60 })
  const studies = studiesData?.result?.data || []
  const traits = traitsData?.result?.data || []

  const analysisMutation = useMutation({
    mutationFn: async (data: GxEFromDbRequest) => apiClient.genomicsPipelineService.runGxeMet({
      study_db_ids: data.study_db_ids,
      trait_db_id: data.trait_db_id,
      method: data.method as 'ammi' | 'gge',
      include_covariates: true,
    }),
    onSuccess: async (results: any) => {
      if (!results?.run_id || !results?.model_version || results?.seed === undefined) {
        setRunError('GxE response missing provenance fields (run_id/model_version/seed).')
        return
      }
      setRunError(null)
      setAnalysisResult(results as GxEResult)
      updateBreedingWorkflowState({
        gxeAnalysis: {
          provenance: {
            run_id: String(results.run_id),
            model_version: String(results.model_version),
            seed: Number(results.seed),
            timestamp: new Date().toISOString(),
            organization_id: String(user?.organization_id || 'unknown'),
            inputs: { study_db_ids: selectedStudyIds, trait_db_id: selectedTrait, method },
          },
          artifacts: {
            anova: results.anova,
            genotype_scores: results.genotype_scores,
            environment_scores: results.environment_scores,
            variance_explained: results.variance_explained,
          },
          target_environment_recommendation: results.target_environment_recommendation,
        },
      })
      await apiClient.genomicsPipelineService.persistArtifacts({
        analysis_type: 'gxe',
        run_id: String(results.run_id),
        provenance: {
          run_id: String(results.run_id),
          model_version: String(results.model_version),
          seed: Number(results.seed),
          timestamp: new Date().toISOString(),
          organization_id: String(user?.organization_id || 'unknown'),
        },
        artifacts: {
          recommendation: results.target_environment_recommendation,
          variance_explained: results.variance_explained,
        },
      })
      toast.success('Analysis completed successfully')
    },
    onError: (err) => {
      console.error(err)
      setRunError(err instanceof Error ? err.message : 'Unknown error')
      toast.error('Analysis failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
    },
  })

  const handleRunAnalysis = () => {
    if (selectedStudyIds.length < 2) return toast.error('Please select at least 2 studies/environments')
    if (!selectedTrait) return toast.error('Please select a trait')
    analysisMutation.mutate({ study_db_ids: selectedStudyIds, trait_db_id: selectedTrait, method, n_components: 2 })
  }

  const toggleStudy = (id: string) => {
    setSelectedStudyIds((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]))
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">G×E Interaction Analysis</h1>
          <p className="text-muted-foreground mt-1">Dataset-driven MET analysis with covariates and recommendations</p>
        </div>
      </div>

      {runError && <Alert variant="destructive"><AlertDescription>{runError}</AlertDescription></Alert>}

      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-7 gap-6">
            <div className="md:col-span-3 space-y-2">
              <p className="text-sm font-medium">Studies (Environments)</p>
              <ScrollArea className="h-40 border rounded-md p-2">
                {studies.map((s: any) => (
                  <div key={s.studyDbId} className="flex items-center gap-2 py-1">
                    <Checkbox checked={selectedStudyIds.includes(s.studyDbId)} onCheckedChange={() => toggleStudy(s.studyDbId)} />
                    <span className="text-sm">{s.studyName}</span>
                  </div>
                ))}
              </ScrollArea>
            </div>
            <div className="md:col-span-2 space-y-2">
              <p className="text-sm font-medium">Trait</p>
              <Select value={selectedTrait} onValueChange={setSelectedTrait}>
                <SelectTrigger><SelectValue placeholder="Select trait" /></SelectTrigger>
                <SelectContent>
                  {traits.map((trait: any) => <SelectItem key={trait.observationVariableDbId} value={trait.observationVariableDbId}>{trait.observationVariableName}</SelectItem>)}
                </SelectContent>
              </Select>
              <p className="text-sm font-medium">Method</p>
              <Select value={method} onValueChange={(v) => setMethod(v as 'ammi' | 'gge')}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(methodsData?.methods || []).filter((m: any) => m.id === 'ammi' || m.id === 'gge').map((m: any) => <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>)}
                </SelectContent>
              </Select>
              <Button className="w-full" onClick={handleRunAnalysis} disabled={analysisMutation.isPending}>{analysisMutation.isPending ? 'Running...' : 'Run G×E Analysis'}</Button>
            </div>
            <div className="md:col-span-2 border-l pl-4 text-sm text-muted-foreground">
              <p>Environments: <strong>{selectedStudyIds.length}</strong></p>
              <p>Method: <strong>{method.toUpperCase()}</strong></p>
              <p>Covariates: <strong>Enabled</strong></p>
              <p>No demo mode in production flow.</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-4 text-center"><p className="text-3xl font-bold text-primary">{analysisResult?.genotype_scores?.length || 0}</p><p className="text-sm text-muted-foreground">Genotypes</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-3xl font-bold text-blue-600">{analysisResult?.environment_scores?.length || 0}</p><p className="text-sm text-muted-foreground">Environments</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-3xl font-bold text-green-600">{analysisResult?.genotype_scores?.length ? (analysisResult.genotype_scores.reduce((a, c) => a + c.mean, 0) / analysisResult.genotype_scores.length).toFixed(2) : '0.00'}</p><p className="text-sm text-muted-foreground">Grand Mean</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-3xl font-bold text-purple-600">{analysisResult?.variance_explained?.[0]?.toFixed(1) || 0}%</p><p className="text-sm text-muted-foreground">PC1 Variance</p></CardContent></Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList><TabsTrigger value="anova">ANOVA</TabsTrigger><TabsTrigger value="biplot">AMMI/GGE Biplot</TabsTrigger><TabsTrigger value="stability">Recommendation</TabsTrigger></TabsList>
        <TabsContent value="anova" className="mt-4">
          <Card><CardHeader><CardTitle>Combined ANOVA</CardTitle></CardHeader><CardContent>{analysisResult?.anova ? <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="text-left p-2">Source</th><th className="text-right p-2">DF</th><th className="text-right p-2">SS</th><th className="text-right p-2">MS</th></tr></thead><tbody>{analysisResult.anova.map((r, i) => <tr key={i} className="border-b"><td className="p-2">{r.source}</td><td className="p-2 text-right">{r.df}</td><td className="p-2 text-right">{r.ss.toFixed(1)}</td><td className="p-2 text-right">{r.ms.toFixed(2)}</td></tr>)}</tbody></table></div> : <p className="text-muted-foreground">Run analysis to see ANOVA.</p>}</CardContent></Card>
        </TabsContent>
        <TabsContent value="biplot" className="mt-4">
          <Card><CardHeader><CardTitle>Biplot</CardTitle></CardHeader><CardContent><p className="text-sm text-muted-foreground">Genotype and environment scores persisted in run artifacts.</p></CardContent></Card>
        </TabsContent>
        <TabsContent value="stability" className="mt-4">
          <Card><CardHeader><CardTitle>Target Environment Recommendation</CardTitle></CardHeader><CardContent>{(analysisResult as any)?.target_environment_recommendation ? <pre className="bg-muted p-3 rounded overflow-auto text-xs">{JSON.stringify((analysisResult as any).target_environment_recommendation, null, 2)}</pre> : <p className="text-muted-foreground">No recommendation yet.</p>}</CardContent></Card>
        </TabsContent>
      </Tabs>

      {analysisResult && <Badge variant="outline">Persisted run: {(analysisResult as any).run_id || 'n/a'}</Badge>}
    </div>
  )
}
