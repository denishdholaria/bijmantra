import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Boxes,
  Database,
  ExternalLink,
  GitBranch,
  Network,
  RefreshCw,
  ShieldCheck,
  type LucideIcon,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { resolveCapabilityManifest } from '@/framework/registry/capabilities';
import { apiClient } from '@/lib/api-client';

function sizeOf(value: unknown): number {
  if (Array.isArray(value)) return value.length;
  if (value && typeof value === 'object') return Object.keys(value).length;
  if (typeof value === 'number') return value;
  return 0;
}

function endpointState(isLoading: boolean, error: unknown, value: unknown): string {
  if (isLoading) return 'Loading';
  if (error) return 'Unavailable';
  return String(sizeOf(value));
}

function CapabilityHeader({
  capabilityId,
  title,
  icon: Icon,
}: {
  capabilityId: string;
  title: string;
  icon: LucideIcon;
}) {
  const manifest = resolveCapabilityManifest(capabilityId);

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div className="flex items-start gap-3">
        <div className="rounded-lg border border-border bg-muted p-2">
          <Icon className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-foreground">{title}</h1>
          <div className="mt-2 flex flex-wrap gap-2">
            {manifest ? <Badge variant="outline">{manifest.lifecycle}</Badge> : null}
            {manifest?.standards.slice(0, 5).map(standard => (
              <Badge key={standard} variant="secondary">{standard}</Badge>
            ))}
          </div>
        </div>
      </div>
      <Button variant="outline" asChild>
        <Link to="/settings">
          <ShieldCheck className="h-4 w-4" />
          Capability Access
        </Link>
      </Button>
    </div>
  );
}

