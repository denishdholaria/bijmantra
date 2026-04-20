import { describe, expect, it } from 'vitest'

import {
  canonicalizeDeveloperMasterBoardJson,
  DEVELOPER_MASTER_BOARD_LEGACY_SCHEMA_VERSION,
  DEVELOPER_MASTER_BOARD_PREVIOUS_SCHEMA_VERSION,
  DEVELOPER_MASTER_BOARD_SCHEMA_VERSION,
  createDeveloperLaneTemplate,
  createDeveloperSubplanTemplate,
  developerMasterBoardVersionPolicy,
  defaultDeveloperMasterBoard,
  normalizeDeveloperMasterBoard,
  parseDeveloperMasterBoard,
  serializeDeveloperMasterBoard,
} from './board'

describe('Developer master board contract parsing', () => {
  it('round-trips the canonical board JSON through the validated parser', () => {
    const rawBoardJson = serializeDeveloperMasterBoard(defaultDeveloperMasterBoard)

    expect(parseDeveloperMasterBoard(rawBoardJson)).toEqual(defaultDeveloperMasterBoard)
  })

  it('encodes the Zero Human Intervention Autonomous Execution Protocol in the default board contract', () => {
    expect(defaultDeveloperMasterBoard.intent).toContain(
      'Zero Human Intervention Autonomous Execution Protocol'
    )
    expect(defaultDeveloperMasterBoard.orchestration_contract.canonical_inputs).toEqual(
      expect.arrayContaining(['human vision', 'optional constraints'])
    )
    expect(defaultDeveloperMasterBoard.orchestration_contract.execution_loop).toEqual(
      expect.arrayContaining([
        'interpret vision into concrete system objectives',
        'monitor runtime and board drift for the next improvement cycle',
      ])
    )
    expect(defaultDeveloperMasterBoard.orchestration_contract.coordination_rules).toEqual(
      expect.arrayContaining([
        'human input is limited to vision and optional constraints',
        'under uncertainty, choose the safest non-destructive path and preserve rollback capability',
      ])
    )
  })

  it('rejects unsupported schema versions before the page touches board fields', () => {
    const invalidBoardJson = JSON.stringify({
      ...defaultDeveloperMasterBoard,
      version: '0.9.0',
    })

    expect(() => parseDeveloperMasterBoard(invalidBoardJson)).toThrow(
      `unsupported schema version ${JSON.stringify('0.9.0')}; supported import versions: ${developerMasterBoardVersionPolicy.supportedImportVersions.join(', ')}; current export version: ${developerMasterBoardVersionPolicy.exportVersion}`
    )
  })

  it('exposes an explicit exact-match version policy for imports and exports', () => {
    expect(developerMasterBoardVersionPolicy).toEqual({
      exportVersion: DEVELOPER_MASTER_BOARD_SCHEMA_VERSION,
      currentVersion: DEVELOPER_MASTER_BOARD_SCHEMA_VERSION,
      supportedImportVersions: [
        DEVELOPER_MASTER_BOARD_LEGACY_SCHEMA_VERSION,
        DEVELOPER_MASTER_BOARD_PREVIOUS_SCHEMA_VERSION,
        DEVELOPER_MASTER_BOARD_SCHEMA_VERSION,
      ],
      compatibilityMode: 'explicit-import-list',
    })
    expect(defaultDeveloperMasterBoard.version).toBe(developerMasterBoardVersionPolicy.exportVersion)
  })

  it('accepts legacy 1.0.0 boards while exporting the current schema version', () => {
    const legacyBoardJson = JSON.stringify({
      ...defaultDeveloperMasterBoard,
      version: DEVELOPER_MASTER_BOARD_LEGACY_SCHEMA_VERSION,
    })

    expect(parseDeveloperMasterBoard(legacyBoardJson).version).toBe(
      DEVELOPER_MASTER_BOARD_LEGACY_SCHEMA_VERSION
    )
    expect(defaultDeveloperMasterBoard.version).toBe(DEVELOPER_MASTER_BOARD_SCHEMA_VERSION)
  })

  it('rejects boards whose version field is not a string', () => {
    const invalidBoardJson = JSON.stringify({
      ...defaultDeveloperMasterBoard,
      version: 1,
    })

    expect(() => parseDeveloperMasterBoard(invalidBoardJson)).toThrow(
      'Invalid developer master board: version must be a string'
    )
  })

  it('rejects structurally invalid lanes', () => {
    const invalidBoardJson = JSON.stringify({
      ...defaultDeveloperMasterBoard,
      lanes: [{ id: 'broken-lane' }],
    })

    expect(() => parseDeveloperMasterBoard(invalidBoardJson)).toThrow(
      'Invalid developer master board: lanes[0] is missing required text fields'
    )
  })

  it('creates collision-safe template ids when existing ids are sparse or reused', () => {
    const laneTemplate = createDeveloperLaneTemplate(4)
    const subplanTemplate = createDeveloperSubplanTemplate(2)

    expect(laneTemplate.id).toMatch(/^new-lane-4-/)
    expect(subplanTemplate.id).toMatch(/^subplan-2-/)
  })

  it('canonicalizes valid board JSON with deterministic root and nested key order', () => {
    const reorderedBoardJson = JSON.stringify({
      title: defaultDeveloperMasterBoard.title,
      board_id: defaultDeveloperMasterBoard.board_id,
      version: defaultDeveloperMasterBoard.version,
      visibility: defaultDeveloperMasterBoard.visibility,
      continuous_operation_goal: defaultDeveloperMasterBoard.continuous_operation_goal,
      intent: defaultDeveloperMasterBoard.intent,
      control_plane: {
        operating_cadence: defaultDeveloperMasterBoard.control_plane.operating_cadence,
        evidence_sources: defaultDeveloperMasterBoard.control_plane.evidence_sources,
        primary_orchestrator: defaultDeveloperMasterBoard.control_plane.primary_orchestrator,
      },
      agent_roles: defaultDeveloperMasterBoard.agent_roles.map((role) => ({
        role: role.role,
        agent: role.agent,
        escalation: role.escalation,
        writes: role.writes,
        reads: role.reads,
      })),
      lanes: defaultDeveloperMasterBoard.lanes.map((lane) => ({
        title: lane.title,
        id: lane.id,
        objective: lane.objective,
        status: lane.status,
        outputs: lane.outputs,
        owners: lane.owners,
        inputs: lane.inputs,
        dependencies: lane.dependencies,
        validation_basis: lane.validation_basis
          ? {
              summary: lane.validation_basis.summary,
              owner: lane.validation_basis.owner,
              last_reviewed_at: lane.validation_basis.last_reviewed_at,
              evidence: lane.validation_basis.evidence,
            }
          : undefined,
        review_state: lane.review_state
          ? {
              spec_review: lane.review_state.spec_review
                ? {
                    reviewed_by: lane.review_state.spec_review.reviewed_by,
                    summary: lane.review_state.spec_review.summary,
                    evidence: lane.review_state.spec_review.evidence,
                    reviewed_at: lane.review_state.spec_review.reviewed_at,
                  }
                : undefined,
              risk_review: lane.review_state.risk_review
                ? {
                    reviewed_by: lane.review_state.risk_review.reviewed_by,
                    summary: lane.review_state.risk_review.summary,
                    evidence: lane.review_state.risk_review.evidence,
                    reviewed_at: lane.review_state.risk_review.reviewed_at,
                  }
                : undefined,
              verification_evidence: lane.review_state.verification_evidence
                ? {
                    reviewed_by: lane.review_state.verification_evidence.reviewed_by,
                    summary: lane.review_state.verification_evidence.summary,
                    evidence: lane.review_state.verification_evidence.evidence,
                    reviewed_at: lane.review_state.verification_evidence.reviewed_at,
                  }
                : undefined,
            }
          : undefined,
        subplans: lane.subplans.map((subplan) => ({
          title: subplan.title,
          id: subplan.id,
          status: subplan.status,
          objective: subplan.objective,
          outputs: subplan.outputs,
        })),
        completion_criteria: lane.completion_criteria,
      })),
      orchestration_contract: {
        coordination_rules: defaultDeveloperMasterBoard.orchestration_contract.coordination_rules,
        execution_loop: defaultDeveloperMasterBoard.orchestration_contract.execution_loop,
        canonical_outputs: defaultDeveloperMasterBoard.orchestration_contract.canonical_outputs,
        canonical_inputs: defaultDeveloperMasterBoard.orchestration_contract.canonical_inputs,
      },
    })

    expect(canonicalizeDeveloperMasterBoardJson(reorderedBoardJson)).toBe(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard)
    )
    expect(serializeDeveloperMasterBoard(parseDeveloperMasterBoard(reorderedBoardJson))).toBe(
      serializeDeveloperMasterBoard(normalizeDeveloperMasterBoard(defaultDeveloperMasterBoard))
    )
  })

  it('round-trips completed lane closure metadata through serialization', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    board.lanes[0] = {
      ...board.lanes[0],
      status: 'completed',
      closure: {
        queue_job_id: 'overnight-lane-control-plane-token1234',
        queue_sha256: 'queue-sha-1234',
        source_board_concurrency_token: 'token-1234',
        closure_summary: 'Completion evidence was reviewed and accepted.',
        evidence: ['Focused tests passed', 'Queue job status is completed'],
        completed_at: '2026-03-18T18:00:00.000Z',
        closeout_receipt: {
          queue_job_id: 'overnight-lane-control-plane-token1234',
          artifact_paths: ['metrics.json'],
          mission_id: 'runtime-mission-control-plane-token1234',
          producer_key: 'openclaw-runtime',
          source_lane_id: 'control-plane',
          source_board_concurrency_token: 'token-1234',
          runtime_profile_id: 'bijmantra-bca-local-verify',
          runtime_policy_sha256: 'policy-sha-1234',
          closeout_status: 'passed',
          state_refresh_required: true,
          receipt_recorded_at: '2026-03-18T18:00:00.000Z',
          verification_evidence_ref: 'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
          queue_sha256_at_closeout: 'queue-sha-1234',
        },
      },
    }

    expect(parseDeveloperMasterBoard(serializeDeveloperMasterBoard(board)).lanes[0]).toMatchObject({
      status: 'completed',
      closure: {
        queue_job_id: 'overnight-lane-control-plane-token1234',
        queue_sha256: 'queue-sha-1234',
        closeout_receipt: {
          mission_id: 'runtime-mission-control-plane-token1234',
          runtime_profile_id: 'bijmantra-bca-local-verify',
          runtime_policy_sha256: 'policy-sha-1234',
        },
      },
    })
  })

  it('round-trips explicit validation_basis metadata through serialization', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    board.lanes[0] = {
      ...board.lanes[0],
      validation_basis: {
        owner: 'OmVishnaveNamah',
        summary: 'Focused contract review remains the explicit active-lane validation basis.',
        evidence: [
          'frontend/src/features/dev-control-plane/contracts/board.test.ts',
          'frontend/src/features/dev-control-plane/autonomy.test.ts',
        ],
        last_reviewed_at: '2026-03-18T20:00:00.000Z',
      },
    }

    expect(parseDeveloperMasterBoard(serializeDeveloperMasterBoard(board)).lanes[0]).toMatchObject({
      validation_basis: {
        owner: 'OmVishnaveNamah',
        last_reviewed_at: '2026-03-18T20:00:00.000Z',
      },
    })
  })

  it('round-trips explicit review_state metadata through serialization', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    board.lanes[0] = {
      ...board.lanes[0],
      review_state: {
        spec_review: {
          reviewed_by: 'OmVishnaveNamah',
          summary: 'Spec review is current.',
          evidence: ['frontend/src/features/dev-control-plane/contracts/board.test.ts'],
          reviewed_at: '2026-03-31T09:00:00.000Z',
        },
        risk_review: {
          reviewed_by: 'OmKlimKalikayeiNamah',
          summary: 'Risk review is current.',
          evidence: ['frontend/src/features/dev-control-plane/reviewedDispatch.test.ts'],
          reviewed_at: '2026-03-31T09:05:00.000Z',
        },
        verification_evidence: {
          reviewed_by: 'OmVishnaveNamah',
          summary: 'Verification evidence is current.',
          evidence: ['frontend/src/features/dev-control-plane/autonomy.test.ts'],
          reviewed_at: '2026-03-31T09:10:00.000Z',
        },
      },
    }

    expect(parseDeveloperMasterBoard(serializeDeveloperMasterBoard(board)).lanes[0]).toMatchObject({
      review_state: {
        spec_review: {
          reviewed_by: 'OmVishnaveNamah',
          reviewed_at: '2026-03-31T09:00:00.000Z',
        },
        verification_evidence: {
          summary: 'Verification evidence is current.',
        },
      },
    })
  })

  it('rejects invalid validation_basis payloads', () => {
    const invalidBoardJson = JSON.stringify({
      ...defaultDeveloperMasterBoard,
      lanes: [
        {
          ...defaultDeveloperMasterBoard.lanes[0],
          validation_basis: {
            owner: 'OmVishnaveNamah',
            summary: 'Missing evidence array',
            last_reviewed_at: '2026-03-18T20:00:00.000Z',
          },
        },
        ...defaultDeveloperMasterBoard.lanes.slice(1),
      ],
    })

    expect(() => parseDeveloperMasterBoard(invalidBoardJson)).toThrow(
      'Invalid developer master board: lanes[0].validation_basis evidence must be a string array'
    )
  })

  it('rejects invalid review_state payloads', () => {
    const invalidBoardJson = JSON.stringify({
      ...defaultDeveloperMasterBoard,
      lanes: [
        {
          ...defaultDeveloperMasterBoard.lanes[0],
          review_state: {
            spec_review: {
              reviewed_by: 'OmVishnaveNamah',
              summary: 'Missing evidence array',
              reviewed_at: '2026-03-31T09:00:00.000Z',
            },
          },
        },
        ...defaultDeveloperMasterBoard.lanes.slice(1),
      ],
    })

    expect(() => parseDeveloperMasterBoard(invalidBoardJson)).toThrow(
      'Invalid developer master board: lanes[0].review_state.spec_review evidence must be a string array'
    )
  })
})
