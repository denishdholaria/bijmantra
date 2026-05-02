import { GitBranch, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { usePedigree } from './hooks/usePedigree';
import type { PedigreeNode } from './types';

interface PedigreeTreeProps {
  germplasmId?: string | null;
  title?: string;
  maxGenerations?: number;
  tree?: PedigreeNode | null;
}

function PlaceholderNode({ label }: { label: string }) {
  return (
    <div className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
      {label}
    </div>
  );
}

function PedigreeBranch({
  node,
  depth,
  maxDepth,
}: {
  node: PedigreeNode;
  depth: number;
  maxDepth: number;
}) {
  const reachedLimit = depth >= maxDepth;

  return (
    <div className="space-y-4">
      <div className="rounded-lg border bg-card p-4 shadow-sm">
        <div className="font-semibold">{node.name}</div>
        <div className="text-sm text-muted-foreground">{node.id}</div>
        <div className="text-xs uppercase tracking-wide text-muted-foreground">
          Generation {depth + 1}
        </div>
      </div>

      {!reachedLimit ? (
        <div className="grid gap-4 pl-6 md:grid-cols-2">
          {node.sire ? (
            <PedigreeBranch node={node.sire} depth={depth + 1} maxDepth={maxDepth} />
          ) : (
            <PlaceholderNode label="Unknown sire" />
          )}
          {node.dam ? (
            <PedigreeBranch node={node.dam} depth={depth + 1} maxDepth={maxDepth} />
          ) : (
            <PlaceholderNode label="Unknown dam" />
          )}
        </div>
      ) : null}
    </div>
  );
}

export function PedigreeTree({
  germplasmId = null,
  title = 'Pedigree Tree',
  maxGenerations = 5,
  tree,
}: PedigreeTreeProps) {
  const pedigreeQuery = usePedigree(tree ? null : germplasmId, maxGenerations);
  const resolvedTree = tree ?? pedigreeQuery.data ?? null;

  if (!tree && !germplasmId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>Select a parent to render its pedigree ancestry.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (!tree && pedigreeQuery.isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-56" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-40 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!tree && pedigreeQuery.isError) {
    return (
      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>
            {pedigreeQuery.error instanceof Error
              ? pedigreeQuery.error.message
              : 'The pedigree request failed.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => pedigreeQuery.refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!resolvedTree) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>
            No pedigree ancestry was returned for the selected germplasm.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <GitBranch className="h-5 w-5" />
          <CardTitle>{title}</CardTitle>
        </div>
        <CardDescription>Rendering up to {maxGenerations} generations of ancestry.</CardDescription>
      </CardHeader>
      <CardContent>
        <PedigreeBranch node={resolvedTree} depth={0} maxDepth={maxGenerations - 1} />
      </CardContent>
    </Card>
  );
}
