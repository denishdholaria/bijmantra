import { describe, expect, it } from 'vitest'

import {
  buildReevuWorkbenchState,
  loadReevuAdvisoryCaseFiles,
  persistReevuAdvisoryCaseFile,
  REEVU_TOOL_REGISTRY,
  type ReevuAdvisoryCaseFile,
  type ReevuWorkbenchMessage,
} from './reevu-workbench'

function createStorage(): Storage {
  const values = new Map<string, string>()

  return {
    get length() {
      return values.size
    },
    clear() {
      values.clear()
    },
    getItem(key: string) {
      return values.get(key) ?? null
    },
    key(index: number) {
      return Array.from(values.keys())[index] ?? null
    },
    removeItem(key: string) {
      values.delete(key)
    },
    setItem(key: string, value: string) {
      values.set(key, value)
    },
  }
}

function createMessages(): ReevuWorkbenchMessage[] {
  return [
    {
      id: 'u1',
      role: 'user',
      content: 'Compare two wheat varieties before release.',
      timestamp: new Date('2026-07-03T08:00:00Z'),
      metadata: {
        attachments: [
          {
            id: 'file-1',
            name: 'trial-summary.csv',
            size: 128,
            mime_type: 'text/csv',
          },
        ],
      },
    },
    {
      id: 'a1',
      role: 'assistant',
      content: 'The comparison is ready for review.',
      timestamp: new Date('2026-07-03T08:01:00Z'),
      metadata: {
        run_events: [
          {
            type: 'reevu_run',
            request_id: 'req-1',
            run_id: 'run-1',
            event: 'run.started',
            status: 'started',
            trust_state: 'model_synthesis',
            case_id: 'req-1',
          },
          {
            type: 'reevu_run',
            request_id: 'req-1',
            run_id: 'run-1',
            event: 'approval.requested',
            status: 'required',
            title: 'Human approval gate',
            tool_name: 'calculate_breeding_value',
            tool_display_name: 'gblup.compute',
            authority_level: 'canonical_reevu_trusted_surface',
            trust_state: 'requires_review',
            approval_id: 'approval-1',
            approval_kind: 'policy_sensitive_recommendation',
            approval_status: 'pending_review',
            approval_reason: 'High-impact compute-backed recommendation requires review.',
          },
          {
            type: 'reevu_run',
            request_id: 'req-1',
            run_id: 'run-1',
            event: 'tool.completed',
            status: 'completed',
            tool_name: 'get_trial_results',
            tool_display_name: 'trial.rank',
            authority_level: 'canonical_reevu_trusted_surface',
            trust_state: 'trusted',
            duration_ms: 35.4,
            records_touched: 8,
            result_type: 'trial_results',
            success: true,
            artifact_ids: ['comparison-table', 'yield-table', 'field-map'],
          },
          {
            type: 'reevu_run',
            request_id: 'req-1',
            run_id: 'run-1',
            event: 'run.completed',
            status: 'completed',
            trust_state: 'trusted',
            case_id: 'req-1',
          },
        ],
        evidence_envelope: {
          claims: ['Variety A outranked Variety B in the scoped trials.'],
          claim_traces: [],
          evidence_refs: [
            {
              source_type: 'database',
              entity_id: 'TRIAL-1',
            },
          ],
          calculation_steps: [
            {
              step_id: 'rank-1',
              formula: 'rank(yield)',
              inputs: { records: 8 },
            },
          ],
          uncertainty: {
            confidence: 0.82,
            missing_data: ['quality score'],
          },
          missing_evidence_signals: ['seed inventory confirmation'],
          policy_flags: [],
        },
        plan_execution_summary: {
          plan_id: 'plan-1',
          is_compound: true,
          domains_involved: ['trials', 'weather'],
          total_steps: 2,
          steps: [
            {
              step_id: 'step-1',
              domain: 'trials',
              description: 'Rank trial performance.',
              status: 'completed',
              completed: true,
              services: ['trial_search_service.search'],
              output_counts: { trials: 8 },
            },
            {
              step_id: 'step-2',
              domain: 'weather',
              description: 'Attach weather context.',
              status: 'missing',
              completed: false,
              services: ['weather_service.get_forecast'],
              output_counts: { locations: 1 },
              missing_reason: 'Weather provider authority is unavailable.',
            },
          ],
        },
      },
    },
  ]
}

