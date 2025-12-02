import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Trophy,
  Medal,
  TrendingUp,
  TrendingDown,
  Search,
  Filter,
  Download,
  Star,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react'

interface RankedEntry {
  rank: number
  previousRank: number
  id: string
  name: string
  yield: number
  gebv: number
  traits: string[]
  score: number
}

export function PerformanceRanking() {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('score')

  const rankings: RankedEntry[] = [
    { rank: 1, previousRank: 2, id: 'BM-2025-045', name: 'Elite Line 45', yield: 7.2, gebv: 2.45, traits: ['High yield', 'Disease resistant'], score: 95 },
    { rank: 2, previousRank: 1, id: 'BM-2025-023', name: 'Elite Line 23', yield: 6.9, gebv: 2.38, traits: ['Drought tolerant'], score: 92 },
    { rank: 3, previousRank: 3, id: 'BM-2025-089', name: 'Elite Line 89', yield: 6.7, gebv: 2.31, traits: ['Quality', 'High yield'], score: 89 },
    { rank: 4, previousRank: 6, id: 'BM-2025-012', name: 'Elite Line 12', yield: 6.5, gebv: 2.28, traits: ['Disease resistant'], score: 86 },
    { rank: 5, previousRank: 4, id: 'BM-2025-067', name: 'Elite Line 67', yield: 6.4, gebv: 2.15, traits: ['Wide adaptation'], score: 84 },
    { rank: 6, previousRank: 5, id: 'BM-2025-034', name: 'Elite Line 34', yield: 6.3, gebv: 2.08, traits: ['Early maturity'], score: 82 },
    { rank: 7, previousRank: 8, id: 'BM-2025-078', name: 'Elite Line 78', yield: 6.2, gebv: 1.95, traits: ['Stress tolerant'], score: 80 },
    { rank: 8, previousRank: 7, id: 'BM-2025-056', name: 'Elite Line 56', yield: 6.1, gebv: 1.82, traits: ['Quality'], score: 78 }
  ]

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
    r.id.toLowerCase().includes(searchQuery.toLowerCase())
  )

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
        <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Rankings</Button>
      </div>

      {/* Top 3 Podium */}
      <div className="grid grid-cols-3 gap-4">
        {rankings.slice(0, 3).map((entry, i) => (
          <Card key={entry.id} className={i === 0 ? 'ring-2 ring-yellow-400' : ''}>
            <CardContent className="p-6 text-center">
              <div className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-4 ${getMedalColor(entry.rank)}`}>
                {entry.rank === 1 ? <Trophy className="h-8 w-8" /> : <Medal className="h-8 w-8" />}
              </div>
              <div className="text-3xl font-bold mb-1">#{entry.rank}</div>
              <h3 className="font-semibold">{entry.name}</h3>
              <p className="text-sm text-muted-foreground">{entry.id}</p>
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

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search entries..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
            </div>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
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
          <CardDescription>All entries ranked by performance</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            <div className="space-y-2">
              {filteredRankings.map((entry) => {
                const change = getRankChange(entry.rank, entry.previousRank)
                return (
                  <div key={entry.id} className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${getMedalColor(entry.rank)}`}>
                      {entry.rank}
                    </div>
                    <div className="flex items-center gap-2">
                      {change.icon}
                      <span className={`text-sm ${change.color}`}>{change.text}</span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold">{entry.name}</h4>
                        <Badge variant="outline">{entry.id}</Badge>
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
              })}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
