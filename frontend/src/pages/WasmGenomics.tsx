import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Checkbox } from '@/components/ui/checkbox'
import { Cpu, CheckCircle2, XCircle, Dna } from 'lucide-react'
import { useWasm } from '@/wasm/hooks'
import { apiClient } from '@/lib/api-client'
import { useAuthStore } from '@/store/auth'
import { updateBreedingWorkflowState } from '@/lib/breeding-workflow'

function WasmGenomics() {
  const { isLoading, isReady, version, error: wasmError } = useWasm()
  const user = useAuthStore((state) => state.user)
  const [variantSetId, setVariantSetId] = useState('')
  const [ops, setOps] = useState<Array<'grm' | 'pca' | 'ld'>>(['grm', 'pca'])
  const [mafThreshold, setMafThreshold] = useState(0.05)
  const [missingnessThreshold, setMissingnessThreshold] = useState(0.1)
  const [runError, setRunError] = useState<string | null>(null)
  const [runResult, setRunResult] = useState<any>(null)

  const { data: variantSetsData } = useQuery({
    queryKey: ['wasm-genomics', 'variant-sets'],
    queryFn: () => apiClient.genotypingService.getVariantSets({ pageSize: 100 }),
  })

  const runMutation = useMutation({
    mutationFn: async () => {
      if (!variantSetId) throw new Error('Select a variant set dataset')
      const response = await apiClient.genomicsPipelineService.runWasmGenomics({
        variant_set_id: variantSetId,
        operations: ops,
        qc: { missingness_threshold: missingnessThreshold, maf_threshold: mafThreshold, imputation: 'mean' },
      })
      if (!response?.run_id || !response?.model_version || response?.seed === undefined) {
        throw new Error('Genomics run missing provenance fields')
      }
      await apiClient.genomicsPipelineService.persistArtifacts({
        analysis_type: 'genomics',
        run_id: String(response.run_id),
        provenance: {
          run_id: String(response.run_id),
          model_version: String(response.model_version),
          seed: Number(response.seed),
          timestamp: new Date().toISOString(),
          organization_id: String(user?.organization_id || 'unknown'),
        },
        artifacts: {
          grm_id: response.grm_id,
          pca_id: response.pca_id,
          ld_id: response.ld_id,
          qc_log_id: response.qc_log_id,
        },
      })
      updateBreedingWorkflowState({
        genomicsAnalysis: {
          provenance: {
            run_id: String(response.run_id),
            model_version: String(response.model_version),
            seed: Number(response.seed),
            timestamp: new Date().toISOString(),
            organization_id: String(user?.organization_id || 'unknown'),
            inputs: { variant_set_id: variantSetId, operations: ops },
          },
          qc: response.qc,
          artifacts: {
            grm_id: response.grm_id,
            pca_id: response.pca_id,
            ld_id: response.ld_id,
          },
        },
      })
      return response
    },
    onSuccess: (res) => {
      setRunError(null)
      setRunResult(res)
    },
    onError: (e: any) => setRunError(e?.message || 'WASM genomics run failed'),
  })

  const toggleOp = (op: 'grm' | 'pca' | 'ld') => {
    setOps((prev) => (prev.includes(op) ? prev.filter((x) => x !== op) : [...prev, op]))
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2"><Cpu className="h-8 w-8 text-orange-500" />Dataset-driven Genomics (WASM)</h1>
          <p className="text-muted-foreground mt-1">QC-first GRM/PCA/LD computations with persisted artifacts</p>
        </div>
        {isLoading ? <Badge variant="secondary">Loading...</Badge> : isReady ? <Badge className="bg-green-500"><CheckCircle2 className="h-3 w-3 mr-1" />WASM v{version}</Badge> : <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Engine Not Available</Badge>}
      </div>

      {wasmError && <Alert variant="destructive"><AlertDescription>{wasmError.message}</AlertDescription></Alert>}
      {runError && <Alert variant="destructive"><AlertDescription>{runError}</AlertDescription></Alert>}

      <Card>
        <CardHeader><CardTitle>Run Configuration</CardTitle><CardDescription>Select real dataset and analysis operations</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Variant Set</Label>
            <select className="w-full border rounded px-3 py-2 mt-1" value={variantSetId} onChange={(e) => setVariantSetId(e.target.value)}>
              <option value="">Select dataset</option>
              {(variantSetsData?.result?.data || []).map((vs: any) => <option key={vs.variantSetDbId} value={String(vs.variantSetDbId)}>{vs.variantSetName}</option>)}
            </select>
          </div>
          <div className="flex gap-6">
            {(['grm', 'pca', 'ld'] as const).map((op) => (
              <label key={op} className="flex items-center gap-2 text-sm">
                <Checkbox checked={ops.includes(op)} onCheckedChange={() => toggleOp(op)} /> {op.toUpperCase()}
              </label>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><Label>MAF Threshold</Label><input type="number" step="0.01" className="w-full border rounded px-2 py-1" value={mafThreshold} onChange={e => setMafThreshold(Number(e.target.value) || 0.05)} /></div>
            <div><Label>Missingness Threshold</Label><input type="number" step="0.01" className="w-full border rounded px-2 py-1" value={missingnessThreshold} onChange={e => setMissingnessThreshold(Number(e.target.value) || 0.1)} /></div>
          </div>
          <Button onClick={() => runMutation.mutate()} disabled={!isReady || runMutation.isPending}>{runMutation.isPending ? 'Running...' : 'Run Genomics Pipeline'}</Button>
        </CardContent>
      </Card>

      <Tabs defaultValue="results" className="space-y-4">
        <TabsList>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="qc">QC Log</TabsTrigger>
        </TabsList>
        <TabsContent value="results">
          <Card>
            <CardHeader><CardTitle>Persisted Artifacts</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm">
              {runResult ? (
                <>
                  <p><strong>Run ID:</strong> {runResult.run_id}</p>
                  <p><strong>Model:</strong> {runResult.model_version}</p>
                  <p><strong>GRM:</strong> {runResult.grm_id || 'n/a'}</p>
                  <p><strong>PCA:</strong> {runResult.pca_id || 'n/a'}</p>
                  <p><strong>LD:</strong> {runResult.ld_id || 'n/a'}</p>
                </>
              ) : (
                <p className="text-muted-foreground">No run yet</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="qc">
          <Card>
            <CardHeader><CardTitle>QC Summary</CardTitle></CardHeader>
            <CardContent className="text-sm">
              {runResult?.qc ? <pre className="bg-muted p-3 rounded overflow-auto">{JSON.stringify(runResult.qc, null, 2)}</pre> : <p className="text-muted-foreground">QC log will appear after run</p>}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Dna className="h-5 w-5" />Downstream Handoff</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Genomics run provenance and artifact IDs are persisted for use in parent selection and cross prediction workflows.
        </CardContent>
      </Card>
    </div>
  )
}

export default WasmGenomics
export { WasmGenomics }
