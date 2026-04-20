import {
  ApiError,
  createApiErrorFromResponse,
  createApiErrorFromNetworkError,
} from "../../api-errors";
import { logger } from "../../logger";
import { withTraceHeaders } from "../../tracing/http";
import { API_URL } from '@/config';

export class ApiClientCore {
  protected baseURL: string;
  protected token: string | null = null;

  private async parseJsonResponse<T>(response: Response): Promise<T> {
    if (response.status === 204 || response.status === 205 || response.status === 304) {
      return undefined as T;
    }

    if (response.headers.get('content-length') === '0') {
      return undefined as T;
    }

    const responseText = await response.text();
    if (!responseText.trim()) {
      return undefined as T;
    }

    return JSON.parse(responseText) as T;
  }

  constructor(baseURL?: string) {
    // Use VITE_API_URL for production deployments (Vercel, etc.)
    // Falls back to empty string for local dev (uses Vite proxy)
    this.baseURL = baseURL ?? (API_URL);
    this.loadToken();
    logger.debug("APIClient initialized", { baseURL: this.baseURL });
  }

  private loadToken() {
    try {
      const storedToken =
        typeof localStorage !== "undefined"
          ? localStorage.getItem("auth_token")
          : null;

      if (storedToken?.startsWith("demo_")) {
        localStorage.removeItem("auth_token");
        this.token = null;
        logger.warn("Removed legacy demo auth token during client initialization");
        return;
      }

      this.token = storedToken;
    } catch {
      // localStorage may not be available in some environments
      this.token = null;
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      try {
        localStorage.setItem("auth_token", token);
      } catch {
        // localStorage may not be available
      }
      logger.debug("Auth token set");
    } else {
      try {
        localStorage.removeItem("auth_token");
      } catch {
        // localStorage may not be available
      }
      logger.debug("Auth token cleared");
    }
  }

  getToken(): string | null {
    return this.token;
  }

  getBaseURL(): string {
    return this.baseURL;
  }

  // Validate token by making a simple API call
  async validateToken(): Promise<boolean> {
    if (!this.token) return false;

    if (this.token.startsWith("demo_")) {
      this.setToken(null);
      logger.warn("Removed legacy demo auth token during token validation");
      return false;
    }

    try {
      const response = await fetch(`${this.baseURL}/api/auth/me`, {
        headers: withTraceHeaders({
          Authorization: `Bearer ${this.token}`,
        }),
      });

      if (response.status === 401) {
        this.setToken(null);
        logger.warn("Token validation failed - 401 Unauthorized");
        return false;
      }

      return response.ok;
    } catch {
      // Network error - can't validate, assume valid for offline mode
      logger.debug("Token validation skipped - network unavailable");
      return true;
    }
  }

  // Helper to get auth headers for external usage if needed
  getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };
    if (this.token) {
        headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  // Generic HTTP methods
  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  async post<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit,
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit,
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async patch<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit,
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }

  public async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Allow FormData to set its own Content-Type (multipart/form-data with boundary)
    if (options.body instanceof FormData) {
      delete headers['Content-Type']
    }

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
      if (endpoint.includes('notifications')) {
         console.error(`[CLIENT-DEBUG] Sending request to ${endpoint} with token: ${this.token.substring(0, 15)}...`)
      }
    } else {
      if (endpoint.includes('notifications')) {
         console.error(`[CLIENT-DEBUG] Sending request to ${endpoint} WITHOUT TOKEN`)
      }
    }

    // Merge any additional headers from options
    if (options.headers) {
      const optHeaders = options.headers as Record<string, string>;
      Object.assign(headers, optHeaders);
    }

    const method = options.method || "GET";
    logger.debug(`API Request: ${method} ${endpoint}`);

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers: withTraceHeaders(headers),
      });

      if (!response.ok) {
        const apiError = await createApiErrorFromResponse(response, {
          endpoint,
          method,
        });

        // Handle 401 Unauthorized - clear token and redirect to login
        if (apiError.isAuthError()) {
          this.setToken(null);
          // Dispatch custom event for auth state change
          if (typeof window !== 'undefined') {
             window.dispatchEvent(new CustomEvent("auth:unauthorized"));
          }
          logger.warn("Authentication error - session cleared", {
            endpoint,
            traceId: apiError.context.traceId,
          });
        } else {
          logger.error(`API Error: ${method} ${endpoint}`, apiError, {
            statusCode: response.status,
            traceId: apiError.context.traceId,
            type: apiError.type,
          });
        }

        throw apiError;
      }

      return this.parseJsonResponse<T>(response);
    } catch (error) {
      // If already an ApiError, rethrow
      if (error instanceof ApiError) {
        throw error;
      }

      // Network/fetch errors
      if (error instanceof TypeError) {
        const networkError = createApiErrorFromNetworkError(error as Error, {
          endpoint,
          method,
        });
        logger.error("Network error", error as Error, { endpoint });
        throw networkError;
      }

      // Unknown errors
      logger.error("Unexpected error in API request", error as Error, {
        endpoint,
      });
      throw error;
    }
  }
}
