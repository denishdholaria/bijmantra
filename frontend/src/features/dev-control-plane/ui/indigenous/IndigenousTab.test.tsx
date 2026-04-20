import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Tabs } from '@/components/ui/tabs'

import { IndigenousTab } from './IndigenousTab'

describe('IndigenousTab', () => {
  it('renders the native world-model brief, blockers, and recommended focus', () => {
    render(
      <Tabs value="indigenous" onValueChange={() => {}}>
        <IndigenousTab
          indigenousBrainState="ready"
          indigenousBrainLastCheckedAt="2026-04-05T10:30:00.000Z"
          indigenousBrainError={null}
          onRefresh={() => {}}
          indigenousBrainBrief={{
            generated_at: '2026-04-05T10:30:00.000Z',
            indigenous_brain: {
              status: 'bootstrapped',
              summary: 'Backend-native world model for the developer control plane.',
              authority_boundary:
                'It synthesizes canonical board, queue, mission, learning, and optional project-brain signals without promoting itself into a new authority source.',
              current_role: 'Turn scattered internal control-plane surfaces into one actionable brief.',
            },
            worldview_summary:
              'Indigenous Brain is now defined as the native control-plane world model rather than a second authority store.',
            board: {
              available: true,
              board_id: 'bijmantra-app-development-master-board',
              title: 'BijMantra Developer Control Plane',
              lane_count: 2,
              status_counts: {
                active: 1,
                planned: 0,
                blocked: 1,
                watch: 0,
                completed: 0,
              },
              active_lane_count: 1,
              blocked_lane_count: 1,
              active_lane_ids: ['control-plane'],
              blocked_lane_ids: ['platform-runtime'],
              lanes_missing_review: [],
              lanes_pending_closure: ['control-plane'],
              primary_orchestrator: 'OmShriMaatreNamaha',
              updated_at: '2026-04-05T10:20:00.000Z',
              detail: null,
            },
            queue: {
              exists: true,
              queue_path: '.agent/jobs/overnight-queue.json',
              queue_sha256: 'queue-sha-1',
              job_count: 1,
              updated_at: '2026-04-05T10:15:00.000Z',
              age_hours: 0.25,
              is_stale: false,
              stale_threshold_hours: 18,
              top_job_ids: ['overnight-lane-control-plane-token1234'],
              detail: null,
            },
            missions: {
              available: true,
              total_count: 1,
              active_count: 1,
              blocked_count: 0,
              escalation_count: 0,
              recent: [],
              detail: null,
            },
            learnings: {
              available: true,
              total_count: 1,
              recent: [],
              detail: null,
            },
            project_brain: {
              available: true,
              base_url: 'http://127.0.0.1:8083',
              query: 'beingbijmantra_surrealdb',
              source_match_count: 1,
              projection_match_count: 1,
              node_match_count: 1,
              provenance_trail_count: 1,
              notable_source_paths: [
                '.beingbijmantra/2026-04-04-being-bijmantra-surrealdb-sidecar-direction.md',
              ],
              notable_node_titles: ['Being Bijmantra SurrealDB Sidecar Direction'],
              detail: null,
            },
            mem0: {
              enabled: true,
              configured: true,
              ready: true,
              host: 'https://api.mem0.ai',
              project_scoped: true,
              org_project_pair_valid: true,
              detail: 'Mem0 is ready as an optional external episodic-memory adapter.',
            },
            recommended_focus: {
              source: 'active-board',
              lane_id: 'control-plane',
              title: 'Control Plane',
              status: 'active',
              objective: 'Make the native control plane operational.',
              reason:
                'This is the first active canonical lane without closure evidence and without blocked dependencies.',
              dependencies: [],
            },
            blockers: [
              {
                key: 'blocked-lanes-present',
                severity: 'blocking',
                surface: 'board',
                summary: 'The canonical board currently carries 1 blocked lane.',
                recommended_action: 'Resolve or downgrade blocked lanes.',
              },
            ],
            missing_capabilities: [
              'Backend planner-critic execution remains the next higher-order autonomy slice beyond this world-model foundation.',
            ],
          }}
        />
      </Tabs>
    )

    expect(screen.getByText('Native World Model')).toBeInTheDocument()
    expect(screen.getByText('Recommended Focus')).toBeInTheDocument()
    expect(screen.getAllByText('Control Plane').length).toBeGreaterThan(0)
    expect(screen.getByText('Material Blockers')).toBeInTheDocument()
    expect(screen.getByText('Project-Brain Enrichment')).toBeInTheDocument()
    expect(screen.getByText('Mem0')).toBeInTheDocument()
  })
})