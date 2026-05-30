import {
  ApiError,
  createApiErrorFromResponse,
  createApiErrorFromNetworkError,
} from "../../api-errors";
import { logger } from "../../logger";
import { withTraceHeaders } from "../../tracing/http";
import { API_URL } from '@/config';
import type { ZodTypeAny, z } from 'zod';

/**
 * Optional Zod schema for runtime validation of API responses.
 *
 * When provided to request<T>(), the parsed JSON is validated against the
 * schema before being returned. Validation failures are logged at WARN level
 * and the raw parsed value is returned (non-blocking) so existing callers
 * are not broken. This allows incremental adoption — add schemas to the
 * highest-risk endpoints first.
 *
 * Usage in a service method:
 *   import { z } from 'zod';
 *   const schema = z.object({ id: z.number(), name: z.string() });
 *   return this.client.get('/api/v2/programs/1', {}, schema);
 */
export type ResponseSchema<T> = ZodTypeAny & { _output: T };

export class ApiClientCore {
  protected baseURL: string;
  protected token: string | null = null;

  private async parseJsonResponse<T>(
    response: Response,
    schema?: ResponseSchema<T>,
  ): Promise<T> {
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

    const parsed = JSON.parse(responseText) as T;

    // Runtime validation — opt-in, non-blocking.
    // Failures are logged but the raw value is still returned so existing
    // callers that don't provide a schema are unaffected.
    if (schema) {
      const result = schema.safeParse(parsed);
      if (!result.success) {
        logger.warn('API response validation failed', {
          url: response.url,
          issues: result.error.issues.slice(0, 5), // cap to avoid log spam
        });
        // Return raw parsed value — non-breaking degradation
        return parsed;
      }
      return result.data as T;
    }

    return parsed;
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
  async get<T>(endpoint: string, options?: RequestInit, schema?: ResponseSchema<T>): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET" }, schema);
  }

  async post<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit,
    schema?: ResponseSchema<T>,
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }, schema);
  }

  async put<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit,
    schema?: ResponseSchema<T>,
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }, schema);
  }

  async patch<T>(
    endpoint: string,
    body?: any,
    options?: RequestInit,
    schema?: ResponseSchema<T>,
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }, schema);
  }

  async delete<T>(endpoint: string, options?: RequestInit, schema?: ResponseSchema<T>): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" }, schema);
  }

  public async request<T>(
    endpoint: string,
    options: RequestInit = {},
    schema?: ResponseSchema<T>,
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

        // In the preview environment, full-backend endpoints (/api/v2/*, etc.)
        // return 404. Replace the raw error with a clean, human-readable message
        // so pages never show "[object Object]" to users.
        if (
          response.status === 404 &&
          !endpoint.startsWith('/api/auth') &&
          !endpoint.startsWith('/api/germplasm') &&
          !endpoint.startsWith('/api/trials') &&
          !endpoint.startsWith('/api/observations') &&
          !endpoint.startsWith('/api/programs') &&
          !endpoint.startsWith('/api/locations') &&
          !endpoint.startsWith('/api/seed-lots') &&
          !endpoint.startsWith('/api/dashboard') &&
          !endpoint.startsWith('/api/export') &&
          !endpoint.startsWith('/brapi/v2')
        ) {
          const previewError = new ApiError(
            'This feature is part of the full BijMantra platform and is not available in the current preview environment.',
            apiError.type,
            404,
            undefined,
            apiError.context,
            false
          );
          throw previewError;
        }

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

      return this.parseJsonResponse<T>(response, schema);
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
