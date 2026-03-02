import { ApiClientCore } from "../core/client";
import { 
  QTL, 
  QTLSummary, 
  CandidateGene, 
  GWASAssociation, 
  GOEnrichment 
} from "./types";

export class QTLMappingService {
  constructor(private client: ApiClientCore) {}

  async getQTLs(params?: {
    trait?: string;
    chromosome?: string;
    min_lod?: number;
    population?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.trait) searchParams.set("trait", params.trait);
    if (params?.chromosome) searchParams.set("chromosome", params.chromosome);
    if (params?.min_lod) searchParams.set("min_lod", params.min_lod.toString());
    if (params?.population) searchParams.set("population", params.population);
    const query = searchParams.toString();
    return this.client.get<{ qtls: QTL[]; total: number }>(
      `/api/v2/qtl-mapping/qtls${query ? `?${query}` : ""}`
    );
  }

  async getQTL(qtlId: string) {
    return this.client.get<QTL>(`/api/v2/qtl-mapping/qtls/${qtlId}`);
  }

  async getCandidateGenes(qtlId: string) {
    return this.client.get<{
      qtl_id: string;
      qtl_name: string;
      confidence_interval: [number, number];
      candidates: CandidateGene[];
      total: number;
    }>(`/api/v2/qtl-mapping/qtls/${qtlId}/candidates`);
  }

  async getGWASResults(params?: {
    trait?: string;
    chromosome?: string;
    min_log_p?: number;
    max_p_value?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.trait) searchParams.set("trait", params.trait);
    if (params?.chromosome) searchParams.set("chromosome", params.chromosome);
    if (params?.min_log_p)
      searchParams.set("min_log_p", params.min_log_p.toString());
    if (params?.max_p_value)
      searchParams.set("max_p_value", params.max_p_value.toString());
    const query = searchParams.toString();
    return this.client.get<{ associations: GWASAssociation[]; total: number }>(
      `/api/v2/qtl-mapping/gwas${query ? `?${query}` : ""}`
    );
  }

  async getManhattanData(trait?: string) {
    const query = trait ? `?trait=${trait}` : "";
    return this.client.get<any>(`/api/v2/qtl-mapping/manhattan${query}`);
  }

  async getLODProfile(chromosome: string, trait?: string) {
    const query = trait ? `?trait=${trait}` : "";
    return this.client.get<any>(
      `/api/v2/qtl-mapping/lod-profile/${chromosome}${query}`
    );
  }

  async getGOEnrichment(qtlIds?: string[]) {
    const query = qtlIds ? `?qtl_ids=${qtlIds.join(",")}` : "";
    return this.client.get<{ enrichment: GOEnrichment[] }>(
      `/api/v2/qtl-mapping/go-enrichment${query}`
    );
  }

  async getQTLSummary() {
    return this.client.get<QTLSummary>("/api/v2/qtl-mapping/summary/qtl");
  }

  async getGWASSummary() {
    return this.client.get<any>("/api/v2/qtl-mapping/summary/gwas");
  }

  async getTraits() {
    return this.client.get<{ traits: string[] }>(
      "/api/v2/qtl-mapping/traits"
    );
  }

  async getPopulations() {
    return this.client.get<{ populations: string[] }>(
      "/api/v2/qtl-mapping/populations"
    );
  }
}
