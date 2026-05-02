import { ApiClientCore } from "../core/client";

export interface TaxonomyValidationResult {
  valid: boolean;
  accepted_name?: string;
  synonyms?: string[];
  error?: string;
}

export class TaxonomyService {
  constructor(private client: ApiClientCore) {}

  async validateTaxonomy(genus: string, species: string, subspecies?: string) {
    const params = new URLSearchParams({ genus, species });
    if (subspecies) {
      params.append("subspecies", subspecies);
    }

    return this.client.post<TaxonomyValidationResult>(`/api/v2/grin/grin-global/validate-taxonomy?${params.toString()}`);
  }
}