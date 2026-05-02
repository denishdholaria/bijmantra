/**
 * Quote System Types
 * 
 * Type definitions for the multilingual agricultural quote system.
 */

export interface Quote {
  original: string
  translation: string
  source: string
  culture: string
  icon: string
  region: string
}

export type QuoteRegion = Quote['region']

export type RegionColorMap = Record<string, string>
