import type {
  DeveloperBoardLaneReviewGate,
  DeveloperBoardLaneReviewState,
  DeveloperBoardLaneValidationBasis,
  DeveloperBoardStatus,
  DeveloperMasterBoard,
} from '../../contracts/board'

export const BOARD_STATUSES: Array<{
  value: DeveloperBoardStatus
  label: string
  description: string
}> = [
  { value: 'active', label: 'Active', description: 'Current execution lanes' },
  { value: 'planned', label: 'Planned', description: 'Defined but not yet started' },
  { value: 'watch', label: 'Watch', description: 'Monitor and revisit deliberately' },
  { value: 'blocked', label: 'Blocked', description: 'Cannot move until dependencies clear' },
]

export type PlannerBoardTextField = 'title' | 'intent' | 'continuous_operation_goal'

export type PlannerLaneField =
  | 'title'
  | 'objective'
  | 'status'
  | 'owners'
  | 'inputs'
  | 'outputs'
  | 'dependencies'
  | 'completion_criteria'

export type PlannerLaneValidationBasisField = keyof DeveloperBoardLaneValidationBasis

export type PlannerLaneReviewStateField = keyof DeveloperBoardLaneReviewState

export type PlannerLaneReviewGateField = keyof DeveloperBoardLaneReviewGate

export type PlannerSubplanField = 'title' | 'objective' | 'status' | 'outputs'

export function statusTone(status: DeveloperBoardStatus) {
  switch (status) {
    case 'active':
      return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
    case 'planned':
      return 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
    case 'blocked':
      return 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
    case 'watch':
      return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
    default:
      return 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
  }
}

export function formatList(items: string[]) {
  return items.join('\n')
}

export function parseList(value: string) {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function summaryCountLabel(count: number, singular: string, plural: string) {
  return `${count} ${count === 1 ? singular : plural}`
}

export function updateBoardTextField(
  commitBoardUpdate: (updater: (board: DeveloperMasterBoard) => void) => void,
  field: PlannerBoardTextField,
  value: string
) {
  commitBoardUpdate((board) => {
    board[field] = value
  })
}