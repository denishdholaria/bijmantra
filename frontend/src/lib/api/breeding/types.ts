export interface BreedingScheme {
  id: string;
  name: string;
  type: "MABC" | "MARS" | "GS" | "Speed";
  status: "active" | "completed" | "planned";
  generation: string;
  progress: number;
  target_traits: string[];
  crop?: string;
  start_date?: string;
  end_date?: string;
}

export interface IntrogressionLine {
  id: string;
  name: string;
  donor: string;
  recurrent: string;
  target_gene: string;
  bc_generation: number;
  rp_recovery: number;
  foreground_status: "fixed" | "segregating" | "absent";
  scheme_id?: string;
}

export interface MolecularBreedingStatistics {
  total_schemes: number;
  active_schemes: number;
  total_lines: number;
  fixed_lines: number;
  target_genes: number;
  avg_progress: number;
}

export interface HaplotypeBlock {
  id: string;
  block_id: string;
  chromosome: string;
  start_mb: number;
  end_mb: number;
  length_kb: number;
  n_markers: number;
  n_haplotypes: number;
  major_haplotype: string;
  major_haplotype_freq: number;
  diversity: number;
  trait?: string;
}

export interface Haplotype {
  haplotype_id: string;
  block_id: string;
  allele_string: string;
  frequency: number;
  effect?: number;
  germplasm?: string[];
}

export interface HaplotypeDiversitySummary {
  total_blocks: number;
  avg_diversity: number;
  avg_haplotypes_per_block: number;
  total_haplotypes: number;
  chromosomes_covered: number;
  avg_block_length_kb: number;
}

export interface HaplotypeStatistics {
  total_blocks: number;
  total_haplotypes: number;
  total_associations: number;
  favorable_haplotypes: number;
  avg_block_length_kb: number;
  avg_markers_per_block: number;
}

export interface QTL {
  id: string;
  name: string;
  trait: string;
  chromosome: string;
  position: number;
  lod: number;
  pve: number;
  add_effect: number;
  confidence_interval?: [number, number];
  flanking_markers?: string[];
  population?: string;
}

export interface GWASAssociation {
  marker: string;
  trait: string;
  chromosome: string;
  position: number;
  p_value: number;
  log_p: number;
  effect: number;
  maf: number;
}

export interface QTLSummary {
  total_qtls: number;
  major_qtls: number;
  total_pve: number;
  average_lod: number;
  traits_analyzed: number;
}

export interface CandidateGene {
  gene_id: string;
  name: string;
  chromosome: string;
  start: number;
  end: number;
  function?: string;
  annotation?: string;
}

export interface GOEnrichment {
  term_id: string;
  name: string;
  p_value: number;
  gene_count: number;
  category: string;
}
