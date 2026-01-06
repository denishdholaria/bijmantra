/**
 * Performance Ranking Page
 * 
 * Rank breeding entries by performance metrics.
 * Connects to /api/v2/performance-ranking endpoints.
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import {
  Trophy, Medal, TrendingUp, Search, Download, Star,
  ArrowUp, ArrowDown, Minus, RefreshCw, BarChart3
} from 'lucide-react'
import { performanceRankingAPI, RankedEntry, RankingStatistics } from '@/lib/api-client'

export function PerformanceRanking() {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('score')
  const [selectedProgram, setSelectedProgram] = useState('')
  const [selectedTrial, setSelectedTrial] = useState('')

  const { data: rankingsData, isLoading: isLoadingRankings, refetch } = useQuery({
    queryKey: ['performance-rankings', sortBy, selectedProgram, selectedTrial, searchQuery],
    queryFn: () => performanceRankingAPI.getRankings({
      program_id: selectedProgram || undefined,
      trial_id: selectedTrial || undefined,
      sort_by: sortBy,
      search: searchQuery || undefined,
    }),
  })

  const { data: statsData, isLoading: isLoadingStats } = useQuery({
    queryKey: ['performance-statistics', selectedProgram, selectedTrial],
    queryFn: () => performanceRankingAPI.getStatistics({
      program_id: selectedProgram || undefined,
      trial_id: selectedTrial || undefined,
    }),
  })

  const { data: programsData } = useQuery({
    queryKey: ['performance-programs'],
    queryFn: () => performanceRankingAPI.getPrograms(),
  })

  const { data: trialsData } = useQuery({
    queryKey: ['performance-trials', selectedProgram],
    queryFn: () => performanceRankingAPI.getTrials(selectedProgram || undefined),
  })

  const rankings: RankedEntry[] = rankingsData?.data || []
  const statistics: RankingStatistics | null = statsData?.data || null
  const programs = programsData?.data || []
  const trials = trialsData?.data || []

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

  const exportRankings = () => {
    const csv = [
      ['Rank', 'Entry ID', 'Name', 'Yield', 'GEBV', 'Score', 'Traits'].join(','),
      ...rankings.map(r => [r.rank, r.entry_id, r.name, r.yield, r.gebv, r.score, `"${r.traits.join('; ')}"`].join(','))
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

  const topThree = rankings.slice(0, 3)
  const isLoading = isLoadingRankings || isLoadingStats

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
          <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />Refresh
          </Button>
          <Button variant="outline" onClick={exportRankings}>
            <Download className="h-4 w-4 mr-2" />Export
          </Button>
        </div>
      </div>

      {isLoadingStats ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-24" />)}</div>
      ) : statistics && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-blue-100 rounded-lg"><BarChart3 className="h-5 w-5 text-blue-600" /></div><div><div className="text-2xl font-bold">{statistics.total_entries}</div><div className="text-sm text-muted-foreground">Total Entries</div></div></div></CardContent></Card>
          <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-green-100 rounded-lg"><TrendingUp className="h-5 w-5 text-green-600" /></div><div><div className="text-2xl font-bold">{statistics.avg_yield?.toFixed(1) || '-'}</div><div className="text-sm text-muted-foreground">Avg Yield</div></div></div></CardContent></Card>
          <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-purple-100 rounded-lg"><Star className="h-5 w-5 text-purple-600" /></div><div><div className="text-2xl font-bold">{statistics.avg_gebv?.toFixed(2) || '-'}</div><div className="text-sm text-muted-foreground">Avg GEBV</div></div></div></CardContent></Card>
          <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-yellow-100 rounded-lg"><Trophy className="h-5 w-5 text-yellow-600" /></div><div><div className="text-lg font-bold truncate">{statistics.top_performer || '-'}</div><div className="text-sm text-muted-foreground">Top Performer</div></div></div></CardContent></Card>
          <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-emerald-100 rounded-lg"><ArrowUp className="h-5 w-5 text-emerald-600" /></div><div><div className="text-lg font-bold truncate">{statistics.most_improved ? `${statistics.most_improved.name} (+${statistics.most_improved.improvement})` : '-'}</div><div className="text-sm text-muted-foreground">Most Improved</div></div></div></CardContent></Card>
        </div>
      )}

      {isLoadingRankings ? (
        <div className="grid grid-cols-3 gap-4">{[1,2,3].map(i => <Skeleton key={i} className="h-48" />)}</div>
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
                  <div className="p-2 bg-muted rounded"><div className="text-muted-foreground">Yield</div><div className="font-bold">{entry.yield} t/ha</div></div>
                  <div className="p-2 bg-muted rounded"><div className="text-muted-foreground">Score</div><div className="font-bold">{entry.score}</div></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search entries..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
            </div>
            <Select value={selectedProgram || '__all__'} onValueChange={(v) => setSelectedProgram(v === '__all__' ? '' : v)}>
              <SelectTrigger className="w-[200px]"><SelectValue placeholder="All Programs" /></SelectTrigger>
              <SelectContent><SelectItem value="__all__">All Programs</SelectItem>{programs.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
            </Select>
            <Select value={selectedTrial || '__all__'} onValueChange={(v) => setSelectedTrial(v === '__all__' ? '' : v)}>
              <SelectTrigger className="w-[200px]"><SelectValue placeholder="All Trials" /></SelectTrigger>
              <SelectContent><SelectItem value="__all__">All Trials</SelectItem>{trials.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="score">Overall Score</SelectItem><SelectItem value="yield">Yield</SelectItem><SelectItem value="gebv">GEBV</SelectItem></SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Complete Rankings</CardTitle><CardDescription>All entries ranked by {sortBy === 'score' ? 'overall score' : sortBy}</CardDescription></CardHeader>
        <CardContent>
          {isLoadingRankings ? (
            <div className="space-y-2">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-20 w-full" />)}</div>
          ) : (
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {rankings.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">No entries found</div>
                ) : rankings.map((entry) => {
                  const change = getRankChange(entry.rank, entry.previous_rank)
                  return (
                    <div key={entry.id} className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${getMedalColor(entry.rank)}`}>{entry.rank}</div>
                      <div className="flex items-center gap-2 w-16">{change.icon}<span className={`text-sm ${change.color}`}>{change.text}</span></div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2"><h4 className="font-semibold">{entry.name}</h4><Badge variant="outline">{entry.entry_id}</Badge>{entry.generation && <Badge variant="secondary" className="text-xs">{entry.generation}</Badge>}</div>
                        <div className="flex gap-1 mt-1">{entry.traits.map((trait, i) => <Badge key={i} variant="secondary" className="text-xs">{trait}</Badge>)}</div>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div><div className="text-sm text-muted-foreground">Yield</div><div className="font-bold">{entry.yield}</div></div>
                        <div><div className="text-sm text-muted-foreground">GEBV</div><div className="font-bold text-green-600">+{entry.gebv}</div></div>
                        <div><div className="text-sm text-muted-foreground">Score</div><div className="font-bold text-primary">{entry.score}</div></div>
                      </div>
                      <Button variant="ghost" size="icon"><Star className="h-4 w-4" /></Button>
                    </div>
                  )
                })}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default PerformanceRanking
