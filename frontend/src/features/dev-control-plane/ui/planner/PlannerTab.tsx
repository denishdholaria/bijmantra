import { AlertTriangle, Download, History, Plus, RotateCcw, Upload } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { TabsContent } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

import type {
  DeveloperBoardLane,
  DeveloperBoardStatus,
  DeveloperMasterBoard,
} from '../../contracts/board'
import type { DeveloperControlPlaneBoardVersionsListResponse } from '../../api/activeBoard'
import { LaneEditorCard } from './LaneEditorCard'
import { SubplansEditorCard } from './SubplansEditorCard'
import {
  BOARD_STATUSES,
  statusTone,
  summaryCountLabel,
  type PlannerBoardTextField,
  type PlannerLaneField,
  type PlannerLaneValidationBasisField,
  type PlannerSubplanField,
  type PlannerLaneReviewGateField,
  type PlannerLaneReviewStateField,
} from './shared'

type PlannerBoardRestoreResult = {
  status: 'restored' | 'conflict' | 'error'
  message: string
  restored: boolean
  restoredFromRevisionId: number | null
  currentBoardConcurrencyToken: string | null
  previousBoardConcurrencyToken: string | null
  approvalReceiptId: number | null
  approvalReceiptRecordedAt: string | null
}

type PlannerTabProps = {
  jsonError: string | null
  parsedBoard: DeveloperMasterBoard | null
  lanes: DeveloperBoardLane[]
  selectedLane: DeveloperBoardLane | null
  availableAgents: string[]
  extraOwnersInput: string
  boardVersionsState: 'idle' | 'loading' | 'ready' | 'error'
  boardVersionsRecord: DeveloperControlPlaneBoardVersionsListResponse | null
  boardVersionsError: string | null
  boardVersionsLastCheckedAt: string | null
  boardRestoreState: 'idle' | 'restoring' | 'restored' | 'conflict' | 'error'
  lastBoardRestoreResult: PlannerBoardRestoreResult | null
  onSetActiveTab: (value: string) => void
  onSelectLane: (laneId: string) => void
  onSetExtraOwnersInput: (value: string) => void
  onResetBoard: () => void
  onCreateLane: () => void
  onDeleteLane: () => void
  onToggleOwner: (owner: string) => void
  onAddExtraOwners: () => void
  onAddSubplan: () => void
  onUpdateBoardTextField: (field: PlannerBoardTextField, value: string) => void
  onUpdateLaneField: (
    field: PlannerLaneField,
    value: string | DeveloperBoardStatus | string[]
  ) => void
  onUpdateValidationBasisField: (
    field: PlannerLaneValidationBasisField,
    value: string | string[]
  ) => void
  onUpdateReviewStateField: (
    reviewField: PlannerLaneReviewStateField,
    field: PlannerLaneReviewGateField,
    value: string | string[]
  ) => void
  onUpdateSubplan: (
    subplanId: string,
    field: PlannerSubplanField,
    value: string | DeveloperBoardStatus | string[]
  ) => void
  onDeleteSubplan: (subplanId: string) => void
  onRefreshBoardVersions: () => Promise<unknown>
  onRestoreBoardVersion: (revisionId: number) => Promise<void>
  onExport: () => void
  onTriggerImport: () => void
}

