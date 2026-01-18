/**
 * API Error Handling Module
 * 
 * Provides structured error handling for API requests including:
 * - Typed error classes for different error scenarios
 * - Error context management for debugging
 * - Retry logic with exponential backoff
 * - Error classification and recovery strategies
 */

/**
 * Enumeration of API error types
 */
export enum ApiErrorType {
  // Client errors (4xx)
  BAD_REQUEST = 'BAD_REQUEST',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  NOT_FOUND = 'NOT_FOUND',
  CONFLICT = 'CONFLICT',
  UNPROCESSABLE_ENTITY = 'UNPROCESSABLE_ENTITY',
  RATE_LIMITED = 'RATE_LIMITED',

  // Server errors (5xx)
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  GATEWAY_TIMEOUT = 'GATEWAY_TIMEOUT',

  // Network errors
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT = 'TIMEOUT',
  CANCELLED = 'CANCELLED',

  // Client errors
  INVALID_REQUEST = 'INVALID_REQUEST',
  PARSE_ERROR = 'PARSE_ERROR',

  // Unknown
  UNKNOWN = 'UNKNOWN',
}

/**
 * HTTP status code mappings to error types
 */
const HTTP_STATUS_ERROR_TYPE_MAP: Record<number, ApiErrorType> = {
  400: ApiErrorType.BAD_REQUEST,
  401: ApiErrorType.UNAUTHORIZED,
  403: ApiErrorType.FORBIDDEN,
  404: ApiErrorType.NOT_FOUND,
  409: ApiErrorType.CONFLICT,
  422: ApiErrorType.UNPROCESSABLE_ENTITY,
  429: ApiErrorType.RATE_LIMITED,
  500: ApiErrorType.INTERNAL_SERVER_ERROR,
  503: ApiErrorType.SERVICE_UNAVAILABLE,
  504: ApiErrorType.GATEWAY_TIMEOUT,
};

/**
 * Error context containing additional debugging information
 */
export interface ApiErrorContext {
  endpoint?: string;
  method?: string;
  statusCode?: number;
  timestamp?: string;
  requestId?: string;
  userId?: string;
  retryCount?: number;
  originalError?: Error;
  metadata?: Record<string, any>;
}

/**
 * Error response structure from API
 */
export interface ApiErrorResponse {
  message?: string;
  error?: string;
  code?: string;
  details?: Record<string, any>;
  errors?: Array<{
    field?: string;
    message?: string;
    code?: string;
  }>;
}

/**
 * Structured API Error class
 */
export class ApiError extends Error {
  readonly type: ApiErrorType;
  readonly statusCode?: number;
  readonly context: ApiErrorContext;
  readonly responseData?: ApiErrorResponse;
  readonly isRetryable: boolean;

  constructor(
    message: string,
    type: ApiErrorType = ApiErrorType.UNKNOWN,
    statusCode?: number,
    responseData?: ApiErrorResponse,
    context: ApiErrorContext = {},
    isRetryable: boolean = false
  ) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.statusCode = statusCode;
    this.responseData = responseData;
    this.context = {
      timestamp: new Date().toISOString(),
      ...context,
    };
    this.isRetryable = isRetryable;

    // Maintain proper prototype chain
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(): string {
    const messageMap: Record<ApiErrorType, string> = {
      [ApiErrorType.BAD_REQUEST]: 'Invalid request. Please check your input.',
      [ApiErrorType.UNAUTHORIZED]: 'Authentication required. Please log in.',
      [ApiErrorType.FORBIDDEN]: 'You do not have permission to access this resource.',
      [ApiErrorType.NOT_FOUND]: 'The requested resource was not found.',
      [ApiErrorType.CONFLICT]: 'A conflict occurred. Please try again.',
      [ApiErrorType.UNPROCESSABLE_ENTITY]: 'Invalid data provided. Please check your input.',
      [ApiErrorType.RATE_LIMITED]: 'Too many requests. Please try again later.',
      [ApiErrorType.INTERNAL_SERVER_ERROR]: 'Server error. Please try again later.',
      [ApiErrorType.SERVICE_UNAVAILABLE]: 'Service is temporarily unavailable.',
      [ApiErrorType.GATEWAY_TIMEOUT]: 'Request timeout. Please try again.',
      [ApiErrorType.NETWORK_ERROR]: 'Network error. Please check your connection.',
      [ApiErrorType.TIMEOUT]: 'Request timed out. Please try again.',
      [ApiErrorType.CANCELLED]: 'Request was cancelled.',
      [ApiErrorType.INVALID_REQUEST]: 'Invalid request.',
      [ApiErrorType.PARSE_ERROR]: 'Failed to parse response.',
      [ApiErrorType.UNKNOWN]: 'An unexpected error occurred.',
    };

    return messageMap[this.type] || this.message;
  }

