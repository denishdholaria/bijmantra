import { Trash2, UserRound } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

import type { DeveloperBoardLane, DeveloperBoardStatus } from '../../contracts/board'
import {
  BOARD_STATUSES,
  formatList,
  parseList,
  type PlannerLaneField,
  type PlannerLaneReviewGateField,
  type PlannerLaneReviewStateField,
  type PlannerLaneValidationBasisField,
} from './shared'

type LaneEditorCardProps = {
  selectedLane: DeveloperBoardLane
  availableAgents: string[]
  extraOwnersInput: string
  onDeleteLane: () => void
  onToggleOwner: (owner: string) => void
  onSetExtraOwnersInput: (value: string) => void
  onAddExtraOwners: () => void
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
}

export function LaneEditorCard({
  selectedLane,
  availableAgents,
  extraOwnersInput,
  onDeleteLane,
  onToggleOwner,
  onSetExtraOwnersInput,
  onAddExtraOwners,
  onUpdateLaneField,
  onUpdateValidationBasisField,
  onUpdateReviewStateField,
}: LaneEditorCardProps) {
  const validationBasis = selectedLane.validation_basis
  const reviewState = selectedLane.review_state
  const reviewSections: Array<{
    key: PlannerLaneReviewStateField
    title: string
    description: string
  }> = [
    {
      key: 'spec_review',
      title: 'Spec review',
      description: 'Explicit review proving the lane scope and intended contract were inspected before reviewed dispatch.',
    },
    {
      key: 'risk_review',
      title: 'Risk review',
      description: 'Explicit review proving the lane still follows bounded, non-destructive control-plane rules.',
    },
    {
      key: 'verification_evidence',
      title: 'Verification evidence',
      description: 'Explicit evidence that must exist on the canonical lane before reviewed completion write-back.',
    },
  ]

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>Lane Editor</CardTitle>
            <CardDescription>
              Manage one lane visually. These fields write back into the canonical JSON immediately.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onDeleteLane}>
            <Trash2 className="h-4 w-4" />
            Delete
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Lane ID</Label>
          <div className="rounded-md border border-border/70 bg-muted/30 px-3 py-2 font-mono text-sm text-muted-foreground">
            {selectedLane.id}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="selected-lane-title">Lane title</Label>
          <Input
            id="selected-lane-title"
            value={selectedLane.title}
            onChange={(event) => onUpdateLaneField('title', event.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label>Lane status</Label>
          <Select value={selectedLane.status} onValueChange={(value: DeveloperBoardStatus) => onUpdateLaneField('status', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              {BOARD_STATUSES.map((statusOption) => (
                <SelectItem key={statusOption.value} value={statusOption.value}>
                  {statusOption.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="selected-lane-objective">Objective</Label>
          <Textarea
            id="selected-lane-objective"
            value={selectedLane.objective}
            onChange={(event) => onUpdateLaneField('objective', event.target.value)}
            className="min-h-[7rem]"
          />
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <UserRound className="h-4 w-4 text-muted-foreground" />
            <Label>Owner assignments</Label>
          </div>
          <div className="flex flex-wrap gap-2">
            {availableAgents.map((agent) => (
              <button
                key={agent}
                type="button"
                onClick={() => onToggleOwner(agent)}
                className={cn(
                  'rounded-full border px-3 py-1.5 text-xs font-medium transition',
                  selectedLane.owners.includes(agent)
                    ? 'border-emerald-400 bg-emerald-50 text-emerald-700 dark:border-emerald-600 dark:bg-emerald-950/20 dark:text-emerald-300'
                    : 'border-border/70 bg-background text-muted-foreground hover:border-emerald-300/70'
                )}
              >
                {agent}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={extraOwnersInput}
              onChange={(event) => onSetExtraOwnersInput(event.target.value)}
              placeholder="Add extra owners, comma separated"
            />
            <Button variant="outline" onClick={onAddExtraOwners}>Add</Button>
          </div>
        </div>

        <div className="grid gap-4">
          <div className="space-y-2">
            <Label htmlFor="selected-lane-inputs">Inputs</Label>
            <Textarea
              id="selected-lane-inputs"
              value={formatList(selectedLane.inputs)}
              onChange={(event) => onUpdateLaneField('inputs', parseList(event.target.value))}
              className="min-h-[6rem]"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="selected-lane-outputs">Outputs</Label>
            <Textarea
              id="selected-lane-outputs"
              value={formatList(selectedLane.outputs)}
              onChange={(event) => onUpdateLaneField('outputs', parseList(event.target.value))}
              className="min-h-[6rem]"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="selected-lane-dependencies">Dependencies</Label>
            <Textarea
              id="selected-lane-dependencies"
              value={formatList(selectedLane.dependencies)}
              onChange={(event) => onUpdateLaneField('dependencies', parseList(event.target.value))}
              className="min-h-[5rem]"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="selected-lane-criteria">Completion criteria</Label>
            <Textarea
              id="selected-lane-criteria"
              value={formatList(selectedLane.completion_criteria)}
              onChange={(event) => onUpdateLaneField('completion_criteria', parseList(event.target.value))}
              className="min-h-[7rem]"
            />
          </div>

          <div className="rounded-2xl border border-border/70 bg-muted/20 p-4 space-y-4">
            <div>
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Validation basis</div>
              <div className="mt-1 text-sm text-muted-foreground">
                Explicit operator-owned validation confidence for this lane. Leave all fields blank to omit it.
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="selected-lane-validation-owner">Validation owner</Label>
                <Input
                  id="selected-lane-validation-owner"
                  value={validationBasis?.owner ?? ''}
                  onChange={(event) => onUpdateValidationBasisField('owner', event.target.value)}
                  placeholder="OmVishnaveNamah"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="selected-lane-validation-reviewed-at">Last reviewed at</Label>
                <Input
                  id="selected-lane-validation-reviewed-at"
                  value={validationBasis?.last_reviewed_at ?? ''}
                  onChange={(event) =>
                    onUpdateValidationBasisField('last_reviewed_at', event.target.value)
                  }
                  placeholder="2026-03-18T20:00:00.000Z"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="selected-lane-validation-summary">Validation summary</Label>
              <Textarea
                id="selected-lane-validation-summary"
                value={validationBasis?.summary ?? ''}
                onChange={(event) => onUpdateValidationBasisField('summary', event.target.value)}
                placeholder="Summarize the explicit validation basis for this lane."
                className="min-h-[6rem]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="selected-lane-validation-evidence">Validation evidence</Label>
              <Textarea
                id="selected-lane-validation-evidence"
                value={formatList(validationBasis?.evidence ?? [])}
                onChange={(event) =>
                  onUpdateValidationBasisField('evidence', parseList(event.target.value))
                }
                placeholder="One evidence reference per line"
                className="min-h-[6rem]"
              />
            </div>
          </div>

          <div className="rounded-2xl border border-border/70 bg-muted/20 p-4 space-y-4">
            <div>
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Review gates</div>
              <div className="mt-1 text-sm text-muted-foreground">
                Explicit reviewed-dispatch and completion gates stored on the canonical lane. Leave one section blank to omit that gate.
              </div>
            </div>

            <div className="space-y-4">
              {reviewSections.map((section) => {
                const reviewGate = reviewState?.[section.key]
                const fieldPrefix = `selected-lane-${section.key}`

                return (
                  <div key={section.key} className="rounded-xl border border-border/60 bg-background/70 p-4 space-y-4">
                    <div>
                      <div className="text-sm font-medium text-foreground">{section.title}</div>
                      <div className="mt-1 text-sm text-muted-foreground">{section.description}</div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor={`${fieldPrefix}-reviewed-by`}>Reviewed by</Label>
                        <Input
                          id={`${fieldPrefix}-reviewed-by`}
                          value={reviewGate?.reviewed_by ?? ''}
                          onChange={(event) =>
                            onUpdateReviewStateField(section.key, 'reviewed_by', event.target.value)
                          }
                          placeholder="OmVishnaveNamah"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor={`${fieldPrefix}-reviewed-at`}>Reviewed at</Label>
                        <Input
                          id={`${fieldPrefix}-reviewed-at`}
                          value={reviewGate?.reviewed_at ?? ''}
                          onChange={(event) =>
                            onUpdateReviewStateField(section.key, 'reviewed_at', event.target.value)
                          }
                          placeholder="2026-03-31T08:00:00.000Z"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor={`${fieldPrefix}-summary`}>Summary</Label>
                      <Textarea
                        id={`${fieldPrefix}-summary`}
                        value={reviewGate?.summary ?? ''}
                        onChange={(event) =>
                          onUpdateReviewStateField(section.key, 'summary', event.target.value)
                        }
                        placeholder={`Summarize the ${section.title.toLowerCase()} evidence for this lane.`}
                        className="min-h-[5rem]"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor={`${fieldPrefix}-evidence`}>Evidence</Label>
                      <Textarea
                        id={`${fieldPrefix}-evidence`}
                        value={formatList(reviewGate?.evidence ?? [])}
                        onChange={(event) =>
                          onUpdateReviewStateField(section.key, 'evidence', parseList(event.target.value))
                        }
                        placeholder="One evidence reference per line"
                        className="min-h-[5rem]"
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}