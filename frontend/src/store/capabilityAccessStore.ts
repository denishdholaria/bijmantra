import { create } from 'zustand';

import type { CapabilityAccessContext } from '@/framework/registry/capabilities';
import { apiClient } from '@/lib/api-client';
import {
  currentCapabilityContextToAccessContext,
  type PlatformCapabilityInstallation,
} from '@/lib/api/system/platform-capabilities';

function createEmptyAccessContext(): CapabilityAccessContext {
  return {
    installedCapabilities: [],
    grantedPermissions: [],
    dataScopes: [],
  };
}

interface CapabilityAccessState {
  organizationId: number | null;
  installations: PlatformCapabilityInstallation[];
  accessContext: CapabilityAccessContext;
  isLoading: boolean;
  error: string | null;
  loadForOrganization: (organizationId: number) => Promise<void>;
  reset: () => void;
}

export const useCapabilityAccessStore = create<CapabilityAccessState>()((set, get) => ({
  organizationId: null,
  installations: [],
  accessContext: createEmptyAccessContext(),
  isLoading: false,
  error: null,

  loadForOrganization: async (organizationId: number) => {
    const state = get();
    if (
      state.organizationId === organizationId &&
      state.installations.length > 0 &&
      !state.error
    ) {
      return;
    }

    set({
      organizationId,
      isLoading: true,
      error: null,
      ...(state.organizationId === organizationId
        ? {}
        : {
            installations: [],
            accessContext: createEmptyAccessContext(),
          }),
    });

    try {
      const response = await apiClient.platformCapabilityService.getCurrentUserContext();
      set({
        organizationId: response.organization_id,
        installations: [],
        accessContext: currentCapabilityContextToAccessContext(response),
        isLoading: false,
        error: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to load capability access state';
      set({
        organizationId,
        installations: [],
        accessContext: createEmptyAccessContext(),
        isLoading: false,
        error: message,
      });
    }
  },

  reset: () => {
    set({
      organizationId: null,
      installations: [],
      accessContext: createEmptyAccessContext(),
      isLoading: false,
      error: null,
    });
  },
}));
