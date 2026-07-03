import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { useAuthStore } from '@/store/auth';
import { useCapabilityAccessStore } from '@/store/capabilityAccessStore';
import { CapabilityProtectedRoute } from './CapabilityProtectedRoute';

describe('CapabilityProtectedRoute', () => {
  beforeEach(() => {
    useCapabilityAccessStore.getState().reset();
    useAuthStore.setState({
      user: {
        id: 1,
        email: 'scientist@example.com',
        full_name: 'Scientist',
        organization_id: 7,
        is_demo: false,
        is_active: true,
        is_superuser: false,
      },
      isAuthenticated: true,
    });
  });

  it('renders children when the installed capability includes the required permission and scope', () => {
    useCapabilityAccessStore.setState({
      organizationId: 7,
      accessContext: {
        installedCapabilities: ['intelligence_fabric.knowledge_graph'],
        grantedPermissions: ['intelligence.knowledge_graph.read'],
        dataScopes: ['organization', 'asset', 'evidence'],
      },
    });

    render(
      <CapabilityProtectedRoute
        capabilityId="intelligence_fabric.knowledge_graph"
        requiredPermission="intelligence.knowledge_graph.read"
        requiredDataScopes={['organization', 'asset']}
      >
        <div>Graph Surface</div>
      </CapabilityProtectedRoute>,
    );

    expect(screen.getByText('Graph Surface')).toBeInTheDocument();
  });

  it('blocks direct route access when the capability is not installed', () => {
    useCapabilityAccessStore.setState({
      organizationId: 7,
      accessContext: {
        installedCapabilities: [],
        grantedPermissions: ['intelligence.knowledge_graph.read'],
        dataScopes: ['organization', 'asset', 'evidence'],
      },
    });

    render(
      <CapabilityProtectedRoute
        capabilityId="intelligence_fabric.knowledge_graph"
        requiredPermission="intelligence.knowledge_graph.read"
      >
        <div>Graph Surface</div>
      </CapabilityProtectedRoute>,
    );

    expect(screen.queryByText('Graph Surface')).not.toBeInTheDocument();
    expect(screen.getByText('Capability Access Denied')).toBeInTheDocument();
  });

  it('blocks direct route access when the current-user data scope is missing', () => {
    useCapabilityAccessStore.setState({
      organizationId: 7,
      accessContext: {
        installedCapabilities: ['germplasm_global_seed_registry.accession_passport'],
        grantedPermissions: ['germplasm.read'],
        dataScopes: ['organization'],
      },
    });

    render(
      <CapabilityProtectedRoute
        capabilityId="germplasm_global_seed_registry.accession_passport"
        requiredPermission="germplasm.read"
        requiredDataScopes={['organization', 'accession']}
      >
        <div>Accession Surface</div>
      </CapabilityProtectedRoute>,
    );

    expect(screen.queryByText('Accession Surface')).not.toBeInTheDocument();
    expect(screen.getByText('Capability Access Denied')).toBeInTheDocument();
    expect(
      screen.getByText('Your current data scope does not include this capability surface.'),
    ).toBeInTheDocument();
  });
});
