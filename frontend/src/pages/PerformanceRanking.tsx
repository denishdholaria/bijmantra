import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { useDemoMode } from '@/hooks/useDemoMode'
import {
  Trophy,
  Medal,
  TrendingUp,
  Search,
  Download,
  Star,
  ArrowUp,
  ArrowDown,
  Minus,
  RefreshCw,
  BarChart3
} from 'lucide-react'

interface RankedEntry {
  id: string
  entry_id: string
  name: string
  rank: number
  previous_rank: number
  yield: number
  gebv: number
  traits: string[]
  score: number
  program_name?: string
  trial_name?: string
  generation?: string
}

interface Statistics {
  total_entries: number
  avg_score: number
  avg_yield: number
  avg_gebv: number
  top_performer: string | null
  most_improved: { name: string; improvement: number } | null
}

interface Program {
  id: string
  name: string
}

interface Trial {
  id: string
  name: string
  program_id: string
}

// Demo data
const DEMO_RANKINGS: RankedEntry[] = [
  { id: '1', entry_id: 'BM-2025-045', name: 'Elite Line 45', rank: 1, previous_rank: 2, yield: 7.2, gebv: 2.45, traits: ['High yield', 'Disease resistant'], score: 95 },
  { id: '2', entry_id: 'BM-2025-023', name: 'Elite Line 23', rank: 2, previous_rank: 1, yield: 6.9, gebv: 2.38, traits: ['Drought tolerant'], score: 92 },
  { id: '3', entry_id: 'BM-2025-089', name: 'Elite Line 89', rank: 3, previous_rank: 3, yield: 6.7, gebv: 2.31, traits: ['Quality', 'High yield'], score: 89 },
  { id: '4', entry_id: 'BM-2025-012', name: 'Elite Line 12', rank: 4, previous_rank: 6, yield: 6.5, gebv: 2.28, traits: ['Disease resistant'], score: 86 },
  { id: '5', entry_id: 'BM-2025-067', name: 'Elite Line 67', rank: 5, previous_rank: 4, yield: 6.4, gebv: 2.15, traits: ['Wide adaptation'], score: 84 },
  { id: '6', entry_id: 'BM-2025-034', name: 'Elite Line 34', rank: 6, previous_rank: 5, yield: 6.3, gebv: 2.08, traits: ['Early maturity'], score: 82 },
  { id: '7', entry_id: 'BM-2025-078', name: 'Elite Line 78', rank: 7, previous_rank: 8, yield: 6.2, gebv: 1.95, traits: ['Stress tolerant'], score: 80 },
  { id: '8', entry_id: 'BM-2025-056', name: 'Elite Line 56', rank: 8, previous_rank: 7, yield: 6.1, gebv: 1.82, traits: ['Quality'], score: 78 }
]

