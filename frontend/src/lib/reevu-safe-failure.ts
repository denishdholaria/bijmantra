export interface ReevuSafeFailure {
  error_category: string
  searched: string[]
  missing: string[]
  next_steps: string[]
  missing_context?: Array<Record<string, unknown>>
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(item => typeof item === 'string')
}

export function isReevuSafeFailure(value: unknown): value is ReevuSafeFailure {
  return Boolean(value)
    && typeof value === 'object'
    && typeof (value as ReevuSafeFailure).error_category === 'string'
    && isStringArray((value as ReevuSafeFailure).searched)
    && isStringArray((value as ReevuSafeFailure).missing)
    && isStringArray((value as ReevuSafeFailure).next_steps)
    && (
      (value as ReevuSafeFailure).missing_context === undefined
      || (
        Array.isArray((value as ReevuSafeFailure).missing_context)
        && (value as ReevuSafeFailure).missing_context!.every(
          item => Boolean(item) && typeof item === 'object' && !Array.isArray(item),
        )
      )
    )
}

export function buildReevuSafeFailureMessage(safeFailure: ReevuSafeFailure): string {
  switch (safeFailure.error_category) {
    case 'insufficient_evidence':
      return 'REEVU could not produce a grounded answer from current system state.'
    case 'streaming_error':
      return 'REEVU could not complete the response stream safely.'
    case 'insufficient_retrieval_scope':
      return 'REEVU could not resolve enough scoped records to answer safely.'
    case 'ambiguous_retrieval_scope':
      return 'REEVU found multiple possible matches and will not guess.'
    case 'insufficient_compute_inputs':
      return 'REEVU could not complete the requested computation with the available inputs.'
    default:
      return 'REEVU stopped with a structured safe failure instead of guessing.'
  }
}
