// TypeScript types for Bijmantra Genomics WASM module

export interface AlleleFrequencies {
  minor_allele_freq: number[];
  major_allele_freq: number[];
  heterozygosity: number[];
  missing_rate: number[];
}

export interface LDResult {
  r_squared: number;
  d_prime: number;
  p_value: number;
}

export interface HWEResult {
  chi_squared: number;
  p_value: number;
  observed_het: number;
  expected_het: number;
  in_equilibrium: boolean;
}

export interface GRMResult {
  matrix: number[];
  n_samples: number;
  n_markers_used: number;
  mean_diagonal: number;
  mean_off_diagonal: number;
}

export interface EigenResult {
  eigenvalues: number[];
  explained_variance: number[];
  cumulative_variance: number[];
}

export interface BLUPResult {
  breeding_values: number[];
  reliability: number[];
  mean: number;
  variance: number;
  heritability: number;
}

export interface GBLUPResult {
  gebv: number[];
  reliability: number[];
  accuracy: number[];
  mean: number;
  genetic_variance: number;
  residual_variance: number;
}

export interface SelectionIndexResult {
  index_values: number[];
  rankings: number[];
  selection_differential: number;
  expected_response: number;
}

export interface GeneticCorrelationResult {
  correlation_matrix: number[];
  n_traits: number;
  trait_means: number[];
  trait_variances: number[];
}

export interface HeritabilityResult {
  heritability: number;
  genetic_variance: number;
  environmental_variance: number;
  phenotypic_variance: number;
  standard_error: number;
}

export interface DiversityMetrics {
  shannon_index: number;
  simpson_index: number;
  nei_diversity: number;
  observed_heterozygosity: number;
  expected_heterozygosity: number;
  inbreeding_coefficient: number;
  effective_alleles: number;
}

export interface FstResult {
  fst: number;
  fis: number;
  fit: number;
  per_marker_fst: number[];
}

export interface GeneticDistanceResult {
  distance_matrix: number[];
  n_samples: number;
  method: string;
}

export interface PCAResult {
  pc1: number[];
  pc2: number[];
  pc3: number[];
  variance_explained: number[];
}

export interface AMMIResult {
  genotype_means: number[];
  environment_means: number[];
  grand_mean: number;
  ipca1_genotype: number[];
  ipca1_environment: number[];
  ipca1_variance: number;
}

export interface AlignmentResult {
  score: number;
  align1: string;
  align2: string;
}

export interface MotifMatch {
  start: number;
  end: number;
  match_str: string;
}

// WASM module interface
export interface BijmantraGenomicsWasm {
  // Core
  get_version(): string;
  is_wasm_ready(): boolean;

  // Genomics
  calculate_allele_frequencies(genotypes: Int32Array, n_samples: number, n_markers: number): AlleleFrequencies;
  calculate_ld_pair(geno1: Int32Array, geno2: Int32Array): LDResult;
  calculate_ld_matrix(genotypes: Int32Array, n_samples: number, n_markers: number): Float64Array;
  test_hwe(genotypes: Int32Array): HWEResult;
  filter_by_maf(genotypes: Int32Array, n_samples: number, n_markers: number, min_maf: number): Uint32Array;
  impute_missing_mean(genotypes: Int32Array, n_samples: number, n_markers: number): Float64Array;

  // Sequence Algorithms
  needleman_wunsch(seq1: string, seq2: string, match_score: number, mismatch_score: number, gap_penalty: number): AlignmentResult;
  smith_waterman(seq1: string, seq2: string, match_score: number, mismatch_score: number, gap_penalty: number): AlignmentResult;
  search_motif(genome: string, motif: string): MotifMatch[];

  // Matrix operations
  calculate_g_matrix(markers: Uint8Array, n_markers: number, n_individuals: number): Float32Array;
  calculate_grm(genotypes: Int32Array, n_samples: number, n_markers: number): GRMResult;
  calculate_a_matrix(sire_ids: Int32Array, dam_ids: Int32Array): Float64Array;
  calculate_kinship(geno1: Int32Array, geno2: Int32Array): number;
  calculate_ibs_matrix(genotypes: Int32Array, n_samples: number, n_markers: number): Float64Array;
  calculate_eigenvalues(matrix: Float64Array, n: number, k: number): EigenResult;

  // Statistics
  estimate_blup(phenotypes: Float64Array, relationship_matrix: Float64Array, n_individuals: number, heritability: number): BLUPResult;
  estimate_gblup(phenotypes: Float64Array, grm: Float64Array, n_individuals: number, heritability: number): GBLUPResult;
  calculate_selection_index(trait_values: Float64Array, economic_weights: Float64Array, n_individuals: number, n_traits: number): SelectionIndexResult;
  calculate_genetic_correlations(trait_values: Float64Array, n_individuals: number, n_traits: number): GeneticCorrelationResult;
  estimate_heritability(phenotypes: Float64Array, grm: Float64Array, n_individuals: number): HeritabilityResult;

  // Population genetics
  calculate_diversity(genotypes: Int32Array, n_samples: number, n_markers: number): DiversityMetrics;
  calculate_fst(genotypes: Int32Array, population_ids: Int32Array, n_samples: number, n_markers: number): FstResult;
  calculate_genetic_distance(genotypes: Int32Array, n_samples: number, n_markers: number): GeneticDistanceResult;
  calculate_pca(genotypes: Int32Array, n_samples: number, n_markers: number): PCAResult;
  calculate_ammi(phenotypes: Float64Array, n_genotypes: number, n_environments: number): AMMIResult;
}
