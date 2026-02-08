/**
 * API Query Builder and Helpers
 * Provides comprehensive utilities for constructing complex API requests
 * with support for pagination, filtering, sorting, and date ranges.
 * 
 * @status AVAILABLE - Not yet integrated into existing api-client.ts methods
 * @phase v1.1 - Gradual adoption in new code
 * 
 * ## Usage Note (January 2026)
 * 
 * This module was created by GitHub Copilot (Claude Haiku 4.5) and reviewed
 * for BijMantra integration. The QueryBuilder is well-designed but the existing
 * api-client.ts uses explicit URLSearchParams in 40+ methods.
 * 
 * **Current Decision**: Keep as utility, do NOT refactor existing methods.
 * **Future Plan**: Use QueryBuilder for NEW API methods where complex filtering is needed.
 * 
 * ## When to Use QueryBuilder
 * 
 * ✅ Good fit:
 * - New endpoints with complex filtering (multiple operators)
 * - Search pages with dynamic filters
 * - Reports with date ranges and sorting
 * 
 * ❌ Not needed:
 * - Simple CRUD endpoints (use existing pattern)
 * - Endpoints with 1-2 fixed parameters
 * 
 * ## Example Usage
 * 
 * ```typescript
 * import { createQueryBuilder } from '@/lib/api-helpers'
 * 
 * const query = createQueryBuilder()
 *   .eq('status', 'active')
 *   .gte('created_at', '2026-01-01')
 *   .sort('name', 'asc')
 *   .page(1, 20)
 * 
 * const url = query.buildUrl('/api/v2/germplasm')
 * // Result: /api/v2/germplasm?status=active&created_at_from=2026-01-01&sort=name:asc&limit=20&offset=0
 * ```
 * 
 * @see api-client.ts - Main API client (uses URLSearchParams directly)
 * @see api-errors.ts - Error handling (integrated)
 * @see logger.ts - Logging utility (integrated)
 */

/**
 * Filter operator types for query conditions
 */
export type FilterOperator =
  | 'eq'      // equals
  | 'ne'      // not equals
  | 'gt'      // greater than
  | 'gte'     // greater than or equal
  | 'lt'      // less than
  | 'lte'     // less than or equal
  | 'in'      // in array
  | 'nin'     // not in array
  | 'like'    // contains/pattern match
  | 'ilike'   // case-insensitive contains
  | 'exists'  // field exists
  | 'between' // between range
  | 'regex';  // regular expression

/**
 * Sort order direction
 */
export type SortDirection = 'asc' | 'desc';

/**
 * Filter condition structure
 */
export interface FilterCondition {
  field: string;
  operator: FilterOperator;
  value: any;
}

/**
 * Sort specification
 */
export interface SortSpec {
  field: string;
  direction: SortDirection;
}

/**
 * Date range specification
 */
export interface DateRange {
  startDate?: Date | string;
  endDate?: Date | string;
  field?: string; // field to apply date range to
}

/**
 * Pagination specification
 */
export interface PaginationSpec {
  limit: number;
  offset: number;
}

/**
 * Query parameters object
 */
export interface QueryParams {
  [key: string]: any;
}

/**
 * Comprehensive QueryBuilder class for constructing complex API requests
 * Supports method chaining for fluent API design
 */
export class QueryBuilder {
  private filters: FilterCondition[] = [];
  private sorts: SortSpec[] = [];
  private pagination: PaginationSpec = { limit: 20, offset: 0 };
  private dateRanges: Map<string, DateRange> = new Map();
  private includes: string[] = [];
  private excludes: string[] = [];
  private searchQuery: string = '';
  private customParams: QueryParams = {};

  /**
   * Add a filter condition to the query
   */
  filter(field: string, operator: FilterOperator, value: any): this {
    this.filters.push({ field, operator, value });
    return this;
  }

  /**
   * Add an equals filter condition (shorthand)
   */
  eq(field: string, value: any): this {
    return this.filter(field, 'eq', value);
  }

