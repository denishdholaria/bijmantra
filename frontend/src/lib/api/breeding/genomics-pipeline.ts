import { ApiClientCore } from '../core/client'

export interface GenomicsRunProvenance {
  run_id: string
  model_version: string
  seed: number
  timestamp: string
  organization_id: string
}

export interface GenomicsQCConfig {
  missingness_threshold: number
  maf_threshold: number
  imputation: 'none' | 'mean'
}

export class GenomicsPipelineService {
  constructor(private client: ApiClientCore) {}

  async runQtlAnalysis(payload: {
    run_name: string
    trait_name: string
    method: 'glm' | 'mlm'
    variant_set_id: number
    phenotype_data: Record<string, number>
    qc: GenomicsQCConfig
  }) {
    return this.client.post<any>('/api/v2/bio-analytics/qtl/run-from-storage', payload)
  }

  async runWasmGenomics(payload: {
    variant_set_id: string
    operations: Array<'grm' | 'pca' | 'ld'>
    qc: GenomicsQCConfig
  }) {
    return this.client.post<any>('/api/v2/genomics-pipeline/wasm/run', payload)
  }

  async runGxeMet(payload: {
    study_db_ids: string[]
    trait_db_id: string
    method: 'ammi' | 'gge'
    include_covariates: boolean
  }) {
    return this.client.post<any>('/api/v2/gxe/analyze-from-db', payload)
  }

  async persistArtifacts(payload: {
    analysis_type: 'qtl' | 'genomics' | 'gxe'
    run_id: string
    provenance: GenomicsRunProvenance
    artifacts: Record<string, unknown>
  }) {
    return this.client.post<any>('/api/v2/analytics/artifacts/persist', payload)
  }
}
