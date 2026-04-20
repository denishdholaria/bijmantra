import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { apiClient } from '@/lib/api-client'
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  GitBranch,
  Loader2,
  Package,
  QrCode,
  Route,
  Search,
  Truck,
} from 'lucide-react'

type TraceabilityLot = Record<string, unknown>
type TraceabilityEvent = Record<string, unknown>
type TraceabilityTransfer = Record<string, unknown>
type TraceabilityQrData = Record<string, unknown>

function getStringValue(record: Record<string, unknown> | null | undefined, key: string) {
  const value = record?.[key]
  return typeof value === 'string' && value.trim().length > 0 ? value : null
}

function getNumberValue(record: Record<string, unknown> | null | undefined, key: string) {
  const value = record?.[key]
  return typeof value === 'number' ? value : null
}

function getBooleanValue(record: Record<string, unknown> | null | undefined, key: string) {
  const value = record?.[key]
  return typeof value === 'boolean' ? value : null
}

function getStringArrayValue(record: Record<string, unknown> | null | undefined, key: string) {
  const value = record?.[key]
  if (!Array.isArray(value)) {
    return []
  }

  return value.filter((entry): entry is string => typeof entry === 'string' && entry.length > 0)
}

function getRecordValue(record: Record<string, unknown> | null | undefined, key: string) {
  const value = record?.[key]
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return 'Not recorded'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString()
}

function formatQuantity(value: unknown) {
  if (typeof value !== 'number') {
    return 'Not recorded'
  }

  return `${value.toLocaleString()} kg`
}

