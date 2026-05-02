import assert from 'node:assert/strict'
import { execFile } from 'node:child_process'
import test from 'node:test'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)
const readCommandScript = `
  import assert from 'node:assert/strict'
  import config from './playwright.config.ts'

  assert.ok(Array.isArray(config.webServer), 'Expected webServer to be an array')
  assert.ok(config.webServer.length > 0, 'Expected at least one webServer entry')

  console.log(config.webServer[0].command)
`

async function readFrontendDevCommand(frontendDevCommand) {
  const { stdout } = await execFileAsync(
    process.execPath,
    [
      '--import',
      'tsx',
      '--input-type=module',
      '-e',
      readCommandScript,
    ],
    {
      cwd: new URL('.', import.meta.url),
      env: frontendDevCommand
        ? { ...process.env, BIJMANTRA_FRONTEND_DEV_COMMAND: frontendDevCommand }
        : process.env,
    },
  )

  return stdout.trim()
}

test('playwright config defaults to npm for the frontend dev server', async () => {
  assert.equal(await readFrontendDevCommand(), 'npm run dev')
})

test('playwright config allows overriding the frontend dev server command', async () => {
  assert.equal(await readFrontendDevCommand('bun run dev'), 'bun run dev')
})
