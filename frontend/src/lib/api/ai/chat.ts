import { ApiClientCore } from "../core/client";

export type ChatUsageSoftAlertState =
  | "healthy"
  | "watch"
  | "warning"
  | "critical"
  | "exhausted";

export type ChatUsageProviderSnapshot = {
  active_provider: string | null;
  active_model: string | null;
  active_provider_source: string | null;
  active_provider_source_label: string | null;
};

export type ChatUsageAttributionDimension = {
  supported: boolean;
  value: string | null;
  reason: string | null;
};

export type ChatUsageTokenTelemetry = {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  coverage_state: "supplemental" | "unavailable";
  coverage_message: string;
};

export type ChatUsageSoftAlert = {
  state: ChatUsageSoftAlertState;
  threshold_basis: string;
  percent_used: number;
  message: string;
};

export type ChatUsageResponse = {
  used: number;
  limit: number;
  remaining: number;
  request_percentage_used: number;
  quota_authority: string;
  provider: ChatUsageProviderSnapshot;
  token_telemetry: ChatUsageTokenTelemetry;
  attribution: {
    lane: ChatUsageAttributionDimension;
    mission: ChatUsageAttributionDimension;
  };
  soft_alert: ChatUsageSoftAlert;
};

export class ChatService {
  constructor(private client: ApiClientCore) {}

  async getStatus() {
    return this.client.get<any>("/api/v2/chat/status");
  }

  async getUsage() {
    return this.client.get<ChatUsageResponse>("/api/v2/chat/usage");
  }


  async sendMessage(data: any) {
    return this.client.post<any>("/api/v2/chat/", data);
  }

  /**
    * Stream a chat message from REEVU (Generator)
   * Yields text chunks as they arrive
   */
  async *streamChatMessage(
    data: Record<string, unknown>,
  ): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${this.client.getBaseURL()}/api/v2/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.client.getToken() ? { Authorization: `Bearer ${this.client.getToken()}` } : {}),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      // Create a basic error if response fails, or use createApiErrorFromResponse if available/imported
      throw new Error(`Chat stream failed: ${response.status} ${response.statusText}`);
    }

    if (!response.body) throw new Error("ReadableStream not supported");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        yield chunk;
      }
    } finally {
      reader.releaseLock();
    }
  }
}
