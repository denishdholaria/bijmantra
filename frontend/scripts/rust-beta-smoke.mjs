import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

async function read(path) {
  return readFile(new URL(`../${path}`, import.meta.url), 'utf8')
}

async function readRoot(path) {
  return readFile(new URL(`../../${path}`, import.meta.url), 'utf8')
}

function requireContains(text, needle, label) {
  assert.ok(text.includes(needle), `${label} should contain ${needle}`)
}

function assertMatchedRoute(routeByPath, path, expectedSurface) {
  const route = routeByPath.get(path)
  assert.ok(route, `read-route-diff should include Rust beta route ${path}`)
  assert.equal(route.surface, expectedSurface, `${path} should belong to ${expectedSurface}`)
  assert.equal(route.routeStatus, 'active', `${path} should be active in Rust beta`)
}

function assertDeferredRoute(deferredPaths, matchedPaths, path) {
  assert.ok(deferredPaths.has(path), `${path} should remain a deferred FastAPI BrAPI route`)
  assert.ok(!matchedPaths.has(path), `${path} should not be exposed as a Rust beta read route`)
}

const [
  config,
  vite,
  client,
  germplasm,
  seedlots,
  crosses,
  playwrightConfigTest,
  readRouteDiffText,
  rustReadRoutesText,
  rustBetaChecklist,
  plantScienceMatrix,
] = await Promise.all([
  read('src/config.ts'),
  read('vite.config.ts'),
  read('src/lib/api/core/client.ts'),
  read('src/lib/api/brapi/germplasm/germplasm.ts'),
  read('src/lib/api/brapi/germplasm/seed-lots.ts'),
  read('src/lib/api/brapi/germplasm/crosses.ts'),
  read('e2e/playwright.config.test.mjs'),
  readRoot('contracts/fastapi-parity/read-route-diff.json'),
  readRoot('contracts/fastapi-parity/rust-read-routes.json'),
  readRoot('docs/rust-beta-checklist.md'),
  readRoot('.ai/tasks/2026-06-30-plant-science-rust-beta-mvp-matrix.md'),
])

requireContains(config, 'VITE_API_URL', 'frontend config')
requireContains(config, 'VITE_API_BASE_URL', 'frontend config')
requireContains(vite, "'/brapi'", 'Vite proxy')
requireContains(vite, "target: 'http://localhost:8000'", 'Vite proxy')

for (const [label, text, route] of [
  ['germplasm client', germplasm, '/brapi/v2/germplasm'],
  ['seedlot client', seedlots, '/brapi/v2/seedlots'],
  ['cross client', crosses, '/brapi/v2/crosses'],
]) {
  requireContains(text, route, label)
}

assert.ok(
  crosses.includes('/brapi/v2/plannedcrosses'),
  'cross client should contain the Rust plannedcrosses BrAPI read path',
)

requireContains(client, "!endpoint.startsWith('/brapi/v2')", 'API error preview exclusion')
requireContains(client, 'this.setToken(null)', 'API auth handling')
requireContains(playwrightConfigTest, 'bun run dev', 'Playwright config test')

const readRouteDiff = JSON.parse(readRouteDiffText)
const rustReadRoutes = JSON.parse(rustReadRoutesText)
const matchedRoutes = new Map(
  readRouteDiff.matchedRustBrapiRoutes.map(route => [route.fastapiPath, route]),
)
const matchedPaths = new Set(matchedRoutes.keys())
const rustOnlyRoutes = new Set(
  readRouteDiff.rustOnlyRuntimeOrProductReads.map(route => route.path),
)
const deferredPaths = new Set(
  readRouteDiff.deferredFastapiBrapiRoutes.map(route => route.path),
)

assert.equal(readRouteDiff.counts.matchedRustBrapiRoutes, 58)
assert.equal(readRouteDiff.counts.deferredFastapiBrapiRoutes, 75)

for (const [path, surface] of [
  ['/germplasm', 'germplasm'],
  ['/germplasm/{germplasmDbId}', 'germplasm'],
  ['/seedlots', 'seedlot-inventory'],
  ['/seedlots/{seedLotDbId}', 'seedlot-inventory'],
  ['/seedlots/transactions', 'seedlot-inventory'],
  ['/crossingprojects', 'cross-workflow'],
  ['/crossingprojects/{crossingProjectDbId}', 'cross-workflow'],
  ['/crosses', 'cross-workflow'],
  ['/crosses/{crossDbId}', 'cross-workflow'],
  ['/plannedcrosses', 'cross-workflow'],
  ['/plannedcrosses/{plannedCrossDbId}', 'cross-workflow'],
  ['/trials', 'core-protected'],
  ['/trials/{trialDbId}', 'core-protected'],
  ['/studies', 'core-protected'],
  ['/studies/{studyDbId}', 'core-protected'],
  ['/observations', 'phenotyping'],
  ['/observations/{observationDbId}', 'phenotyping'],
  ['/observationunits', 'phenotyping'],
  ['/observationunits/{observationUnitDbId}', 'phenotyping'],
]) {
  assertMatchedRoute(matchedRoutes, path, surface)
}

assert.ok(
  rustOnlyRoutes.has('/api/v2/seed-inventory/summary'),
  'seed inventory summary should be a Rust beta product read',
)

for (const path of ['/allelematrix', '/images', '/events', '/observations/table']) {
  assertDeferredRoute(deferredPaths, matchedPaths, path)
}

for (const route of rustReadRoutes.routes) {
  assert.equal(route.method, 'GET', `${route.path} should stay read-only in Rust beta`)
}

for (const required of [
  '| Observation reads | Pass |',
  '| Germplasm workflow | Pass |',
  '| Seedlot inventory | Pass |',
  '| Security | Pass |',
  'the guarded seedlot adjustment write route is the only public Rust write path',
]) {
  requireContains(rustBetaChecklist, required, 'Rust beta checklist')
}

for (const required of [
  '| Germplasm | Protected BrAPI read list/detail',
  '| Seedlots / seed inventory | Protected BrAPI seedlot and transaction reads',
  '| Crosses / planned crosses | Protected BrAPI crossing project, cross, and planned-cross list/detail reads.',
  '| Trials / studies | Protected BrAPI programs, locations, trials, studies, seasons, people, list/detail reads with tenant isolation.',
  '| Observations | Protected BrAPI traits, methods, scales, variables, observations, and observation-unit reads.',
  'Route Live Addendum',
  'POST /api/v2/seed-inventory/adjustments',
  'FastAPI remains the fallback for deferred BrAPI GET routes and all writes.',
]) {
  requireContains(plantScienceMatrix, required, 'Plant Science Rust Beta MVP matrix')
}

console.log('Rust beta frontend smoke passed; Plant Science walkthrough smoke passed')
