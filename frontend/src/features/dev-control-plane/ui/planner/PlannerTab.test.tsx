import type { ComponentProps } from 'react'

import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { defaultDeveloperMasterBoard } from '../../contracts/board'
import { Tabs } from '@/components/ui/tabs'
import { PlannerTab } from './PlannerTab'

type PlannerTabProps = ComponentProps<typeof PlannerTab>

function createPlannerTabProps(overrides: Partial<PlannerTabProps> = {}): PlannerTabProps {
  const board = structuredClone(defaultDeveloperMasterBoard)

  return {
    jsonError: null,
    parsedBoard: board,
    lanes: board.lanes,
    selectedLane: structuredClone(board.lanes[0]),
    availableAgents: ['OmShriMaatreNamaha', 'OmVishnaveNamah'],
    extraOwnersInput: '',
    boardVersionsState: 'idle',
    boardVersionsRecord: null,
    boardVersionsError: null,
    boardVersionsLastCheckedAt: null,
    boardRestoreState: 'idle',
    lastBoardRestoreResult: null,
    onSetActiveTab: vi.fn(),
    onSelectLane: vi.fn(),
    onSetExtraOwnersInput: vi.fn(),
    onResetBoard: vi.fn(),
    onCreateLane: vi.fn(),
    onDeleteLane: vi.fn(),
    onToggleOwner: vi.fn(),
    onAddExtraOwners: vi.fn(),
    onAddSubplan: vi.fn(),
    onUpdateBoardTextField: vi.fn(),
    onUpdateLaneField: vi.fn(),
    onUpdateValidationBasisField: vi.fn(),
    onUpdateReviewStateField: vi.fn(),
    onUpdateSubplan: vi.fn(),
    onDeleteSubplan: vi.fn(),
    onRefreshBoardVersions: vi.fn(async () => null),
    onRestoreBoardVersion: vi.fn(async () => undefined),
    onExport: vi.fn(),
    onTriggerImport: vi.fn(),
    ...overrides,
  }
}

function renderPlannerTab(overrides: Partial<PlannerTabProps> = {}) {
  const props = createPlannerTabProps(overrides)

  render(
    <Tabs value="planner" onValueChange={() => {}}>
      <PlannerTab {...props} />
    </Tabs>
  )

  return props
}

