import { ApiClientCore } from "../core/client";

export class MolecularBreedingService {
  constructor(private client: ApiClientCore) {}

  async getHaplotypeBlocks(chromosome?: string) {
    const query = chromosome ? `?chromosome=${chromosome}` : "";
    return this.client.get<{ data: any[] }>(
      `/api/v2/molecular-breeding/haplotypes/blocks${query}`
    );
  }

  async getBlockHaplotypes(blockId: string) {
    return this.client.get<{ data: any[] }>(
      `/api/v2/molecular-breeding/haplotypes/blocks/${blockId}`
    );
  }

  async getHaplotypeDiversity() {
    return this.client.get<{ data: any }>(
      "/api/v2/molecular-breeding/haplotypes/diversity"
    );
  }

  async getHaplotypeStatistics() {
    return this.client.get<{ data: any }>(
      "/api/v2/molecular-breeding/haplotypes/statistics"
    );
  }

  async getLDDemoData() {
    return this.client.get<{ data: any }>(
      "/api/v2/molecular-breeding/ld/demo"
    );
  }

  async getSchemes() {
    return this.client.get<{ data: any[] }>(
      "/api/v2/molecular-breeding/schemes"
    );
  }

  async getLines() {
    return this.client.get<{ data: any[] }>(
      "/api/v2/molecular-breeding/lines"
    );
  }

  async getStatistics() {
    return this.client.get<{ data: any }>(
      "/api/v2/molecular-breeding/statistics"
    );
  }
}
