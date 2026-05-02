import { apiClient } from '@/lib/api-client';
import type {
  CrossPlan,
  CrossPlanCandidate,
  CrossPlanFormValues,
  CrossPlanListResult,
  PedigreeNode,
} from '../types';

interface CrossPlannerPayload {
  metadata?: {
    pagination?: {
      totalCount?: number;
      currentPage?: number;
      pageSize?: number;
      totalPages?: number;
    };
  };
  result?: {
    data?: CrossPlan[];
    crossId?: string;
  };
}

interface GermplasmPayload {
  result?: {
    data?: Array<{
      id: string;
      germplasmDbId?: string;
      accessionNumber?: string;
      name: string;
    }>;
  };
}

interface PedigreePayload {
  success: boolean;
  tree?: PedigreeNode;
}

class CrossPlanningService {
  async getCrossPlans(page = 0, pageSize = 20): Promise<CrossPlanListResult> {
    const query = new URLSearchParams({
      page: String(page),
      pageSize: String(pageSize),
    });

    const payload = await apiClient.get<CrossPlannerPayload>(
      `/api/v2/crossing-planner?${query.toString()}`
    );

    const pagination = payload.metadata?.pagination;
    const items = payload.result?.data ?? [];

    return {
      items,
      total: pagination?.totalCount ?? items.length,
      page: pagination?.currentPage ?? page,
      pageSize: pagination?.pageSize ?? pageSize,
      totalPages: pagination?.totalPages ?? Math.max(1, Math.ceil(items.length / pageSize)),
    };
  }

  async createCrossPlan(values: CrossPlanFormValues): Promise<CrossPlan> {
    const payload = await apiClient.post<{ metadata: object; result: CrossPlan }>(
      '/api/v2/crossing-planner',
      {
        femaleParentId: values.femaleParentId,
        maleParentId: values.maleParentId,
        crossName: values.name,
        objective: values.objective,
        targetDate: values.plannedDate,
        notes: values.description,
      }
    );

    return payload.result;
  }

  async searchParentCandidates(search?: string): Promise<CrossPlanCandidate[]> {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    const payload = await apiClient.get<GermplasmPayload>(`/api/v2/crossing-planner/germplasm${query}`);
    return (payload.result?.data ?? []).map((item) => ({
      id: item.id,
      name: item.name,
      germplasmDbId: item.germplasmDbId,
      accessionNumber: item.accessionNumber,
    }));
  }

  async getPedigreeTree(germplasmId: string, maxGenerations = 5): Promise<PedigreeNode | null> {
    const payload = await apiClient.get<PedigreePayload>(
      `/api/v2/pedigree/ancestors/${germplasmId}?max_generations=${maxGenerations}`
    );
    return payload.tree ?? null;
  }
}

export const crossPlanningService = new CrossPlanningService();
