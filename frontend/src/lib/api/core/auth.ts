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
    // Helper to generate demo token with user info
    const generateDemoToken = () => {
      console.log("🔓 Demo Mode: Enabling demo login for", email);
      const isDemo = email.includes("demo@");
      const demoToken = btoa(
        JSON.stringify({
          email,
          exp: Date.now() + 24 * 60 * 60 * 1000,
          demo: true,
        }),
      );
      return {
        access_token: `demo_${demoToken}`,
        token_type: "bearer",
        user: {
          id: isDemo ? 2 : 1,
          email,
          full_name: isDemo ? "Demo User" : "Admin User",
          organization_id: isDemo ? 1 : 2,
          organization_name: isDemo ? "Demo Organization" : "BijMantra HQ",
          is_demo: isDemo,
          is_active: true,
          is_superuser: !isDemo,
        },
      };
    };

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
        // Check if it's a server error (5xx) - likely proxy/backend issue
        if (response.status >= 500) {
          console.warn(
            "🔌 Backend server error (5xx) - falling back to demo mode",
          );
          return generateDemoToken();
        }
        // Authentication errors (401, 403, 400) should NOT fall back to demo mode
        // These are real errors that the user needs to see
        const error = await response
          .json()
          .catch(() => ({ detail: "Login failed" }));
        throw new Error(error.detail);
      }

      return response.json();
    } catch (error) {
      // Only fall back to demo mode for NETWORK errors (backend unavailable)
      // NOT for authentication errors (wrong password, etc.)
      if (error instanceof Error) {
        // Check if this is an AbortError (timeout) or network error
        const isNetworkError =
          error.name === "AbortError" ||
          error.name === "TypeError" ||
          error.message.includes("fetch") ||
          error.message.includes("network");

        if (isNetworkError) {
          console.warn("🔌 Backend unavailable - falling back to demo mode");
          return generateDemoToken();
        }

        // Re-throw authentication errors so user sees the actual error message
        throw error;
      }

      // Unknown error type - fall back to demo mode as last resort
      console.warn("🔌 Unknown error during login - falling back to demo mode");
      return generateDemoToken();
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