  /**
   * Get technical details for logging
   */
  getTechnicalDetails(): Record<string, any> {
    return {
      type: this.type,
      message: this.message,
      statusCode: this.statusCode,
      context: this.context,
      responseData: this.responseData,
      isRetryable: this.isRetryable,
      stack: this.stack,
    };
  }

  /**
   * Check if error is due to authentication issues
   */
  isAuthError(): boolean {
    return [ApiErrorType.UNAUTHORIZED, ApiErrorType.FORBIDDEN].includes(
      this.type
    );
  }

  /**
   * Check if error is a client error (4xx)
   */
  isClientError(): boolean {
    return this.statusCode ? this.statusCode >= 400 && this.statusCode < 500 : false;
  }

  /**
   * Check if error is a server error (5xx)
   */
  isServerError(): boolean {
    return this.statusCode ? this.statusCode >= 500 && this.statusCode < 600 : false;
  }
}

/**
 * Retry configuration options
 */
export interface RetryConfig {
  maxAttempts?: number;
  initialDelayMs?: number;
  maxDelayMs?: number;
  backoffMultiplier?: number;
  retryableErrorTypes?: ApiErrorType[];
  retryableStatusCodes?: number[];
  onRetry?: (attempt: number, error: ApiError, delayMs: number) => void;
}

/**
 * Default retry configuration
 */
const DEFAULT_RETRY_CONFIG: Required<RetryConfig> = {
  maxAttempts: 3,
  initialDelayMs: 100,
  maxDelayMs: 10000,
  backoffMultiplier: 2,
  retryableErrorTypes: [
    ApiErrorType.TIMEOUT,
    ApiErrorType.NETWORK_ERROR,
    ApiErrorType.SERVICE_UNAVAILABLE,
    ApiErrorType.GATEWAY_TIMEOUT,
    ApiErrorType.RATE_LIMITED,
  ],
  retryableStatusCodes: [408, 429, 500, 502, 503, 504],
  onRetry: () => {}, // No-op by default
};

/**
 * Retry handler with exponential backoff
 */
export class RetryHandler {
  private config: Required<RetryConfig>;

  constructor(config: RetryConfig = {}) {
    this.config = { ...DEFAULT_RETRY_CONFIG, ...config };
  }

  /**
   * Determine if an error should be retried
   */
  shouldRetry(error: ApiError, attemptNumber: number): boolean {
    if (attemptNumber >= this.config.maxAttempts) {
      return false;
    }

    // Check if error type is retryable
    if (
      this.config.retryableErrorTypes.includes(error.type) &&
      error.isRetryable
    ) {
      return true;
    }

    // Check if status code is retryable
    if (
      error.statusCode &&
      this.config.retryableStatusCodes.includes(error.statusCode)
    ) {
      return true;
    }

    return false;
  }

  /**
   * Calculate exponential backoff delay
   */
  getDelayMs(attemptNumber: number): number {
    const exponentialDelay =
      this.config.initialDelayMs *
      Math.pow(this.config.backoffMultiplier, attemptNumber - 1);

    // Add random jitter (±10%) to prevent thundering herd
    const jitter = exponentialDelay * 0.1 * (Math.random() * 2 - 1);
    let delay = exponentialDelay + jitter;

    // Cap at max delay
    delay = Math.min(delay, this.config.maxDelayMs);

    // Ensure positive delay
    return Math.max(Math.ceil(delay), 0);
  }

  /**
   * Wait for specified delay
   */
  async wait(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Execute function with retry logic
   */
  async execute<T>(
    fn: () => Promise<T>,
    context: ApiErrorContext = {}
  ): Promise<T> {
    let lastError: ApiError | null = null;

    for (let attempt = 1; attempt <= this.config.maxAttempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        const apiError = this.normalizeError(error, attempt, context);

        if (this.shouldRetry(apiError, attempt)) {
          const delayMs = this.getDelayMs(attempt);
          apiError.context.retryCount = attempt;

          this.config.onRetry?.(attempt, apiError, delayMs);

          await this.wait(delayMs);
          lastError = apiError;
          continue;
        }

        throw apiError;
      }
    }

    throw (
      lastError ||
      new ApiError(
        'Max retry attempts reached',
        ApiErrorType.UNKNOWN,
        undefined,
        undefined,
        context
      )
    );
  }

