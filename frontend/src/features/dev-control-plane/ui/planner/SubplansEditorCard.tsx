import { Plus, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

import type { DeveloperBoardStatus, DeveloperBoardSubplan } from '../../contracts/board'
import {
  BOARD_STATUSES,
  formatList,
  parseList,
  type PlannerSubplanField,
} from './shared'

type SubplansEditorCardProps = {
  subplans: DeveloperBoardSubplan[]
  onAddSubplan: () => void
  onUpdateSubplan: (
    subplanId: string,
    field: PlannerSubplanField,
    value: string | DeveloperBoardStatus | string[]
  ) => void
  onDeleteSubplan: (subplanId: string) => void
}

export function SubplansEditorCard({
  subplans,
  onAddSubplan,
  onUpdateSubplan,
  onDeleteSubplan,
}: SubplansEditorCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>Sub-Plans</CardTitle>
            <CardDescription>
              Break the selected lane into smaller bounded slices without leaving the planner.
            </CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={onAddSubplan}>
            <Plus className="h-4 w-4" />
            Add sub-plan
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {subplans.length > 0 ? (
          subplans.map((subplan) => (
            <div key={subplan.id} className="rounded-2xl border border-border/70 bg-muted/20 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{subplan.id}</div>
                  <div className="mt-1 font-medium">{subplan.title}</div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label={`Delete ${subplan.id}`}
                  onClick={() => onDeleteSubplan(subplan.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>

              <div className="mt-4 space-y-3">
                <div className="space-y-2">
                  <Label htmlFor={`${subplan.id}-title`}>Sub-plan title</Label>
                  <Input
                    id={`${subplan.id}-title`}
                    value={subplan.title}
                    onChange={(event) => onUpdateSubplan(subplan.id, 'title', event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor={`${subplan.id}-status`}>Status</Label>
                  <Select
                    value={subplan.status}
                    onValueChange={(value: DeveloperBoardStatus) => onUpdateSubplan(subplan.id, 'status', value)}
                  >
                    <SelectTrigger id={`${subplan.id}-status`}>
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
                  <Label htmlFor={`${subplan.id}-objective`}>Objective</Label>
                  <Textarea
                    id={`${subplan.id}-objective`}
                    value={subplan.objective}
                    onChange={(event) => onUpdateSubplan(subplan.id, 'objective', event.target.value)}
                    className="min-h-[5rem]"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor={`${subplan.id}-outputs`}>Outputs</Label>
                  <Textarea
                    id={`${subplan.id}-outputs`}
                    value={formatList(subplan.outputs)}
                    onChange={(event) => onUpdateSubplan(subplan.id, 'outputs', parseList(event.target.value))}
                    className="min-h-[4rem]"
                  />
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
            No sub-plans yet. Use sub-plans for bounded slices inside the selected lane.
          </div>
        )}
      </CardContent>
    </Card>
  )
}