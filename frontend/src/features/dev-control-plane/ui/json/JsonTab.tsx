import {
  AlertTriangle,
  Download,
  Eye,
  FileJson2,
  RefreshCcw,
  Shield,
  Upload,
  Workflow,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { DeveloperControlPlanePersistenceStatus } from '../../state/selectors'
import { TabsContent } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'

type JsonTabProps = {
  jsonError: string | null
  rawBoardJson: string
  onRawBoardJsonChange: (value: string) => void
  onFormatJson: () => void
  onExport: () => void
  onTriggerImport: () => void
  onResetBoard: () => void
  persistenceStatus: DeveloperControlPlanePersistenceStatus
}

export function JsonTab({
  jsonError,
  rawBoardJson,
  onRawBoardJsonChange,
  onFormatJson,
  onExport,
  onTriggerImport,
  onResetBoard,
  persistenceStatus,
}: JsonTabProps) {
  return (
    <TabsContent value="json" className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>Canonical Control-Plane JSON</CardTitle>
                <CardDescription>
                  Direct view for canonical board editing, import, export, and recovery. Agents should treat this as the machine-readable planning contract.
                </CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" onClick={onFormatJson} disabled={!!jsonError}>
                  <FileJson2 className="h-4 w-4" />
                  Format JSON
                </Button>
                <Button variant="outline" size="sm" onClick={onExport}>
                  <Download className="h-4 w-4" />
                  Export
                </Button>
                <Button variant="outline" size="sm" onClick={onTriggerImport}>
                  <Upload className="h-4 w-4" />
                  Import
                </Button>
                <Button variant="ghost" size="sm" onClick={onResetBoard}>
                  <RefreshCcw className="h-4 w-4" />
                  Reset Seed
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {jsonError && (
              <div className="flex items-start gap-3 rounded-xl border border-amber-300/50 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-700/50 dark:bg-amber-950/30 dark:text-amber-200">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <div>
                  <div className="font-medium">Invalid board JSON</div>
                  <div className="mt-1">{jsonError}</div>
                </div>
              </div>
            )}
            <Textarea
              value={rawBoardJson}
              onChange={(event) => onRawBoardJsonChange(event.target.value)}
              spellCheck={false}
              className="min-h-[34rem] font-mono text-xs leading-6"
            />
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>How to use this</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>Use the Planner tab as the preferred human editing surface for the canonical board.</p>
              <p>Use this JSON tab when you need direct machine-readable edits or want to import or export a canonical board snapshot.</p>
              <p>The Graph and Orchestration tabs are derived from this same canonical control-plane JSON.</p>
              <p>
                Persistence status: <span className="font-medium text-foreground">{persistenceStatus.label}</span>. {persistenceStatus.description}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Hidden Surface Contract</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <div className="flex items-start gap-2">
                <Eye className="mt-0.5 h-4 w-4 text-slate-500" />
                <span>Not registered in workspace or division navigation.</span>
              </div>
              <div className="flex items-start gap-2">
                <Shield className="mt-0.5 h-4 w-4 text-slate-500" />
                <span>Superuser-only route protected by the existing auth shell.</span>
              </div>
              <div className="flex items-start gap-2">
                <Workflow className="mt-0.5 h-4 w-4 text-slate-500" />
                <span>The canonical JSON stays authoritative so agents can parse it before acting.</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </TabsContent>
  )
}