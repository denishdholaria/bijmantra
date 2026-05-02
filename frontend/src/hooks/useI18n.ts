import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Language,
  SUPPORTED_LANGUAGES,
  TranslationKey,
  getTranslation,
  getTranslations,
  formatNumber,
  formatDate,
  formatRelativeTime,
} from '@/lib/i18n';

const STORAGE_KEY = 'bijmantra-language';

// Detect browser language
function detectBrowserLanguage(): Language {
  const browserLang = navigator.language.split('-')[0];
  if (browserLang in SUPPORTED_LANGUAGES) {
    return browserLang as Language;
  }
  return 'en';
}

// Get initial language from storage or browser
function getInitialLanguage(): Language {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && stored in SUPPORTED_LANGUAGES) {
    return stored as Language;
  }
  return detectBrowserLanguage();
}

export function useI18n() {
  const [language, setLanguageState] = useState<Language>(getInitialLanguage);
  const [isRTL, setIsRTL] = useState(false);

  // Get language config
  const languageConfig = useMemo(() => SUPPORTED_LANGUAGES[language], [language]);

  // Get all translations for current language
  const translations = useMemo(() => getTranslations(language), [language]);

  // Update document direction when language changes
  useEffect(() => {
    const config = SUPPORTED_LANGUAGES[language];
    const direction = config.direction;
    
    document.documentElement.dir = direction;
    document.documentElement.lang = language;
    setIsRTL(direction === 'rtl');

    // Add RTL class for styling
    if (direction === 'rtl') {
      document.documentElement.classList.add('rtl');
    } else {
      document.documentElement.classList.remove('rtl');
    }
  }, [language]);

  // Set language and persist
  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem(STORAGE_KEY, lang);
  }, []);

  // Translation function
  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>): string => {
      let text = getTranslation(language, key);
      
      // Replace parameters like {name} with values
      if (params) {
        Object.entries(params).forEach(([param, value]) => {
          text = text.replace(new RegExp(`\\{${param}\\}`, 'g'), String(value));
        });
      }
      
      return text;
    },
    [language]
  );

  // Format number
  const n = useCallback(
    (value: number): string => formatNumber(value, language),
    [language]
  );

  // Format date
  const d = useCallback(
    (date: Date | string): string => formatDate(date, language),
    [language]
  );

  // Format relative time
  const r = useCallback(
    (date: Date | string): string => formatRelativeTime(date, language),
    [language]
  );

  return {
    language,
    setLanguage,
    languageConfig,
    isRTL,
    t,
    n,
    d,
    r,
    translations,
    supportedLanguages: SUPPORTED_LANGUAGES,
  };
}

export type UseI18nReturn = ReturnType<typeof useI18n>;
