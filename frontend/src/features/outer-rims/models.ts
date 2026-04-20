export type OuterRimsPhaseId = 'explore' | 'seek' | 'go' | 'transcend'

export interface Initiative {
  id: string
  phaseId: OuterRimsPhaseId
  title: string
  mission: string
  modelLeap: string
  narrative: string
  northStarSignals: string[]
}

export interface PhaseSummary {
  phaseId: OuterRimsPhaseId
  label: string
  description: string
  status: 'planned' | 'active' | 'complete'
}

export interface Workstream {
  id: string
  phaseId: OuterRimsPhaseId
  initiativeId: string
  title: string
  owner: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'in-progress' | 'completed'
}

export interface Milestone {
  id: string
  phaseId: OuterRimsPhaseId
  title: string
  dueDate: string
  status: 'pending' | 'in-progress' | 'completed'
}

export interface Risk {
  id: string
  phaseId: OuterRimsPhaseId
  title: string
  severity: 'low' | 'medium' | 'high'
  mitigation: string
}

export interface BacklogItem {
  id: string
  phaseId: OuterRimsPhaseId
  title: string
  owner: string
  status: 'ready' | 'queued' | 'blocked'
}

export interface Kpi {
  id: string
  phaseId: OuterRimsPhaseId
  name: string
  current: number
  target: number
  unit: string
}

export interface GovernanceRule {
  id: string
  title: string
  description: string
}