/**
 * Bijmantra Internationalization (i18n) System
 * Supports multiple languages including RTL (Right-to-Left) languages
 */

export type Language = 'en' | 'hi' | 'ar' | 'es' | 'fr' | 'pt' | 'zh';

export interface LanguageConfig {
  code: Language;
  name: string;
  nativeName: string;
  direction: 'ltr' | 'rtl';
  dateFormat: string;
  numberFormat: Intl.NumberFormatOptions;
}

export const SUPPORTED_LANGUAGES: Record<Language, LanguageConfig> = {
  en: {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    direction: 'ltr',
    dateFormat: 'MM/DD/YYYY',
    numberFormat: { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 2 },
  },
  hi: {
    code: 'hi',
    name: 'Hindi',
    nativeName: 'हिन्दी',
    direction: 'ltr',
    dateFormat: 'DD/MM/YYYY',
    numberFormat: { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 2 },
  },
  ar: {
    code: 'ar',
    name: 'Arabic',
    nativeName: 'العربية',
    direction: 'rtl',
    dateFormat: 'DD/MM/YYYY',
    numberFormat: { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 2 },
  },
  es: {
    code: 'es',
    name: 'Spanish',
    nativeName: 'Español',
    direction: 'ltr',
    dateFormat: 'DD/MM/YYYY',
    numberFormat: { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 2 },
  },
  fr: {
    code: 'fr',
    name: 'French',
    nativeName: 'Français',
    direction: 'ltr',
    dateFormat: 'DD/MM/YYYY',
    numberFormat: { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 2 },
  },
  pt: {
    code: 'pt',
    name: 'Portuguese',
    nativeName: 'Português',
    direction: 'ltr',
    dateFormat: 'DD/MM/YYYY',
    numberFormat: { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 2 },
  },
  zh: {
    code: 'zh',
    name: 'Chinese',
    nativeName: '中文',
    direction: 'ltr',
    dateFormat: 'YYYY/MM/DD',
    numberFormat: { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 2 },
  },
};

// Translation keys type
export type TranslationKey = keyof typeof translations.en;

