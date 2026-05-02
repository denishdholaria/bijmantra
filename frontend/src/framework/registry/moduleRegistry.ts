import { LucideIcon, Home, Grid } from 'lucide-react';
import React from 'react';

export interface ShellModule {
  id: string;
  title: string;
  subtitle: string;
  icon: LucideIcon;
  component?: React.ComponentType<any>;
  route?: string;
}

export const REGISTERED_APPS: ShellModule[] = [
  { id: 'app1', title: 'App 1', icon: Home, subtitle: 'Test App' },
  { id: 'app2', title: 'App 2', icon: Grid, subtitle: 'Test App 2' },
];

export const launcherModules: ShellModule[] = REGISTERED_APPS;
export const dockApps: ShellModule[] = REGISTERED_APPS;
export const defaultShortcutIds: string[] = ['app1'];

export const getApp = (id: string) => REGISTERED_APPS.find(app => app.id === id);
