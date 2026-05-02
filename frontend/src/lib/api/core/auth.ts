import { ApiClientCore } from "./client";
import { LoginResponseSchema, type LoginResponse } from "./schemas";

export class AuthService {
  constructor(private client: ApiClientCore) {}

  async login(
    email: string,
    password: string,
  ): Promise<LoginResponse> {
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

      const raw = await response.json();

      // Validate the login response shape at runtime.
      // If validation fails, log a warning and return the raw value — the
      // auth store will handle missing fields gracefully.
      const result = LoginResponseSchema.safeParse(raw);
      if (!result.success) {
        console.warn('[AuthService] Login response validation failed:', result.error.issues);
        return raw as LoginResponse;
      }
      return result.data;
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