// English translations (base)
const translations = {
  en: {
    // Common
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.create': 'Create',
    'common.search': 'Search',
    'common.filter': 'Filter',
    'common.export': 'Export',
    'common.import': 'Import',
    'common.loading': 'Loading...',
    'common.noData': 'No data available',
    'common.confirm': 'Confirm',
    'common.back': 'Back',
    'common.next': 'Next',
    'common.previous': 'Previous',
    'common.submit': 'Submit',
    'common.reset': 'Reset',
    'common.close': 'Close',
    'common.yes': 'Yes',
    'common.no': 'No',
    'common.all': 'All',
    'common.none': 'None',
    'common.select': 'Select',
    'common.required': 'Required',
    'common.optional': 'Optional',
    'common.actions': 'Actions',
    'common.status': 'Status',
    'common.date': 'Date',
    'common.name': 'Name',
    'common.description': 'Description',
    'common.type': 'Type',
    'common.value': 'Value',
    'common.total': 'Total',
    'common.active': 'Active',
    'common.inactive': 'Inactive',
    'common.pending': 'Pending',
    'common.completed': 'Completed',
    'common.error': 'Error',
    'common.success': 'Success',
    'common.warning': 'Warning',
    'common.info': 'Info',

    // Navigation
    'nav.dashboard': 'Dashboard',
    'nav.programs': 'Programs',
    'nav.trials': 'Trials',
    'nav.studies': 'Studies',
    'nav.germplasm': 'Germplasm',
    'nav.traits': 'Traits',
    'nav.observations': 'Observations',
    'nav.locations': 'Locations',
    'nav.people': 'People',
    'nav.settings': 'Settings',
    'nav.help': 'Help',
    'nav.logout': 'Logout',

    // Divisions
    'division.plantSciences': 'Plant Sciences',
    'division.seedBank': 'Seed Bank',
    'division.earthSystems': 'Earth Systems',
    'division.sunEarth': 'Sun-Earth Systems',
    'division.sensorNetworks': 'Sensor Networks',
    'division.commercial': 'Commercial',
    'division.spaceResearch': 'Space Research',
    'division.integrations': 'Integrations',
    'division.knowledge': 'Knowledge',
    'division.seedOperations': 'Seed Operations',

    // Breeding
    'breeding.program': 'Breeding Program',
    'breeding.trial': 'Trial',
    'breeding.study': 'Study',
    'breeding.cross': 'Cross',
    'breeding.selection': 'Selection',
    'breeding.pedigree': 'Pedigree',
    'breeding.generation': 'Generation',
    'breeding.cycle': 'Cycle',
    'breeding.yield': 'Yield',
    'breeding.heritability': 'Heritability',
    'breeding.geneticGain': 'Genetic Gain',
    'breeding.selectionIndex': 'Selection Index',
    'breeding.breedingValue': 'Breeding Value',

    // Germplasm
    'germplasm.accession': 'Accession',
    'germplasm.variety': 'Variety',
    'germplasm.line': 'Line',
    'germplasm.population': 'Population',
    'germplasm.donor': 'Donor',
    'germplasm.origin': 'Origin',
    'germplasm.passport': 'Passport Data',
    'germplasm.collection': 'Collection',

    // Traits
    'trait.phenotype': 'Phenotype',
    'trait.genotype': 'Genotype',
    'trait.quantitative': 'Quantitative',
    'trait.qualitative': 'Qualitative',
    'trait.measurement': 'Measurement',
    'trait.scale': 'Scale',
    'trait.method': 'Method',
    'trait.unit': 'Unit',

    // Field
    'field.plot': 'Plot',
    'field.block': 'Block',
    'field.replicate': 'Replicate',
    'field.row': 'Row',
    'field.column': 'Column',
    'field.position': 'Position',
    'field.layout': 'Field Layout',
    'field.design': 'Experimental Design',

    // Quality
    'quality.germination': 'Germination',
    'quality.purity': 'Purity',
    'quality.moisture': 'Moisture',
    'quality.vigor': 'Vigor',
    'quality.certificate': 'Certificate',
    'quality.test': 'Test',
    'quality.sample': 'Sample',

    // Messages
    'message.saveSuccess': 'Saved successfully',
    'message.deleteSuccess': 'Deleted successfully',
    'message.createSuccess': 'Created successfully',
    'message.updateSuccess': 'Updated successfully',
    'message.errorOccurred': 'An error occurred',
    'message.confirmDelete': 'Are you sure you want to delete this item?',
    'message.unsavedChanges': 'You have unsaved changes',
    'message.noResults': 'No results found',
    'message.loadingData': 'Loading data...',
  },
  hi: {
    // Common
    'common.save': 'सहेजें',
    'common.cancel': 'रद्द करें',
    'common.delete': 'हटाएं',
    'common.edit': 'संपादित करें',
    'common.create': 'बनाएं',
    'common.search': 'खोजें',
    'common.filter': 'फ़िल्टर',
    'common.export': 'निर्यात',
    'common.import': 'आयात',
    'common.loading': 'लोड हो रहा है...',
    'common.noData': 'कोई डेटा उपलब्ध नहीं',
    'common.confirm': 'पुष्टि करें',
    'common.back': 'वापस',
    'common.next': 'अगला',
    'common.previous': 'पिछला',
    'common.submit': 'जमा करें',
    'common.reset': 'रीसेट',
    'common.close': 'बंद करें',
    'common.yes': 'हाँ',
    'common.no': 'नहीं',
    'common.all': 'सभी',
    'common.none': 'कोई नहीं',
    'common.select': 'चुनें',
    'common.required': 'आवश्यक',
    'common.optional': 'वैकल्पिक',
    'common.actions': 'क्रियाएं',
    'common.status': 'स्थिति',
    'common.date': 'तारीख',
    'common.name': 'नाम',
    'common.description': 'विवरण',
    'common.type': 'प्रकार',
    'common.value': 'मान',
    'common.total': 'कुल',
    'common.active': 'सक्रिय',
    'common.inactive': 'निष्क्रिय',
    'common.pending': 'लंबित',
    'common.completed': 'पूर्ण',
    'common.error': 'त्रुटि',
    'common.success': 'सफलता',
    'common.warning': 'चेतावनी',
    'common.info': 'जानकारी',

    // Navigation
    'nav.dashboard': 'डैशबोर्ड',
    'nav.programs': 'कार्यक्रम',
    'nav.trials': 'परीक्षण',
    'nav.studies': 'अध्ययन',
    'nav.germplasm': 'जर्मप्लाज्म',
    'nav.traits': 'लक्षण',
    'nav.observations': 'अवलोकन',
    'nav.locations': 'स्थान',
    'nav.people': 'लोग',
    'nav.settings': 'सेटिंग्स',
    'nav.help': 'सहायता',
    'nav.logout': 'लॉगआउट',

    // Divisions
    'division.plantSciences': 'पादप विज्ञान',
    'division.seedBank': 'बीज बैंक',
    'division.earthSystems': 'पृथ्वी प्रणाली',
    'division.sunEarth': 'सूर्य-पृथ्वी प्रणाली',
    'division.sensorNetworks': 'सेंसर नेटवर्क',
    'division.commercial': 'वाणिज्यिक',
    'division.spaceResearch': 'अंतरिक्ष अनुसंधान',
    'division.integrations': 'एकीकरण',
    'division.knowledge': 'ज्ञान',
    'division.seedOperations': 'बीज संचालन',

    // Breeding
    'breeding.program': 'प्रजनन कार्यक्रम',
    'breeding.trial': 'परीक्षण',
    'breeding.study': 'अध्ययन',
    'breeding.cross': 'क्रॉस',
    'breeding.selection': 'चयन',
    'breeding.pedigree': 'वंशावली',
    'breeding.generation': 'पीढ़ी',
    'breeding.cycle': 'चक्र',
    'breeding.yield': 'उपज',
    'breeding.heritability': 'वंशागति',
    'breeding.geneticGain': 'आनुवंशिक लाभ',
    'breeding.selectionIndex': 'चयन सूचकांक',
    'breeding.breedingValue': 'प्रजनन मूल्य',

    // Germplasm
    'germplasm.accession': 'परिग्रहण',
    'germplasm.variety': 'किस्म',
    'germplasm.line': 'लाइन',
    'germplasm.population': 'जनसंख्या',
    'germplasm.donor': 'दाता',
    'germplasm.origin': 'उत्पत्ति',
    'germplasm.passport': 'पासपोर्ट डेटा',
    'germplasm.collection': 'संग्रह',

    // Traits
    'trait.phenotype': 'फेनोटाइप',
    'trait.genotype': 'जीनोटाइप',
    'trait.quantitative': 'मात्रात्मक',
    'trait.qualitative': 'गुणात्मक',
    'trait.measurement': 'माप',
    'trait.scale': 'पैमाना',
    'trait.method': 'विधि',
    'trait.unit': 'इकाई',

    // Field
    'field.plot': 'प्लॉट',
    'field.block': 'ब्लॉक',
    'field.replicate': 'प्रतिकृति',
    'field.row': 'पंक्ति',
    'field.column': 'स्तंभ',
    'field.position': 'स्थिति',
    'field.layout': 'क्षेत्र लेआउट',
    'field.design': 'प्रयोगात्मक डिज़ाइन',

    // Quality
    'quality.germination': 'अंकुरण',
    'quality.purity': 'शुद्धता',
    'quality.moisture': 'नमी',
    'quality.vigor': 'ओज',
    'quality.certificate': 'प्रमाणपत्र',
    'quality.test': 'परीक्षण',
    'quality.sample': 'नमूना',

    // Messages
    'message.saveSuccess': 'सफलतापूर्वक सहेजा गया',
    'message.deleteSuccess': 'सफलतापूर्वक हटाया गया',
    'message.createSuccess': 'सफलतापूर्वक बनाया गया',
    'message.updateSuccess': 'सफलतापूर्वक अपडेट किया गया',
    'message.errorOccurred': 'एक त्रुटि हुई',
    'message.confirmDelete': 'क्या आप वाकई इस आइटम को हटाना चाहते हैं?',
    'message.unsavedChanges': 'आपके पास सहेजे नहीं गए परिवर्तन हैं',
    'message.noResults': 'कोई परिणाम नहीं मिला',
    'message.loadingData': 'डेटा लोड हो रहा है...',
  },
  ar: {
    // Common (Arabic - RTL)
    'common.save': 'حفظ',
    'common.cancel': 'إلغاء',
    'common.delete': 'حذف',
    'common.edit': 'تعديل',
    'common.create': 'إنشاء',
    'common.search': 'بحث',
    'common.filter': 'تصفية',
    'common.export': 'تصدير',
    'common.import': 'استيراد',
    'common.loading': 'جاري التحميل...',
    'common.noData': 'لا توجد بيانات',
    'common.confirm': 'تأكيد',
    'common.back': 'رجوع',
    'common.next': 'التالي',
    'common.previous': 'السابق',
    'common.submit': 'إرسال',
    'common.reset': 'إعادة تعيين',
    'common.close': 'إغلاق',
    'common.yes': 'نعم',
    'common.no': 'لا',
    'common.all': 'الكل',
    'common.none': 'لا شيء',
    'common.select': 'اختر',
    'common.required': 'مطلوب',
    'common.optional': 'اختياري',
    'common.actions': 'إجراءات',
    'common.status': 'الحالة',
    'common.date': 'التاريخ',
    'common.name': 'الاسم',
    'common.description': 'الوصف',
    'common.type': 'النوع',
    'common.value': 'القيمة',
    'common.total': 'المجموع',
    'common.active': 'نشط',
    'common.inactive': 'غير نشط',
    'common.pending': 'قيد الانتظار',
    'common.completed': 'مكتمل',
    'common.error': 'خطأ',
    'common.success': 'نجاح',
    'common.warning': 'تحذير',
    'common.info': 'معلومات',

    // Navigation
    'nav.dashboard': 'لوحة التحكم',
    'nav.programs': 'البرامج',
    'nav.trials': 'التجارب',
    'nav.studies': 'الدراسات',
    'nav.germplasm': 'الموارد الوراثية',
    'nav.traits': 'الصفات',
    'nav.observations': 'الملاحظات',
    'nav.locations': 'المواقع',
    'nav.people': 'الأشخاص',
    'nav.settings': 'الإعدادات',
    'nav.help': 'المساعدة',
    'nav.logout': 'تسجيل الخروج',

    // Divisions
    'division.plantSciences': 'علوم النبات',
    'division.seedBank': 'بنك البذور',
    'division.earthSystems': 'أنظمة الأرض',
    'division.sunEarth': 'أنظمة الشمس والأرض',
    'division.sensorNetworks': 'شبكات الاستشعار',
    'division.commercial': 'التجاري',
    'division.spaceResearch': 'أبحاث الفضاء',
    'division.integrations': 'التكاملات',
    'division.knowledge': 'المعرفة',
    'division.seedOperations': 'عمليات البذور',

    // Breeding
    'breeding.program': 'برنامج التربية',
    'breeding.trial': 'تجربة',
    'breeding.study': 'دراسة',
    'breeding.cross': 'تهجين',
    'breeding.selection': 'انتخاب',
    'breeding.pedigree': 'النسب',
    'breeding.generation': 'الجيل',
    'breeding.cycle': 'الدورة',
    'breeding.yield': 'المحصول',
    'breeding.heritability': 'التوريث',
    'breeding.geneticGain': 'المكسب الوراثي',
    'breeding.selectionIndex': 'مؤشر الانتخاب',
    'breeding.breedingValue': 'القيمة التربوية',

    // Germplasm
    'germplasm.accession': 'المدخل',
    'germplasm.variety': 'الصنف',
    'germplasm.line': 'السلالة',
    'germplasm.population': 'المجتمع',
    'germplasm.donor': 'المانح',
    'germplasm.origin': 'الأصل',
    'germplasm.passport': 'بيانات الجواز',
    'germplasm.collection': 'المجموعة',

    // Traits
    'trait.phenotype': 'النمط الظاهري',
    'trait.genotype': 'النمط الوراثي',
    'trait.quantitative': 'كمي',
    'trait.qualitative': 'نوعي',
    'trait.measurement': 'القياس',
    'trait.scale': 'المقياس',
    'trait.method': 'الطريقة',
    'trait.unit': 'الوحدة',

    // Field
    'field.plot': 'القطعة',
    'field.block': 'الكتلة',
    'field.replicate': 'المكرر',
    'field.row': 'الصف',
    'field.column': 'العمود',
    'field.position': 'الموقع',
    'field.layout': 'تخطيط الحقل',
    'field.design': 'التصميم التجريبي',

    // Quality
    'quality.germination': 'الإنبات',
    'quality.purity': 'النقاوة',
    'quality.moisture': 'الرطوبة',
    'quality.vigor': 'القوة',
    'quality.certificate': 'الشهادة',
    'quality.test': 'الاختبار',
    'quality.sample': 'العينة',

    // Messages
    'message.saveSuccess': 'تم الحفظ بنجاح',
    'message.deleteSuccess': 'تم الحذف بنجاح',
    'message.createSuccess': 'تم الإنشاء بنجاح',
    'message.updateSuccess': 'تم التحديث بنجاح',
    'message.errorOccurred': 'حدث خطأ',
    'message.confirmDelete': 'هل أنت متأكد من حذف هذا العنصر؟',
    'message.unsavedChanges': 'لديك تغييرات غير محفوظة',
    'message.noResults': 'لم يتم العثور على نتائج',
    'message.loadingData': 'جاري تحميل البيانات...',
  },
} as const;

