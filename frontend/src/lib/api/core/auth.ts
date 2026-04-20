import { ApiClientCore } from "./client";

export class AuthService {
  constructor(private client: ApiClientCore) {}

  async login(
    email: string,
    password: string,
  ): Promise<{
    access_token: string;
    token_type: string;
    user?: {
      id: number;
      email: string;
      full_name: string;
      organization_id: number;
      organization_name?: string;
      is_demo: boolean;
      is_active: boolean;
      is_superuser: boolean;
    };
  }> {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const response = await fetch(`${this.client["baseURL"]}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response
          .json()
          .catch(() => ({ detail: "Login failed" }));
        throw new Error(error.detail);
      }

      return response.json();
    } catch (error) {
      if (error instanceof Error) {
        const message = error.message.toLowerCase()

        if (error.name === "AbortError") {
          throw new Error("Login request timed out. Check backend availability and try again.");
        }

        if (
          error.name === "TypeError" ||
          message.includes("network") ||
          message.includes("fetch")
        ) {
          throw new Error("Unable to reach the server. Check connectivity and try again.");
        }

        throw error;
      }

      throw new Error("Login failed. Please try again.");
    }
  }

  async register(
    email: string,
    password: string,
    fullName: string,
    organizationId: number,
  ) {
    return this.client.post("/api/auth/register", {
      email,
      password,
      full_name: fullName,
      organization_id: organizationId,
    });
  }
}
