/**
 * Ollama connectivity and model availability utilities.
 * Pure functions — no React dependencies, fully testable in isolation.
 */

/**
 * Connectivity status of the configured Ollama host.
 *
 * - `'reachable'`           — Ollama host responded with at least one model
 * - `'reachable_no_models'` — Ollama host responded HTTP 200 but the models array is empty
 * - `'unreachable'`         — Query failed (network error, non-200, timeout) or no data received
 * - `'no_provider'`         — No Ollama AIProvider record exists for this organization
 */
export type OllamaConnectivityStatus =
  | 'reachable'
  | 'reachable_no_models'
  | 'unreachable'
  | 'no_provider';

/**
 * Subset of the React Query state for the Ollama models endpoint.
 * Decouples components from React Query internals while exposing
 * the fields needed to derive connectivity and refresh state.
 */
export interface OllamaQueryState {
  data: { models: string[] } | undefined;
  isError: boolean;
  isLoading: boolean;
  isFetching: boolean;
}

/**
 * Derive the Ollama host connectivity status from provider existence
 * and the current query response state.
 *
 * The mapping is deterministic and total — every valid combination of
 * inputs produces exactly one status value:
 *
 * - `!hasOllamaProvider`                              → `'no_provider'`
 * - `hasOllamaProvider && isError`                    → `'unreachable'`
 * - `hasOllamaProvider && !isError && data undefined` → `'unreachable'`
 * - `hasOllamaProvider && !isError && models.length > 0`  → `'reachable'`
 * - `hasOllamaProvider && !isError && models.length === 0` → `'reachable_no_models'`
 *
 * @param hasOllamaProvider - Whether an Ollama AIProvider record exists for the org
 * @param queryState - Current state of the Ollama models query
 * @returns Exactly one of the four `OllamaConnectivityStatus` values
 */
export function deriveOllamaConnectivity(
  hasOllamaProvider: boolean,
  queryState: OllamaQueryState,
): OllamaConnectivityStatus {
  if (!hasOllamaProvider) return 'no_provider';
  if (queryState.isError) return 'unreachable';
  if (!queryState.data) return 'unreachable';
  if (queryState.data.models.length > 0) return 'reachable';
  return 'reachable_no_models';
}

/**
 * Return the set of persisted Ollama model names that are NOT present
 * in the live model list fetched from the Ollama host.
 *
 * When the live list is empty, an empty set is returned regardless of
 * persisted contents. An empty live list signals a connectivity or
 * host-level issue — not a per-model availability problem — so
 * per-model warnings would be misleading.
 *
 * @param persistedModelNames - Model names from persisted AIProviderModel records
 * @param liveModelNames - Model names returned by the Ollama `/api/tags` endpoint
 * @returns Set of persisted model names not found in the live list
 */
export function getUnavailableOllamaModels(
  persistedModelNames: string[],
  liveModelNames: string[],
): Set<string> {
  if (liveModelNames.length === 0) return new Set();

  const liveSet = new Set(liveModelNames);
  const unavailable = new Set<string>();

  for (const name of persistedModelNames) {
    if (!liveSet.has(name)) {
      unavailable.add(name);
    }
  }

  return unavailable;
}
