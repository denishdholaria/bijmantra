/**
 * Seed Bank - Offline Vaults Hook
 *
 * Typed hook for offline-first vault management.
 */

import { useCallback } from 'react';
import { useOfflineData } from '@/framework/sync/hooks';
import { OfflineVault } from '@/framework/sync/db';

export interface VaultInput {
  name: string;
  type: 'base' | 'active' | 'cryo';
  temperature: number;
  humidity: number;
  capacity: number;
  used?: number;
  organization_id: string;
}

export function useOfflineVaults() {
  const {
    data,
    isLoading,
    error,
    reload,
    create: baseCreate,
    update,
    remove,
    getById,
  } = useOfflineData<OfflineVault>('vaults');

  const create = useCallback(
    async (input: VaultInput) => {
      return baseCreate({
        name: input.name,
        type: input.type,
        temperature: input.temperature,
        humidity: input.humidity,
        capacity: input.capacity,
        used: input.used ?? 0,
        status: 'optimal',
        organizationId: input.organization_id,
      } as any);
    },
    [baseCreate]
  );

  // Filter by type
  const filterByType = useCallback(
    (type: 'base' | 'active' | 'cryo') => {
      return data.filter((vault) => vault.type === type);
    },
    [data]
  );

  // Get vaults with warnings
  const getWarningVaults = useCallback(() => {
    return data.filter(
      (vault) => vault.status === 'warning' || vault.status === 'critical'
    );
  }, [data]);

  // Get capacity utilization
  const getCapacityStats = useCallback(() => {
    const totalCapacity = data.reduce((sum, v) => sum + v.capacity, 0);
    const totalUsed = data.reduce((sum, v) => sum + v.used, 0);
    return {
      totalCapacity,
      totalUsed,
      utilization: totalCapacity > 0 ? (totalUsed / totalCapacity) * 100 : 0,
    };
  }, [data]);

  return {
    vaults: data,
    isLoading,
    error,
    reload,
    create,
    update,
    remove,
    getById,
    filterByType,
    getWarningVaults,
    getCapacityStats,
    stats: {
      total: data.length,
      base: data.filter((v) => v.type === 'base').length,
      active: data.filter((v) => v.type === 'active').length,
      cryo: data.filter((v) => v.type === 'cryo').length,
      warnings: data.filter((v) => v.status !== 'optimal').length,
    },
  };
}

export default useOfflineVaults;