// Add partial translations for other languages (Spanish, French, Portuguese, Chinese)
// These would be filled in by translators
const partialTranslations: Record<string, Record<string, string>> = {
  es: {
    'common.save': 'Guardar',
    'common.cancel': 'Cancelar',
    'common.delete': 'Eliminar',
    'common.search': 'Buscar',
    'nav.dashboard': 'Panel de Control',
    'nav.programs': 'Programas',
    'division.plantSciences': 'Ciencias Vegetales',
  },
  fr: {
    'common.save': 'Enregistrer',
    'common.cancel': 'Annuler',
    'common.delete': 'Supprimer',
    'common.search': 'Rechercher',
    'nav.dashboard': 'Tableau de Bord',
    'nav.programs': 'Programmes',
    'division.plantSciences': 'Sciences Végétales',
  },
  pt: {
    'common.save': 'Salvar',
    'common.cancel': 'Cancelar',
    'common.delete': 'Excluir',
    'common.search': 'Pesquisar',
    'nav.dashboard': 'Painel',
    'nav.programs': 'Programas',
    'division.plantSciences': 'Ciências Vegetais',
  },
  zh: {
    'common.save': '保存',
    'common.cancel': '取消',
    'common.delete': '删除',
    'common.search': '搜索',
    'nav.dashboard': '仪表板',
    'nav.programs': '项目',
    'division.plantSciences': '植物科学',
  },
};

