import { RefreshCw } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

import type { DeveloperControlPlaneMem0CaptureLearningResponse } from '../../api/mem0'
import type { DeveloperControlPlaneLearningLedgerResponse } from '../../api/activeBoard'

type LearningTabState = 'idle' | 'loading' | 'ready' | 'error'
type Mem0ActionState = 'idle' | 'submitting' | 'success' | 'error'

type Mem0LearningCaptureCardProps = {
  learningState: LearningTabState
  learningRecord: DeveloperControlPlaneLearningLedgerResponse | null
  learningError: string | null
  captureState: Mem0ActionState
  captureError: string | null
  capturingLearningId: number | null
  lastCaptureResult: DeveloperControlPlaneMem0CaptureLearningResponse | null
  onRefreshLearnings: () => Promise<void> | void
  onCaptureLearning: (learningEntryId: number) => Promise<void> | void
}

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2)
}

export function Mem0LearningCaptureCard({
  learningState,
  learningRecord,
  learningError,
  captureState,
  captureError,
  capturingLearningId,
  lastCaptureResult,
  onRefreshLearnings,
  onCaptureLearning,
}: Mem0LearningCaptureCardProps) {
  return (
    <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <CardTitle>Capture Canonical Learnings</CardTitle>
          <CardDescription>
            Pull selected learning ledger entries into Mem0 as optional developer recall, without changing canonical authority.
          </CardDescription>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={() => void onRefreshLearnings()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh Learnings
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm text-muted-foreground">
          {learningState === 'loading'
            ? 'Loading recent canonical learnings...'
            : learningState === 'error'
              ? learningError
              : `${learningRecord?.total_count ?? 0} canonical learning entries available.`}
        </div>
        {captureError && <div className="text-sm text-rose-600 dark:text-rose-300">{captureError}</div>}
        {learningRecord?.entries.length ? (
          <div className="space-y-3">
            {learningRecord.entries.map((entry) => (
              <div
                key={entry.learning_entry_id}
                className="rounded-2xl border border-slate-200/80 bg-slate-50/90 p-4 dark:border-white/10 dark:bg-slate-950/50"
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="outline">#{entry.learning_entry_id}</Badge>
                      <Badge variant="outline">{entry.entry_type}</Badge>
                      <Badge variant="outline">{entry.source_classification}</Badge>
                    </div>
                    <div className="text-sm font-semibold text-foreground">{entry.title}</div>
                    <div className="text-sm text-muted-foreground">{entry.summary}</div>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => void onCaptureLearning(entry.learning_entry_id)}
                    disabled={captureState === 'submitting' && capturingLearningId === entry.learning_entry_id}
                  >
                    {captureState === 'submitting' && capturingLearningId === entry.learning_entry_id
                      ? 'Capturing...'
                      : 'Capture to Mem0'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : null}
        {lastCaptureResult && (
          <pre className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-slate-50/90 p-3 text-xs text-slate-800 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-100">
            {formatJson(lastCaptureResult)}
          </pre>
        )}
      </CardContent>
    </Card>
  )
}