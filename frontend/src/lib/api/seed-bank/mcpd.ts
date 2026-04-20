import { ApiClientCore } from "../core/client";

export interface MCPDCodeEntry {
  code: string;
  description?: string;
  name?: string;
}

export interface MCPDCodeResponse {
  field: string;
  description: string;
  codes: MCPDCodeEntry[];
}

export interface MCPDImportError {
  row: number;
  accession_number?: string | null;
  errors: string[];
}

export interface MCPDImportResult {
  total_records: number;
  imported: number;
  skipped: number;
  errors: MCPDImportError[];
}

export interface MCPDJsonExportResponse {
  mcpd_version: string;
  institute_code: string;
  export_date: string;
  total_records: number;
  data: Array<Record<string, string | number | boolean | null>>;
}

export class MCPDService {
  constructor(private client: ApiClientCore) {}

  async getBiologicalStatusCodes(): Promise<MCPDCodeResponse> {
    return this.client.get<MCPDCodeResponse>("/api/v2/seed-bank/mcpd/codes/biological-status");
  }

  async getAcquisitionSourceCodes(): Promise<MCPDCodeResponse> {
    return this.client.get<MCPDCodeResponse>("/api/v2/seed-bank/mcpd/codes/acquisition-source");
  }

  async getStorageTypeCodes(): Promise<MCPDCodeResponse> {
    return this.client.get<MCPDCodeResponse>("/api/v2/seed-bank/mcpd/codes/storage-type");
  }

  async downloadTemplate(): Promise<Blob> {
    return this.downloadBlob("/api/v2/seed-bank/mcpd/template");
  }

  async exportCsv(instCode?: string): Promise<Blob> {
    const params = new URLSearchParams();
    if (instCode) {
      params.append("inst_code", instCode);
    }
    const suffix = params.toString();
    return this.downloadBlob(`/api/v2/seed-bank/mcpd/export/csv${suffix ? `?${suffix}` : ""}`);
  }

  async exportJson(instCode?: string): Promise<MCPDJsonExportResponse> {
    const params = new URLSearchParams();
    if (instCode) {
      params.append("inst_code", instCode);
    }
    return this.client.get<MCPDJsonExportResponse>(`/api/v2/seed-bank/mcpd/export/json${params.toString() ? `?${params}` : ""}`);
  }

  async importCsv(file: File, options?: { skipDuplicates?: boolean; validateOnly?: boolean }): Promise<MCPDImportResult> {
    const params = new URLSearchParams();
    params.append("skip_duplicates", String(options?.skipDuplicates ?? true));
    params.append("validate_only", String(options?.validateOnly ?? false));

    const formData = new FormData();
    formData.append("file", file);

    return this.uploadForm<MCPDImportResult>(`/api/v2/seed-bank/mcpd/import?${params.toString()}`, formData);
  }

  private async downloadBlob(endpoint: string): Promise<Blob> {
    const response = await fetch(`${this.client.getBaseURL()}${endpoint}`, {
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(await this.readError(response));
    }

    return response.blob();
  }

  private async uploadForm<T>(endpoint: string, formData: FormData): Promise<T> {
    const response = await fetch(`${this.client.getBaseURL()}${endpoint}`, {
      method: "POST",
      headers: this.getAuthHeaders(false),
      body: formData,
    });

    if (!response.ok) {
      throw new Error(await this.readError(response));
    }

    return response.json();
  }

  private getAuthHeaders(includeContentType = false): HeadersInit {
    const token = this.client.getToken();
    const headers: Record<string, string> = {};

    if (includeContentType) {
      headers["Content-Type"] = "application/json";
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  }

  private async readError(response: Response): Promise<string> {
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") {
        return payload.detail;
      }
      return JSON.stringify(payload);
    } catch {
      return response.statusText || "Request failed";
    }
  }
}