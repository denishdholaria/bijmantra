import { Search, Upload } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

type Mem0ActionState = 'idle' | 'submitting' | 'success' | 'error'

type Mem0MemoryWorkbenchProps = {
  userId: string
  appId: string
  runId: string
  category: string
  memoryText: string
  searchQuery: string
  addState: Mem0ActionState
  addError: string | null
  lastAddResult: unknown
  searchState: Mem0ActionState
  searchError: string | null
  lastSearchResult: unknown
  onUserIdChange: (value: string) => void
  onAppIdChange: (value: string) => void
  onRunIdChange: (value: string) => void
  onCategoryChange: (value: string) => void
  onMemoryTextChange: (value: string) => void
  onSearchQueryChange: (value: string) => void
  onAddMemory: () => Promise<void> | void
  onSearchMemory: () => Promise<void> | void
}

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2)
}

export function Mem0MemoryWorkbench({
  userId,
  appId,
  runId,
  category,
  memoryText,
  searchQuery,
  addState,
  addError,
  lastAddResult,
  searchState,
  searchError,
  lastSearchResult,
  onUserIdChange,
  onAppIdChange,
  onRunIdChange,
  onCategoryChange,
  onMemoryTextChange,
  onSearchQueryChange,
  onAddMemory,
  onSearchMemory,
}: Mem0MemoryWorkbenchProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
      <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Add Developer Memory
          </CardTitle>
          <CardDescription>
            Store short developer notes, decisions, blockers, or architecture reminders in Mem0 cloud memory.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <Input value={userId} onChange={(event) => onUserIdChange(event.target.value)} placeholder="user id" />
            <Input value={appId} onChange={(event) => onAppIdChange(event.target.value)} placeholder="app id" />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <Input value={runId} onChange={(event) => onRunIdChange(event.target.value)} placeholder="run id (optional)" />
            <Input value={category} onChange={(event) => onCategoryChange(event.target.value)} placeholder="category" />
          </div>
          <Textarea
            value={memoryText}
            onChange={(event) => onMemoryTextChange(event.target.value)}
            placeholder="Example: Keep Mem0 separate from REEVU and use it only for developer micro-memory."
            rows={5}
          />
          <div className="flex items-center gap-3">
            <Button
              type="button"
              onClick={() => void onAddMemory()}
              disabled={!memoryText.trim() || addState === 'submitting'}
            >
              Add Memory
            </Button>
            <span className="text-sm text-muted-foreground">
              {addState === 'submitting'
                ? 'Submitting...'
                : addState === 'success'
                  ? 'Submitted'
                  : addState === 'error'
                    ? 'Failed'
                    : 'Idle'}
            </span>
          </div>
          {addError && <div className="text-sm text-rose-600 dark:text-rose-300">{addError}</div>}
          {lastAddResult && (
            <pre className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-slate-50/90 p-3 text-xs text-slate-800 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-100">
              {formatJson(lastAddResult)}
            </pre>
          )}
        </CardContent>
      </Card>

      <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Search Developer Memory
          </CardTitle>
          <CardDescription>
            Query scoped developer recall without treating Mem0 as canonical authority.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <Input value={userId} onChange={(event) => onUserIdChange(event.target.value)} placeholder="user id" />
            <Input value={appId} onChange={(event) => onAppIdChange(event.target.value)} placeholder="app id" />
          </div>
          <Input value={runId} onChange={(event) => onRunIdChange(event.target.value)} placeholder="run id (optional)" />
          <Textarea
            value={searchQuery}
            onChange={(event) => onSearchQueryChange(event.target.value)}
            placeholder="Example: How should Mem0 relate to REEVU?"
            rows={4}
          />
          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => void onSearchMemory()}
              disabled={!searchQuery.trim() || searchState === 'submitting'}
            >
              Search Memory
            </Button>
            <span className="text-sm text-muted-foreground">
              {searchState === 'submitting'
                ? 'Searching...'
                : searchState === 'success'
                  ? 'Loaded'
                  : searchState === 'error'
                    ? 'Failed'
                    : 'Idle'}
            </span>
          </div>
          {searchError && <div className="text-sm text-rose-600 dark:text-rose-300">{searchError}</div>}
          {lastSearchResult && (
            <pre className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-slate-50/90 p-3 text-xs text-slate-800 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-100">
              {formatJson(lastSearchResult)}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  )
}