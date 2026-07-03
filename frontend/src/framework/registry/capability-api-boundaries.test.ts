import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

import { describe, expect, it } from 'vitest';

const sourceRoot = join(process.cwd(), 'src');

const firstWaveCapabilityUiRoots = [
  'features/knowledge',
];

const productionFilePattern = /\.(ts|tsx)$/;
const testFilePattern = /\.(test|spec)\.(ts|tsx)$/;

const forbiddenRequestPatterns = [
  {
    label: 'direct apiClient HTTP method',
    pattern: /\bapiClient\.(?:get|post|put|patch|delete|request)\s*(?:<|\()/,
  },
  {
    label: 'direct browser fetch',
    pattern: /\bfetch\s*\(/,
  },
];

function collectSourceFiles(directory: string): string[] {
  const entries = readdirSync(directory);
  const files: string[] = [];

  for (const entry of entries) {
    const path = join(directory, entry);
    const stats = statSync(path);

    if (stats.isDirectory()) {
      files.push(...collectSourceFiles(path));
      continue;
    }

    if (productionFilePattern.test(path) && !testFilePattern.test(path)) {
      files.push(path);
    }
  }

  return files;
}

describe('capability API boundaries', () => {
  it('keeps first-wave capability UI off raw HTTP calls', () => {
    const violations: string[] = [];

    for (const root of firstWaveCapabilityUiRoots) {
      const absoluteRoot = join(sourceRoot, root);

      for (const file of collectSourceFiles(absoluteRoot)) {
        const content = readFileSync(file, 'utf8');

        for (const rule of forbiddenRequestPatterns) {
          if (rule.pattern.test(content)) {
            violations.push(`${relative(sourceRoot, file)} uses ${rule.label}`);
          }
        }
      }
    }

    expect(violations).toEqual([]);
  });
});
