/**
 * QTL Mapping Interface
 * Dataset-driven QTL/GWAS execution with persisted provenance
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { apiClient, GOEnrichment } from '@/lib/api-client'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useToast } from '@/hooks/use-toast'
import { updateBreedingWorkflowState } from '@/lib/breeding-workflow'
import { useAuthStore } from '@/store/auth'

export function QTLMapping() {
  const [analysisType, setAnalysisType] = useState('linkage')
  const [selectedTrait, setSelectedTrait] = useState('all')
  const [lodThreshold, setLodThreshold] = useState([3.0])
  const [pThreshold, setPThreshold] = useState([5])
  const { toast } = useToast()
  const user = useAuthStore((state) => state.user)

  const [openGWAS, setOpenGWAS] = useState(false)
  const [runningGWAS, setRunningGWAS] = useState(false)
  const [runError, setRunError] = useState<string | null>(null)
  const [lastRunId, setLastRunId] = useState<string | null>(null)
  const [gwasConfig, setGwasConfig] = useState({
    run_name: `QTL_Run_${new Date().toISOString().split('T')[0]}`,
    trait_name: 'Yield',
    method: 'mlm',
    variant_set_id: '',
    phenotype_json: '{"sample_1": 5.2, "sample_2": 4.8}',
    missingness_threshold: 0.1,
    maf_threshold: 0.05,
  })

  const { data: variantSetsData } = useQuery({
    queryKey: ['qtl-mapping', 'variant-sets'],
    queryFn: () => apiClient.genotypingService.getVariantSets({ pageSize: 100 }),
  })
  const trainableVariantSets = (variantSetsData?.result?.data || []).filter((variantSet: any) => Boolean(variantSet.variantSetDbId))

  const handleRunGWAS = async () => {
    setRunningGWAS(true)
    setRunError(null)
    try {
      if (!gwasConfig.variant_set_id) {
        throw new Error('Select a variant set dataset')
      }
      const phenotypeData = JSON.parse(gwasConfig.phenotype_json) as Record<string, number>
      const res = await apiClient.genomicsPipelineService.runQtlAnalysis({
        run_name: gwasConfig.run_name,
        trait_name: gwasConfig.trait_name,
        method: gwasConfig.method as 'glm' | 'mlm',
        variant_set_id: Number(gwasConfig.variant_set_id),
        phenotype_data: phenotypeData,
        qc: {
          missingness_threshold: gwasConfig.missingness_threshold,
          maf_threshold: gwasConfig.maf_threshold,
          imputation: 'mean',
        },
      })

      if (!res?.run_id || !res?.model_version || res?.seed === undefined) {
        throw new Error('QTL run missing provenance fields')
      }

      setLastRunId(String(res.run_id))
      updateBreedingWorkflowState({
        qtlAnalysis: {
          provenance: {
            run_id: String(res.run_id),
            model_version: String(res.model_version),
            seed: Number(res.seed),
            timestamp: new Date().toISOString(),
            organization_id: String(user?.organization_id || 'unknown'),
            inputs: {
              variant_set_id: gwasConfig.variant_set_id,
              trait_name: gwasConfig.trait_name,
              method: gwasConfig.method,
            },
          },
          qc: {
            missingness_threshold: gwasConfig.missingness_threshold,
            maf_threshold: gwasConfig.maf_threshold,
            filtered_markers: res.filtered_markers,
          },
          artifacts: {
            manhattan_plot_url: res.manhattan_plot_url,
            qq_plot_url: res.qq_plot_url,
            hits_table_id: res.hits_table_id,
          },
        },
      })

      await apiClient.genomicsPipelineService.persistArtifacts({
        analysis_type: 'qtl',
        run_id: String(res.run_id),
        provenance: {
          run_id: String(res.run_id),
          model_version: String(res.model_version),
          seed: Number(res.seed),
          timestamp: new Date().toISOString(),
          organization_id: String(user?.organization_id || 'unknown'),
        },
        artifacts: {
          manhattan_plot_url: res.manhattan_plot_url,
          qq_plot_url: res.qq_plot_url,
          significant_markers: res.significant_markers,
        },
      })

      toast({ title: 'QTL analysis complete', description: `Run ${res.run_id} persisted with QC metadata.` })
      setOpenGWAS(false)
    } catch (err: any) {
      setRunError(err?.message || 'QTL run failed')
      toast({ title: 'Analysis Failed', description: err?.message || 'Unknown error', variant: 'destructive' })
    } finally {
      setRunningGWAS(false)
    }
  }

  const { data: traitsData } = useQuery({ queryKey: ['qtl-mapping', 'traits'], queryFn: () => apiClient.qtlMappingService.getTraits() })
  const { data: qtlsData, isLoading: loadingQTLs } = useQuery({
    queryKey: ['qtl-mapping', 'qtls', selectedTrait, lodThreshold[0]],
    queryFn: () => apiClient.qtlMappingService.getQTLs({ trait: selectedTrait !== 'all' ? selectedTrait : undefined, min_lod: lodThreshold[0] }),
  })
  const { data: gwasData, isLoading: loadingGWAS } = useQuery({
    queryKey: ['qtl-mapping', 'gwas', selectedTrait, pThreshold[0]],
    queryFn: () => apiClient.qtlMappingService.getGWASResults({ trait: selectedTrait !== 'all' ? selectedTrait : undefined, min_log_p: pThreshold[0] }),
  })
  const { data: qtlSummary } = useQuery({ queryKey: ['qtl-mapping', 'summary', 'qtl'], queryFn: () => apiClient.qtlMappingService.getQTLSummary() })
  const { data: goData } = useQuery({ queryKey: ['qtl-mapping', 'go-enrichment'], queryFn: () => apiClient.qtlMappingService.getGOEnrichment() })

  const traits: string[] = traitsData?.traits || []
  const qtls: any[] = qtlsData?.qtls || []
  const gwasResults: any[] = gwasData?.associations || []
  const goEnrichment: GOEnrichment[] = goData?.enrichment || []

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">QTL Mapping</h1>
          <p className="text-muted-foreground mt-1">Marker-trait association and QTL analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedTrait} onValueChange={setSelectedTrait}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Select trait" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Traits</SelectItem>
              {traits.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
            </SelectContent>
          </Select>
          <Dialog open={openGWAS} onOpenChange={setOpenGWAS}>
            <DialogTrigger asChild><Button>Run Analysis</Button></DialogTrigger>
            <DialogContent className="max-h-[80vh] overflow-y-auto">
              <DialogHeader><DialogTitle>Run dataset-driven GWAS/QTL</DialogTitle><DialogDescription>No synthetic data paths.</DialogDescription></DialogHeader>
              <div className="grid gap-3 py-2">
                <Label>Run Name</Label><Input value={gwasConfig.run_name} onChange={e => setGwasConfig({ ...gwasConfig, run_name: e.target.value })} />
                <Label>Trait Name</Label><Input value={gwasConfig.trait_name} onChange={e => setGwasConfig({ ...gwasConfig, trait_name: e.target.value })} />
                <Label>Variant Set Dataset</Label>
                <Select value={gwasConfig.variant_set_id} onValueChange={e => setGwasConfig({ ...gwasConfig, variant_set_id: e })}>
                  <SelectTrigger><SelectValue placeholder="Select Variant Set" /></SelectTrigger>
                  <SelectContent>
                    {trainableVariantSets.length > 0 ? trainableVariantSets.map((vs: any) => (
                      <SelectItem key={vs.variantSetDbId} value={String(vs.variantSetDbId)}>{vs.variantSetName}</SelectItem>
                    )) : <SelectItem value="__none" disabled>No runnable variant sets available</SelectItem>}
                  </SelectContent>
                </Select>
                <Label>Method</Label>
                <Select value={gwasConfig.method} onValueChange={e => setGwasConfig({ ...gwasConfig, method: e })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="glm">GLM</SelectItem><SelectItem value="mlm">MLM</SelectItem></SelectContent>
                </Select>
                <Label>Phenotype Map (JSON sample_id→value)</Label>
                <Textarea value={gwasConfig.phenotype_json} onChange={e => setGwasConfig({ ...gwasConfig, phenotype_json: e.target.value })} rows={5} />
                <Label>Missingness Threshold ({gwasConfig.missingness_threshold.toFixed(2)})</Label>
                <Slider value={[gwasConfig.missingness_threshold * 100]} onValueChange={([v]) => setGwasConfig({ ...gwasConfig, missingness_threshold: v / 100 })} min={0} max={50} step={1} />
                <Label>MAF Threshold ({gwasConfig.maf_threshold.toFixed(2)})</Label>
                <Slider value={[gwasConfig.maf_threshold * 100]} onValueChange={([v]) => setGwasConfig({ ...gwasConfig, maf_threshold: v / 100 })} min={0} max={50} step={1} />
                <Button onClick={handleRunGWAS} disabled={runningGWAS}>{runningGWAS ? 'Running...' : 'Start Analysis'}</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {runError && <Alert variant="destructive"><AlertDescription>{runError}</AlertDescription></Alert>}
      {lastRunId && <p className="text-xs text-muted-foreground">Latest persisted QTL run: {lastRunId}</p>}

      {qtlSummary && <div className="grid grid-cols-2 md:grid-cols-5 gap-4"><Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-primary">{qtlSummary.total_qtls}</p><p className="text-xs text-muted-foreground">Total QTLs</p></CardContent></Card></div>}

      <Tabs value={analysisType} onValueChange={setAnalysisType}>
        <TabsList>
          <TabsTrigger value="linkage">Linkage Mapping</TabsTrigger>
          <TabsTrigger value="gwas">GWAS</TabsTrigger>
          <TabsTrigger value="candidates">Candidate Genes</TabsTrigger>
        </TabsList>
        <TabsContent value="linkage" className="space-y-4 mt-4">
          <Card><CardHeader><CardTitle>Linkage QTL Hits</CardTitle></CardHeader><CardContent>{loadingQTLs ? <Skeleton className="h-24" /> : qtls.slice(0, 15).map((q, i) => <div key={i} className="flex justify-between border-b py-2 text-sm"><span>{q.trait || q.name || 'QTL'}</span><Badge>{q.lod || 'n/a'} LOD</Badge></div>)}</CardContent></Card>
        </TabsContent>
        <TabsContent value="gwas" className="space-y-4 mt-4">
          <Card><CardHeader><CardTitle>GWAS Associations</CardTitle><CardDescription>Threshold: -log10(p) ≥ {pThreshold[0]}</CardDescription></CardHeader><CardContent><Slider value={pThreshold} onValueChange={setPThreshold} min={3} max={12} step={0.5} />{loadingGWAS ? <Skeleton className="h-24 mt-3" /> : gwasResults.slice(0, 20).map((a, i) => <div key={i} className="flex justify-between border-b py-2 text-sm"><span>{a.marker || a.snp || 'marker'}</span><Badge variant="outline">{a.log_p || a.neg_log10_p || 'n/a'}</Badge></div>)}</CardContent></Card>
        </TabsContent>
        <TabsContent value="candidates" className="space-y-4 mt-4">
          <Card><CardHeader><CardTitle>GO Enrichment</CardTitle></CardHeader><CardContent>{goEnrichment.length > 0 ? goEnrichment.slice(0, 10).map((g) => <div key={g.go_id} className="text-sm py-1">{g.term}: {g.p_value}</div>) : <p className="text-sm text-muted-foreground">No GO enrichment results available.</p>}</CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
