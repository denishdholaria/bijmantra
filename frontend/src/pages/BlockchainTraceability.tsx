import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { 
  Link2, Shield, Search, QrCode, CheckCircle, 
  Clock, FileText, ArrowRight, ExternalLink
} from 'lucide-react'

interface TraceRecord {
  id: string
  txHash: string
  event: string
  timestamp: string
  actor: string
  data: string
  verified: boolean
}

interface SeedLotTrace {
  lotId: string
  variety: string
  origin: string
  currentHolder: string
  status: 'verified' | 'pending'
  events: TraceRecord[]
}

export function BlockchainTraceability() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLot, setSelectedLot] = useState<SeedLotTrace | null>(null)

  const traceLots: SeedLotTrace[] = [
    { lotId: 'SL-2025-001', variety: 'BIJ-R-001', origin: 'Station A', currentHolder: 'AgriCorp Seeds', status: 'verified', events: [
      { id: '1', txHash: '0x1a2b...3c4d', event: 'Seed Lot Created', timestamp: '2025-06-15 10:30', actor: 'Station A', data: 'Initial lot: 5000 seeds', verified: true },
      { id: '2', txHash: '0x2b3c...4d5e', event: 'Quality Certified', timestamp: '2025-06-20 14:15', actor: 'Seed Lab', data: 'Germination: 95%, Purity: 99%', verified: true },
      { id: '3', txHash: '0x3c4d...5e6f', event: 'Ownership Transfer', timestamp: '2025-07-01 09:00', actor: 'Station A → AgriCorp', data: 'Transfer of 3000 seeds', verified: true },
    ]},
    { lotId: 'SL-2025-002', variety: 'BIJ-W-003', origin: 'Station B', currentHolder: 'Farmers Coop', status: 'verified', events: [] },
    { lotId: 'SL-2025-003', variety: 'BIJ-R-015', origin: 'Station A', currentHolder: 'Pending Verification', status: 'pending', events: [] },
  ]

  const stats = { totalLots: traceLots.length, verified: traceLots.filter(l => l.status === 'verified').length, transactions: traceLots.reduce((s, l) => s + l.events.length, 0) }

  const filteredLots = traceLots.filter(l => l.lotId.toLowerCase().includes(searchQuery.toLowerCase()) || l.variety.toLowerCase().includes(searchQuery.toLowerCase()))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Blockchain Traceability</h1>
          <p className="text-muted-foreground">Track seed provenance on the blockchain</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><QrCode className="mr-2 h-4 w-4" />Scan QR</Button>
          <Button><Link2 className="mr-2 h-4 w-4" />Register Lot</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Link2 className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{stats.totalLots}</p><p className="text-xs text-muted-foreground">Tracked Lots</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Shield className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{stats.verified}</p><p className="text-xs text-muted-foreground">Verified</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><FileText className="h-8 w-8 text-purple-500" /><div><p className="text-2xl font-bold">{stats.transactions}</p><p className="text-xs text-muted-foreground">Transactions</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><CheckCircle className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">100%</p><p className="text-xs text-muted-foreground">Integrity</p></div></div></CardContent></Card>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search by lot ID or variety..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Seed Lots</CardTitle><CardDescription>Select a lot to view trace history</CardDescription></CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {filteredLots.map((lot) => (
                <div key={lot.lotId} className={`p-4 cursor-pointer hover:bg-accent ${selectedLot?.lotId === lot.lotId ? 'bg-accent' : ''}`} onClick={() => setSelectedLot(lot)}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{lot.lotId}</p>
                      <p className="text-sm text-muted-foreground">{lot.variety} • {lot.origin}</p>
                    </div>
                    <Badge className={lot.status === 'verified' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>{lot.status}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Current: {lot.currentHolder}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Trace History</CardTitle><CardDescription>{selectedLot ? `${selectedLot.lotId} - ${selectedLot.variety}` : 'Select a lot'}</CardDescription></CardHeader>
          <CardContent>
            {selectedLot ? (
              selectedLot.events.length > 0 ? (
                <div className="space-y-4">
                  {selectedLot.events.map((event, idx) => (
                    <div key={event.id} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center ${event.verified ? 'bg-green-100' : 'bg-gray-100'}`}>
                          {event.verified ? <CheckCircle className="h-4 w-4 text-green-600" /> : <Clock className="h-4 w-4 text-gray-400" />}
                        </div>
                        {idx < selectedLot.events.length - 1 && <div className="w-0.5 h-full bg-gray-200 my-1" />}
                      </div>
                      <div className="flex-1 pb-4">
                        <p className="font-medium">{event.event}</p>
                        <p className="text-sm text-muted-foreground">{event.data}</p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                          <span>{event.timestamp}</span>
                          <span>•</span>
                          <span>{event.actor}</span>
                        </div>
                        <code className="text-xs text-blue-600 flex items-center gap-1 mt-1">{event.txHash}<ExternalLink className="h-3 w-3" /></code>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">No events recorded yet</p>
              )
            ) : (
              <p className="text-center text-muted-foreground py-8">Select a seed lot to view its blockchain trace</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
