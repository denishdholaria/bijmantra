import { Copy } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

import {
  activityFilterLabel,
  activityKindLabel,
  mem0ActivityFilterOptions,
  type Mem0ActivityEntry,
  type Mem0ActivityFilter,
} from './activityTrail'

type Mem0SessionTrailCardProps = {
  activityTrail: Mem0ActivityEntry[]
  filteredActivityTrail: Mem0ActivityEntry[]
  activityFilter: Mem0ActivityFilter
  onSetActivityFilter: (filter: Mem0ActivityFilter) => void
  onCopyVisibleActivitySummaries: () => Promise<void> | void
  onClearActivityTrail: () => void
  onCopyActivitySummary: (entry: Mem0ActivityEntry) => Promise<void> | void
}

export function Mem0SessionTrailCard({
  activityTrail,
  filteredActivityTrail,
  activityFilter,
  onSetActivityFilter,
  onCopyVisibleActivitySummaries,
  onClearActivityTrail,
  onCopyActivitySummary,
}: Mem0SessionTrailCardProps) {
  return (
    <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <CardTitle>Recent Session Trail</CardTitle>
          <CardDescription>
            Session-scoped operator trail for successful Mem0 writes from this hidden tab. It is visible recall only, not canonical authority.
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void onCopyVisibleActivitySummaries()}
            disabled={filteredActivityTrail.length === 0}
          >
            <Copy className="mr-2 h-4 w-4" />
            Copy Visible Summaries
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onClearActivityTrail}
            disabled={activityTrail.length === 0}
          >
            Clear Trail
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {mem0ActivityFilterOptions.map((option) => {
            const count =
              option === 'all'
                ? activityTrail.length
                : activityTrail.filter((entry) => entry.kind === option).length

            return (
              <Button
                key={option}
                type="button"
                size="sm"
                variant={activityFilter === option ? 'default' : 'outline'}
                onClick={() => onSetActivityFilter(option)}
              >
                {`${activityFilterLabel(option)} (${count})`}
              </Button>
            )
          })}
        </div>
        {activityTrail.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No successful Mem0 writes have been recorded in this session yet.
          </div>
        ) : filteredActivityTrail.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No session trail entries match {activityFilterLabel(activityFilter).toLowerCase()} yet.
          </div>
        ) : (
          <div className="space-y-3">
            {filteredActivityTrail.map((entry) => (
              <div
                key={entry.id}
                className="rounded-2xl border border-slate-200/80 bg-slate-50/90 p-4 dark:border-white/10 dark:bg-slate-950/50"
              >
                <div className="flex flex-col gap-3">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="outline">{activityKindLabel(entry.kind)}</Badge>
                      <Badge variant="outline">{entry.scopeLabel}</Badge>
                      {entry.resultId && <Badge variant="outline">{entry.resultId}</Badge>}
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => void onCopyActivitySummary(entry)}
                    >
                      <Copy className="mr-2 h-4 w-4" />
                      Copy Summary
                    </Button>
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm font-semibold text-foreground">{entry.title}</div>
                    <div className="text-sm text-muted-foreground">{entry.summary}</div>
                    <div className="text-xs text-muted-foreground">
                      Recorded {new Date(entry.recordedAt).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}