function MetricTile({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className="rounded-lg bg-primary/10 p-2">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div className="min-w-0">
          <div className="text-2xl font-semibold text-foreground">{value}</div>
          <div className="truncate text-sm text-muted-foreground">{label}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function EndpointList({
  endpoints,
}: {
  endpoints: Array<{ label: string; path: string; state: string }>;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Live Endpoints</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-border rounded-lg border border-border">
          {endpoints.map(endpoint => (
            <div
              key={endpoint.path}
              className="grid gap-2 p-3 text-sm md:grid-cols-[minmax(0,1fr)_auto]"
            >
              <div className="min-w-0">
                <div className="font-medium text-foreground">{endpoint.label}</div>
                <div className="truncate font-mono text-xs text-muted-foreground">{endpoint.path}</div>
              </div>
              <Badge variant={endpoint.state === 'Unavailable' ? 'warning' : 'outline'}>
                {endpoint.state}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ManifestPanel({ capabilityId }: { capabilityId: string }) {
  const manifest = resolveCapabilityManifest(capabilityId);

  if (!manifest) return null;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>Owner</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Dominion</span>
            <span className="font-medium">{manifest.dominion}</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Domain</span>
            <span className="font-medium">{manifest.ownerDomain}</span>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Permissions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {manifest.requiredPermissions.map(permission => (
            <Badge key={permission} variant="outline">{permission}</Badge>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Data Scopes</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {manifest.dataScopes.map(scope => (
            <Badge key={scope} variant="secondary">{scope}</Badge>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export function KnowledgeGraphApp() {
  const facets = useQuery({
    queryKey: ['knowledge-graph', 'facets'],
    queryFn: () => apiClient.knowledgeGraphService.getFacets(),
  });
  const edges = useQuery({
    queryKey: ['knowledge-graph', 'edges'],
    queryFn: () => apiClient.knowledgeGraphService.listEdges({ limit: 25 }),
  });
  const diagnostics = useQuery({
    queryKey: ['knowledge-graph', 'retrieval-diagnostics'],
    queryFn: () => apiClient.knowledgeGraphService.getRetrievalDiagnostics({ limit: 25 }),
  });

  const facetCount = useMemo(() => (
    sizeOf(facets.data?.source_asset_types)
    + sizeOf(facets.data?.target_asset_types)
    + sizeOf(facets.data?.relationship_types)
  ), [facets.data]);

  return (
    <div className="space-y-6">
      <CapabilityHeader
        capabilityId="intelligence_fabric.knowledge_graph"
        title="Knowledge Graph"
        icon={Network}
      />
      <div className="grid gap-4 md:grid-cols-3">
        <MetricTile label="Facet Groups" value={endpointState(facets.isLoading, facets.error, facetCount)} icon={GitBranch} />
        <MetricTile label="Edges" value={endpointState(edges.isLoading, edges.error, edges.data)} icon={Network} />
        <MetricTile label="Diagnostics" value={endpointState(diagnostics.isLoading, diagnostics.error, diagnostics.data)} icon={Activity} />
      </div>
      <EndpointList
        endpoints={[
          {
            label: 'Facets',
            path: '/api/v2/knowledge-graph/facets',
            state: endpointState(facets.isLoading, facets.error, facetCount),
          },
          {
            label: 'Edges',
            path: '/api/v2/knowledge-graph/edges',
            state: endpointState(edges.isLoading, edges.error, edges.data),
          },
          {
            label: 'Retrieval Diagnostics',
            path: '/api/v2/knowledge-graph/retrieval-diagnostics',
            state: endpointState(diagnostics.isLoading, diagnostics.error, diagnostics.data),
          },
        ]}
      />
      <ManifestPanel capabilityId="intelligence_fabric.knowledge_graph" />
    </div>
  );
}

function ResearchAssetSurface({ mode }: { mode: 'research-assets' | 'federated-assets' }) {
  const metadata = useQuery({
    queryKey: ['research-assets', 'fair-metadata'],
    queryFn: () => apiClient.researchAssetService.listFairMetadata({ limit: 25 }),
  });
  const assets = useQuery({
    queryKey: ['research-assets', 'federated-assets'],
    queryFn: () => apiClient.researchAssetService.listFederatedAssets({ limit: 25 }),
  });
  const connectors = useQuery({
    queryKey: ['research-assets', 'connectors'],
    queryFn: () => apiClient.researchAssetService.listConnectors(),
  });
  const receipts = useQuery({
    queryKey: ['research-assets', 'receipts'],
    queryFn: () => apiClient.researchAssetService.listSyncReceipts({ limit: 25 }),
  });

  const isFederated = mode === 'federated-assets';

  return (
    <div className="space-y-6">
      <CapabilityHeader
        capabilityId="scientific_publishing_fair_exchange.research_asset_core"
        title={isFederated ? 'Federated Assets' : 'Research Assets'}
        icon={isFederated ? Boxes : Database}
      />
      <div className="grid gap-4 md:grid-cols-4">
        <MetricTile label="FAIR Metadata" value={endpointState(metadata.isLoading, metadata.error, metadata.data)} icon={Database} />
        <MetricTile label="Federated Assets" value={endpointState(assets.isLoading, assets.error, assets.data)} icon={Boxes} />
        <MetricTile label="Connectors" value={endpointState(connectors.isLoading, connectors.error, connectors.data)} icon={ExternalLink} />
        <MetricTile label="Sync Receipts" value={endpointState(receipts.isLoading, receipts.error, receipts.data)} icon={RefreshCw} />
      </div>
      <EndpointList
        endpoints={[
          {
            label: 'FAIR Metadata',
            path: '/api/v2/fair-metadata',
            state: endpointState(metadata.isLoading, metadata.error, metadata.data),
          },
          {
            label: 'Federated Registry',
            path: '/api/v2/federated-assets/registry',
            state: endpointState(assets.isLoading, assets.error, assets.data),
          },
          {
            label: 'Connectors',
            path: '/api/v2/federated-assets/connectors',
            state: endpointState(connectors.isLoading, connectors.error, connectors.data),
          },
          {
            label: 'Sync Receipts',
            path: '/api/v2/federated-assets/receipts',
            state: endpointState(receipts.isLoading, receipts.error, receipts.data),
          },
        ]}
      />
      <ManifestPanel capabilityId="scientific_publishing_fair_exchange.research_asset_core" />
    </div>
  );
}

export function ResearchAssetsApp() {
  return <ResearchAssetSurface mode="research-assets" />;
}

export function FederatedAssetsApp() {
  return <ResearchAssetSurface mode="federated-assets" />;
}
