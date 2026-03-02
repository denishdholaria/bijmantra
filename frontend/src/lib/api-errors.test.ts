import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { RetryHandler, ApiError, ApiErrorType, RetryConfig, createApiErrorFromResponse } from './api-errors';

describe('RetryHandler', () => {
  let retryHandler: RetryHandler;

  beforeEach(() => {
    retryHandler = new RetryHandler();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('shouldRetry', () => {
    it('should return false when max attempts reached', () => {
      // Default maxAttempts is 3
      const error = new ApiError('Timeout', ApiErrorType.TIMEOUT, undefined, undefined, {}, true);

      expect(retryHandler.shouldRetry(error, 3)).toBe(false);
      expect(retryHandler.shouldRetry(error, 4)).toBe(false);
    });

    it('should return true for retryable error type within attempt limit', () => {
      const error = new ApiError('Timeout', ApiErrorType.TIMEOUT, undefined, undefined, {}, true);
      expect(retryHandler.shouldRetry(error, 1)).toBe(true);
      expect(retryHandler.shouldRetry(error, 2)).toBe(true);
    });

    it('should return false for non-retryable error type', () => {
      const error = new ApiError('Bad Request', ApiErrorType.BAD_REQUEST, 400, undefined, {}, false);
      expect(retryHandler.shouldRetry(error, 1)).toBe(false);
    });

    it('should return true for retryable status code within attempt limit', () => {
      // 503 is in default retryable status codes
      const error = new ApiError('Service Unavailable', ApiErrorType.SERVICE_UNAVAILABLE, 503, undefined, {}, false);
      // Status code override should make it true even if isRetryable was initialized as false
      expect(retryHandler.shouldRetry(error, 1)).toBe(true);
    });

    it('should return false for non-retryable status code', () => {
      const error = new ApiError('Not Found', ApiErrorType.NOT_FOUND, 404, undefined, {}, false);
      expect(retryHandler.shouldRetry(error, 1)).toBe(false);
    });

    it('should return false if error type is retryable but isRetryable flag is false', () => {
      // TIMEOUT is retryable type, but we explicitly set isRetryable=false
      const error = new ApiError('Timeout', ApiErrorType.TIMEOUT, undefined, undefined, {}, false);
      expect(retryHandler.shouldRetry(error, 1)).toBe(false);
    });

    it('should respect custom configuration', () => {
      const customConfig: RetryConfig = {
        maxAttempts: 2,
        retryableErrorTypes: [ApiErrorType.BAD_REQUEST],
        retryableStatusCodes: [418]
      };
      const customHandler = new RetryHandler(customConfig);

      // Custom maxAttempts
      const timeoutError = new ApiError('Timeout', ApiErrorType.TIMEOUT, undefined, undefined, {}, true);
      // default TIMEOUT is not in our custom retryableErrorTypes
      expect(customHandler.shouldRetry(timeoutError, 1)).toBe(false);

      // Custom retryable type
      const badRequestError = new ApiError('Bad', ApiErrorType.BAD_REQUEST, 400, undefined, {}, true);
      expect(customHandler.shouldRetry(badRequestError, 1)).toBe(true);
      // Check max attempts (2)
      expect(customHandler.shouldRetry(badRequestError, 2)).toBe(false);

      // Custom retryable status code
      const teapotError = new ApiError('Teapot', ApiErrorType.UNKNOWN, 418, undefined, {}, false);
      expect(customHandler.shouldRetry(teapotError, 1)).toBe(true);
    });
  });

  describe('getDelayMs', () => {
    it('should calculate exponential backoff correctly with no jitter', () => {
      // Mock Math.random to return 0.5, which results in 0 jitter
      // jitter = exponentialDelay * 0.1 * (0.5 * 2 - 1) = exponentialDelay * 0.1 * 0 = 0
      vi.spyOn(Math, 'random').mockReturnValue(0.5);

      const handler = new RetryHandler({
        initialDelayMs: 100,
        backoffMultiplier: 2,
        maxDelayMs: 10000,
      });

      // Attempt 1: 100 * 2^0 = 100
      expect(handler.getDelayMs(1)).toBe(100);

      // Attempt 2: 100 * 2^1 = 200
      expect(handler.getDelayMs(2)).toBe(200);

      // Attempt 3: 100 * 2^2 = 400
      expect(handler.getDelayMs(3)).toBe(400);
    });

    it('should apply random jitter within ±10% range', () => {
      const handler = new RetryHandler({
        initialDelayMs: 100,
        backoffMultiplier: 2,
      });

      // Test lower bound of jitter
      // Math.random() = 0 => jitter = 100 * 0.1 * (0 * 2 - 1) = -10
      vi.spyOn(Math, 'random').mockReturnValue(0);
      expect(handler.getDelayMs(1)).toBe(90);

      // Test upper bound of jitter
      // Math.random() = 1 => jitter = 100 * 0.1 * (1 * 2 - 1) = 10
      vi.spyOn(Math, 'random').mockReturnValue(1);
      expect(handler.getDelayMs(1)).toBe(110);
    });

    it('should cap delay at maxDelayMs', () => {
      vi.spyOn(Math, 'random').mockReturnValue(0.5); // No jitter

      const handler = new RetryHandler({
        initialDelayMs: 100,
        backoffMultiplier: 2,
        maxDelayMs: 500,
      });

      // Attempt 10: 100 * 2^9 = 51200 > 500
      expect(handler.getDelayMs(10)).toBe(500);
    });

    it('should respect custom configuration', () => {
      vi.spyOn(Math, 'random').mockReturnValue(0.5); // No jitter

      const handler = new RetryHandler({
        initialDelayMs: 50,
        backoffMultiplier: 3,
      });

      // Attempt 1: 50 * 3^0 = 50
      expect(handler.getDelayMs(1)).toBe(50);

      // Attempt 2: 50 * 3^1 = 150
      expect(handler.getDelayMs(2)).toBe(150);
    });

    it('should handle attempt 0 gracefully', () => {
      vi.spyOn(Math, 'random').mockReturnValue(0.5);
      const handler = new RetryHandler({ initialDelayMs: 100, backoffMultiplier: 2 });
      // Attempt 0: 100 * 2^-1 = 50
      expect(handler.getDelayMs(0)).toBe(50);
    });
    });
  });

describe('createApiErrorFromResponse', () => {
  it('should create an ApiError from a JSON response', async () => {
    const responseBody = { message: 'Invalid input data' };
    const response = new Response(JSON.stringify(responseBody), {
      status: 400,
      headers: { 'content-type': 'application/json' },
    });

    const error = await createApiErrorFromResponse(response);

    expect(error.message).toBe('Invalid input data');
    expect(error.type).toBe(ApiErrorType.BAD_REQUEST);
    expect(error.statusCode).toBe(400);
    expect(error.responseData).toEqual(responseBody);
    expect(error.isRetryable).toBe(false);
  });

  it('should create an ApiError from a text response', async () => {
    const responseText = 'Internal Server Error';
    const response = new Response(responseText, {
      status: 500,
      headers: { 'content-type': 'text/plain' },
    });

    const error = await createApiErrorFromResponse(response);

    expect(error.message).toBe('Internal Server Error');
    expect(error.type).toBe(ApiErrorType.INTERNAL_SERVER_ERROR);
    expect(error.statusCode).toBe(500);
    expect(error.isRetryable).toBe(true);
  });

  it('should handle malformed JSON gracefully', async () => {
    const malformedJson = '{ invalid: json }';
    const response = new Response(malformedJson, {
      status: 422,
      headers: { 'content-type': 'application/json' },
    });

    const error = await createApiErrorFromResponse(response);

    // Should fall back to status text/code as parsing failed
    expect(error.message).toBe('HTTP 422');
    expect(error.type).toBe(ApiErrorType.UNPROCESSABLE_ENTITY);
    expect(error.statusCode).toBe(422);
  });

  it('should handle empty response body', async () => {
    const response = new Response(null, {
      status: 404,
    });

    const error = await createApiErrorFromResponse(response);

    expect(error.message).toBe('HTTP 404');
    expect(error.type).toBe(ApiErrorType.NOT_FOUND);
    expect(error.statusCode).toBe(404);
  });

  it('should map various status codes correctly', async () => {
    const testCases = [
      { status: 401, expectedType: ApiErrorType.UNAUTHORIZED },
      { status: 403, expectedType: ApiErrorType.FORBIDDEN },
      { status: 429, expectedType: ApiErrorType.RATE_LIMITED },
      { status: 503, expectedType: ApiErrorType.SERVICE_UNAVAILABLE },
    ];

    for (const { status, expectedType } of testCases) {
      const response = new Response(null, { status });
      const error = await createApiErrorFromResponse(response);
      expect(error.type).toBe(expectedType);
      expect(error.statusCode).toBe(status);
    }
  });

  it('should mark rate limit and server errors as retryable', async () => {
    const retryableStatuses = [429, 500, 502, 503, 504];
    const nonRetryableStatuses = [400, 401, 403, 404, 422];

    for (const status of retryableStatuses) {
      const response = new Response(null, { status });
      const error = await createApiErrorFromResponse(response);
      expect(error.isRetryable).toBe(true);
    }

    for (const status of nonRetryableStatuses) {
      const response = new Response(null, { status });
      const error = await createApiErrorFromResponse(response);
      expect(error.isRetryable).toBe(false);
    }
  });

  it('should preserve passed context', async () => {
    const context = { endpoint: '/api/test', method: 'POST' };
    const response = new Response(null, { status: 400 });

    const error = await createApiErrorFromResponse(response, context);

    expect(error.context).toMatchObject(context);
    expect(error.context.statusCode).toBe(400);
    expect(error.context.timestamp).toBeDefined();
  });
});

describe('ApiError.getUserMessage', () => {
  it('returns mapped user-facing text for each ApiErrorType', () => {
    const expectedMessages: Record<ApiErrorType, string> = {
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

    Object.entries(expectedMessages).forEach(([type, expectedMessage]) => {
      const error = new ApiError('Original error message', type as ApiErrorType);
      expect(error.getUserMessage()).toBe(expectedMessage);
    });
  });

  it('falls back to original message for unknown runtime type', () => {
    const unknownType = 'NON_EXISTENT_TYPE' as ApiErrorType;
    const error = new ApiError('Fallback message', unknownType);
    expect(error.getUserMessage()).toBe('Fallback message');
  });

  it('uses UNKNOWN default mapping when type is omitted', () => {
    const error = new ApiError('Some error');
    expect(error.getUserMessage()).toBe('An unexpected error occurred.');
  });
});
