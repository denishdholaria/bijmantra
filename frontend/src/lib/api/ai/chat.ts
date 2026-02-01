import { ApiClientCore } from "../core/client";

export class ChatService {
  constructor(private client: ApiClientCore) {}

  async getStatus() {
    return this.client.get<any>("/api/v2/chat/status");
  }


  async sendMessage(data: any) {
    return this.client.post<any>("/api/v2/chat/", data);
  }

  /**
   * Stream a chat message from Veena (Generator)
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
