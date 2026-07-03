import { useEffect } from 'react';

import {
  evaluateCapabilityAccess,
  resolveCapabilityManifest,
  type CapabilityAccessDecision,
} from '@/framework/registry/capabilities';
import { useAuthStore } from '@/store/auth';
import { useCapabilityAccessStore } from '@/store/capabilityAccessStore';

interface CapabilityProtectedRouteProps {
  capabilityId: string;
  requiredPermission?: string;
  requiredDataScopes?: string[];
  children: React.ReactNode;
}

function capabilityAccessMessage(decision: CapabilityAccessDecision): string {
  if (decision.reason === 'capability_not_installed') {
    return 'This capability app is not installed for the current organization.';
  }

  if (decision.reason === 'missing_permission') {
    return 'Your role does not include the required capability permission.';
  }

  if (decision.reason === 'missing_data_scope') {
    return 'Your current data scope does not include this capability surface.';
  }

  return 'Capability access is unavailable.';
}

function CapabilityAccessDenied({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <div className="flex min-h-[50vh] items-center justify-center p-6">
      <div className="max-w-md rounded-lg border border-border bg-card p-6 text-center shadow-sm">
        <h2 className="text-xl font-semibold text-foreground">{title}</h2>
        <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}

export function CapabilityProtectedRoute({
  capabilityId,
  requiredPermission,
  requiredDataScopes,
  children,
}: CapabilityProtectedRouteProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const organizationId = useAuthStore((state) => state.user?.organization_id ?? null);
  const loadedOrganizationId = useCapabilityAccessStore((state) => state.organizationId);
  const accessContext = useCapabilityAccessStore((state) => state.accessContext);
  const isLoading = useCapabilityAccessStore((state) => state.isLoading);
  const error = useCapabilityAccessStore((state) => state.error);
  const loadForOrganization = useCapabilityAccessStore((state) => state.loadForOrganization);

  const manifest = resolveCapabilityManifest(capabilityId);

  useEffect(() => {
    if (!isAuthenticated || !organizationId || loadedOrganizationId === organizationId || isLoading) {
      return;
    }

    void loadForOrganization(organizationId);
  }, [isAuthenticated, isLoading, loadForOrganization, loadedOrganizationId, organizationId]);

  if (!manifest) {
    return (
      <CapabilityAccessDenied
        title="Capability Not Registered"
        message={`No frontend capability manifest exists for ${capabilityId}.`}
      />
    );
  }

  if (!isAuthenticated || !organizationId || isLoading || loadedOrganizationId !== organizationId) {
    return null;
  }

  if (error) {
    return (
      <CapabilityAccessDenied
        title="Capability State Unavailable"
        message={error}
      />
    );
  }

  const decision = evaluateCapabilityAccess(manifest, accessContext, {
    requiredPermission,
    requiredDataScopes,
  });

  if (!decision.allowed) {
    return (
      <CapabilityAccessDenied
        title="Capability Access Denied"
        message={capabilityAccessMessage(decision)}
      />
    );
  }

  return <>{children}</>;
}
