import { ApiClientCore } from "../core/client";

export interface Backup {
  id: string;
  name: string;
  size: string;
  type: "full" | "incremental" | "manual";
  status: "completed" | "in_progress" | "failed";
  created_at: string;
  created_by: string;
}

export interface BackupStats {
  total_backups: number;
  successful_backups: number;
  latest_size: string;
  auto_backup_schedule: string;
}

export class BackupService {
  constructor(private client: ApiClientCore) {}

  async listBackups() {
    return this.client.get<Backup[]>("/api/v2/backup/");
  }

  async getStats() {
    return this.client.get<BackupStats>("/api/v2/backup/stats");
  }

  async createBackup(type: "full" | "incremental" | "manual" = "manual") {
    return this.client.post<Backup>("/api/v2/backup/create", { type });
  }

  async restoreBackup(backupId: string) {
    return this.client.post<any>("/api/v2/backup/restore", {
      backup_id: backupId,
    });
  }

  async downloadBackup(backupId: string) {
    // Note: This likely returns a blob or similar, but ApiClientCore.get assumes JSON by default usually. 
    // If ApiClientCore wrapper doesn't handle blobs, we might need a workaround.
    // Assuming backend returns a link or we rely on window.location for now, or this returns metadata.
    // Original used r.json() so it's probably returning a presigned URL or metadata.
    return this.client.get<any>(`/api/v2/backup/download/${backupId}`);
  }

  async deleteBackup(backupId: string) {
    return this.client.delete<any>(`/api/v2/backup/${backupId}`);
  }
}
