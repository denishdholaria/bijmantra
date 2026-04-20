import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ControlPlanePage } from './ControlPlanePage'

function buildControllerState() {
  return {
    fileInputRef: { current: null },
    rawBoardJson: '{}',
    lastUpdatedAt: '2026-03-20T00:00:00.000Z',
    activeTab: 'planner',
    extraOwnersInput: '',
    parsedBoard: {
      agent_roles: [],
      control_plane: {
        primary_orchestrator: 'OmShriMaatreNamaha',
        operating_cadence: [],
      },
    },
    jsonError: null,
    lanes: [],
    activeLaneCount: 0,
    blockedLaneCount: 0,
    subplanCount: 0,
    dependencyCount: 0,
    selectedLane: null,
    availableAgents: [],
    autonomyAnalysis: null,
    selectedLaneAnalysis: null,
    recommendedLane: null,
    persistenceStatus: {
      tone: 'synced',
      label: 'Shared backend persistence active',
      description: 'Shared backend persistence is active for this hidden surface.',
    },
    dispatchPacket: null,
    queueCandidate: null,
    queueEntryMaterialization: {
      entry: null,
      unresolvedDependencyLaneIds: [],
    },
    selectedLaneQueueJobId: null,
    queueWriteState: 'idle',
    completionWriteState: 'idle',
    queueStatusState: 'idle',
    queueStatusRecord: null,
    queueStatusError: null,
    queueStatusLastRefreshedAt: null,
    closeoutReceiptState: 'idle',
    closeoutReceiptRecord: null,
    closeoutReceiptError: null,
    closeoutReceiptLastCheckedAt: null,
    runtimeWatchdogState: 'idle',
    runtimeWatchdogRecord: null,
    runtimeWatchdogError: null,
    runtimeWatchdogLastCheckedAt: null,
    runtimeAutonomyCycleState: 'idle',
    runtimeAutonomyCycleRecord: null,
    runtimeAutonomyCycleError: null,
    runtimeAutonomyCycleLastCheckedAt: null,
    runtimeCompletionAssistState: 'idle',
    runtimeCompletionAssistRecord: null,
    runtimeCompletionAssistError: null,
    runtimeCompletionAssistLastCheckedAt: null,
    silentMonitorsState: 'idle',
    silentMonitorsRecord: null,
    silentMonitorsError: null,
    silentMonitorsLastCheckedAt: null,
    learningLedgerState: 'idle',
    learningLedgerRecord: null,
    learningLedgerError: null,
    learningLedgerLastCheckedAt: null,
    learningLedgerQuery: { limit: 6 },
    missionStateState: 'idle',
    missionStateRecord: null,
    missionStateError: null,
    missionStateLastCheckedAt: null,
    missionDetailState: 'idle',
    missionDetailRecord: null,
    missionDetailError: null,
    missionDetailLastCheckedAt: null,
    indigenousBrainState: 'idle',
    indigenousBrainBrief: null,
    indigenousBrainError: null,
    indigenousBrainLastCheckedAt: null,
    lastQueueWriteResult: null,
    completionClosureSummary: '',
    completionEvidenceInput: '',
    lastCompletionWriteResult: null,
    replaceBoardJson: vi.fn(),
    formatBoardJson: vi.fn(),
    resetBoard: vi.fn(),
    setActiveTab: vi.fn(),
    setSelectedLaneId: vi.fn(),
    setExtraOwnersInput: vi.fn(),
    handleUpdateBoardTextField: vi.fn(),
    updateLaneField: vi.fn(),
    updateValidationBasisField: vi.fn(),
    handleCreateLane: vi.fn(),
    handleDeleteLane: vi.fn(),
    handleToggleOwner: vi.fn(),
    handleAddExtraOwners: vi.fn(),
    handleAddSubplan: vi.fn(),
    handleUpdateSubplan: vi.fn(),
    handleDeleteSubplan: vi.fn(),
    handlePromoteLane: vi.fn(),
    handleCopyDispatchPacket: vi.fn(),
    handleCopyQueueCandidate: vi.fn(),
    handleCopyQueueEntry: vi.fn(),
    refreshQueueStatus: vi.fn(),
    loadLearnings: vi.fn(),
    refreshIndigenousBrain: vi.fn(),
    handleRefreshRecommendedTargets: vi.fn(),
    handleRefreshAndRetryQueueWrite: vi.fn(),
    handleRefreshAndRetryLaneCompletion: vi.fn(),
    loadBoardVersions: vi.fn(),
    handleRestoreBoardVersion: vi.fn(),
    setCompletionClosureSummary: vi.fn(),
    setCompletionEvidenceInput: vi.fn(),
    handleDraftLaneCompletionFromCurrentState: vi.fn(),
    handleDraftLaneCompletionForLane: vi.fn(),
    handleWriteLaneCompletion: vi.fn(),
    handleWriteQueueEntry: vi.fn(),
    handleExport: vi.fn(),
    triggerImport: vi.fn(),
    handleImport: vi.fn(),
  }
}

let mockControllerState = buildControllerState()

vi.mock('./planner/PlannerTab', () => ({
  PlannerTab: () => <div>Planner Tab Body</div>,
}))

vi.mock('./overview/OverviewTab', () => ({
  OverviewTab: () => <div>Overview Tab Body</div>,
}))

vi.mock('./indigenous/IndigenousTab', () => ({
  IndigenousTab: () => <div>Indigenous Brain Tab Body</div>,
}))

vi.mock('./autonomy/AutonomyTab', () => ({
  AutonomyTab: () => <div>Autonomy Tab Body</div>,
}))

vi.mock('./mem0/Mem0Tab', () => ({
  Mem0Tab: () => <div>Mem0 Tab Body</div>,
}))

vi.mock('./arielma/ArielmaTab', () => ({
  ArielmaTab: () => <div>Diagram Tab Body</div>,
}))

vi.mock('./json/JsonTab', () => ({
  JsonTab: () => <div>JSON Tab Body</div>,
}))

vi.mock('./orchestration/OrchestrationTab', () => ({
  OrchestrationTab: () => <div>Orchestration Tab Body</div>,
}))

vi.mock('./useControlPlaneController', () => ({
  useControlPlaneController: () => mockControllerState,
}))

beforeEach(() => {
  mockControllerState = buildControllerState()
})

describe('ControlPlanePage', () => {
  it('renders the hidden control-plane shell with planner, autonomy, diagram, JSON, and orchestration tabs', () => {
    render(<ControlPlanePage />)

    expect(screen.getByRole('heading', { name: 'BijMantra Developer Control Plane' })).toBeInTheDocument()
    expect(screen.getByText('/admin/developer/master-board')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Indigenous Brain' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Planner' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Autonomy' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Mem0' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Diagram' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'JSON' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Orchestration' })).toBeInTheDocument()
  })

  it('shows Diagram in the current view card when the diagram tab is active', () => {
    mockControllerState.activeTab = 'arielma'

    render(<ControlPlanePage />)

    expect(screen.getAllByText('Diagram').length).toBeGreaterThan(0)
    expect(screen.queryByText('arielma')).not.toBeInTheDocument()
  })

  it('shows partial telemetry when queue data is live but runtime signals are degraded', () => {
    mockControllerState.queueStatusState = 'ready'
    mockControllerState.runtimeWatchdogState = 'error'
    mockControllerState.runtimeAutonomyCycleState = 'ready'
    mockControllerState.silentMonitorsState = 'ready'

    render(<ControlPlanePage />)

    expect(screen.getByText('partial telemetry')).toBeInTheDocument()
  })
})
