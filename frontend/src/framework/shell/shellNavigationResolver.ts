import type { Division, DivisionNavItem, DivisionSection } from '@/framework/registry/types';

export const SHELL_DESKTOP_ROUTES = new Set(['/', '/gateway', '/dashboard']);

export function resolveShellNavPath(
  divisionRoute: string,
  route: string,
  isAbsolute?: boolean,
): string {
  return isAbsolute ? route : `${divisionRoute}${route}`;
}

export function isShellPathActive(pathname: string, path: string): boolean {
  return pathname === path || pathname.startsWith(path + '/');
}

export function isDesktopShellRoute(pathname: string): boolean {
  return SHELL_DESKTOP_ROUTES.has(pathname);
}

export function isShellNavItemActive(
  pathname: string,
  divisionRoute: string,
  item: Pick<DivisionNavItem, 'route' | 'isAbsolute'>,
): boolean {
  return isShellPathActive(pathname, resolveShellNavPath(divisionRoute, item.route, item.isAbsolute));
}

export function isShellSectionActive(
  pathname: string,
  divisionRoute: string,
  section: Pick<DivisionSection, 'route' | 'isAbsolute' | 'items'>,
): boolean {
  if (section.items?.length) {
    return section.items.some(item => isShellNavItemActive(pathname, divisionRoute, item));
  }

  return isShellPathActive(
    pathname,
    resolveShellNavPath(divisionRoute, section.route, section.isAbsolute),
  );
}

export function findActiveShellDivision(
  divisions: Division[],
  pathname: string,
): Division | null {
  const sortedDivisions = [...divisions].sort((left, right) => right.route.length - left.route.length);

  const prefixMatch = sortedDivisions.find(division => pathname.startsWith(division.route));
  if (prefixMatch) {
    return prefixMatch;
  }

  for (const division of sortedDivisions) {
    if (!division.sections?.length) {
      continue;
    }

    for (const section of division.sections) {
      if (isShellSectionActive(pathname, division.route, section)) {
        return division;
      }
    }
  }

  return null;
}

export function findActiveShellSection(
  division: Division | null,
  pathname: string,
): DivisionSection | null {
  if (!division?.sections?.length) {
    return null;
  }

  for (const section of division.sections) {
    if (isShellSectionActive(pathname, division.route, section)) {
      return section;
    }
  }

  return null;
}

export function getActiveShellSubgroups(
  division: Pick<Division, 'route' | 'sections'>,
  pathname: string,
): Set<string> {
  const active = new Set<string>();

  if (!division.sections?.length) {
    return active;
  }

  for (const section of division.sections) {
    if (section.items?.length && isShellSectionActive(pathname, division.route, section)) {
      active.add(section.id);
    }
  }

  return active;
}