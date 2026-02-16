import { ApiClientCore } from "../core/client";

export interface Language {
  code: string;
  name: string;
  native_name: string;
  flag: string;
  progress: number;
  is_default: boolean;
  is_enabled: boolean;
}

export interface TranslationKey {
  key: string;
  en: string;
  es?: string;
  fr?: string;
  pt?: string;
  hi?: string;
  zh?: string;
  ar?: string;
  sw?: string;
  ja?: string;
  de?: string;
  status: "complete" | "pending";
}

export interface LanguageStats {
  total_languages: number;
  enabled_languages: number;
  total_strings: number;
  translated: number;
  needs_review: number;
  untranslated: number;
  average_progress: number;
}

export class LanguageService {
  constructor(private client: ApiClientCore) {}

  async listLanguages(enabledOnly: boolean = false) {
    const params = new URLSearchParams();
    if (enabledOnly) params.append("enabled_only", "true");
    return this.client.get<{
      status: string;
      data: Language[];
      total: number;
    }>(`/api/v2/languages?${params}`);
  }

  async getStats() {
    return this.client.get<{ status: string; data: LanguageStats }>(
      "/api/v2/languages/stats"
    );
  }

  async getLanguage(languageCode: string) {
    return this.client.get<{ status: string; data: Language }>(
      `/api/v2/languages/${languageCode}`
    );
  }

  async updateLanguage(
    languageCode: string,
    data: { is_enabled?: boolean; is_default?: boolean }
  ) {
    return this.client.patch<{
      status: string;
      data: Language;
      message: string;
    }>(`/api/v2/languages/${languageCode}`, data);
  }

  async listTranslationKeys(params?: {
    language_code?: string;
    status?: string;
    limit?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.language_code)
      searchParams.append("language_code", params.language_code);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.limit) searchParams.append("limit", String(params.limit));
    
    return this.client.get<{
      status: string;
      data: TranslationKey[];
      total: number;
    }>(`/api/v2/languages/translations/keys?${searchParams}`);
  }

  async createTranslationKey(key: string, enValue: string) {
    return this.client.post<{
      status: string;
      data: TranslationKey;
      message: string;
    }>(
      `/api/v2/languages/translations/keys?key=${encodeURIComponent(
        key
      )}&en_value=${encodeURIComponent(enValue)}`,
      {}
    );
  }

  async updateTranslation(key: string, languageCode: string, value: string) {
    return this.client.patch<{
      status: string;
      data: TranslationKey;
      message: string;
    }>(`/api/v2/languages/translations/keys/${encodeURIComponent(key)}`, {
      key,
      language_code: languageCode,
      value,
    });
  }

  async exportTranslations(languageCode: string, format: string = "json") {
    return this.client.post<{
      status: string;
      data: {
        language: string;
        format: string;
        translations: Record<string, string>;
        count: number;
      };
      message: string;
    }>(
      `/api/v2/languages/export?language_code=${languageCode}&format=${format}`,
      {}
    );
  }
  async autoTranslate(languageCode: string) {
    return this.client.post<{
      status: string;
      message: string;
      note?: string;
    }>(`/api/v2/languages/${languageCode}/auto-translate`, {});
  }
}