export function PlannerTab({
  jsonError,
  parsedBoard,
  lanes,
  selectedLane,
  availableAgents,
  extraOwnersInput,
  boardVersionsState,
  boardVersionsRecord,
  boardVersionsError,
  boardVersionsLastCheckedAt,
  boardRestoreState,
  lastBoardRestoreResult,
  onSetActiveTab,
  onSelectLane,
  onSetExtraOwnersInput,
  onResetBoard,
  onCreateLane,
  onDeleteLane,
  onToggleOwner,
  onAddExtraOwners,
  onAddSubplan,
  onUpdateBoardTextField,
  onUpdateLaneField,
  onUpdateValidationBasisField,
  onUpdateReviewStateField,
  onUpdateSubplan,
  onDeleteSubplan,
  onRefreshBoardVersions,
  onRestoreBoardVersion,
  onExport,
  onTriggerImport,
}: PlannerTabProps) {
  const versions = boardVersionsRecord?.versions ?? []
  const currentRevisionId = versions.find((version) => version.is_current)?.revision_id

  return (
    <TabsContent value="planner" className="space-y-4">
      {jsonError ? (
        <Card>
          <CardContent className="flex flex-col gap-4 p-6">
            <div className="flex items-start gap-3 rounded-xl border border-amber-300/50 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-700/50 dark:bg-amber-950/30 dark:text-amber-200">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <div className="font-medium">Planner unavailable while the canonical JSON is invalid.</div>
                <div className="mt-1">{jsonError}</div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => onSetActiveTab('json')}>Go to JSON tab</Button>
              <Button variant="outline" onClick={onResetBoard}>Reset seed</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <CardTitle>Visual Planner</CardTitle>
                    <CardDescription>
                      Create lanes, assign owners, and manage sub-plans visually while editing the canonical control-plane board.
                    </CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" onClick={onCreateLane}>
                      <Plus className="h-4 w-4" />
                      Add lane
                    </Button>
                    <Button variant="outline" size="sm" onClick={onExport}>
                      <Download className="h-4 w-4" />
                      Export JSON
                    </Button>
                    <Button variant="outline" size="sm" onClick={onTriggerImport}>
                      <Upload className="h-4 w-4" />
                      Import JSON
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="board-title">Board title</Label>
                    <Input
                      id="board-title"
                      value={parsedBoard?.title ?? ''}
                      onChange={(event) => onUpdateBoardTextField('title', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="board-goal">Continuous operation goal</Label>
                    <Input
                      id="board-goal"
                      value={parsedBoard?.continuous_operation_goal ?? ''}
                      onChange={(event) => onUpdateBoardTextField('continuous_operation_goal', event.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="board-intent">Board intent</Label>
                  <Textarea
                    id="board-intent"
                    value={parsedBoard?.intent ?? ''}
                    onChange={(event) => onUpdateBoardTextField('intent', event.target.value)}
                    className="min-h-[6rem]"
                  />
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-4">
              {BOARD_STATUSES.map((statusColumn) => {
                const columnLanes = lanes.filter((lane) => lane.status === statusColumn.value)

                return (
                  <Card key={statusColumn.value} className="min-h-[20rem] border-border/70">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <CardTitle className="text-base">{statusColumn.label}</CardTitle>
                          <CardDescription>{statusColumn.description}</CardDescription>
                        </div>
                        <Badge className={cn('capitalize', statusTone(statusColumn.value))}>{columnLanes.length}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {columnLanes.length > 0 ? (
                        columnLanes.map((lane) => {
                          const isSelected = lane.id === selectedLane?.id

                          return (
                            <button
                              key={lane.id}
                              type="button"
                              onClick={() => onSelectLane(lane.id)}
                              className={cn(
                                'w-full rounded-2xl border p-4 text-left transition',
                                isSelected
                                  ? 'border-emerald-400 bg-emerald-50 shadow-sm dark:border-emerald-600 dark:bg-emerald-950/20'
                                  : 'border-border/70 bg-background hover:border-emerald-300/70 hover:bg-muted/30'
                              )}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{lane.id}</div>
                                  <div className="mt-1 font-medium text-foreground">{lane.title}</div>
                                </div>
                                <Badge className={cn('capitalize', statusTone(lane.status))}>{lane.status}</Badge>
                              </div>
                              <p className="mt-3 line-clamp-3 text-sm text-muted-foreground">{lane.objective}</p>
                              <div className="mt-3 flex flex-wrap gap-2">
                                {lane.owners.slice(0, 3).map((owner) => (
                                  <span key={owner} className="rounded-full border border-border/70 px-2.5 py-1 text-[11px] text-muted-foreground">
                                    {owner}
                                  </span>
                                ))}
                              </div>
                              <div className="mt-3 text-xs text-muted-foreground">
                                {summaryCountLabel(lane.subplans.length, 'sub-plan', 'sub-plans')} · {summaryCountLabel(lane.dependencies.length, 'dependency', 'dependencies')}
                              </div>
                            </button>
                          )
                        })
                      ) : (
                        <div className="rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
                          No lanes in this column yet.
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <History className="h-4 w-4 text-sky-500" />
                      Immutable Board History
                    </CardTitle>
                    <CardDescription>
                      Review explicit board revisions and restore a prior canonical state without creating a second planning surface.
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void onRefreshBoardVersions()}
                    disabled={boardVersionsState === 'loading' || boardRestoreState === 'restoring'}
                  >
                    Refresh history
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline">State: {boardVersionsState}</Badge>
                  {typeof currentRevisionId === 'number' ? (
                    <Badge variant="outline">Current revision: {currentRevisionId}</Badge>
                  ) : null}
                  {boardVersionsLastCheckedAt ? (
                    <span>Last checked {new Date(boardVersionsLastCheckedAt).toLocaleString()}</span>
                  ) : null}
                </div>

                {boardVersionsError ? (
                  <div className="rounded-2xl border border-amber-300/50 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-700/50 dark:bg-amber-950/30 dark:text-amber-200">
                    {boardVersionsError}
                  </div>
                ) : null}

                {versions.length > 0 ? (
                  <div className="space-y-2">
                    {versions.map((version) => (
                      <div
                        key={version.revision_id}
                        className="rounded-2xl border border-border/70 bg-background px-4 py-3"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <div className="font-medium text-foreground">Revision {version.revision_id}</div>
                              {version.is_current ? <Badge>Active head</Badge> : null}
                              <Badge variant="outline">{version.save_source}</Badge>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Saved {new Date(version.created_at).toLocaleString()}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Board token {version.concurrency_token}
                            </div>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={version.is_current || boardRestoreState === 'restoring'}
                            onClick={() => void onRestoreBoardVersion(version.revision_id)}
                          >
                            <RotateCcw className="h-4 w-4" />
                            {version.is_current ? 'Current head' : 'Restore'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
                    {boardVersionsState === 'loading'
                      ? 'Loading immutable board history.'
                      : 'No immutable board revisions are loaded yet.'}
                  </div>
                )}

                {lastBoardRestoreResult ? (
                  <div
                    className={cn(
                      'rounded-2xl border px-4 py-3 text-sm',
                      lastBoardRestoreResult.status === 'restored'
                        ? 'border-emerald-300/60 bg-emerald-50 text-emerald-900 dark:border-emerald-700/40 dark:bg-emerald-950/20 dark:text-emerald-200'
                        : 'border-amber-300/60 bg-amber-50 text-amber-900 dark:border-amber-700/40 dark:bg-amber-950/20 dark:text-amber-200'
                    )}
                  >
                    <div className="font-medium">{lastBoardRestoreResult.message}</div>
                    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs">
                      {lastBoardRestoreResult.restoredFromRevisionId ? (
                        <span>Revision {lastBoardRestoreResult.restoredFromRevisionId}</span>
                      ) : null}
                      {lastBoardRestoreResult.approvalReceiptId ? (
                        <span>Approval receipt {lastBoardRestoreResult.approvalReceiptId}</span>
                      ) : null}
                      {lastBoardRestoreResult.approvalReceiptRecordedAt ? (
                        <span>
                          Recorded {new Date(lastBoardRestoreResult.approvalReceiptRecordedAt).toLocaleString()}
                        </span>
                      ) : null}
                      {lastBoardRestoreResult.previousBoardConcurrencyToken ? (
                        <span>Previous token {lastBoardRestoreResult.previousBoardConcurrencyToken}</span>
                      ) : null}
                      {lastBoardRestoreResult.currentBoardConcurrencyToken ? (
                        <span>Current token {lastBoardRestoreResult.currentBoardConcurrencyToken}</span>
                      ) : null}
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            {selectedLane ? (
              <>
                <LaneEditorCard
                  selectedLane={selectedLane}
                  availableAgents={availableAgents}
                  extraOwnersInput={extraOwnersInput}
                  onDeleteLane={onDeleteLane}
                  onToggleOwner={onToggleOwner}
                  onSetExtraOwnersInput={onSetExtraOwnersInput}
                  onAddExtraOwners={onAddExtraOwners}
                  onUpdateLaneField={onUpdateLaneField}
                  onUpdateValidationBasisField={onUpdateValidationBasisField}
                  onUpdateReviewStateField={onUpdateReviewStateField}
                />
                <SubplansEditorCard
                  subplans={selectedLane.subplans}
                  onAddSubplan={onAddSubplan}
                  onUpdateSubplan={onUpdateSubplan}
                  onDeleteSubplan={onDeleteSubplan}
                />
              </>
            ) : (
              <Card>
                <CardContent className="p-6 text-sm text-muted-foreground">
                  Create your first lane to start managing the board visually.
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </TabsContent>
  )
}