export type Translations = typeof translations;

// Get translation for a key
export function getTranslation(lang: Language, key: TranslationKey): string {
  // Try to get from full translations
  if (lang in translations) {
    const langTranslations = translations[lang as keyof typeof translations];
    if (key in langTranslations) {
      return langTranslations[key as keyof typeof langTranslations];
    }
  }

  // Try partial translations
  if (lang in partialTranslations) {
    const partial = partialTranslations[lang];
    if (partial && key in partial) {
      return partial[key as keyof typeof partial] as string;
    }
  }

  // Fallback to English
  return translations.en[key];
}

// Get all translations for a language
export function getTranslations(lang: Language): Record<TranslationKey, string> {
  const base = { ...translations.en };
  
  if (lang in translations && lang !== 'en') {
    Object.assign(base, translations[lang as keyof typeof translations]);
  } else if (lang in partialTranslations) {
    Object.assign(base, partialTranslations[lang]);
  }

  return base;
}

// Format number according to locale
export function formatNumber(value: number, lang: Language): string {
  const config = SUPPORTED_LANGUAGES[lang];
  return new Intl.NumberFormat(lang, config.numberFormat).format(value);
}

// Format date according to locale
export function formatDate(date: Date | string, lang: Language): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(lang, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(d);
}

// Format relative time
export function formatRelativeTime(date: Date | string, lang: Language): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  const rtf = new Intl.RelativeTimeFormat(lang, { numeric: 'auto' });

  if (diffDays === 0) {
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours === 0) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      return rtf.format(-diffMinutes, 'minute');
    }
    return rtf.format(-diffHours, 'hour');
  } else if (diffDays < 30) {
    return rtf.format(-diffDays, 'day');
  } else if (diffDays < 365) {
    return rtf.format(-Math.floor(diffDays / 30), 'month');
  }
  return rtf.format(-Math.floor(diffDays / 365), 'year');
}

export { translations };
