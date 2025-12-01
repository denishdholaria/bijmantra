/**
 * Progeny Page - BrAPI Germplasm Module
 * View and manage offspring of germplasm entries
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface ProgenyEntry {
  germplasmDbId: string
  germplasmName: string
  parentType: 'FEMALE' | 'MALE' | 'SELF' | 'POPULATION'
  progeny: Array<{
    germplasmDbId: string
    germplasmName: string
    parentType: string
  }>
}

const mockProgenyData: ProgenyEntry[] = [
  {
    germplasmDbId: 'g001',
    germplasmName: 'IR64',
    parentType: 'FEMALE',
    progeny: [
      { germplasmDbId: 'g010', germplasmName: 'IR64-NIL-1', parentType: 'FEMALE' },
      { germplasmDbId: 'g011', germplasmName: 'IR64-NIL-2', parentType: 'FEMALE' },
      { germplasmDbId: 'g012', germplasmName: 'IR64 × Azucena F1', parentType: 'FEMALE' },
    ],
  },
  {
    germplasmDbId: 'g002',
    germplasmName: 'Nipponbare',
    parentType: 'MALE',
    progeny: [
      { germplasmDbId: 'g013', germplasmName: 'Nip × Kas RIL-1', parentType: 'MALE' },
      { germplasmDbId: 'g014', germplasmName: 'Nip × Kas RIL-2', parentType: 'MALE' },
    ],
  },
  {
    germplasmDbId: 'g003',
    germplasmName: 'Kasalath',
    parentType: 'FEMALE',
    progeny: [
      { germplasmDbId: 'g015', germplasmName: 'Kas-Derived-1', parentType: 'FEMALE' },
      { germplasmDbId: 'g016', germplasmName: 'Kas-Derived-2', parentType: 'FEMALE' },
      { germplasmDbId: 'g017', germplasmName: 'Kas-Derived-3', parentType: 'FEMALE' },
      { germplasmDbId: 'g018', germplasmName: 'Kas-Derived-4', parentType: 'FEMALE' },
    ],
  },
]

export function Progeny() {
  const [search, setSearch] = useState('')
  const [selectedParent, setSelectedParent] = useState<string>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['progeny', search, selectedParent],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockProgenyData
      if (search) {
        filtered = filtered.filter(p => 
          p.germplasmName.toLowerCase().includes(search.toLowerCase()) ||
          p.progeny.some(pr => pr.germplasmName.toLowerCase().includes(search.toLowerCase()))
        )
      }
      if (selectedParent !== 'all') {
        filtered = filtered.filter(p => p.germplasmDbId === selectedParent)
      }
      return filtered
    },
  })

  const progenyData = data || []
  const totalProgeny = mockProgenyData.reduce((sum, p) => sum + p.progeny.length, 0)

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

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Progeny</h1>
          <p className="text-muted-foreground mt-1">Offspring and descendants of germplasm</p>
        </div>
        <Button variant="outline" asChild>
          <Link to="/germplasm">🌱 View All Germplasm</Link>
        </Button>
      </div>

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
                {mockProgenyData.map(p => (
                  <SelectItem key={p.germplasmDbId} value={p.germplasmDbId}>{p.germplasmName}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockProgenyData.length}</div>
            <p className="text-sm text-muted-foreground">Parents</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{totalProgeny}</div>
            <p className="text-sm text-muted-foreground">Total Progeny</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{(totalProgeny / mockProgenyData.length).toFixed(1)}</div>
            <p className="text-sm text-muted-foreground">Avg Offspring</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{Math.max(...mockProgenyData.map(p => p.progeny.length))}</div>
            <p className="text-sm text-muted-foreground">Max Offspring</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-48 w-full" />)}
        </div>
      ) : progenyData.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No progeny data found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {progenyData.map((parent) => (
            <Card key={parent.germplasmDbId}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center text-2xl">
                      🌱
                    </div>
                    <div>
                      <CardTitle className="text-lg">
                        <Link to={`/germplasm/${parent.germplasmDbId}`} className="hover:text-primary">
                          {parent.germplasmName}
                        </Link>
                      </CardTitle>
                      <CardDescription>
                        {parent.progeny.length} offspring recorded
                      </CardDescription>
                    </div>
                  </div>
                  <Badge className={getParentTypeColor(parent.parentType)}>
                    {getParentIcon(parent.parentType)} {parent.parentType}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {parent.progeny.map((offspring) => (
                    <Link
                      key={offspring.germplasmDbId}
                      to={`/germplasm/${offspring.germplasmDbId}`}
                      className="p-3 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">🌿</span>
                        <div>
                          <p className="font-medium text-sm">{offspring.germplasmName}</p>
                          <p className="text-xs text-muted-foreground">
                            {getParentIcon(offspring.parentType)} from {offspring.parentType.toLowerCase()}
                          </p>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
                
                {/* Visual tree representation */}
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-muted-foreground mb-2">Lineage Tree</p>
                  <div className="flex items-center gap-2">
                    <div className="px-3 py-1 bg-green-100 rounded-full text-sm font-medium">
                      {parent.germplasmName}
                    </div>
                    <span className="text-gray-400">→</span>
                    <div className="flex flex-wrap gap-1">
                      {parent.progeny.slice(0, 5).map((p, i) => (
                        <span key={i} className="px-2 py-0.5 bg-blue-50 rounded text-xs">
                          {p.germplasmName}
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