describe('buildReevuWorkbenchState', () => {
  it('derives case files, tools, approvals, lanes, artifacts, playbooks, and trust labels', () => {
    const state = buildReevuWorkbenchState(createMessages())

    expect(state.caseFile).toMatchObject({
      id: 'reevu-case-run-1',
      status: 'requires_review',
      messageCount: 2,
      runCount: 1,
      evidenceSnapshotCount: 1,
    })

    expect(state.toolCalls).toHaveLength(1)
    expect(state.toolCalls[0]).toMatchObject({
      displayName: 'trial.rank',
      status: 'completed',
      trustState: 'trusted',
      recordsTouched: 8,
      resultType: 'trial_results',
    })

    expect(state.approvalGates).toHaveLength(1)
    expect(state.approvalGates[0]).toMatchObject({
      id: 'approval-1',
      kind: 'policy_sensitive_recommendation',
      status: 'pending_review',
      trustState: 'requires_review',
      toolDisplayName: 'gblup.compute',
    })

    expect(state.artifacts.map(artifact => artifact.kind)).toEqual(
      expect.arrayContaining(['csv', 'evidence_packet', 'run_summary', 'comparison', 'generated_table', 'map']),
    )
    expect(state.artifacts.find(artifact => artifact.kind === 'csv')).toMatchObject({
      trustState: 'user_provided',
      detail: 'User-uploaded task context; not trusted evidence until formally ingested.',
    })

    expect(state.domainLanes.find(lane => lane.id === 'phenotyping')).toMatchObject({
      status: 'completed',
      evidenceCount: 8,
    })
    expect(state.domainLanes.find(lane => lane.id === 'climate')).toMatchObject({
      status: 'missing',
      trustState: 'partial',
      missingReason: 'Weather provider authority is unavailable.',
    })

    expect(state.playbooks.map(playbook => playbook.title)).toEqual(
      expect.arrayContaining([
        'Compare Varieties',
        'Diagnose Trial Failure',
        'Plan Cross',
        'Validate Recommendation',
        'Prepare Release Dossier',
        'Seed Inventory Risk',
      ]),
    )
    expect(state.toolRegistry.map(tool => tool.id)).toEqual(
      expect.arrayContaining([
        'breeding.search',
        'trial.rank',
        'phenotype.compare',
        'weather.enrich',
        'gblup.compute',
      ]),
    )
    expect(state.trustStates.map(entry => entry.state)).toEqual(
      expect.arrayContaining(['trusted', 'partial', 'user_provided', 'model_synthesis', 'missing_authority', 'requires_review']),
    )
    expect(REEVU_TOOL_REGISTRY.some(tool => tool.category === 'brapi')).toBe(true)
    expect(REEVU_TOOL_REGISTRY.some(tool => tool.category === 'rust-compute')).toBe(true)
  })
})

describe('REEVU advisory case persistence', () => {
  it('stores resumable case-file summaries without coupling to backend storage', () => {
    const storage = createStorage()
    const caseFile: ReevuAdvisoryCaseFile = {
      id: 'reevu-case-run-1',
      title: 'Compare varieties',
      status: 'requires_review',
      messageCount: 2,
      runCount: 1,
      evidenceSnapshotCount: 1,
      artifactCount: 4,
      decisionCount: 1,
      updatedAt: '2026-07-03T08:02:00Z',
    }

    persistReevuAdvisoryCaseFile(caseFile, storage)

    expect(loadReevuAdvisoryCaseFiles(storage)).toEqual([caseFile])
  })
})
