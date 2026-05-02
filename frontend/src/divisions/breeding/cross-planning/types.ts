export interface CrossPlan {
  crossId: string;
  crossName: string;
  femaleParentId: string | null;
  femaleParentName: string | null;
  maleParentId: string | null;
  maleParentName: string | null;
  objective: string;
  priority: string;
  targetDate: string;
  status: string;
  expectedProgeny: number;
  actualProgeny: number;
  crossType: string;
  season: string;
  location: string;
  breeder: string;
  notes: string;
  created: string | null;
}

export interface CrossPlanListResult {
  items: CrossPlan[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface CrossPlanFormValues {
  femaleParentId: string;
  maleParentId: string;
  name: string;
  description: string;
  plannedDate: string;
  objective: string;
}

export interface CrossPlanCandidate {
  id: string;
  name: string;
  germplasmDbId?: string;
  accessionNumber?: string;
}

export interface PedigreeNode {
  id: string;
  name: string;
  generation: number;
  type: string;
  sire?: PedigreeNode | null;
  dam?: PedigreeNode | null;
}
