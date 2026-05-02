import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { spawnSync } from 'node:child_process'
import { test } from 'node:test'
import assert from 'node:assert/strict'

const WORK_PREFIX = 'reevu-guard-'
const SOURCE_GUARD = join(process.cwd(), 'scripts/check-reevu-canonical.mjs')

function withFixture(files, runAssertions) {
  const root = mkdtempSync(join(tmpdir(), WORK_PREFIX))
  const scriptsDir = join(root, 'scripts')
  const srcDir = join(root, 'src')

  try {
    mkdirSync(scriptsDir, { recursive: true })
    mkdirSync(srcDir, { recursive: true })

    writeFileSync(join(scriptsDir, 'check-reevu-canonical.mjs'), readFileSync(SOURCE_GUARD, 'utf8'))

    for (const [relativePath, content] of Object.entries(files)) {
      const filePath = join(srcDir, relativePath)
      mkdirSync(dirname(filePath), { recursive: true })
      writeFileSync(filePath, content)
    }

    const result = spawnSync('node', [join(scriptsDir, 'check-reevu-canonical.mjs')], {
      cwd: root,
      encoding: 'utf8',
    })

    runAssertions(result)
  } finally {
    rmSync(root, { recursive: true, force: true })
  }
}

test('passes for canonical REEVU import usage', () => {
  withFixture(
    {
      'components/Foo.tsx': "import { useReevuChat } from '@/hooks/useReevuChat'\nexport const Foo = () => null\n",
      'lib/legacyReevu.ts': "export const LEGACY_REEVU_ROUTE = '/veena' as const\n",
      'lib/api/analytics/analytics.ts': 'export async function x(){ return "/api/v2/analytics/veena-summary" }\n',
      'lib/api/agronomy/weather.ts': 'export async function y(){ return `/api/v2/weather/veena/summary/1` }\n',
      'components/ai/index.ts': "export { VeenaSidebar } from './VeenaSidebar'\n",
      'hooks/useVeenaChat.ts': 'export const useVeenaChat = () => {}\n',
      'hooks/useVeenaVoice.ts': 'export const useVeenaVoice = () => {}\n',
      'store/veenaSidebarStore.ts': 'export const useVeenaSidebarStore = () => {}\n',
      'pages/VeenaChat.tsx': 'export const VeenaChat = () => null\n',
      'components/VeenaVoiceInput.tsx': 'export const VeenaVoiceInput = () => null\n',
      'components/ai/VeenaSidebar.tsx': 'export const VeenaSidebar = () => null\n',
      'components/ai/VeenaTrigger.tsx': 'export const VeenaTrigger = () => null\n',
    },
    (result) => {
      assert.equal(result.status, 0, result.stderr)
      assert.match(result.stdout, /REEVU canonical import check passed\./)
    },
  )
})

test('fails on legacy Veena direct import path', () => {
  withFixture(
    {
      'components/Foo.tsx': "import { useVeenaChat } from '@/hooks/useVeenaChat'\n",
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /legacy Veena compatibility violations/i)
      assert.match(result.stderr, /@\/hooks\/useVeenaChat/)
    },
  )
})

test('fails on veena-logo literal outside compatibility file', () => {
  withFixture(
    {
      'components/Foo.tsx': "const icon = 'veena-logo'\n",
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /const icon = 'veena-logo'/)
    },
  )
})

test('fails on /veena literal outside allowlisted files', () => {
  withFixture(
    {
      'routes/ai.tsx': "const bad = '/veena'\n",
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /const bad = '\/veena'/)
    },
  )
})

test('passes when legacy API aliases are defined only in allowlisted compatibility files', () => {
  withFixture(
    {
      'lib/legacyReevu.ts': "export const LEGACY_REEVU_ROUTE = '/veena' as const\n",
      'lib/api/analytics/analytics.ts': 'export function getVeenaSummary(){ return 1 }\n',
      'lib/api/agronomy/weather.ts': 'export function getWeatherVeenaSummary(){ return 1 }\n',
      'components/Foo.tsx': "import { useReevuChat } from '@/hooks/useReevuChat'\nexport const Foo = () => null\n",
    },
    (result) => {
      assert.equal(result.status, 0, result.stderr)
      assert.match(result.stdout, /REEVU canonical import check passed\./)
    },
  )
})