  /**
   * Add a not equals filter condition (shorthand)
   */
  ne(field: string, value: any): this {
    return this.filter(field, 'ne', value);
  }

  /**
   * Add a greater than filter condition (shorthand)
   */
  gt(field: string, value: any): this {
    return this.filter(field, 'gt', value);
  }

  /**
   * Add a greater than or equal filter condition (shorthand)
   */
  gte(field: string, value: any): this {
    return this.filter(field, 'gte', value);
  }

  /**
   * Add a less than filter condition (shorthand)
   */
  lt(field: string, value: any): this {
    return this.filter(field, 'lt', value);
  }

  /**
   * Add a less than or equal filter condition (shorthand)
   */
  lte(field: string, value: any): this {
    return this.filter(field, 'lte', value);
  }

  /**
   * Add an "in" filter condition (shorthand)
   */
  in(field: string, values: any[]): this {
    return this.filter(field, 'in', values);
  }

  /**
   * Add a "not in" filter condition (shorthand)
   */
  nin(field: string, values: any[]): this {
    return this.filter(field, 'nin', values);
  }

  /**
   * Add a contains/pattern match filter (shorthand)
   */
  like(field: string, value: string): this {
    return this.filter(field, 'like', value);
  }

  /**
   * Add a case-insensitive contains filter (shorthand)
   */
  ilike(field: string, value: string): this {
    return this.filter(field, 'ilike', value);
  }

  /**
   * Add a between range filter
   */
  between(field: string, min: any, max: any): this {
    return this.filter(field, 'between', { min, max });
  }

  /**
   * Add a sorting criterion
   */
  sort(field: string, direction: SortDirection = 'asc'): this {
    this.sorts.push({ field, direction });
    return this;
  }

  /**
   * Add multiple sorting criteria
   */
  sortBy(sorts: Array<{ field: string; direction?: SortDirection }>): this {
    sorts.forEach((sort) => {
      this.sort(sort.field, sort.direction || 'asc');
    });
    return this;
  }

  /**
   * Set pagination parameters
   */
  paginate(limit: number, offset: number = 0): this {
    this.pagination = { limit, offset };
    return this;
  }

  /**
   * Set limit only (keeps current offset)
   */
  limit(limit: number): this {
    this.pagination.limit = limit;
    return this;
  }

  /**
   * Set offset (page) only (keeps current limit)
   */
  offset(offset: number): this {
    this.pagination.offset = offset;
    return this;
  }

  /**
   * Set pagination using page number and page size
   */
  page(pageNumber: number, pageSize: number = 20): this {
    if (pageNumber < 1) {
      throw new Error('Page number must be greater than 0');
    }
    this.pagination = {
      limit: pageSize,
      offset: (pageNumber - 1) * pageSize,
    };
    return this;
  }

  /**
   * Add a date range filter
   */
  dateRange(
    startDate?: Date | string,
    endDate?: Date | string,
    field: string = 'createdAt'
  ): this {
    this.dateRanges.set(field, { startDate, endDate, field });
    return this;
  }

  /**
   * Add a date range filter for a specific field
   */
  dateRangeFor(
    field: string,
    startDate?: Date | string,
    endDate?: Date | string
  ): this {
    return this.dateRange(startDate, endDate, field);
  }

  /**
   * Add fields to include in response
   */
  include(...fields: string[]): this {
    this.includes.push(...fields);
    return this;
  }

  /**
   * Add fields to exclude from response
   */
  exclude(...fields: string[]): this {
    this.excludes.push(...fields);
    return this;
  }

  /**
   * Set search query
   */
  search(query: string): this {
    this.searchQuery = query;
    return this;
  }

  /**
   * Add custom query parameter
   */
  param(key: string, value: any): this {
    this.customParams[key] = value;
    return this;
  }

  /**
   * Add multiple custom parameters
   */
  params(params: QueryParams): this {
    this.customParams = { ...this.customParams, ...params };
    return this;
  }