  /**
   * Normalize different error types into ApiError
   */
  private normalizeError(
    error: unknown,
    attemptNumber: number,
    context: ApiErrorContext
  ): ApiError {
    const mergedContext: ApiErrorContext = {
      ...context,
      retryCount: attemptNumber - 1,
    };

    if (error instanceof ApiError) {
      const updatedContext = { ...error.context, ...mergedContext };
      return new ApiError(
        error.message,
        error.type,
        error.statusCode,
        error.responseData,
        updatedContext,
        error.isRetryable
      );
    }

    if (error instanceof TypeError) {
      if (error.message.includes('network')) {
        return new ApiError(
          error.message,
          ApiErrorType.NETWORK_ERROR,
          undefined,
          undefined,
          mergedContext,
          true
        );
      }
      return new ApiError(
        error.message,
        ApiErrorType.INVALID_REQUEST,
        undefined,
        undefined,
        mergedContext
      );
    }

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return new ApiError(
          'Request cancelled',
          ApiErrorType.CANCELLED,
          undefined,
          undefined,
          mergedContext
        );
      }
      return new ApiError(
        error.message,
        ApiErrorType.UNKNOWN,
        undefined,
        undefined,
        mergedContext,
        true
      );
    }

    return new ApiError(
      'Unknown error occurred',
      ApiErrorType.UNKNOWN,
      undefined,
      undefined,
      mergedContext,
      true
    );
  }
}

/**
 * Create ApiError from fetch response
 */
export async function createApiErrorFromResponse(
  response: Response,
  context: ApiErrorContext = {}
): Promise<ApiError> {
  const statusCode = response.status;
  const errorType = HTTP_STATUS_ERROR_TYPE_MAP[statusCode] || ApiErrorType.UNKNOWN;

  let responseData: ApiErrorResponse | undefined;
  let message = `HTTP ${statusCode}`;

  try {
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      responseData = await response.json();
      if (responseData) {
        message =
          responseData.message ||
          responseData.error ||
          message;
      }
    } else {
      message = await response.text() || message;
    }
  } catch (parseError) {
    // Continue with default message if parsing fails
  }

  const isRetryable =
    statusCode === 429 || // Rate limited
    (statusCode >= 500 && statusCode < 600); // Server errors

  return new ApiError(
    message,
    errorType,
    statusCode,
    responseData,
    { ...context, statusCode },
    isRetryable
  );
}

/**
 * Create ApiError from network/timeout errors
 */
export function createApiErrorFromNetworkError(
  error: Error,
  context: ApiErrorContext = {}
): ApiError {
  let errorType = ApiErrorType.NETWORK_ERROR;
  let isRetryable = true;

  if (error.name === 'AbortError') {
    errorType = ApiErrorType.CANCELLED;
    isRetryable = false;
  } else if (error.message.includes('timeout')) {
    errorType = ApiErrorType.TIMEOUT;
  }

  return new ApiError(
    error.message,
    errorType,
    undefined,
    undefined,
    context,
    isRetryable
  );
}

/**
 * Error logging utility
 */
export class ApiErrorLogger {
  static log(error: ApiError, context?: string): void {
    const logContext = context ? `[${context}] ` : '';
    console.error(
      `${logContext}API Error:`,
      error.getTechnicalDetails()
    );
  }

  static logWarning(error: ApiError, context?: string): void {
    const logContext = context ? `[${context}] ` : '';
    console.warn(
      `${logContext}API Warning:`,
      error.getTechnicalDetails()
    );
  }

  static logRetry(attempt: number, error: ApiError, delayMs: number, context?: string): void {
    const logContext = context ? `[${context}] ` : '';
    console.info(
      `${logContext}Retrying request (attempt ${attempt}). Delay: ${delayMs}ms. Error:`,
      error.message
    );
  }
}

/**
 * Export all types and utilities
 */
export default {
  ApiError,
  ApiErrorType,
  RetryHandler,
  ApiErrorLogger,
  createApiErrorFromResponse,
  createApiErrorFromNetworkError,
  DEFAULT_RETRY_CONFIG,
};