test('fails on getVeenaSummary usage outside compatibility files', () => {
  withFixture(
    {
      'components/Foo.tsx': 'export function run(x){ return x.getVeenaSummary() }\n',
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /getVeenaSummary\(\)/)
    },
  )
})

test('fails on getWeatherVeenaSummary usage outside compatibility files', () => {
  withFixture(
    {
      'components/Foo.tsx': 'export function run(x){ return x.getWeatherVeenaSummary() }\n',
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /getWeatherVeenaSummary\(\)/)
    },
  )
})

test('fails on Veena symbol import from AI barrel outside compatibility barrel', () => {
  withFixture(
    {
      'components/Foo.tsx': "import { VeenaTrigger } from '@/components/ai'\n",
      'components/ai/index.ts': 'export { VeenaTrigger } from \'./VeenaTrigger\'\n',
      'components/ai/VeenaTrigger.tsx': 'export const VeenaTrigger = () => null\n',
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /import \{ VeenaTrigger \} from '@\/components\/ai'/)
    },
  )
})

test('fails on Veena export outside compatibility facade files', () => {
  withFixture(
    {
      'components/Foo.tsx': 'export const VeenaBadge = () => null\n',
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /export const VeenaBadge = \(\) => null/)
    },
  )
})

test('ignores violations under src/archive', () => {
  withFixture(
    {
      'archive/Foo.tsx': "import { useVeenaChat } from '@/hooks/useVeenaChat'\n",
      'components/Okay.tsx': "import { useReevuChat } from '@/hooks/useReevuChat'\nexport const Okay = () => null\n",
    },
    (result) => {
      assert.equal(result.status, 0, result.stderr)
      assert.match(result.stdout, /REEVU canonical import check passed\./)
    },
  )
})

test('fails on veena_conversation_history literal outside compatibility file', () => {
  withFixture(
    {
      'hooks/useFoo.ts': "const key = 'veena_conversation_history'\n",
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /const key = 'veena_conversation_history'/)
    },
  )
})

test('passes when veena_conversation_history literal is defined in legacy constants file', () => {
  withFixture(
    {
      'lib/legacyReevu.ts': "export const LEGACY_REEVU_STORAGE_KEY = 'veena_conversation_history' as const\n",
      'components/Foo.tsx': "import { LEGACY_REEVU_STORAGE_KEY } from '@/lib/legacyReevu'\nexport const Foo = () => LEGACY_REEVU_STORAGE_KEY\n",
    },
    (result) => {
      assert.equal(result.status, 0, result.stderr)
      assert.match(result.stdout, /REEVU canonical import check passed\./)
    },
  )
})

test('passes on Veena exports in explicitly allowlisted compatibility facades', () => {
  withFixture(
    {
      'hooks/useVeenaChat.ts': 'export const useVeenaChat = () => {}\n',
      'hooks/useVeenaVoice.ts': 'export const useVeenaVoice = () => {}\n',
      'store/veenaSidebarStore.ts': 'export const useVeenaSidebarStore = () => {}\n',
      'pages/VeenaChat.tsx': 'export const VeenaChat = () => null\n',
      'components/VeenaVoiceInput.tsx': 'export const VeenaVoiceInput = () => null\n',
      'components/ai/VeenaSidebar.tsx': 'export const VeenaSidebar = () => null\n',
      'components/ai/VeenaTrigger.tsx': 'export const VeenaTrigger = () => null\n',
      'components/ai/index.ts': "export { VeenaSidebar } from './VeenaSidebar'\n",
      'components/Foo.tsx': "import { useReevuChat } from '@/hooks/useReevuChat'\nexport const Foo = () => null\n",
      'lib/legacyReevu.ts': "export const LEGACY_REEVU_ROUTE = '/veena' as const\n",
      'lib/api/analytics/analytics.ts': 'export async function x(){ return "/api/v2/analytics/veena-summary" }\n',
      'lib/api/agronomy/weather.ts': 'export async function y(){ return `/api/v2/weather/veena/summary/1` }\n',
    },
    (result) => {
      assert.equal(result.status, 0, result.stderr)
      assert.match(result.stdout, /REEVU canonical import check passed\./)
    },
  )
})