  /**
   * Clear all filters
   */
  clearFilters(): this {
    this.filters = [];
    return this;
  }

  /**
   * Clear all sorts
   */
  clearSorts(): this {
    this.sorts = [];
    return this;
  }

  /**
   * Clear all date ranges
   */
  clearDateRanges(): this {
    this.dateRanges.clear();
    return this;
  }

  /**
   * Reset builder to initial state
   */
  reset(): this {
    this.filters = [];
    this.sorts = [];
    this.dateRanges.clear();
    this.includes = [];
    this.excludes = [];
    this.searchQuery = '';
    this.customParams = {};
    this.pagination = { limit: 20, offset: 0 };
    return this;
  }

  /**
   * Get current filters
   */
  getFilters(): FilterCondition[] {
    return [...this.filters];
  }

  /**
   * Get current sorts
   */
  getSorts(): SortSpec[] {
    return [...this.sorts];
  }

  /**
   * Get current pagination
   */
  getPagination(): PaginationSpec {
    return { ...this.pagination };
  }

  /**
   * Get current date ranges
   */
  getDateRanges(): DateRange[] {
    return Array.from(this.dateRanges.values());
  }

  /**
   * Build query string for URL
   */
  buildQueryString(): string {
    const params = this.buildParams();
    const queryString = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((v) => queryString.append(key, String(v)));
      } else if (value !== null && value !== undefined && value !== '') {
        queryString.append(key, String(value));
      }
    });

    return queryString.toString();
  }

  /**
   * Build complete query parameters object
   */
  buildParams(): QueryParams {
    const params: QueryParams = {};

    // Add pagination
    params.limit = this.pagination.limit;
    params.offset = this.pagination.offset;

    // Add filters
    if (this.filters.length > 0) {
      params.filters = this.filters.map((f) => ({
        field: f.field,
        operator: f.operator,
        value: f.value,
      }));
    }

    // Add sorts
    if (this.sorts.length > 0) {
      params.sort = this.sorts
        .map((s) => `${s.field}:${s.direction}`)
        .join(',');
    }

    // Add date ranges
    if (this.dateRanges.size > 0) {
      this.dateRanges.forEach((range, field) => {
        if (range.startDate) {
          params[`${field}_from`] = this.formatDate(range.startDate);
        }
        if (range.endDate) {
          params[`${field}_to`] = this.formatDate(range.endDate);
        }
      });
    }

    // Add includes
    if (this.includes.length > 0) {
      params.include = this.includes.join(',');
    }

    // Add excludes
    if (this.excludes.length > 0) {
      params.exclude = this.excludes.join(',');
    }

    // Add search
    if (this.searchQuery) {
      params.search = this.searchQuery;
    }

    // Add custom parameters
    return { ...params, ...this.customParams };
  }

  /**
   * Build URL with query parameters
   */
  buildUrl(baseUrl: string): string {
    const queryString = this.buildQueryString();
    if (!queryString) return baseUrl;

    const separator = baseUrl.includes('?') ? '&' : '?';
    return `${baseUrl}${separator}${queryString}`;
  }

  /**
   * Clone the current builder state
   */
  clone(): QueryBuilder {
    const cloned = new QueryBuilder();
    cloned.filters = JSON.parse(JSON.stringify(this.filters));
    cloned.sorts = JSON.parse(JSON.stringify(this.sorts));
    cloned.pagination = { ...this.pagination };
    cloned.includes = [...this.includes];
    cloned.excludes = [...this.excludes];
    cloned.searchQuery = this.searchQuery;
    cloned.customParams = { ...this.customParams };

    this.dateRanges.forEach((range, key) => {
      cloned.dateRanges.set(key, { ...range });
    });

    return cloned;
  }

  /**
   * Format date to ISO string
   */
  private formatDate(date: Date | string): string {
    if (typeof date === 'string') return date;
    return date.toISOString().split('T')[0];
  }

  /**
   * Get a human-readable representation of the query
   */
  toString(): string {
    const parts: string[] = [];

    if (this.filters.length > 0) {
      parts.push(
        `Filters: ${this.filters.map((f) => `${f.field} ${f.operator} ${JSON.stringify(f.value)}`).join(', ')}`
      );
    }

    if (this.sorts.length > 0) {
      parts.push(
        `Sort: ${this.sorts.map((s) => `${s.field} ${s.direction}`).join(', ')}`
      );
    }

    if (this.searchQuery) {
      parts.push(`Search: "${this.searchQuery}"`);
    }

    parts.push(
      `Pagination: limit=${this.pagination.limit}, offset=${this.pagination.offset}`
    );

    return parts.join(' | ');
  }
}

