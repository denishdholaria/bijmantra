/**
 * Quote System Rotation Logic
 * 
 * Handles quote selection, rotation, and region-aware randomization.
 */

import type { QuoteRegion } from './types'
import { quotes, quoteRegions } from './data'

export function formatRegionLabel(region: string) {
  return region
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function getRandomItem<T>(items: T[]) {
  return items[Math.floor(Math.random() * items.length)]
}

export function getQuoteIndicesForRegion(region: QuoteRegion, excludedIndex?: number) {
  return quotes
    .map((quote, index) => ({ index, region: quote.region }))
    .filter((quote) => quote.region === region && quote.index !== excludedIndex)
    .map((quote) => quote.index)
}

export function getPreferredQuoteIndex(currentIndex: number, preferredRegion: QuoteRegion | null) {
  if (!preferredRegion) {
    return getBalancedRandomQuoteIndex(currentIndex)
  }

  const preferred = getQuoteIndicesForRegion(preferredRegion, currentIndex)
  if (preferred.length > 0) {
    return getRandomItem(preferred)
  }

  return getBalancedRandomQuoteIndex(currentIndex)
}

export function getRegionAwareRandomQuoteIndex(currentIndex: number, preferredRegion: QuoteRegion | null) {
  if (!preferredRegion) {
    return getBalancedRandomQuoteIndex(currentIndex)
  }

  const preferred = getQuoteIndicesForRegion(preferredRegion, currentIndex)
  const global = preferredRegion === 'global' ? [] : getQuoteIndicesForRegion('global', currentIndex)
  const others = quotes
    .map((quote, index) => ({ index, region: quote.region }))
    .filter((quote) => quote.index !== currentIndex && quote.region !== preferredRegion && quote.region !== 'global')
    .map((quote) => quote.index)

  const pools = [
    preferred.length > 0 ? { weight: 55, indices: preferred } : null,
    global.length > 0 ? { weight: 20, indices: global } : null,
    others.length > 0 ? { weight: 25, indices: others } : null,
  ].filter((pool): pool is { weight: number; indices: number[] } => pool !== null)

  if (pools.length === 0) {
    return getBalancedRandomQuoteIndex(currentIndex)
  }

  const totalWeight = pools.reduce((sum, pool) => sum + pool.weight, 0)
  let threshold = Math.random() * totalWeight

  for (const pool of pools) {
    threshold -= pool.weight
    if (threshold <= 0) {
      return getRandomItem(pool.indices)
    }
  }

  return getRandomItem(pools[pools.length - 1].indices)
}

export function getBalancedRandomQuoteIndex(currentIndex: number) {
  if (quotes.length <= 1 || quoteRegions.length <= 1) {
    return 0
  }

  const currentRegion = quotes[currentIndex]?.region
  const candidateRegions = quoteRegions.filter((region) => region !== currentRegion)
  const nextRegion = candidateRegions[Math.floor(Math.random() * candidateRegions.length)]
  const candidates = quotes
    .map((quote, index) => ({ index, region: quote.region }))
    .filter((quote) => quote.region === nextRegion && quote.index !== currentIndex)

  return candidates[Math.floor(Math.random() * candidates.length)].index
}
