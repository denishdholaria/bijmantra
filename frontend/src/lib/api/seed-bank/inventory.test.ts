import { describe, expect, it, vi } from 'vitest';

import type { ApiClientCore } from '../core/client';

import { InventoryService } from './inventory';

function makeClient() {
  return {
    get: vi.fn(),
    post: vi.fn(),
  } as unknown as ApiClientCore & {
    get: ReturnType<typeof vi.fn>;
    post: ReturnType<typeof vi.fn>;
  };
}

describe('InventoryService', () => {
  it('calls the guarded seed lot adjustment endpoint with the contract payload', async () => {
    const client = makeClient();
    client.post.mockResolvedValue({
      success: true,
      adjustment: {
        publicId: '018f5f31-a61b-7cc2-9f6e-6f7a8d000001',
        seedLotDbId: 'seedlot_IR64_0001',
        adjustmentType: 'correction',
        quantityDelta: '-12.500',
        unit: 'g',
        resultingLedgerStatus: 'recorded',
        createdAt: '2026-07-02T00:00:00Z',
      },
      audit: {
        event: 'seed_lot.adjusted',
        actorUserId: 2,
        organizationId: 1,
      },
    });
    const service = new InventoryService(client);

    const response = await service.createSeedLotAdjustment({
      publicId: '018f5f31-a61b-7cc2-9f6e-6f7a8d000001',
      idempotencyKey: 'seedlot-adjust-20260702-0001',
      seedLotDbId: 'seedlot_IR64_0001',
      adjustmentType: 'correction',
      quantityDelta: '-12.500',
      unit: 'g',
      reason: 'Cycle count correction after warehouse recount',
      observedAt: '2026-07-02T00:00:00.000Z',
      metadata: {
        source: 'warehouse_cycle_count',
      },
    });

    expect(response.success).toBe(true);
    expect(client.post).toHaveBeenCalledWith('/api/v2/seed-inventory/adjustments', {
      publicId: '018f5f31-a61b-7cc2-9f6e-6f7a8d000001',
      idempotencyKey: 'seedlot-adjust-20260702-0001',
      seedLotDbId: 'seedlot_IR64_0001',
      adjustmentType: 'correction',
      quantityDelta: '-12.500',
      unit: 'g',
      reason: 'Cycle count correction after warehouse recount',
      observedAt: '2026-07-02T00:00:00.000Z',
      metadata: {
        source: 'warehouse_cycle_count',
      },
    });
  });

  it('propagates client request failures for the guarded adjustment route', async () => {
    const client = makeClient();
    client.post.mockRejectedValue(new Error('network down'));
    const service = new InventoryService(client);

    await expect(
      service.createSeedLotAdjustment({
        publicId: '018f5f31-a61b-7cc2-9f6e-6f7a8d000001',
        idempotencyKey: 'seedlot-adjust-20260702-0001',
        seedLotDbId: 'seedlot_IR64_0001',
        adjustmentType: 'increase',
        quantityDelta: '5',
        unit: 'seeds',
        reason: 'Batch top-up',
      }),
    ).rejects.toThrow('network down');
  });
});
