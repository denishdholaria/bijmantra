import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, extname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(SCRIPT_DIR, '../src')

const LEGACY_IMPORT_PATTERNS = [
  "@/hooks/useVeenaChat",
  "@/hooks/useVeenaVoice",
  "@/store/veenaSidebarStore",
  "@/components/ai/VeenaSidebar",
  "@/components/ai/VeenaTrigger",
  "@/pages/VeenaChat",
  "@/components/VeenaVoiceInput",
]

const AI_BARREL_IMPORT_PATTERN = /from\s+['"]@\/components\/ai['"]/;
const LEGACY_VEENA_SYMBOL_PATTERN = /\bVeena[A-Za-z0-9_]*\b/;
const ALLOWED_VEENA_SYMBOL_FILES = new Set([
  normalizePath(join(ROOT, 'components/ai/index.ts')),
])

const VEENA_EXPORT_PATTERN = /\bexport\b[^\n]*\bVeena[A-Za-z0-9_]*\b/;
const ALLOWED_VEENA_EXPORT_FILES = new Set([
  normalizePath(join(ROOT, 'hooks/useVeenaChat.ts')),
  normalizePath(join(ROOT, 'hooks/useVeenaVoice.ts')),
  normalizePath(join(ROOT, 'store/veenaSidebarStore.ts')),
  normalizePath(join(ROOT, 'pages/VeenaChat.tsx')),
  normalizePath(join(ROOT, 'components/VeenaVoiceInput.tsx')),
  normalizePath(join(ROOT, 'components/ai/index.ts')),
  normalizePath(join(ROOT, 'components/ai/VeenaSidebar.tsx')),
  normalizePath(join(ROOT, 'components/ai/VeenaTrigger.tsx')),
])

const LEGACY_API_ALIAS_PATTERNS = [
  /\bgetVeenaSummary\s*\(/,
  /\bgetWeatherVeenaSummary\s*\(/,
]
const ALLOWED_LEGACY_API_ALIAS_FILES = new Set([
  normalizePath(join(ROOT, 'lib/api/analytics/analytics.ts')),
  normalizePath(join(ROOT, 'lib/api/agronomy/weather.ts')),
])

const LEGACY_ROUTE_LITERAL_PATTERN = /\/veena\b/
const ALLOWED_LEGACY_ROUTE_LITERAL_FILES = new Set([
  normalizePath(join(ROOT, 'lib/legacyReevu.ts')),
  normalizePath(join(ROOT, 'lib/api/analytics/analytics.ts')),
  normalizePath(join(ROOT, 'lib/api/agronomy/weather.ts')),
])

const LEGACY_LOGO_LITERAL_PATTERN = /\bveena-logo\b/
const LEGACY_TOUR_LITERAL_PATTERN = /\bveena-ai\b/
const LEGACY_STORAGE_LITERAL_PATTERN = /\bveena_conversation_history\b/
const LEGACY_EXACT_VEENA_LITERAL_PATTERN = /(['"])veena\1/
const ALLOWED_LEGACY_UI_LITERAL_FILES = new Set([
  normalizePath(join(ROOT, 'lib/legacyReevu.ts')),
])
const ALLOWED_LEGACY_STORAGE_LITERAL_FILES = new Set([
  normalizePath(join(ROOT, 'lib/legacyReevu.ts')),
])
const ALLOWED_LEGACY_EXACT_VEENA_LITERAL_FILES = new Set([
  normalizePath(join(ROOT, 'lib/legacyReevu.ts')),
])

const FILE_EXTENSIONS = new Set(['.ts', '.tsx'])
const EXCLUDED_DIRECTORIES = new Set(['archive'])

function walk(dirPath, files = []) {
  for (const entry of readdirSync(dirPath)) {
    const fullPath = join(dirPath, entry)
    const stat = statSync(fullPath)
    if (stat.isDirectory()) {
      if (EXCLUDED_DIRECTORIES.has(entry)) {
        continue
      }
      walk(fullPath, files)
      continue
    }

    const ext = extname(entry)
    if (FILE_EXTENSIONS.has(ext)) {
      files.push(fullPath)
    }
  }
  return files
}

function normalizePath(pathname) {
  return pathname.replace(/\\/g, '/')
}

const violations = []
const files = walk(ROOT)

for (const file of files) {
  const normalizedFile = normalizePath(file)
  const content = readFileSync(file, 'utf8')
  const lines = content.split('\n')

  lines.forEach((line, index) => {
    for (const pattern of LEGACY_IMPORT_PATTERNS) {
      if (line.includes(pattern)) {
        violations.push({
          file: normalizePath(file),
          line: index + 1,
          pattern,
          source: line.trim(),
        })
      }
    }

    if (
      !ALLOWED_VEENA_SYMBOL_FILES.has(normalizedFile) &&
      AI_BARREL_IMPORT_PATTERN.test(line) &&
      LEGACY_VEENA_SYMBOL_PATTERN.test(line)
    ) {
      violations.push({
        file: normalizedFile,
        line: index + 1,
        pattern: 'Legacy Veena symbol import from @/components/ai',
        source: line.trim(),
      })
    }

    if (
      !ALLOWED_VEENA_EXPORT_FILES.has(normalizedFile) &&
      VEENA_EXPORT_PATTERN.test(line)
    ) {
      violations.push({
        file: normalizedFile,
        line: index + 1,
        pattern: 'Legacy Veena export outside compatibility facade',
        source: line.trim(),
      })
    }

    if (!ALLOWED_LEGACY_API_ALIAS_FILES.has(normalizedFile)) {
      for (const pattern of LEGACY_API_ALIAS_PATTERNS) {
        if (pattern.test(line)) {
          violations.push({
            file: normalizedFile,
            line: index + 1,
            pattern: 'Legacy API alias usage outside compatibility layer',
            source: line.trim(),
          })
        }
      }
    }

    if (
      !ALLOWED_LEGACY_ROUTE_LITERAL_FILES.has(normalizedFile) &&
      LEGACY_ROUTE_LITERAL_PATTERN.test(line)
    ) {
      violations.push({
        file: normalizedFile,
        line: index + 1,
        pattern: 'Legacy /veena literal outside compatibility layer',
        source: line.trim(),
      })
    }

    if (
      !ALLOWED_LEGACY_UI_LITERAL_FILES.has(normalizedFile) &&
      LEGACY_LOGO_LITERAL_PATTERN.test(line)
    ) {
      violations.push({
        file: normalizedFile,
        line: index + 1,
        pattern: 'Legacy veena-logo literal outside compatibility layer',
        source: line.trim(),
      })
    }

    if (
      !ALLOWED_LEGACY_UI_LITERAL_FILES.has(normalizedFile) &&
      LEGACY_TOUR_LITERAL_PATTERN.test(line)
    ) {
      violations.push({
        file: normalizedFile,
        line: index + 1,
        pattern: 'Legacy veena-ai literal outside compatibility layer',
        source: line.trim(),
      })
    }

    if (
      !ALLOWED_LEGACY_STORAGE_LITERAL_FILES.has(normalizedFile) &&
      LEGACY_STORAGE_LITERAL_PATTERN.test(line)
    ) {
      violations.push({
        file: normalizedFile,
        line: index + 1,
        pattern: 'Legacy veena_conversation_history literal outside compatibility layer',
        source: line.trim(),
      })
    }

    if (
      !ALLOWED_LEGACY_EXACT_VEENA_LITERAL_FILES.has(normalizedFile) &&
      LEGACY_EXACT_VEENA_LITERAL_PATTERN.test(line)
    ) {
      violations.push({
        file: normalizedFile,
        line: index + 1,
        pattern: 'Legacy exact veena literal outside compatibility layer',
        source: line.trim(),
      })
    }
  })
}

if (violations.length > 0) {
  console.error('Found legacy Veena compatibility violations. Use canonical Reevu modules and constants instead:\n')
  for (const v of violations) {
    console.error(`- ${v.file}:${v.line}`)
    console.error(`  ${v.source}`)
  }
  process.exit(1)
}

console.log('REEVU canonical import check passed.')
