import { ApiClientCore } from "../core/client";

export class TrialDesignService {
  constructor(private client: ApiClientCore) {}

  async getTrialDesignTypes() {
    return this.client.get<{ designs: any[] }>("/api/v2/trial-design/designs");
  }

  async getDesigns() {
    return this.getTrialDesignTypes().then(res => res.designs);
  }

  async generateRCBD(data: {
    genotypes: string[];
    n_blocks: number;
    field_rows?: number;
    seed?: number;
  }) {
    return this.client.post<{
      success: boolean;
      design_type: string;
      n_genotypes: number;
      n_blocks: number;
      total_plots: number;
      layout: any[];
      field_layout: any;
      seed: number | null;
    }>("/api/v2/trial-design/rcbd", data);
  }

  async generateAlphaLattice(data: {
    genotypes: string[];
    n_blocks: number;
    block_size: number;
    seed?: number;
  }) {
    return this.client.post<{
      success: boolean;
      design_type: string;
      n_genotypes: number;
      n_blocks: number;
      block_size: number;
      total_plots: number;
      layout: any[];
      field_layout: any;
      seed: number | null;
    }>("/api/v2/trial-design/alpha-lattice", data);
  }

  async generateAugmented(data: {
    test_genotypes: string[];
    check_genotypes: string[];
    n_blocks: number;
    checks_per_block?: number;
    seed?: number;
  }) {
    return this.client.post<{
      success: boolean;
      design_type: string;
      n_test_genotypes: number;
      n_check_genotypes: number;
      n_blocks: number;
      total_plots: number;
      layout: any[];
      field_layout: any;
      seed: number | null;
    }>("/api/v2/trial-design/augmented", data);
  }

  async generateSplitPlot(data: {
    main_treatments: string[];
    sub_treatments: string[];
    n_blocks: number;
    seed?: number;
  }) {
    return this.client.post<{
      success: boolean;
      design_type: string;
      n_main_treatments: number;
      n_sub_treatments: number;
      n_blocks: number;
      total_plots: number;
      layout: any[];
      field_layout: any;
      seed: number | null;
    }>("/api/v2/trial-design/split-plot", data);
  }

  async generateCRD(data: {
    genotypes: string[];
    n_reps: number;
    seed?: number;
  }) {
    return this.client.post<{
      success: boolean;
      design_type: string;
      n_genotypes: number;
      n_reps: number;
      total_plots: number;
      layout: any[];
      field_layout: any;
      seed: number | null;
    }>("/api/v2/trial-design/crd", data);
  }

  async generateFieldMap(data: {
    design_type: string;
    genotypes: string[];
    n_blocks: number;
    plot_width?: number;
    plot_length?: number;
    alley_width?: number;
    seed?: number;
  }) {
    return this.client.post<{
      success: boolean;
      plots: any[];
      field_dimensions: { width: number; length: number };
      total_plots: number;
    }>("/api/v2/trial-design/field-map", data);
  }
}
