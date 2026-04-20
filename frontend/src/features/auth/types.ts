/**
 * Auth Feature Types
 * 
 * Type definitions for authentication feature.
 */

import type { LucideIcon } from 'lucide-react'

export interface LoginFormData {
  email: string;
  password: string;
}

export interface LoginResult {
  success: boolean;
  shouldNavigateToGateway: boolean;
  workspaceRoute?: string;
}

export interface PlatformSignal {
  label: string
  value: string
  accent: string
}

export interface TrustMarker {
  icon: LucideIcon
  title: string
  detail: string
}