/**
 * Helper function to create a new QueryBuilder instance
 */
export function createQueryBuilder(): QueryBuilder {
  return new QueryBuilder();
}

/**
 * Helper function to encode query parameters for API requests
 */
export function encodeQueryParams(params: QueryParams): string {
  const searchParams = new URLSearchParams();

  const addParam = (key: string, value: any) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        searchParams.append(key, String(item));
      });
    } else if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, String(value));
    }
  };

  Object.entries(params).forEach(([key, value]) => {
    addParam(key, value);
  });

  return searchParams.toString();
}

/**
 * Helper function to decode query parameters from URL
 */
export function decodeQueryParams(queryString: string): QueryParams {
  const params: QueryParams = {};
  const searchParams = new URLSearchParams(queryString);

  searchParams.forEach((value, key) => {
    if (params[key] === undefined) {
      params[key] = value;
    } else if (Array.isArray(params[key])) {
      params[key].push(value);
    } else {
      params[key] = [params[key], value];
    }
  });

  return params;
}

/**
 * Helper function to build API request headers with common defaults
 */
export interface RequestHeaderOptions {
  contentType?: 'application/json' | 'application/x-www-form-urlencoded';
  authorization?: string;
  customHeaders?: Record<string, string>;
}

export function buildRequestHeaders(options: RequestHeaderOptions = {}): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': options.contentType || 'application/json',
  };

  if (options.authorization) {
    headers['Authorization'] = options.authorization;
  }

  if (options.customHeaders) {
    Object.assign(headers, options.customHeaders);
  }

  return headers;
}

/**
 * API Response wrapper interface
 */
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
  errors?: Record<string, string[]>;
  meta?: {
    total?: number;
    page?: number;
    pageSize?: number;
    hasMore?: boolean;
  };
}

/**
 * Helper to handle API response transformations
 */
export async function handleApiResponse<T>(
  response: Response
): Promise<ApiResponse<T>> {
  const data = await response.json();

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} - ${data.message || 'Unknown error'}`);
  }

  return {
    status: response.status,
    data: data.data || data,
    message: data.message,
    errors: data.errors,
    meta: data.meta,
  };
}

/**
 * Create an API request with query builder
 */
export async function makeApiRequest<T>(
  url: string,
  queryBuilder: QueryBuilder,
  options: RequestInit & RequestHeaderOptions = {}
): Promise<ApiResponse<T>> {
  const builtUrl = queryBuilder.buildUrl(url);
  const headers = buildRequestHeaders({
    contentType: 'application/json',
    ...options,
  });

  const response = await fetch(builtUrl, {
    ...options,
    headers,
  });

  return handleApiResponse<T>(response);
}

/**
 * Validation helper for query parameters
 */
export interface ValidationRule {
  field: string;
  validate: (value: any) => boolean | string; // Returns true if valid, error message if invalid
}

export function validateQueryParams(
  params: QueryParams,
  rules?: ValidationRule[]
): { valid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {};

  if (!rules) {
    return { valid: true, errors: {} };
  }

  rules.forEach((rule) => {
    const value = params[rule.field];
    const result = rule.validate(value);

    if (result !== true && typeof result === 'string') {
      errors[rule.field] = result;
    }
  });

  return {
    valid: Object.keys(errors).length === 0,
    errors,
  };
}
