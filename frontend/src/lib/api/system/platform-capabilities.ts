import type { CapabilityAccessContext } from '@/framework/registry/capabilities';

import { ApiClientCore } from '../core/client';

export interface PlatformCapabilityManifest {
  id: string;
  title: string;
  dominion: string;
  owner_domain: string;
  supporting_domains: string[];
  lifecycle: string;
  standards: string[];
  frontend_routes: string[];
  backend_routes: string[];
  data_scopes: string[];
  required_permissions: string[];
  suggested_roles: string[];
  semantic_spine_adrs: string[];
  install_behavior: string;
  uninstall_behavior: string;
  tests: string[];
  audit_events: string[];
  source_context: string[];
  backend_code_root?: string | null;
  frontend_code_root?: string | null;
}

export interface PlatformCapabilityInstallation {
  capability_id: string;
  organization_id: number;
  enabled: boolean;
  lifecycle_state: string;
  granted_permissions: string[];
  data_scopes: string[];
  settings?: Record<string, unknown> | null;
  installed_by_user_id?: number | null;
  disabled_by_user_id?: number | null;
  disabled_at?: string | null;
}

export interface PlatformCapabilityState {
  manifest: PlatformCapabilityManifest;
  installation: PlatformCapabilityInstallation | null;
}

export interface PlatformCapabilityManifestListResponse {
  capabilities: PlatformCapabilityManifest[];
}

export interface PlatformCapabilityInstallationListResponse {
  organization_id: number;
  installations: PlatformCapabilityInstallation[];
}

export interface PlatformCurrentCapabilityOrganization {
  id: number;
}

export interface PlatformCapabilityAccessDecision {
  capability_id: string;
  allowed: boolean;
  reason: 'allowed' | 'capability_not_installed' | 'missing_permission' | 'missing_data_scope';
  missing_permissions: string[];
  missing_data_scopes: string[];
}

export interface PlatformCurrentCapabilityContextResponse {
  current_organization: PlatformCurrentCapabilityOrganization;
  organization_id: number;
  user_id: number;
  installed_capability_ids: string[];
  enabled_capability_ids: string[];
  granted_permissions: string[];
  data_scopes: string[];
  roles: string[];
  capability_decisions: PlatformCapabilityAccessDecision[];
}

export interface PlatformCapabilityInstallRequest {
  organization_id?: number;
  granted_permissions?: string[];
  data_scopes?: string[];
  settings?: Record<string, unknown> | null;
}

export interface PlatformCapabilityBootstrapRequest {
  organization_id?: number;
  capability_ids?: string[];
}

export interface PlatformCapabilityBootstrapReceipt {
  capability_id: string;
  organization_id: number;
  action: 'installed' | 'already_installed' | 'skipped_disabled';
  enabled: boolean;
  lifecycle_state: string;
}

export interface PlatformCapabilityBootstrapResponse {
  organization_id: number;
  default_capability_ids: string[];
  receipts: PlatformCapabilityBootstrapReceipt[];
}

export class PlatformCapabilityService {
  constructor(private client: ApiClientCore) {}

  async listManifests(): Promise<PlatformCapabilityManifestListResponse> {
    return this.client.get<PlatformCapabilityManifestListResponse>(
      '/api/v2/system/capabilities/manifest',
    );
  }

  async listInstallations(
    organizationId?: number,
  ): Promise<PlatformCapabilityInstallationListResponse> {
    const query = organizationId ? `?organization_id=${organizationId}` : '';
    return this.client.get<PlatformCapabilityInstallationListResponse>(
      `/api/v2/system/capabilities/installations${query}`,
    );
  }

  async getCurrentUserContext(): Promise<PlatformCurrentCapabilityContextResponse> {
    return this.client.get<PlatformCurrentCapabilityContextResponse>(
      '/api/v2/platform/capabilities/me',
    );
  }

  async getState(capabilityId: string, organizationId?: number): Promise<PlatformCapabilityState> {
    const query = organizationId ? `?organization_id=${organizationId}` : '';
    return this.client.get<PlatformCapabilityState>(
      `/api/v2/system/capabilities/${encodeURIComponent(capabilityId)}${query}`,
    );
  }

  async install(
    capabilityId: string,
    payload: PlatformCapabilityInstallRequest = {},
  ): Promise<PlatformCapabilityState> {
    return this.client.put<PlatformCapabilityState>(
      `/api/v2/system/capabilities/${encodeURIComponent(capabilityId)}`,
      payload,
    );
  }

  async disable(capabilityId: string, organizationId?: number): Promise<PlatformCapabilityState> {
    const query = organizationId ? `?organization_id=${organizationId}` : '';
    return this.client.delete<PlatformCapabilityState>(
      `/api/v2/system/capabilities/${encodeURIComponent(capabilityId)}${query}`,
    );
  }

  async bootstrapFirstWave(
    payload: PlatformCapabilityBootstrapRequest = {},
  ): Promise<PlatformCapabilityBootstrapResponse> {
    return this.client.post<PlatformCapabilityBootstrapResponse>(
      '/api/v2/system/capabilities/bootstrap',
      payload,
    );
  }
}

export function capabilityInstallationsToAccessContext(
  installations: PlatformCapabilityInstallation[],
): CapabilityAccessContext {
  const enabledInstallations = installations.filter(installation => installation.enabled);

  return {
    installedCapabilities: unique(
      enabledInstallations.map(installation => installation.capability_id),
    ),
    grantedPermissions: unique(
      enabledInstallations.flatMap(installation => installation.granted_permissions),
    ),
    dataScopes: unique(enabledInstallations.flatMap(installation => installation.data_scopes)),
  };
}

export function currentCapabilityContextToAccessContext(
  context: PlatformCurrentCapabilityContextResponse,
): CapabilityAccessContext {
  return {
    installedCapabilities: unique(context.enabled_capability_ids),
    grantedPermissions: unique(context.granted_permissions),
    dataScopes: unique(context.data_scopes),
    roles: unique(context.roles),
  };
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values));
}
