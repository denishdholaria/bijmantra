import { RefreshCw } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

import type { DeveloperControlPlaneMem0CaptureMissionResponse } from '../../api/mem0'
import type { DeveloperControlPlaneMissionStateResponse } from '../../api/activeBoard'

type LearningTabState = 'idle' | 'loading' | 'ready' | 'error'
type Mem0ActionState = 'idle' | 'submitting' | 'success' | 'error'

type Mem0MissionCaptureCardProps = {
  missionState: LearningTabState
  missionRecord: DeveloperControlPlaneMissionStateResponse | null
  missionError: string | null
  captureMissionState: Mem0ActionState
  captureMissionError: string | null
  capturingMissionId: string | null
  lastMissionCaptureResult: DeveloperControlPlaneMem0CaptureMissionResponse | null
  onRefreshMissions: () => Promise<void> | void
  onCaptureMission: (missionId: string) => Promise<void> | void
}

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2)
}

export function Mem0MissionCaptureCard({
  missionState,
  missionRecord,
  missionError,
  captureMissionState,
  captureMissionError,
  capturingMissionId,
  lastMissionCaptureResult,
  onRefreshMissions,
  onCaptureMission,
}: Mem0MissionCaptureCardProps) {
  const captureableMissions =
    missionRecord?.missions.filter(
      (mission) =>
        Boolean(mission.final_summary) ||
        mission.status === 'completed' ||
        mission.status === 'failed' ||
        Boolean(mission.queue_job_id)
    ) ?? []

  return (
    <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <CardTitle>Capture Mission Outcomes</CardTitle>
          <CardDescription>
            Copy recent canonical mission outcomes and closeout evidence into Mem0 as optional developer recall.
          </CardDescription>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={() => void onRefreshMissions()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh Missions
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm text-muted-foreground">
          {missionState === 'loading'
            ? 'Loading recent canonical mission outcomes...'
            : missionState === 'error'
              ? missionError
              : `${captureableMissions.length} recent missions available for explicit capture.`}
        </div>
        {captureMissionError && (
          <div className="text-sm text-rose-600 dark:text-rose-300">{captureMissionError}</div>
        )}
        {captureableMissions.length ? (
          <div className="space-y-3">
            {captureableMissions.map((mission) => (
              <div
                key={mission.mission_id}
                className="rounded-2xl border border-slate-200/80 bg-slate-50/90 p-4 dark:border-white/10 dark:bg-slate-950/50"
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="outline">{mission.status}</Badge>
                      <Badge variant="outline">{mission.priority}</Badge>
                      {mission.queue_job_id && <Badge variant="outline">{mission.queue_job_id}</Badge>}
                    </div>
                    <div className="text-sm font-semibold text-foreground">{mission.objective}</div>
                    <div className="text-sm text-muted-foreground">
                      {mission.final_summary ??
                        'No final summary is recorded yet; capture will use the current canonical mission state and verification counts.'}
                    </div>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => void onCaptureMission(mission.mission_id)}
                    disabled={
                      captureMissionState === 'submitting' && capturingMissionId === mission.mission_id
                    }
                  >
                    {captureMissionState === 'submitting' && capturingMissionId === mission.mission_id
                      ? 'Capturing...'
                      : 'Capture Mission to Mem0'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : null}
        {lastMissionCaptureResult && (
          <pre className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-slate-50/90 p-3 text-xs text-slate-800 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-100">
            {formatJson(lastMissionCaptureResult)}
          </pre>
        )}
      </CardContent>
    </Card>
  )
}