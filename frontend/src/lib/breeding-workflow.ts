export interface RunProvenance {
  run_id: string
  model_version: string
  seed: number
  timestamp: string
  organization_id: string
  inputs: Record<string, unknown>
}

export interface BreedingWorkflowState {
  simulation?: {
    provenance: RunProvenance
    assumptions: string[]
    summary?: Record<string, unknown>
  }
  parentSelection?: {
    provenance: RunProvenance
    selected_parent_ids: string[]
    optimization: {
      gain_weight: number
      diversity_weight: number
      max_coancestry: number
    }
  }
  selectionIndex?: {
    provenance: RunProvenance
    index_definition: {
      name: string
      method: string
      version: string
      trait_weights: Record<string, number>
    }
  }
  crossPrediction?: {
    provenance: RunProvenance
    parent1_id: string
    parent2_id: string
    confidence?: number
    uncertainty?: string
  }
  qtlAnalysis?: {
    provenance: RunProvenance
    qc: {
      missingness_threshold: number
      maf_threshold: number
      filtered_markers?: number
    }
    artifacts?: Record<string, unknown>
  }
  genomicsAnalysis?: {
    provenance: RunProvenance
    qc?: Record<string, unknown>
    artifacts?: Record<string, unknown>
  }
  gxeAnalysis?: {
    provenance: RunProvenance
    artifacts?: Record<string, unknown>
    target_environment_recommendation?: Record<string, unknown>
  }

  trialDesign?: {
    provenance: RunProvenance
    design_type: string
    randomization_manifest?: Record<string, unknown>
    plot_book_payload?: Record<string, unknown>
  }
  geneticGain?: {
    provenance: RunProvenance
    expected_gain?: Record<string, unknown>
    realized_gain?: Record<string, unknown>
    uncertainty?: Record<string, unknown>
  }
}

const STORAGE_KEY = 'bijmantra.breeding.workflow.v1'

export function loadBreedingWorkflowState(): BreedingWorkflowState {
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (!raw) return {}
  try {
    return JSON.parse(raw) as BreedingWorkflowState
  } catch {
    return {}
  }
}

export function saveBreedingWorkflowState(next: BreedingWorkflowState) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
}

export function updateBreedingWorkflowState(partial: Partial<BreedingWorkflowState>) {
  const current = loadBreedingWorkflowState()
  const next = { ...current, ...partial }
  saveBreedingWorkflowState(next)
  return next
}
