/**
 * Germplasm Collection Page
 * Manage germplasm collections and accessions
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'

interface Collection {
  id: string
  name: string
  description: string
  type: 'core' | 'working' | 'active' | 'base' | 'breeding'
  accessionCount: number
  species: string[]
  curator: string
  lastUpdated: string
}

const sampleCollections: Collection[] = [
  { id: 'COL001', name: 'Core Collection 2024', description: 'Representative diversity set', type: 'core', accessionCount: 250, species: ['Wheat', 'Barley'], curator: 'Dr. Smith', lastUpdated: '2024-11-15' },
  { id: 'COL002', name: 'Working Collection', description: 'Active breeding materials', type: 'working', accessionCount: 1500, species: ['Wheat'], curator: 'Dr. Johnson', lastUpdated: '2024-11-28' },
  { id: 'COL003', name: 'Elite Lines 2024', description: 'Advanced breeding lines', type: 'breeding', accessionCount: 85, species: ['Wheat'], curator: 'Dr. Williams', lastUpdated: '2024-11-20' },
  { id: 'COL004', name: 'Base Collection', description: 'Long-term conservation', type: 'base', accessionCount: 5000, species: ['Wheat', 'Barley', 'Oat'], curator: 'Dr. Brown', lastUpdated: '2024-06-01' },
  { id: 'COL005', name: 'Active Collection', description: 'Medium-term storage', type: 'active', accessionCount: 3200, species: ['Wheat', 'Barley'], curator: 'Dr. Davis', lastUpdated: '2024-10-15' },
]

export function GermplasmCollection() {
  const [collections] = useState<Collection[]>(sampleCollections)
  const [search, setSearch] = useState('')

  const filteredCollections = collections.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.description.toLowerCase().includes(search.toLowerCase())
  )

  const totalAccessions = collections.reduce((sum, c) => sum + c.accessionCount, 0)

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'core': return 'bg-purple-100 text-purple-700'
      case 'working': return 'bg-blue-100 text-blue-700'
      case 'active': return 'bg-green-100 text-green-700'
      case 'base': return 'bg-orange-100 text-orange-700'
      case 'breeding': return 'bg-pink-100 text-pink-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Germplasm Collections</h1>
          <p className="text-muted-foreground mt-1">Manage germplasm collections</p>
        </div>
        <Button>➕ New Collection</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{collections.length}</p><p className="text-xs text-muted-foreground">Collections</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-green-600">{totalAccessions.toLocaleString()}</p><p className="text-xs text-muted-foreground">Total Accessions</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-blue-600">{new Set(collections.flatMap(c => c.species)).size}</p><p className="text-xs text-muted-foreground">Species</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-purple-600">{new Set(collections.map(c => c.curator)).size}</p><p className="text-xs text-muted-foreground">Curators</p></CardContent></Card>
      </div>

      {/* Search */}
      <Input
        placeholder="Search collections..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />

      {/* Collections Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredCollections.map((collection) => (
          <Card key={collection.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-base">{collection.name}</CardTitle>
                  <CardDescription>{collection.id}</CardDescription>
                </div>
                <Badge className={getTypeColor(collection.type)}>{collection.type}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">{collection.description}</p>
              
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">{collection.accessionCount.toLocaleString()}</span>
                <span className="text-sm text-muted-foreground">accessions</span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span>Collection size</span>
                  <span>{((collection.accessionCount / totalAccessions) * 100).toFixed(1)}%</span>
                </div>
                <Progress value={(collection.accessionCount / totalAccessions) * 100} className="h-2" />
              </div>

              <div className="flex flex-wrap gap-1">
                {collection.species.map(s => (
                  <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                ))}
              </div>

              <div className="flex justify-between text-xs text-muted-foreground pt-2 border-t">
                <span>👤 {collection.curator}</span>
                <span>📅 {collection.lastUpdated}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
