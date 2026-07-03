import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { ApiError } from '@/lib/api-errors';
import { apiClient } from '@/lib/api-client';
import { useCapabilityAccessStore } from '@/store/capabilityAccessStore';
import { generateIdempotencyKey, generateUuid7 } from '@/lib/uuid';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

import type {
  SeedLotAdjustmentRequest,
  SeedLotAdjustmentResponse,
  SeedLotAdjustmentType,
  SeedLotAdjustmentUnit,
} from '@/lib/api/seed-bank/inventory';

const CAPABILITY_ID = 'seedops_commercialization.seed_lot_traceability';
const REQUIRED_PERMISSION = 'seedops.seed_lots.adjust';
const REQUIRED_DATA_SCOPES = ['organization', 'lot'] as const;

const ADJUSTMENT_TYPES: SeedLotAdjustmentType[] = [
  'increase',
  'decrease',
  'correction',
  'reservation',
  'release',
];

const ADJUSTMENT_UNITS: SeedLotAdjustmentUnit[] = ['g', 'kg', 'seeds', 'packets', 'other'];

interface AdjustmentFormData {
  adjustmentType: SeedLotAdjustmentType;
  quantityDelta: string;
  unit: SeedLotAdjustmentUnit;
  reason: string;
  observedAt: string;
  metadataJson: string;
}

function formatApiError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.getUserMessage();
  }

  return error instanceof Error ? error.message : 'Failed to record the seed lot adjustment.';
}

function normalizeQuantityDelta(
  rawQuantityDelta: string,
  adjustmentType: SeedLotAdjustmentType,
): string {
  const trimmed = rawQuantityDelta.trim();

  if (adjustmentType === 'decrease' && trimmed && !trimmed.startsWith('-')) {
    return `-${trimmed}`;
  }

  if (adjustmentType === 'increase' && trimmed.startsWith('-')) {
    return trimmed.slice(1);
  }

  return trimmed;
}

function parseMetadata(metadataJson: string): Record<string, unknown> | undefined {
  const trimmed = metadataJson.trim();
  if (!trimmed) {
    return undefined;
  }

  const parsed = JSON.parse(trimmed) as unknown;
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('Metadata must be a JSON object.');
  }

  return parsed as Record<string, unknown>;
}

function getAccessGaps(
  installedCapabilities: string[],
  grantedPermissions: string[],
  dataScopes: string[],
): { missingPermissions: string[]; missingDataScopes: string[]; capabilityInstalled: boolean } {
  const capabilityInstalled = installedCapabilities.includes(CAPABILITY_ID);

  return {
    capabilityInstalled,
    missingPermissions: capabilityInstalled && grantedPermissions.includes(REQUIRED_PERMISSION)
      ? []
      : [REQUIRED_PERMISSION],
    missingDataScopes: REQUIRED_DATA_SCOPES.filter((scope) => !dataScopes.includes(scope)),
  };
}

