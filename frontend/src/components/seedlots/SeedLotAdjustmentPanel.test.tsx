import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCapabilityAccessStore } from '@/store/capabilityAccessStore';

import { SeedLotAdjustmentPanel } from './SeedLotAdjustmentPanel';

const { createSeedLotAdjustment } = vi.hoisted(() => ({
  createSeedLotAdjustment: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    inventoryService: {
      createSeedLotAdjustment,
    },
  },
}));

vi.mock('@/lib/uuid', () => ({
  generateUuid7: vi.fn(() => '018f5f31-a61b-7cc2-9f6e-6f7a8d000001'),
  generateIdempotencyKey: vi.fn(() => 'seedlot-adjust-018f5f31-a61b-7cc2-9f6e-6f7a8d000002'),
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

function renderPanel() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <SeedLotAdjustmentPanel
        seedLotDbId="seedlot_IR64_0001"
        seedLotName="IR64"
        unit="g"
      />
    </QueryClientProvider>,
  );
}

describe('SeedLotAdjustmentPanel', () => {
  beforeEach(() => {
    useCapabilityAccessStore.setState({
      organizationId: 7,
      accessContext: {
        installedCapabilities: ['seedops_commercialization.seed_lot_traceability'],
        grantedPermissions: ['seedops.seed_lots.adjust'],
        dataScopes: ['organization', 'lot'],
      },
      isLoading: false,
      error: null,
      installations: [],
      loadForOrganization: vi.fn(),
      reset: vi.fn(),
    });
    createSeedLotAdjustment.mockReset();
  });

  it('renders the guarded adjustment form when the capability is available', () => {
    renderPanel();

    expect(screen.getByText('Adjust Inventory')).toBeInTheDocument();
    expect(screen.getByLabelText('Quantity Delta')).toBeInTheDocument();
    expect(screen.getByText('Record adjustment')).toBeInTheDocument();
  });

  it('submits a typed adjustment payload and shows the recorded public id', async () => {
    createSeedLotAdjustment.mockResolvedValue({
      success: true,
      adjustment: {
        publicId: '018f5f31-a61b-7cc2-9f6e-6f7a8d000001',
        seedLotDbId: 'seedlot_IR64_0001',
        adjustmentType: 'increase',
        quantityDelta: '5',
        unit: 'g',
        resultingLedgerStatus: 'recorded',
        createdAt: '2026-07-02T00:00:00Z',
      },
      audit: {
        event: 'seed_lot.adjusted',
        actorUserId: 2,
        organizationId: 7,
      },
    });

    renderPanel();

    fireEvent.change(screen.getByLabelText('Quantity Delta'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('Reason'), {
      target: { value: 'Cycle count correction after warehouse recount' },
    });
    fireEvent.change(screen.getByLabelText('Metadata JSON'), {
      target: { value: '{"source":"warehouse_cycle_count"}' },
    });
    fireEvent.click(screen.getByText('Record adjustment'));

    await waitFor(() => {
      expect(createSeedLotAdjustment).toHaveBeenCalledWith({
        publicId: '018f5f31-a61b-7cc2-9f6e-6f7a8d000001',
        idempotencyKey: 'seedlot-adjust-018f5f31-a61b-7cc2-9f6e-6f7a8d000002',
        seedLotDbId: 'seedlot_IR64_0001',
        adjustmentType: 'increase',
        quantityDelta: '5',
        unit: 'g',
        reason: 'Cycle count correction after warehouse recount',
        observedAt: undefined,
        metadata: {
          source: 'warehouse_cycle_count',
        },
      });
    });

    expect(await screen.findByText(/Public ID 018f5f31-a61b-7cc2-9f6e-6f7a8d000001/)).toBeInTheDocument();
  });

  it('hides the workflow when the capability is not installed', () => {
    useCapabilityAccessStore.setState({
      organizationId: 7,
      accessContext: {
        installedCapabilities: [],
        grantedPermissions: [],
        dataScopes: ['organization'],
      },
      isLoading: false,
      error: null,
      installations: [],
      loadForOrganization: vi.fn(),
      reset: vi.fn(),
    });

    renderPanel();

    expect(screen.getByText('Capability not installed')).toBeInTheDocument();
    expect(screen.queryByText('Record adjustment')).not.toBeInTheDocument();
  });
});