export function PerformanceRanking() {
  const { isDemoMode } = useDemoMode()
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('score')
  const [selectedProgram, setSelectedProgram] = useState('')
  const [selectedTrial, setSelectedTrial] = useState('')
  
  const [rankings, setRankings] = useState<RankedEntry[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [programs, setPrograms] = useState<Program[]>([])
  const [trials, setTrials] = useState<Trial[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [sortBy, selectedProgram, selectedTrial, isDemoMode])

  const fetchData = async () => {
    if (isDemoMode) {
      setRankings(DEMO_RANKINGS)
      setStatistics({
        total_entries: DEMO_RANKINGS.length,
        avg_score: 85.8,
        avg_yield: 6.5,
        avg_gebv: 2.18,
        top_performer: 'Elite Line 45',
        most_improved: { name: 'Elite Line 12', improvement: 2 }
      })
      setPrograms([{ id: 'prog-001', name: 'Rice Improvement Program' }])
      setTrials([{ id: 'trial-001', name: 'Advanced Yield Trial 2025', program_id: 'prog-001' }])
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      // Build query params
      const params = new URLSearchParams()
      if (selectedProgram) params.append('program_id', selectedProgram)
      if (selectedTrial) params.append('trial_id', selectedTrial)
      params.append('sort_by', sortBy)
      if (searchQuery) params.append('search', searchQuery)

      // Fetch rankings
      const rankingsRes = await fetch(`/api/v2/performance-ranking/rankings?${params}`)
      if (rankingsRes.ok) {
        const data = await rankingsRes.json()
        setRankings(data.data || [])
      }

      // Fetch statistics
      const statsParams = new URLSearchParams()
      if (selectedProgram) statsParams.append('program_id', selectedProgram)
      if (selectedTrial) statsParams.append('trial_id', selectedTrial)
      
      const statsRes = await fetch(`/api/v2/performance-ranking/statistics?${statsParams}`)
      if (statsRes.ok) {
        const data = await statsRes.json()
        setStatistics(data.data)
      }

      // Fetch programs
      const programsRes = await fetch('/api/v2/performance-ranking/programs')
      if (programsRes.ok) {
        const data = await programsRes.json()
        setPrograms(data.data || [])
      }

      // Fetch trials
      const trialsParams = selectedProgram ? `?program_id=${selectedProgram}` : ''
      const trialsRes = await fetch(`/api/v2/performance-ranking/trials${trialsParams}`)
      if (trialsRes.ok) {
        const data = await trialsRes.json()
        setTrials(data.data || [])
      }
    } catch (error) {
      console.error('Error fetching data:', error)
      setRankings(DEMO_RANKINGS)
      toast.error('Failed to load data, showing demo data')
    } finally {
      setLoading(false)
    }
  }

  const getRankChange = (current: number, previous: number) => {
    if (current < previous) return { icon: <ArrowUp className="h-4 w-4 text-green-500" />, text: `+${previous - current}`, color: 'text-green-500' }
    if (current > previous) return { icon: <ArrowDown className="h-4 w-4 text-red-500" />, text: `-${current - previous}`, color: 'text-red-500' }
    return { icon: <Minus className="h-4 w-4 text-gray-400" />, text: '0', color: 'text-gray-400' }
  }

  const getMedalColor = (rank: number) => {
    if (rank === 1) return 'bg-yellow-100 text-yellow-700 border-yellow-300'
    if (rank === 2) return 'bg-gray-100 text-gray-700 border-gray-300'
    if (rank === 3) return 'bg-orange-100 text-orange-700 border-orange-300'
    return 'bg-muted'
  }

  const filteredRankings = rankings.filter(r =>
    r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.entry_id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const exportRankings = () => {
    const csv = [
      ['Rank', 'Entry ID', 'Name', 'Yield', 'GEBV', 'Score', 'Traits'].join(','),
      ...filteredRankings.map(r => [
        r.rank,
        r.entry_id,
        r.name,
        r.yield,
        r.gebv,
        r.score,
        `"${r.traits.join('; ')}"`
      ].join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `performance-rankings-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Rankings exported to CSV')
  }

  const topThree = filteredRankings.slice(0, 3)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Trophy className="h-8 w-8 text-primary" />
            Performance Ranking
          </h1>
          <p className="text-muted-foreground mt-1">Rank breeding entries by performance metrics</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportRankings}>
            <Download className="h-4 w-4 mr-2" />Export Rankings
          </Button>
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg"><BarChart3 className="h-5 w-5 text-blue-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{statistics.total_entries}</div>
                  <div className="text-sm text-muted-foreground">Total Entries</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg"><TrendingUp className="h-5 w-5 text-green-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{statistics.avg_yield}</div>
                  <div className="text-sm text-muted-foreground">Avg Yield (t/ha)</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg"><Star className="h-5 w-5 text-purple-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{statistics.avg_gebv}</div>
                  <div className="text-sm text-muted-foreground">Avg GEBV</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg"><Trophy className="h-5 w-5 text-yellow-600" /></div>
                <div>
                  <div className="text-lg font-bold truncate">{statistics.top_performer || '-'}</div>
                  <div className="text-sm text-muted-foreground">Top Performer</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-100 rounded-lg"><ArrowUp className="h-5 w-5 text-emerald-600" /></div>
                <div>
                  <div className="text-lg font-bold truncate">
                    {statistics.most_improved ? `${statistics.most_improved.name} (+${statistics.most_improved.improvement})` : '-'}
                  </div>
                  <div className="text-sm text-muted-foreground">Most Improved</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Top 3 Podium */}
      {loading ? (
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      ) : topThree.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          {topThree.map((entry, i) => (
            <Card key={entry.id} className={i === 0 ? 'ring-2 ring-yellow-400' : ''}>
              <CardContent className="p-6 text-center">
                <div className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-4 ${getMedalColor(entry.rank)}`}>
                  {entry.rank === 1 ? <Trophy className="h-8 w-8" /> : <Medal className="h-8 w-8" />}
                </div>
                <div className="text-3xl font-bold mb-1">#{entry.rank}</div>
                <h3 className="font-semibold">{entry.name}</h3>
                <p className="text-sm text-muted-foreground">{entry.entry_id}</p>
                <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                  <div className="p-2 bg-muted rounded">
                    <div className="text-muted-foreground">Yield</div>
                    <div className="font-bold">{entry.yield} t/ha</div>
                  </div>
                  <div className="p-2 bg-muted rounded">
                    <div className="text-muted-foreground">Score</div>
                    <div className="font-bold">{entry.score}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search entries..." 
                value={searchQuery} 
                onChange={(e) => setSearchQuery(e.target.value)} 
                className="pl-10" 
              />
            </div>
            <Select value={selectedProgram} onValueChange={setSelectedProgram}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="All Programs" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Programs</SelectItem>
                {programs.map(p => (
                  <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={selectedTrial} onValueChange={setSelectedTrial}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="All Trials" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Trials</SelectItem>
                {trials.map(t => (
                  <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-[150px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="score">Overall Score</SelectItem>
                <SelectItem value="yield">Yield</SelectItem>
                <SelectItem value="gebv">GEBV</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Full Rankings */}
      <Card>
        <CardHeader>
          <CardTitle>Complete Rankings</CardTitle>
          <CardDescription>All entries ranked by {sortBy === 'score' ? 'overall score' : sortBy}</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map(i => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : (
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {filteredRankings.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No entries found matching your criteria
                  </div>
                ) : (
                  filteredRankings.map((entry) => {
                    const change = getRankChange(entry.rank, entry.previous_rank)
                    return (
                      <div key={entry.id} className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${getMedalColor(entry.rank)}`}>
                          {entry.rank}
                        </div>
                        <div className="flex items-center gap-2 w-16">
                          {change.icon}
                          <span className={`text-sm ${change.color}`}>{change.text}</span>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold">{entry.name}</h4>
                            <Badge variant="outline">{entry.entry_id}</Badge>
                            {entry.generation && (
                              <Badge variant="secondary" className="text-xs">{entry.generation}</Badge>
                            )}
                          </div>
                          <div className="flex gap-1 mt-1">
                            {entry.traits.map((trait, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">{trait}</Badge>
                            ))}
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-center">
                          <div>
                            <div className="text-sm text-muted-foreground">Yield</div>
                            <div className="font-bold">{entry.yield}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">GEBV</div>
                            <div className="font-bold text-green-600">+{entry.gebv}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">Score</div>
                            <div className="font-bold text-primary">{entry.score}</div>
                          </div>
                        </div>
                        <Button variant="ghost" size="icon"><Star className="h-4 w-4" /></Button>
                      </div>
                    )
                  })
                )}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
