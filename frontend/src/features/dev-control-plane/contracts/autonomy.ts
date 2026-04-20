import type { DeveloperBoardStatus } from './board'

export type DeveloperLaneReadiness = 'ready' | 'watch' | 'blocked' | 'completed'

export type DeveloperLaneStructuralWarningCode =
  | 'missing-owners'
  | 'unregistered-owners'
  | 'missing-outputs'
  | 'missing-completion-criteria'
  | 'orphaned-dependencies'
  | 'stale-watch-lane'
  | 'active-without-validation-evidence'
  | 'completed-without-closure'

export type DeveloperLaneStructuralWarningSeverity = 'blocking' | 'advisory'

export type DeveloperLaneStructuralWarning = {
  code: DeveloperLaneStructuralWarningCode
  severity: DeveloperLaneStructuralWarningSeverity
  message: string
  remediation: string
}

export type DeveloperLaneAutonomyAnalysis = {
  laneId: string
  title: string
  status: DeveloperBoardStatus
  readiness: DeveloperLaneReadiness
  score: number
  structuralWarnings: DeveloperLaneStructuralWarning[]
  missingFields: string[]
  advisoryGaps: string[]
  unresolvedDependencies: string[]
  recommendations: string[]
}

export type DeveloperBoardAutonomyAnalysis = {
  laneAnalyses: DeveloperLaneAutonomyAnalysis[]
  readyLaneIds: string[]
  blockedLaneIds: string[]
  driftedLaneIds: string[]
  blockingStructuralWarningCount: number
  advisoryStructuralWarningCount: number
  nextRecommendedLaneId: string | null
  systemRecommendations: string[]
}