describe('PlannerTab', () => {
  it('renders and wires validation basis editing for the selected lane', () => {
    const onUpdateLaneField = vi.fn()
    const onUpdateValidationBasisField = vi.fn()
    const onUpdateReviewStateField = vi.fn()

    renderPlannerTab({
      onUpdateLaneField,
      onUpdateValidationBasisField,
      onUpdateReviewStateField,
    })

    expect(screen.getByText('Owner assignments')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Add extra owners, comma separated')).toBeInTheDocument()
    expect(screen.getByLabelText('Validation owner')).toHaveValue('OmVishnaveNamah')
    expect(screen.getByLabelText('Validation summary')).toHaveValue(
      'Focused control-plane contract and autonomy checkpoints remain the current execution-confidence basis for this lane.'
    )
    expect(screen.getByLabelText('Reviewed by', { selector: '#selected-lane-spec_review-reviewed-by' })).toHaveValue(
      'OmVishnaveNamah'
    )

    fireEvent.change(screen.getByLabelText('Validation owner'), {
      target: { value: 'OmShriMaatreNamaha' },
    })
    fireEvent.change(screen.getByLabelText('Last reviewed at'), {
      target: { value: '2026-03-18T21:00:00.000Z' },
    })
    fireEvent.change(screen.getByLabelText('Validation summary'), {
      target: { value: 'Updated validation confidence summary.' },
    })
    fireEvent.change(screen.getByLabelText('Validation evidence'), {
      target: { value: 'evidence/a\nevidence/b' },
    })
    fireEvent.change(screen.getByLabelText('Reviewed by', { selector: '#selected-lane-spec_review-reviewed-by' }), {
      target: { value: 'OmShriMaatreNamaha' },
    })
    fireEvent.change(screen.getByLabelText('Reviewed at', { selector: '#selected-lane-spec_review-reviewed-at' }), {
      target: { value: '2026-03-31T09:30:00.000Z' },
    })
    fireEvent.change(screen.getByLabelText('Summary', { selector: '#selected-lane-spec_review-summary' }), {
      target: { value: 'Updated spec review summary.' },
    })
    fireEvent.change(screen.getByLabelText('Evidence', { selector: '#selected-lane-spec_review-evidence' }), {
      target: { value: 'review/a\nreview/b' },
    })

    expect(onUpdateValidationBasisField).toHaveBeenNthCalledWith(1, 'owner', 'OmShriMaatreNamaha')
    expect(onUpdateValidationBasisField).toHaveBeenNthCalledWith(
      2,
      'last_reviewed_at',
      '2026-03-18T21:00:00.000Z'
    )
    expect(onUpdateValidationBasisField).toHaveBeenNthCalledWith(
      3,
      'summary',
      'Updated validation confidence summary.'
    )
    expect(onUpdateValidationBasisField).toHaveBeenNthCalledWith(4, 'evidence', ['evidence/a', 'evidence/b'])
    expect(onUpdateReviewStateField).toHaveBeenNthCalledWith(
      1,
      'spec_review',
      'reviewed_by',
      'OmShriMaatreNamaha'
    )
    expect(onUpdateReviewStateField).toHaveBeenNthCalledWith(
      2,
      'spec_review',
      'reviewed_at',
      '2026-03-31T09:30:00.000Z'
    )
    expect(onUpdateReviewStateField).toHaveBeenNthCalledWith(
      3,
      'spec_review',
      'summary',
      'Updated spec review summary.'
    )
    expect(onUpdateReviewStateField).toHaveBeenNthCalledWith(
      4,
      'spec_review',
      'evidence',
      ['review/a', 'review/b']
    )
    expect(onUpdateLaneField).not.toHaveBeenCalledWith('completion_criteria', expect.anything())
  })

  it('renders immutable board history and dispatches refresh and restore actions', () => {
    const onRefreshBoardVersions = vi.fn(async () => null)
    const onRestoreBoardVersion = vi.fn(async () => undefined)

    renderPlannerTab({
      boardVersionsState: 'ready',
      boardVersionsRecord: {
        board_id: 'bijmantra-app-development-master-board',
        current_concurrency_token: 'shared-token-8',
        total_count: 2,
        versions: [
          {
            revision_id: 8,
            schema_version: '1.0.0',
            visibility: 'internal-superuser',
            concurrency_token: 'shared-token-8',
            saved_by_user_id: 1,
            save_source: 'hidden-route-ui',
            summary_metadata: null,
            created_at: '2026-03-31T10:00:00.000Z',
            is_current: true,
          },
          {
            revision_id: 7,
            schema_version: '1.0.0',
            visibility: 'internal-superuser',
            concurrency_token: 'shared-token-7',
            saved_by_user_id: 1,
            save_source: 'hidden-route-restore',
            summary_metadata: null,
            created_at: '2026-03-31T09:30:00.000Z',
            is_current: false,
          },
        ],
      },
      boardVersionsLastCheckedAt: '2026-03-31T10:05:00.000Z',
      boardRestoreState: 'restored',
      lastBoardRestoreResult: {
        status: 'restored',
        message: 'Board restored from immutable revision 7. Approval receipt recorded: 91.',
        restored: true,
        restoredFromRevisionId: 7,
        currentBoardConcurrencyToken: 'shared-token-9',
        previousBoardConcurrencyToken: 'shared-token-8',
        approvalReceiptId: 91,
        approvalReceiptRecordedAt: '2026-03-31T10:06:00.000Z',
      },
      onRefreshBoardVersions,
      onRestoreBoardVersion,
    })

    expect(screen.getByText('Immutable Board History')).toBeInTheDocument()
    expect(screen.getByText('Current revision: 8')).toBeInTheDocument()
    expect(screen.getByText('Approval receipt 91')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Refresh history' }))
    fireEvent.click(screen.getByRole('button', { name: 'Restore' }))

    expect(onRefreshBoardVersions).toHaveBeenCalledTimes(1)
    expect(onRestoreBoardVersion).toHaveBeenCalledWith(7)
  })

  it('routes operators to the JSON tab when the canonical board is invalid', () => {
    const onSetActiveTab = vi.fn()
    const onResetBoard = vi.fn()

    renderPlannerTab({
      jsonError: 'Developer board JSON is invalid.',
      parsedBoard: null,
      lanes: [],
      selectedLane: null,
      onSetActiveTab,
      onResetBoard,
    })

    expect(screen.getByText('Planner unavailable while the canonical JSON is invalid.')).toBeInTheDocument()
    expect(screen.getByText('Developer board JSON is invalid.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Go to JSON tab' }))
    fireEvent.click(screen.getByRole('button', { name: 'Reset seed' }))

    expect(onSetActiveTab).toHaveBeenCalledWith('json')
    expect(onResetBoard).toHaveBeenCalledTimes(1)
  })

  it('shows the planner empty state when no lane is selected and still allows lane selection', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const onSelectLane = vi.fn()

    renderPlannerTab({
      parsedBoard: board,
      lanes: board.lanes,
      selectedLane: null,
      onSelectLane,
    })

    expect(screen.getByText('Create your first lane to start managing the board visually.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: new RegExp(board.lanes[1]!.title) }))

    expect(onSelectLane).toHaveBeenCalledWith(board.lanes[1]!.id)
  })

  it('wires planner toolbar, board edits, lane ownership, list fields, and sub-plan editing', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const selectedLane = structuredClone(board.lanes[0])
    const onCreateLane = vi.fn()
    const onExport = vi.fn()
    const onTriggerImport = vi.fn()
    const onUpdateBoardTextField = vi.fn()
    const onToggleOwner = vi.fn()
    const onSetExtraOwnersInput = vi.fn()
    const onAddExtraOwners = vi.fn()
    const onUpdateLaneField = vi.fn()
    const onDeleteLane = vi.fn()
    const onAddSubplan = vi.fn()
    const onUpdateSubplan = vi.fn()

    renderPlannerTab({
      parsedBoard: board,
      lanes: board.lanes,
      selectedLane,
      onCreateLane,
      onExport,
      onTriggerImport,
      onUpdateBoardTextField,
      onToggleOwner,
      onSetExtraOwnersInput,
      onAddExtraOwners,
      onUpdateLaneField,
      onDeleteLane,
      onAddSubplan,
      onUpdateSubplan,
    })

    fireEvent.click(screen.getByRole('button', { name: 'Add lane' }))
    fireEvent.click(screen.getByRole('button', { name: 'Export JSON' }))
    fireEvent.click(screen.getByRole('button', { name: 'Import JSON' }))

    fireEvent.change(screen.getByLabelText('Board title'), {
      target: { value: 'Updated Developer Control Plane' },
    })
    fireEvent.change(screen.getByLabelText('Continuous operation goal'), {
      target: { value: 'Keep planner execution bounded and current.' },
    })
    fireEvent.change(screen.getByLabelText('Board intent'), {
      target: { value: 'Updated board intent for planner test coverage.' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'OmShriMaatreNamaha' }))
    fireEvent.change(screen.getByPlaceholderText('Add extra owners, comma separated'), {
      target: { value: 'Agent Alpha, Agent Beta' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Add' }))

    fireEvent.change(screen.getByLabelText('Inputs'), {
      target: { value: 'input/a\ninput/b' },
    })
    fireEvent.change(screen.getByLabelText('Completion criteria'), {
      target: { value: 'criterion/a\ncriterion/b' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    fireEvent.click(screen.getByRole('button', { name: 'Add sub-plan' }))
    fireEvent.change(
      screen.getByLabelText('Sub-plan title', {
        selector: `#${selectedLane.subplans[0]!.id}-title`,
      }),
      {
      target: { value: 'Updated sub-plan title' },
      }
    )
    fireEvent.change(
      screen.getByLabelText('Objective', {
        selector: `#${selectedLane.subplans[0]!.id}-objective`,
      }),
      {
      target: { value: 'Updated sub-plan objective' },
      }
    )
    fireEvent.change(
      screen.getByLabelText('Outputs', {
        selector: `#${selectedLane.subplans[0]!.id}-outputs`,
      }),
      {
      target: { value: 'output/a\noutput/b' },
      }
    )

    expect(onCreateLane).toHaveBeenCalledTimes(1)
    expect(onExport).toHaveBeenCalledTimes(1)
    expect(onTriggerImport).toHaveBeenCalledTimes(1)
    expect(onUpdateBoardTextField).toHaveBeenNthCalledWith(1, 'title', 'Updated Developer Control Plane')
    expect(onUpdateBoardTextField).toHaveBeenNthCalledWith(
      2,
      'continuous_operation_goal',
      'Keep planner execution bounded and current.'
    )
    expect(onUpdateBoardTextField).toHaveBeenNthCalledWith(
      3,
      'intent',
      'Updated board intent for planner test coverage.'
    )
    expect(onToggleOwner).toHaveBeenCalledWith('OmShriMaatreNamaha')
    expect(onSetExtraOwnersInput).toHaveBeenCalledWith('Agent Alpha, Agent Beta')
    expect(onAddExtraOwners).toHaveBeenCalledTimes(1)
    expect(onUpdateLaneField).toHaveBeenCalledWith('inputs', ['input/a', 'input/b'])
    expect(onUpdateLaneField).toHaveBeenCalledWith('completion_criteria', ['criterion/a', 'criterion/b'])
    expect(onDeleteLane).toHaveBeenCalledTimes(1)
    expect(onAddSubplan).toHaveBeenCalledTimes(1)
    expect(onUpdateSubplan).toHaveBeenNthCalledWith(
      1,
      selectedLane.subplans[0]!.id,
      'title',
      'Updated sub-plan title'
    )
    expect(onUpdateSubplan).toHaveBeenNthCalledWith(
      2,
      selectedLane.subplans[0]!.id,
      'objective',
      'Updated sub-plan objective'
    )
    expect(onUpdateSubplan).toHaveBeenNthCalledWith(
      3,
      selectedLane.subplans[0]!.id,
      'outputs',
      ['output/a', 'output/b']
    )
  })
})