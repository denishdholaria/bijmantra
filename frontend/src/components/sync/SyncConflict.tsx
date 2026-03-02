import { AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export type SyncConflictItem = {
  id: string
  entityType: string
  summary: string
}

interface SyncConflictProps {
  conflicts: SyncConflictItem[]
  onResolve: () => void
}

export function SyncConflict({ conflicts, onResolve }: SyncConflictProps) {
  if (conflicts.length === 0) return null

  return (
    <Card className="border-amber-300/70 bg-amber-50/70 dark:border-amber-700/50 dark:bg-amber-950/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-amber-700 dark:text-amber-300">
          <AlertTriangle className="h-5 w-5" />
          Sync conflicts need review
        </CardTitle>
        <CardDescription>
          We detected {conflicts.length} local/server data conflicts. Review before next sync.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {conflicts.slice(0, 3).map((conflict) => (
          <div key={conflict.id} className="rounded border border-amber-200/80 bg-white/80 p-2 text-sm dark:border-amber-800/70 dark:bg-slate-900/50">
            <div className="font-semibold">{conflict.entityType}</div>
            <div className="text-muted-foreground">{conflict.summary}</div>
          </div>
        ))}
        <Button onClick={onResolve} variant="outline" className="border-amber-400 text-amber-700 hover:bg-amber-100">
          Resolve conflicts
        </Button>
      </CardContent>
    </Card>
  )
}
