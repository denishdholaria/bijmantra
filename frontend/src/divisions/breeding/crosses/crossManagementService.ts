/**
 * Service layer for breeding cross management operations
 */

import type { Cross, CrossFilter } from './types';

class CrossManagementService {
  async fetchCrosses(filter: CrossFilter): Promise<Cross[]> {
    // TODO: Replace with actual API call
    const params = new URLSearchParams();
    if (filter.status) params.append('status', filter.status);
    if (filter.generation) params.append('generation', filter.generation);
    if (filter.parentId) params.append('parent_id', filter.parentId);
    if (filter.searchTerm) params.append('search', filter.searchTerm);
    if (filter.startDate) params.append('start_date', filter.startDate.toISOString());
    if (filter.endDate) params.append('end_date', filter.endDate.toISOString());

    const response = await fetch(`/api/v2/breeding/crosses?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch crosses');
    }
    return response.json();
  }

  async createCross(cross: Omit<Cross, 'id'>): Promise<Cross> {
    const response = await fetch('/api/v2/breeding/crosses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cross),
    });
    if (!response.ok) {
      throw new Error('Failed to create cross');
    }
    return response.json();
  }

  async updateCross(id: string, updates: Partial<Cross>): Promise<Cross> {
    const response = await fetch(`/api/v2/breeding/crosses/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      throw new Error('Failed to update cross');
    }
    return response.json();
  }
}

export const crossManagementService = new CrossManagementService();
