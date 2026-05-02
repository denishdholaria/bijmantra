import { ApiClientCore } from "../../core/client";
import { BrAPIListResponse, BrAPIResponse } from "../../core/types";

export type OntologyRecord = {
  ontologyDbId: string;
  ontologyName: string;
  description?: string;
  authors?: string;
  version?: string;
  copyright?: string;
  licence?: string;
  documentationURL?: string;
  additionalInfo?: Record<string, unknown>;
  termCount?: number;
};

export type CreateOntologyPayload = {
  ontologyName: string;
  description?: string;
  authors?: string;
  version?: string;
  copyright?: string;
  licence?: string;
  documentationURL?: string;
  additionalInfo?: Record<string, unknown>;
};

export interface OntologyFormulaInput {
  name: string;
  unit: string;
}

export interface OntologyFormulaOutput {
  name: string;
  unit: string;
}

export interface OntologyFormula {
  id: string;
  name: string;
  category: string;
  formula: string;
  inputs: OntologyFormulaInput[];
  output: OntologyFormulaOutput;
}

export class OntologiesService {
  constructor(private client: ApiClientCore) {}

  async getOntologies(params?: {
    ontologyDbId?: string;
    ontologyName?: string;
    page?: number;
    pageSize?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.ontologyDbId)
      searchParams.append("ontologyDbId", params.ontologyDbId);
    if (params?.ontologyName)
      searchParams.append("ontologyName", params.ontologyName);
    if (params?.page !== undefined)
      searchParams.append("page", String(params.page));
    if (params?.pageSize)
      searchParams.append("pageSize", String(params.pageSize));

    return this.client.get<BrAPIListResponse<OntologyRecord>>(
      `/brapi/v2/ontologies?${searchParams}`
    );
  }

  async getOntology(ontologyDbId: string) {
    return this.client.get<BrAPIResponse<OntologyRecord>>(
      `/brapi/v2/ontologies/${ontologyDbId}`
    );
  }

  async createOntology(data: CreateOntologyPayload) {
    return this.client.post<BrAPIListResponse<OntologyRecord>>(
      "/brapi/v2/ontologies",
      [data]
    );
  }

  // APEX Extensions (Phase 8 Validation)
  async getFormulas() {
    return this.client.get<{ formulas: OntologyFormula[] }>(`/api/v2/ontology/formulas`);
  }

  async calculateFormula(formulaId: string, inputs: Record<string, number>) {
    return this.client.post<{ result: number; unit: string }>(
      `/api/v2/ontology/formulas/calculate`,
      { formula_id: formulaId, inputs }
    );
  }
}
