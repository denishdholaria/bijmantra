/**
 * Property-based tests for Ollama connectivity and model availability utilities.
 *
 * Uses fast-check to validate correctness properties from the design spec:
 * - Property 1: getUnavailableOllamaModels is the set difference
 * - Property 2: deriveOllamaConnectivity is a total function over response states
 *
 * Feature: ollama-dynamic-model-selection
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import {
  deriveOllamaConnectivity,
  getUnavailableOllamaModels,
  type OllamaConnectivityStatus,
  type OllamaQueryState,
} from './ollama-utils';

// ── Arbitraries ──────────────────────────────────────────────────────

/** Arbitrary for non-empty model name strings (Ollama model names like "llama3.2:3b"). */
const modelNameArb = fc.string({ minLength: 1, maxLength: 30 });

/** Arbitrary for a non-empty array of model names. */
const nonEmptyModelListArb = fc.array(modelNameArb, { minLength: 1, maxLength: 20 });

/** Arbitrary for any array of model names (including empty). */
const modelListArb = fc.array(modelNameArb, { minLength: 0, maxLength: 20 });

// ── Property 1: Model availability comparison is set difference ──────

describe('Feature: ollama-dynamic-model-selection, Property 1: getUnavailableOllamaModels is set difference', () => {
  it('for any persisted[] and any non-empty live[], result equals { m ∈ persisted | m ∉ live }', () => {
    fc.assert(
      fc.property(
        modelListArb,
        nonEmptyModelListArb,
        (persisted, live) => {
          const result = getUnavailableOllamaModels(persisted, live);
          const liveSet = new Set(live);

          // Every element in result must be in persisted and NOT in live
          for (const name of result) {
            expect(persisted).toContain(name);
            expect(liveSet.has(name)).toBe(false);
          }

          // Every persisted element NOT in live must be in result
          for (const name of persisted) {
            if (!liveSet.has(name)) {
              expect(result.has(name)).toBe(true);
            }
          }

          // No element in result should be in live
          for (const name of result) {
            expect(liveSet.has(name)).toBe(false);
          }
        },
      ),
      { numRuns: 200 },
    );
  });

  it('when live is empty, result is always empty regardless of persisted contents', () => {
    fc.assert(
      fc.property(
        modelListArb,
        (persisted) => {
          const result = getUnavailableOllamaModels(persisted, []);
          expect(result.size).toBe(0);
        },
      ),
      { numRuns: 200 },
    );
  });

  it('when persisted is a subset of live, result is empty', () => {
    fc.assert(
      fc.property(
        nonEmptyModelListArb,
        (live) => {
          // Pick a random subset of live as persisted
          const persisted = live.slice(0, Math.max(1, Math.floor(live.length / 2)));
          const result = getUnavailableOllamaModels(persisted, live);
          expect(result.size).toBe(0);
        },
      ),
      { numRuns: 200 },
    );
  });

  it('when persisted and live are disjoint, result equals the persisted set', () => {
    fc.assert(
      fc.property(
        fc.array(fc.constant('a_model'), { minLength: 1, maxLength: 5 }),
        fc.array(fc.constant('b_model'), { minLength: 1, maxLength: 5 }),
        (persisted, live) => {
          const result = getUnavailableOllamaModels(persisted, live);
          const persistedSet = new Set(persisted);
          expect(result.size).toBe(persistedSet.size);
          for (const name of persistedSet) {
            expect(result.has(name)).toBe(true);
          }
        },
      ),
      { numRuns: 100 },
    );
  });
});

// ── Property 2: Connectivity status derivation is a total function ───

const VALID_STATUSES: OllamaConnectivityStatus[] = [
  'reachable',
  'reachable_no_models',
  'unreachable',
  'no_provider',
];

describe('Feature: ollama-dynamic-model-selection, Property 2: deriveOllamaConnectivity is a total function', () => {
  it('for any combination of inputs, returns exactly one of the four status values', () => {
    fc.assert(
      fc.property(
        fc.boolean(),  // hasOllamaProvider
        fc.boolean(),  // isError
        fc.boolean(),  // isLoading
        fc.boolean(),  // isFetching
        fc.option(modelListArb, { nil: undefined }),  // data?.models or undefined
        (hasOllamaProvider, isError, isLoading, isFetching, models) => {
          const queryState: OllamaQueryState = {
            data: models !== undefined ? { models } : undefined,
            isError,
            isLoading,
            isFetching,
          };

          const result = deriveOllamaConnectivity(hasOllamaProvider, queryState);

          // Must be exactly one of the four valid statuses
          expect(VALID_STATUSES).toContain(result);
        },
      ),
      { numRuns: 500 },
    );
  });

  it('!hasOllamaProvider always yields no_provider regardless of query state', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        fc.boolean(),
        fc.boolean(),
        fc.option(modelListArb, { nil: undefined }),
        (isError, isLoading, isFetching, models) => {
          const queryState: OllamaQueryState = {
            data: models !== undefined ? { models } : undefined,
            isError,
            isLoading,
            isFetching,
          };

          expect(deriveOllamaConnectivity(false, queryState)).toBe('no_provider');
        },
      ),
      { numRuns: 200 },
    );
  });

  it('hasOllamaProvider && isError always yields unreachable', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        fc.boolean(),
        fc.option(modelListArb, { nil: undefined }),
        (isLoading, isFetching, models) => {
          const queryState: OllamaQueryState = {
            data: models !== undefined ? { models } : undefined,
            isError: true,
            isLoading,
            isFetching,
          };

          expect(deriveOllamaConnectivity(true, queryState)).toBe('unreachable');
        },
      ),
      { numRuns: 200 },
    );
  });

  it('hasOllamaProvider && !isError && data undefined yields unreachable', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        fc.boolean(),
        (isLoading, isFetching) => {
          const queryState: OllamaQueryState = {
            data: undefined,
            isError: false,
            isLoading,
            isFetching,
          };

          expect(deriveOllamaConnectivity(true, queryState)).toBe('unreachable');
        },
      ),
      { numRuns: 100 },
    );
  });

  it('hasOllamaProvider && !isError && non-empty models yields reachable', () => {
    fc.assert(
      fc.property(
        nonEmptyModelListArb,
        fc.boolean(),
        fc.boolean(),
        (models, isLoading, isFetching) => {
          const queryState: OllamaQueryState = {
            data: { models },
            isError: false,
            isLoading,
            isFetching,
          };

          expect(deriveOllamaConnectivity(true, queryState)).toBe('reachable');
        },
      ),
      { numRuns: 200 },
    );
  });

  it('hasOllamaProvider && !isError && empty models yields reachable_no_models', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        fc.boolean(),
        (isLoading, isFetching) => {
          const queryState: OllamaQueryState = {
            data: { models: [] },
            isError: false,
            isLoading,
            isFetching,
          };

          expect(deriveOllamaConnectivity(true, queryState)).toBe('reachable_no_models');
        },
      ),
      { numRuns: 100 },
    );
  });
});
