/**
 * Type definitions for Breeding Crosses module
 */

export interface Cross {
  id: string;
  crossCode: string;
  maternalParent: string;
  paternalParent: string;
  crossDate: Date;
  generation: string;
  status: 'planned' | 'in_progress' | 'completed' | 'failed';
  seedsProduced: number;
  notes: string;
  createdBy: string;
}

export interface CrossFilter {
  status?: Cross['status'];
  generation?: string;
  parentId?: string;
  searchTerm?: string;
  startDate?: Date;
  endDate?: Date;
}

export interface CrossManagementState {
  crosses: Cross[];
  loading: boolean;
  error: string | null;
  filter: CrossFilter;
}
