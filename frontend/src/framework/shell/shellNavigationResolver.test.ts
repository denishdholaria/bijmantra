import { describe, expect, it } from 'vitest';
import type { Division } from '@/framework/registry/types';
import {
  findActiveShellDivision,
  findActiveShellSection,
  getActiveShellSubgroups,
  isDesktopShellRoute,
  isShellNavItemActive,
  resolveShellNavPath,
} from './shellNavigationResolver';

const divisions: Division[] = [
  {
    id: 'plant-sciences',
    name: 'Plant Sciences',
    description: 'Plant science tools',
    icon: 'leaf',
    route: '/plant-sciences',
    requiredPermissions: [],
    status: 'active',
    version: '1.0.0',
    sections: [
      {
        id: 'programs',
        name: 'Programs',
        route: '/programs',
        isAbsolute: true,
      },
      {
        id: 'trials',
        name: 'Trials',
        route: '/trials',
        items: [
          {
            id: 'planned-crosses',
            name: 'Planned Crosses',
            route: '/plannedcrosses',
            isAbsolute: true,
          },
          {
            id: 'nursery',
            name: 'Nursery',
            route: '/nursery',
          },
        ],
      },
    ],
  },
  {
    id: 'settings',
    name: 'Settings',
    description: 'System settings',
    icon: 'settings',
    route: '/settings',
    requiredPermissions: [],
    status: 'active',
    version: '1.0.0',
    sections: [],
  },
];

describe('shellNavigationResolver', () => {
  it('resolves relative and absolute paths correctly', () => {
    expect(resolveShellNavPath('/plant-sciences', '/nursery')).toBe('/plant-sciences/nursery');
    expect(resolveShellNavPath('/plant-sciences', '/programs', true)).toBe('/programs');
  });

  it('detects desktop shell routes', () => {
    expect(isDesktopShellRoute('/dashboard')).toBe(true);
    expect(isDesktopShellRoute('/settings')).toBe(false);
  });

  it('matches active navigation items', () => {
    expect(
      isShellNavItemActive('/plannedcrosses/123', '/plant-sciences', {
        route: '/plannedcrosses',
        isAbsolute: true,
      }),
    ).toBe(true);

    expect(
      isShellNavItemActive('/plant-sciences/nursery/entry', '/plant-sciences', {
        route: '/nursery',
      }),
    ).toBe(true);
  });

  it('finds the active division from prefix and absolute routes', () => {
    expect(findActiveShellDivision(divisions, '/settings/profile')?.id).toBe('settings');
    expect(findActiveShellDivision(divisions, '/plannedcrosses')?.id).toBe('plant-sciences');
  });

  it('finds the active section within the active division', () => {
    const division = findActiveShellDivision(divisions, '/plannedcrosses');
    expect(findActiveShellSection(division ?? null, '/plannedcrosses')?.id).toBe('trials');

    const programsDivision = findActiveShellDivision(divisions, '/programs');
    expect(findActiveShellSection(programsDivision ?? null, '/programs')?.id).toBe('programs');
  });

  it('finds active shell subgroups for nested items', () => {
    expect(Array.from(getActiveShellSubgroups(divisions[0], '/plannedcrosses/details'))).toEqual(['trials']);
    expect(Array.from(getActiveShellSubgroups(divisions[0], '/programs'))).toEqual([]);
  });
});