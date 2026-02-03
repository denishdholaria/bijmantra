import { ApiClientCore } from "../core/client";

export interface AuditEntry {
  id: string;
  timestamp: string;
  category: string;
  severity: string;
  action: string;
  actor: string | null;
  target: string | null;
  source_ip: string | null;
  details: Record<string, any>;
  success: boolean;
}

export interface AuditStats {
  total_entries: number;
  entries_last_24h: number;
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
  failed_actions: number;
  unique_actors: number;
  unique_ips: number;
}

export class AuditLogService {
  constructor(private client: ApiClientCore) {}

  async getEntries(params: Record<string, any>) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      searchParams.append(key, String(value));
    });
    return this.client.get<{ entries: AuditEntry[]; total: number }>(
      `/api/v2/audit/entries?${searchParams}`
    );
  }

  async getStats(hours: number) {
    return this.client.get<AuditStats>(`/api/v2/audit/stats?hours=${hours}`);
  }

  async searchLogs(query: string) {
    return this.client.get<{ results: AuditEntry[]; total: number }>(
      `/api/v2/audit/search?q=${encodeURIComponent(query)}`
    );
  }

  async exportLogs(params: {
    start_date: string;
    end_date: string;
    format: "json" | "csv";
  }) {
    const searchParams = new URLSearchParams({
      start_date: params.start_date,
      end_date: params.end_date,
      format: params.format,
    });
    return this.client.get<{ data: any }>(
      `/api/v2/audit/export?${searchParams}`
    );
  }
}
