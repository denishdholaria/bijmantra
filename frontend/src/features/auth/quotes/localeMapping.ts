/**
 * Quote System Locale Mapping
 * 
 * Maps user locales to quote regions for personalized quote selection.
 */

import type { QuoteRegion } from './types'

export const localeCountryRegionMap: Record<string, QuoteRegion> = {
  IN: 'india',
  LK: 'south-asia',
  NP: 'south-asia',
  BD: 'south-asia',
  PK: 'south-asia',
  BT: 'south-asia',
  MV: 'south-asia',
  CN: 'east-asia',
  JP: 'east-asia',
  KR: 'east-asia',
  KP: 'east-asia',
  TW: 'east-asia',
  HK: 'east-asia',
  MO: 'east-asia',
  TH: 'southeast-asia',
  VN: 'southeast-asia',
  ID: 'southeast-asia',
  MY: 'southeast-asia',
  SG: 'southeast-asia',
  PH: 'southeast-asia',
  KH: 'southeast-asia',
  LA: 'southeast-asia',
  MM: 'southeast-asia',
  BN: 'southeast-asia',
  TL: 'southeast-asia',
  AE: 'middle-east',
  SA: 'middle-east',
  IR: 'middle-east',
  IQ: 'middle-east',
  IL: 'middle-east',
  JO: 'middle-east',
  LB: 'middle-east',
  OM: 'middle-east',
  QA: 'middle-east',
  KW: 'middle-east',
  BH: 'middle-east',
  PS: 'middle-east',
  YE: 'middle-east',
  NG: 'africa',
  ET: 'africa',
  KE: 'africa',
  TZ: 'africa',
  UG: 'africa',
  GH: 'africa',
  ZA: 'africa',
  RW: 'africa',
  MX: 'americas',
  BR: 'americas',
  AR: 'americas',
  CL: 'americas',
  PE: 'americas',
  CO: 'americas',
  EC: 'americas',
  BO: 'americas',
  PY: 'americas',
  UY: 'americas',
  US: 'americas',
  CA: 'americas',
  FR: 'europe',
  DE: 'europe',
  IT: 'europe',
  ES: 'europe',
  PT: 'europe',
  GR: 'europe',
  NL: 'europe',
  BE: 'europe',
  PL: 'europe',
  CZ: 'europe',
  HU: 'europe',
  RO: 'europe',
  DK: 'europe',
  SE: 'europe',
  FI: 'europe',
  NO: 'europe',
  IE: 'europe',
  GB: 'europe',
  UA: 'europe',
  RU: 'europe',
  AU: 'oceania',
  NZ: 'oceania',
  FJ: 'oceania',
  WS: 'oceania',
  TO: 'oceania',
  PG: 'oceania',
}

export const localeLanguageRegionMap: Record<string, QuoteRegion> = {
  hi: 'india',
  sa: 'india',
  ta: 'south-asia',
  zh: 'east-asia',
  ja: 'east-asia',
  ko: 'east-asia',
  th: 'southeast-asia',
  vi: 'southeast-asia',
  id: 'southeast-asia',
  ms: 'southeast-asia',
  ar: 'middle-east',
  fa: 'middle-east',
  he: 'middle-east',
  sw: 'africa',
  am: 'africa',
  yo: 'africa',
  qu: 'americas',
  mi: 'oceania',
  fr: 'europe',
  de: 'europe',
  ru: 'europe',
  el: 'europe',
  es: 'europe',
  pt: 'europe',
  nl: 'europe',
}

export function extractLocaleParts(locale: string) {
  const normalizedLocale = locale.replace(/_/g, '-')
  const parts = normalizedLocale.split('-')
  const language = parts[0]?.toLowerCase() ?? ''
  const region = parts.find((part) => /^[A-Z]{2}$/.test(part)) ?? parts.find((part) => /^\d{3}$/.test(part))

  return {
    language,
    region: region?.toUpperCase(),
  }
}

export function inferThoughtRegion(locales: readonly string[]): QuoteRegion | null {
  for (const locale of locales) {
    const { region } = extractLocaleParts(locale)
    if (region && localeCountryRegionMap[region]) {
      return localeCountryRegionMap[region]
    }
  }

  for (const locale of locales) {
    const { language } = extractLocaleParts(locale)
    if (language && localeLanguageRegionMap[language]) {
      return localeLanguageRegionMap[language]
    }
  }

  return null
}