function titleize(value: string | null | undefined) {
  if (!value) {
    return 'Not recorded'
  }

  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

export function TraceabilityTimeline() {
  const [lotNumber, setLotNumber] = useState('')
  const [searching, setSearching] = useState(false)
  const [lookupError, setLookupError] = useState<string | null>(null)
  const [lotDetails, setLotDetails] = useState<TraceabilityLot | null>(null)
  const [history, setHistory] = useState<TraceabilityEvent[]>([])
  const [lineage, setLineage] = useState<TraceabilityLot[]>([])
  const [qrData, setQrData] = useState<TraceabilityQrData | null>(null)
  const [recentTransfers, setRecentTransfers] = useState<TraceabilityTransfer[]>([])
  const [transferState, setTransferState] = useState<'loading' | 'ready' | 'error'>('loading')

  useEffect(() => {
    void (async () => {
      try {
        const response = await apiClient.traceabilityService.getTraceabilityTransfers()
        setRecentTransfers(Array.isArray(response.data) ? response.data : [])
        setTransferState('ready')
      } catch {
        setRecentTransfers([])
        setTransferState('error')
      }
    })()
  }, [])

  const recentTransferSummary = useMemo(() => recentTransfers.slice(0, 8), [recentTransfers])

  const handleLookup = async () => {
    if (!lotNumber.trim()) {
      return
    }

    setSearching(true)
    setLookupError(null)
    setLotDetails(null)
    setHistory([])
    setLineage([])
    setQrData(null)

    try {
      const normalizedLotNumber = lotNumber.trim()
      const [lotResponse, historyResponse, lineageResponse, qrResponse] = await Promise.all([
        apiClient.traceabilityService.getTraceabilityLot(normalizedLotNumber),
        apiClient.traceabilityService.getLotHistory(normalizedLotNumber).catch(() => ({ data: [] })),
        apiClient.traceabilityService.traceLotLineage(normalizedLotNumber).catch(() => ({ data: null })),
        apiClient.traceabilityService.getLotQRData(normalizedLotNumber).catch(() => ({ data: null })),
      ])

      if (lotResponse.status !== 'success' || !lotResponse.data) {
        throw new Error('Lot not found. Check the lot number and try again.')
      }

      setLotDetails(lotResponse.data)
      setHistory(Array.isArray(historyResponse.data) ? historyResponse.data : [])
      setLineage(Array.isArray(lineageResponse.data?.lineage) ? lineageResponse.data.lineage : [])
      setQrData(qrResponse.data && typeof qrResponse.data === 'object' ? qrResponse.data : null)
    } catch (error) {
      setLookupError(error instanceof Error ? error.message : 'Traceability lookup failed.')
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="container mx-auto space-y-6 p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <h1 className="text-2xl font-bold">Traceability</h1>
          <p className="max-w-3xl text-sm text-muted-foreground">
            Use recorded lot details, event history, lineage, QR payloads, and transfers to inspect seed provenance.
            Ledger-style chain verification is not available on this route, so this page only shows backend-confirmed traceability records.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/seed-operations/track">Track Lot</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/seed-operations/lineage">Lineage</Link>
          </Button>
        </div>
      </div>

      <Card className="border-amber-300 bg-amber-50">
        <CardContent className="flex items-start gap-3 pt-6 text-sm text-amber-950">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>
            The previous mock blockchain timeline and simulated integrity check were removed. This surface now stays within the live traceability contract and avoids inventing chain state, validators, or QR payloads.
          </span>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lookup Lot</CardTitle>
          <CardDescription>Search a lot number to load its recorded traceability details.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              placeholder="Enter lot number"
              value={lotNumber}
              onChange={(event) => setLotNumber(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  void handleLookup()
                }
              }}
            />
            <Button onClick={() => void handleLookup()} disabled={searching || lotNumber.trim().length === 0}>
              {searching ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
              {searching ? 'Loading...' : 'Load Traceability'}
            </Button>
          </div>

          {lookupError && (
            <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
              {lookupError}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-4 w-4" />
                Lot Snapshot
              </CardTitle>
              <CardDescription>Current recorded lot state from the traceability service.</CardDescription>
            </CardHeader>
            <CardContent>
              {lotDetails ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="secondary">{getStringValue(lotDetails, 'lot_id') ?? 'Unknown lot'}</Badge>
                    <Badge variant="outline">{getStringValue(lotDetails, 'seed_class') ?? 'Unclassified'}</Badge>
                    <Badge variant="outline">
                      {titleize(getStringValue(lotDetails, 'status') ?? getStringValue(lotDetails, 'current_status'))}
                    </Badge>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Crop</p>
                      <p className="font-medium">{getStringValue(lotDetails, 'crop') ?? 'Not recorded'}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Variety</p>
                      <p className="font-medium">{getStringValue(lotDetails, 'variety_name') ?? 'Not recorded'}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Producer</p>
                      <p className="font-medium">{getStringValue(lotDetails, 'producer_name') ?? 'Not recorded'}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Quantity</p>
                      <p className="font-medium">
                        {formatQuantity(
                          getNumberValue(lotDetails, 'current_quantity_kg') ?? getNumberValue(lotDetails, 'quantity_kg')
                        )}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Production Year</p>
                      <p className="font-medium">
                        {getNumberValue(lotDetails, 'production_year')?.toString() ?? 'Not recorded'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Parent Lot</p>
                      <p className="font-medium">{getStringValue(lotDetails, 'parent_lot_id') ?? 'None'}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Load a lot to see its recorded traceability details.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Route className="h-4 w-4" />
                Event History
              </CardTitle>
              <CardDescription>Recorded lot events ordered by backend timestamps.</CardDescription>
            </CardHeader>
            <CardContent>
              {history.length > 0 ? (
                <ScrollArea className="h-[320px] pr-4">
                  <div className="space-y-3">
                    {history.map((event, index) => (
                      <div
                        key={
                          getStringValue(event, 'id') ??
                          getStringValue(event, 'event_id') ??
                          `${getStringValue(event, 'event_type') ?? 'event'}-${index}`
                        }
                        className="rounded-lg border p-3"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{titleize(getStringValue(event, 'event_type'))}</Badge>
                            {getStringValue(event, 'location') ? (
                              <span className="text-xs text-muted-foreground">{getStringValue(event, 'location')}</span>
                            ) : null}
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {formatDateTime(getStringValue(event, 'timestamp'))}
                          </span>
                        </div>
                        {(getStringValue(event, 'operator_name') || getStringValue(event, 'operator_id')) && (
                          <p className="mt-2 text-sm text-muted-foreground">
                            By {getStringValue(event, 'operator_name') ?? getStringValue(event, 'operator_id')}
                          </p>
                        )}
                        {getRecordValue(event, 'details') &&
                        Object.keys(getRecordValue(event, 'details') ?? {}).length > 0 && (
                          <pre className="mt-2 overflow-x-auto rounded bg-muted p-2 text-xs">
                            {JSON.stringify(getRecordValue(event, 'details'), null, 2)}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <p className="text-sm text-muted-foreground">No recorded events are loaded for the selected lot yet.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-4 w-4" />
                Lineage
              </CardTitle>
              <CardDescription>Parent chain returned by the traceability lineage endpoint.</CardDescription>
            </CardHeader>
            <CardContent>
              {lineage.length > 0 ? (
                <div className="space-y-3">
                  <div className="text-sm text-muted-foreground">{lineage.length} recorded generation entries</div>
                  <Separator />
                  {lineage.map((entry, index) => (
                    <div key={getStringValue(entry, 'lot_id') ?? `${index}`} className="space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{getStringValue(entry, 'lot_id') ?? 'Unknown lot'}</span>
                        <Badge variant={index === 0 ? 'default' : 'outline'}>
                          {index === 0 ? 'Current lot' : `Generation ${index}`}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {getStringValue(entry, 'crop') ?? 'Unknown crop'} · {getStringValue(entry, 'variety_name') ?? 'Unknown variety'}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No lineage chain is loaded for the selected lot yet.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <QrCode className="h-4 w-4" />
                QR Payload
              </CardTitle>
              <CardDescription>Backend-generated traceability payload for labels or verification flows.</CardDescription>
            </CardHeader>
            <CardContent>
              {qrData ? (
                <div className="space-y-3 text-sm">
                  <div className="flex items-center gap-2">
                    {getBooleanValue(qrData, 'certified') ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-amber-600" />
                    )}
                    <span>
                      {getBooleanValue(qrData, 'certified')
                        ? 'Certification present'
                        : 'No valid certification recorded'}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Trace URL</p>
                    <p className="font-mono text-xs">{getStringValue(qrData, 'trace_url') ?? 'Not recorded'}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Certificate Numbers</p>
                    <p>{getStringArrayValue(qrData, 'cert_numbers').length > 0 ? getStringArrayValue(qrData, 'cert_numbers').join(', ') : 'None'}</p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    This route no longer renders a third-party QR image. Use the backend payload above or the linked seed-operations traceability pages for operator workflows.
                  </p>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Load a lot to inspect its recorded QR payload.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Truck className="h-4 w-4" />
                Recent Transfers
              </CardTitle>
              <CardDescription>Latest transfers returned by the shared traceability transfer feed.</CardDescription>
            </CardHeader>
            <CardContent>
              {transferState === 'loading' ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading transfer history...
                </div>
              ) : transferState === 'error' ? (
                <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-950">
                  Transfer history is unavailable right now. This page no longer invents fallback shipment records.
                </div>
              ) : recentTransferSummary.length > 0 ? (
                <div className="space-y-3">
                  {recentTransferSummary.map((transfer, index) => (
                    <div
                      key={
                        getStringValue(transfer, 'transfer_id') ??
                        getStringValue(transfer, 'id') ??
                        `${getStringValue(transfer, 'lot_id') ?? 'transfer'}-${index}`
                      }
                      className="rounded-lg border p-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{getStringValue(transfer, 'lot_id') ?? 'Unknown lot'}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatDateTime(
                            getStringValue(transfer, 'timestamp') ??
                              getStringValue(transfer, 'transfer_date') ??
                              getStringValue(transfer, 'created_at')
                          )}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {getStringValue(transfer, 'from_entity_name') ?? 'Unknown source'}
                        <ArrowRight className="mx-1 inline h-3 w-3" />
                        {getStringValue(transfer, 'to_entity_name') ?? 'Unknown destination'}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline">{titleize(getStringValue(transfer, 'transfer_type'))}</Badge>
                        <span>{formatQuantity(getNumberValue(transfer, 'quantity_kg'))}</span>
                        {getStringValue(transfer, 'variety_name') ? (
                          <span>{getStringValue(transfer, 'variety_name')}</span>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No transfers are currently recorded in the shared traceability feed.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default TraceabilityTimeline