test('passes on /veena literals in allowlisted compatibility files', () => {
  withFixture(
    {
      'lib/legacyReevu.ts': "export const LEGACY_REEVU_ROUTE = '/veena' as const\n",
      'lib/api/analytics/analytics.ts': 'export async function x(){ return "/api/v2/analytics/veena-summary" }\n',
      'lib/api/agronomy/weather.ts': 'export async function y(){ return `/api/v2/weather/veena/summary/1` }\n',
      'components/Foo.tsx': "import { useReevuChat } from '@/hooks/useReevuChat'\nexport const Foo = () => null\n",
    },
    (result) => {
      assert.equal(result.status, 0, result.stderr)
      assert.match(result.stdout, /REEVU canonical import check passed\./)
    },
  )
})

test('fails on all blocked legacy direct import paths', () => {
  withFixture(
    {
      'components/Imports.tsx': [
        "import { useVeenaChat } from '@/hooks/useVeenaChat'",
        "import { useVeenaVoice } from '@/hooks/useVeenaVoice'",
        "import { useVeenaSidebarStore } from '@/store/veenaSidebarStore'",
        "import { VeenaSidebar } from '@/components/ai/VeenaSidebar'",
        "import { VeenaTrigger } from '@/components/ai/VeenaTrigger'",
        "import { VeenaChat } from '@/pages/VeenaChat'",
        "import { VeenaVoiceInput } from '@/components/VeenaVoiceInput'",
      ].join('\n') + '\n',
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /@\/hooks\/useVeenaChat/)
      assert.match(result.stderr, /@\/hooks\/useVeenaVoice/)
      assert.match(result.stderr, /@\/store\/veenaSidebarStore/)
      assert.match(result.stderr, /@\/components\/ai\/VeenaSidebar/)
      assert.match(result.stderr, /@\/components\/ai\/VeenaTrigger/)
      assert.match(result.stderr, /@\/pages\/VeenaChat/)
      assert.match(result.stderr, /@\/components\/VeenaVoiceInput/)
    },
  )
})

test('passes when veena-logo and veena-ai literals are defined in legacy constants file', () => {
  withFixture(
    {
      'lib/legacyReevu.ts': [
        "export const LEGACY_REEVU_LOGO_ICON = 'veena-logo' as const",
        "export const LEGACY_REEVU_TOUR_TARGET = 'veena-ai' as const",
      ].join('\n') + '\n',
      'components/Foo.tsx': "import { LEGACY_REEVU_LOGO_ICON, LEGACY_REEVU_TOUR_TARGET } from '@/lib/legacyReevu'\nexport const Foo = () => `${LEGACY_REEVU_LOGO_ICON}:${LEGACY_REEVU_TOUR_TARGET}`\n",
    },
    (result) => {
      assert.equal(result.status, 0, result.stderr)
      assert.match(result.stdout, /REEVU canonical import check passed\./)
    },
  )
})

test("fails on exact 'veena' literal outside compatibility file", () => {
  withFixture(
    {
      'components/Foo.tsx': "const legacyId = 'veena'\n",
    },
    (result) => {
      assert.notEqual(result.status, 0)
      assert.match(result.stderr, /const legacyId = 'veena'/)
    },
  )
})

test("passes when exact 'veena' literals are defined in legacy constants file", () => {
  withFixture(
    {
      'lib/legacyReevu.ts': [
        "export const LEGACY_REEVU_ICON_KEY = 'veena' as const",
        "export const LEGACY_REEVU_ORCHESTRATOR_ID = 'veena' as const",
      ].join('\n') + '\n',
      'components/Foo.tsx': "import { LEGACY_REEVU_ICON_KEY } from '@/lib/legacyReevu'\nexport const Foo = () => LEGACY_REEVU_ICON_KEY\n",
    },
    (result) => {
      assert.equal(result.status, 0, result.stderr)
      assert.match(result.stdout, /REEVU canonical import check passed\./)
    },
  )
})