export function SeedLotAdjustmentPanel({
  seedLotDbId,
  seedLotName,
  unit,
}: {
  seedLotDbId: string;
  seedLotName?: string;
  unit?: string;
}) {
  const queryClient = useQueryClient();
  const accessContext = useCapabilityAccessStore((state) => state.accessContext);
  const isLoadingAccess = useCapabilityAccessStore((state) => state.isLoading);
  const accessError = useCapabilityAccessStore((state) => state.error);
  const [success, setSuccess] = useState<SeedLotAdjustmentResponse | null>(null);

  const { register, handleSubmit, reset, setError, watch, setValue, formState: { errors } } = useForm<AdjustmentFormData>({
    defaultValues: {
      adjustmentType: 'increase',
      quantityDelta: '',
      unit: (unit as SeedLotAdjustmentUnit) || 'seeds',
      reason: '',
      observedAt: '',
      metadataJson: '',
    },
  });

  const adjustmentMutation = useMutation({
    mutationFn: async (data: AdjustmentFormData) => {
      const parsedQuantity = Number.parseFloat(data.quantityDelta);
      if (!Number.isFinite(parsedQuantity) || parsedQuantity === 0) {
        throw new Error('Quantity delta must be a non-zero number.');
      }

      let observedAt: string | undefined;
      if (data.observedAt.trim()) {
        const observedDate = new Date(data.observedAt);
        if (Number.isNaN(observedDate.getTime())) {
          throw new Error('Observed at must be a valid date and time.');
        }

        observedAt = observedDate.toISOString();
      }

      const payload: SeedLotAdjustmentRequest = {
        publicId: generateUuid7(),
        idempotencyKey: generateIdempotencyKey('seedlot-adjust'),
        seedLotDbId,
        adjustmentType: data.adjustmentType,
        quantityDelta: normalizeQuantityDelta(data.quantityDelta, data.adjustmentType),
        unit: data.unit,
        reason: data.reason.trim(),
        observedAt,
        metadata: parseMetadata(data.metadataJson),
      };

      return apiClient.inventoryService.createSeedLotAdjustment(payload);
    },
    onSuccess: (response) => {
      setSuccess(response);
      toast.success(`Seed lot adjustment recorded: ${response.adjustment.publicId}`);
      queryClient.invalidateQueries({ queryKey: ['seedlot', seedLotDbId] });
      queryClient.invalidateQueries({ queryKey: ['seedlot-transactions', seedLotDbId] });
      queryClient.invalidateQueries({ queryKey: ['seedlots'] });
      reset({
        adjustmentType: 'increase',
        quantityDelta: '',
        unit: (unit as SeedLotAdjustmentUnit) || 'seeds',
        reason: '',
        observedAt: '',
        metadataJson: '',
      });
    },
    onError: (error) => {
      toast.error(formatApiError(error));
    },
  });

  const accessGaps = getAccessGaps(
    accessContext.installedCapabilities,
    accessContext.grantedPermissions,
    accessContext.dataScopes ?? [],
  );

  if (isLoadingAccess) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Adjust Inventory</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (accessError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Adjust Inventory</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">{accessError}</p>
        </CardContent>
      </Card>
    );
  }

  if (!accessGaps.capabilityInstalled || accessGaps.missingPermissions.length > 0 || accessGaps.missingDataScopes.length > 0) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle>Adjust Inventory</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            The guarded seed lot adjustment workflow is hidden until the capability, permission, and data scope are available for this organization.
          </p>
          <div className="flex flex-wrap gap-2">
            {!accessGaps.capabilityInstalled && <Badge variant="secondary">Capability not installed</Badge>}
            {accessGaps.missingPermissions.map((permission) => (
              <Badge key={permission} variant="outline">{permission}</Badge>
            ))}
            {accessGaps.missingDataScopes.map((scope) => (
              <Badge key={scope} variant="outline">{scope}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const selectedType = watch('adjustmentType');

  return (
    <Card className="border-primary/30">
      <CardHeader>
        <CardTitle>Adjust Inventory</CardTitle>
        <p className="text-sm text-muted-foreground">
          Record a guarded seed lot adjustment for {seedLotName || seedLotDbId}. The write path emits the contract audit event and keeps the seedlots table read-only.
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        <form
          className="space-y-5"
          onSubmit={handleSubmit((data) => {
            if (data.reason.trim().length === 0) {
              setError('reason', { type: 'validate', message: 'Reason is required.' });
              return;
            }

            try {
              parseMetadata(data.metadataJson);
            } catch (error) {
              setError('metadataJson', {
                type: 'validate',
                message: error instanceof Error ? error.message : 'Metadata must be valid JSON.',
              });
              return;
            }

            adjustmentMutation.mutate(data);
          })}
        >
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor={`seed-lot-adjustment-type-${seedLotDbId}`}>Adjustment Type</Label>
              <Select
                value={watch('adjustmentType')}
                onValueChange={(value) => setValue('adjustmentType', value as SeedLotAdjustmentType)}
              >
                <SelectTrigger id={`seed-lot-adjustment-type-${seedLotDbId}`}>
                  <SelectValue placeholder="Choose adjustment type" />
                </SelectTrigger>
                <SelectContent>
                  {ADJUSTMENT_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor={`seed-lot-adjustment-unit-${seedLotDbId}`}>Unit</Label>
              <Select
                value={watch('unit')}
                onValueChange={(value) => setValue('unit', value as SeedLotAdjustmentUnit)}
              >
                <SelectTrigger id={`seed-lot-adjustment-unit-${seedLotDbId}`}>
                  <SelectValue placeholder="Choose unit" />
                </SelectTrigger>
                <SelectContent>
                  {ADJUSTMENT_UNITS.map((item) => (
                    <SelectItem key={item} value={item}>{item}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor={`seed-lot-adjustment-quantity-${seedLotDbId}`}>Quantity Delta</Label>
              <Input
                id={`seed-lot-adjustment-quantity-${seedLotDbId}`}
                type="number"
                step="0.000001"
                placeholder={selectedType === 'decrease' ? '-12.5' : '12.5'}
                {...register('quantityDelta', { required: 'Quantity delta is required.' })}
              />
              {errors.quantityDelta && <p className="text-sm text-red-600">{errors.quantityDelta.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor={`seed-lot-adjustment-observed-${seedLotDbId}`}>Observed At</Label>
              <Input
                id={`seed-lot-adjustment-observed-${seedLotDbId}`}
                type="datetime-local"
                {...register('observedAt')}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor={`seed-lot-adjustment-reason-${seedLotDbId}`}>Reason</Label>
            <Textarea
              id={`seed-lot-adjustment-reason-${seedLotDbId}`}
              rows={3}
              placeholder="Cycle count correction, damaged packaging, reservation release..."
              {...register('reason', { required: 'Reason is required.' })}
            />
            {errors.reason && <p className="text-sm text-red-600">{errors.reason.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor={`seed-lot-adjustment-metadata-${seedLotDbId}`}>Metadata JSON</Label>
            <Textarea
              id={`seed-lot-adjustment-metadata-${seedLotDbId}`}
              rows={4}
              placeholder='{"source":"warehouse_cycle_count"}'
              {...register('metadataJson')}
            />
            {errors.metadataJson && <p className="text-sm text-red-600">{errors.metadataJson.message}</p>}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={adjustmentMutation.isPending}>
              {adjustmentMutation.isPending ? 'Recording adjustment...' : 'Record adjustment'}
            </Button>
            <span className="text-xs uppercase tracking-[0.22em] text-muted-foreground">
              Requires {REQUIRED_PERMISSION} and {REQUIRED_DATA_SCOPES.join(', ')} scope
            </span>
          </div>
        </form>

        {success && (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-900 dark:border-emerald-900/40 dark:bg-emerald-950/40 dark:text-emerald-100">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="bg-emerald-600 text-white">Recorded</Badge>
              <span className="font-medium">Public ID {success.adjustment.publicId}</span>
            </div>
            <p className="mt-2 text-sm">
              Audit event {success.audit.event} stored for organization {success.audit.organizationId} by user {success.audit.actorUserId}.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
