/**
 * Progeny Page - BrAPI Germplasm Module
 * View and manage offspring of germplasm entries
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'
import { useDemoMode } from '@/hooks/useDemoMode'
import { RefreshCw, Download, Users, Sprout, TrendingUp, Award } from 'lucide-react'

interface ProgenyItem {
  germplasm_id: string
  germplasm_name: string
  parent_type: string
  generation?: string
  cross_year?: number
}

interface ProgenyEntry {
  id: string
  germplasm_id: string
  germplasm_name: string
  parent_type: 'FEMALE' | 'MALE' | 'SELF' | 'POPULATION'
  species?: string
  generation?: string
  progeny: ProgenyItem[]
}

interface Statistics {
  total_parents: number
  total_progeny: number
  avg_offspring: number
  max_offspring: number
  max_offspring_parent: string | null
  by_parent_type: Record<string, number>
  by_species: Record<string, number>
}

// Demo data
const DEMO_PROGENY: ProgenyEntry[] = [
  {
    id: 'parent-001',
    germplasm_id: 'g001',
    germplasm_name: 'IR64',
    parent_type: 'FEMALE',
    species: 'Oryza sativa',
    progeny: [
      { germplasm_id: 'g010', germplasm_name: 'IR64-NIL-1', parent_type: 'FEMALE', generation: 'F1', cross_year: 2022 },
      { germplasm_id: 'g011', germplasm_name: 'IR64-NIL-2', parent_type: 'FEMALE', generation: 'F1', cross_year: 2022 },
      { germplasm_id: 'g012', germplasm_name: 'IR64 × Azucena F1', parent_type: 'FEMALE', generation: 'F1', cross_year: 2023 },
    ],
  },
  {
    id: 'parent-002',
    germplasm_id: 'g002',
    germplasm_name: 'Nipponbare',
    parent_type: 'MALE',
    species: 'Oryza sativa',
    progeny: [
      { germplasm_id: 'g013', germplasm_name: 'Nip × Kas RIL-1', parent_type: 'MALE', generation: 'RIL', cross_year: 2018 },
      { germplasm_id: 'g014', germplasm_name: 'Nip × Kas RIL-2', parent_type: 'MALE', generation: 'RIL', cross_year: 2018 },
    ],
  },
  {
    id: 'parent-003',
    germplasm_id: 'g003',
    germplasm_name: 'Kasalath',
    parent_type: 'FEMALE',
    species: 'Oryza sativa',
    progeny: [
      { germplasm_id: 'g015', germplasm_name: 'Kas-Derived-1', parent_type: 'FEMALE', generation: 'F6', cross_year: 2019 },
      { germplasm_id: 'g016', germplasm_name: 'Kas-Derived-2', parent_type: 'FEMALE', generation: 'F6', cross_year: 2019 },
      { germplasm_id: 'g017', germplasm_name: 'Kas-Derived-3', parent_type: 'FEMALE', generation: 'F5', cross_year: 2020 },
      { germplasm_id: 'g018', germplasm_name: 'Kas-Derived-4', parent_type: 'FEMALE', generation: 'F5', cross_year: 2020 },
    ],
  },
]

export function Progeny() {
  const { isDemoMode } = useDemoMode()
  const [search, setSearch] = useState('')
  const [selectedParent, setSelectedParent] = useState<string>('all')
  const [parentTypeFilter, setParentTypeFilter] = useState<string>('all')
  
  const [progenyData, setProgenyData] = useState<ProgenyEntry[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [isDemoMode])

  const fetchData = async () => {
    if (isDemoMode) {
      setProgenyData(DEMO_PROGENY)
      const totalProgeny = DEMO_PROGENY.reduce((sum, p) => sum + p.progeny.length, 0)
      setStatistics({
        total_parents: DEMO_PROGENY.length,
        total_progeny: totalProgeny,
        avg_offspring: totalProgeny / DEMO_PROGENY.length,
        max_offspring: Math.max(...DEMO_PROGENY.map(p => p.progeny.length)),
        max_offspring_parent: 'Kasalath',
        by_parent_type: { FEMALE: 2, MALE: 1 },
        by_species: { 'Oryza sativa': 3 }
      })
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      // Fetch parents with progeny
      const params = new URLSearchParams()
      if (search) params.append('search', search)
      if (parentTypeFilter !== 'all') params.append('parent_type', parentTypeFilter)

      const parentsRes = await fetch(`/api/v2/progeny/parents?${params}`)
      if (parentsRes.ok) {
        const data = await parentsRes.json()
        setProgenyData(data.data || [])
      }

      // Fetch statistics
      const statsRes = await fetch('/api/v2/progeny/statistics')
      if (statsRes.ok) {
        const data = await statsRes.json()
        setStatistics(data.data)
      }
    } catch (error) {
      console.error('Error fetching data:', error)
      setProgenyData(DEMO_PROGENY)
      toast.error('Failed to load data, showing demo data')
    } finally {
      setLoading(false)
    }
  }

  const getParentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      FEMALE: 'bg-pink-100 text-pink-800',
      MALE: 'bg-blue-100 text-blue-800',
      SELF: 'bg-purple-100 text-purple-800',
      POPULATION: 'bg-green-100 text-green-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const getParentIcon = (type: string) => {
    const icons: Record<string, string> = {
      FEMALE: '♀',
      MALE: '♂',
      SELF: '⟳',
      POPULATION: '👥',
    }
    return icons[type] || '•'
  }

  const filteredData = progenyData.filter(p => {
    const matchesSearch = !search || 
      p.germplasm_name.toLowerCase().includes(search.toLowerCase()) ||
      p.progeny.some(pr => pr.germplasm_name.toLowerCase().includes(search.toLowerCase()))
    const matchesParent = selectedParent === 'all' || p.id === selectedParent
    const matchesType = parentTypeFilter === 'all' || p.parent_type === parentTypeFilter
    return matchesSearch && matchesParent && matchesType
  })

  const exportProgeny = () => {
    const rows = []
    rows.push(['Parent', 'Parent Type', 'Progeny', 'Generation', 'Cross Year'].join(','))
    
    for (const parent of filteredData) {
      for (const prog of parent.progeny) {
        rows.push([
          parent.germplasm_name,
          parent.parent_type,
          prog.germplasm_name,
          prog.generation || '',
          prog.cross_year || ''
        ].join(','))
      }
    }

    const csv = rows.join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `progeny-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Progeny data exported to CSV')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Sprout className="h-8 w-8 text-primary" />
            Progeny
          </h1>
          <p className="text-muted-foreground mt-1">Offspring and descendants of germplasm</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportProgeny}>
            <Download className="h-4 w-4 mr-2" />Export
          </Button>
          <Button variant="outline" asChild>
            <Link to="/germplasm">🌱 View All Germplasm</Link>
          </Button>
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg"><Users className="h-5 w-5 text-blue-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{statistics.total_parents}</div>
                  <div className="text-sm text-muted-foreground">Parents</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg"><Sprout className="h-5 w-5 text-green-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{statistics.total_progeny}</div>
                  <div className="text-sm text-muted-foreground">Total Progeny</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg"><TrendingUp className="h-5 w-5 text-purple-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{statistics.avg_offspring.toFixed(1)}</div>
                  <div className="text-sm text-muted-foreground">Avg Offspring</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg"><Award className="h-5 w-5 text-yellow-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{statistics.max_offspring}</div>
                  <div className="text-sm text-muted-foreground">Max Offspring</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search parents or progeny..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={selectedParent} onValueChange={setSelectedParent}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select parent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Parents</SelectItem>
                {progenyData.map(p => (
                  <SelectItem key={p.id} value={p.id}>{p.germplasm_name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={parentTypeFilter} onValueChange={setParentTypeFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Parent type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="FEMALE">♀ Female</SelectItem>
                <SelectItem value="MALE">♂ Male</SelectItem>
                <SelectItem value="SELF">⟳ Self</SelectItem>
                <SelectItem value="POPULATION">👥 Population</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Progeny List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-48 w-full" />)}
        </div>
      ) : filteredData.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No progeny data found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredData.map((parent) => (
            <Card key={parent.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center text-2xl">
                      🌱
                    </div>
                    <div>
                      <CardTitle className="text-lg">
                        <Link to={`/germplasm/${parent.germplasm_id}`} className="hover:text-primary">
                          {parent.germplasm_name}
                        </Link>
                      </CardTitle>
                      <CardDescription>
                        {parent.progeny.length} offspring recorded
                        {parent.species && ` • ${parent.species}`}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge className={getParentTypeColor(parent.parent_type)}>
                    {getParentIcon(parent.parent_type)} {parent.parent_type}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {parent.progeny.map((offspring) => (
                    <Link
                      key={offspring.germplasm_id}
                      to={`/germplasm/${offspring.germplasm_id}`}
                      className="p-3 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">🌿</span>
                        <div>
                          <p className="font-medium text-sm">{offspring.germplasm_name}</p>
                          <p className="text-xs text-muted-foreground">
                            {offspring.generation && `${offspring.generation} • `}
                            {offspring.cross_year && `${offspring.cross_year}`}
                          </p>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
                
                {/* Visual tree representation */}
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-muted-foreground mb-2">Lineage Tree</p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="px-3 py-1 bg-green-100 rounded-full text-sm font-medium">
                      {parent.germplasm_name}
                    </div>
                    <span className="text-gray-400">→</span>
                    <div className="flex flex-wrap gap-1">
                      {parent.progeny.slice(0, 5).map((p, i) => (
                        <span key={i} className="px-2 py-0.5 bg-blue-50 rounded text-xs">
                          {p.germplasm_name}
                        </span>
                      ))}
                      {parent.progeny.length > 5 && (
                        <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                          +{parent.progeny.length - 5} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
