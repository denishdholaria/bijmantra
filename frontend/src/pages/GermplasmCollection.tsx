/**
 * Germplasm Collection Page
 * Manage germplasm collections and accessions
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { apiClient } from '@/lib/api-client'
import { CalendarDays } from 'lucide-react'

export function GermplasmCollection() {
  const [search, setSearch] = useState('')

  // Fetch collections
  const { data: collectionsData, isLoading, error } = useQuery({
    queryKey: ['germplasm-collections', search],
    queryFn: () => apiClient.germplasmCollectionService.getCollections({ search: search || undefined }),
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['germplasm-collection-stats'],
    queryFn: () => apiClient.germplasmCollectionService.getStats(),
  })

  const collections = collectionsData?.data || []
  const stats = statsData?.data || { total_collections: 0, total_accessions: 0, unique_species: 0, unique_curators: 0 }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'core': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
      case 'working': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
      case 'active': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
      case 'base': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
      case 'breeding': return 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400'
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
    }
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        Error loading collections. Please try again.
      </div>
    )
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
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{stats.total_collections}</p><p className="text-xs text-muted-foreground">Collections</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-green-600">{stats.total_accessions?.toLocaleString()}</p><p className="text-xs text-muted-foreground">Total Accessions</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-blue-600">{stats.unique_species}</p><p className="text-xs text-muted-foreground">Species</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-purple-600">{stats.unique_curators}</p><p className="text-xs text-muted-foreground">Curators</p></CardContent></Card>
      </div>

      {/* Search */}
      <div className="max-w-sm">
        <Label htmlFor="search-collections" className="sr-only">Search</Label>
        <Input
          id="search-collections"
          placeholder="Search collections..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Collections Grid */}
      {isLoading ? (
        <div className="text-center py-8 text-muted-foreground">Loading collections...</div>
      ) : collections.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">No collections found</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {collections.map((collection: {
            id: string;
            name: string;
            type: string;
            description: string;
            accession_count: number;
            species: string[];
            curator: string;
            updated_at: string;
          }) => (
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
                  <span className="text-2xl font-bold">{collection.accession_count?.toLocaleString()}</span>
                  <span className="text-sm text-muted-foreground">accessions</span>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Collection size</span>
                    <span>{stats.total_accessions > 0 ? ((collection.accession_count / stats.total_accessions) * 100).toFixed(1) : 0}%</span>
                  </div>
                  <Progress value={stats.total_accessions > 0 ? (collection.accession_count / stats.total_accessions) * 100 : 0} className="h-2" />
                </div>

                <div className="flex flex-wrap gap-1">
                  {collection.species?.map((s: string) => (
                    <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                  ))}
                </div>

                <div className="flex justify-between text-xs text-muted-foreground pt-2 border-t">
                  <span>👤 {collection.curator}</span>
                  <span className="flex items-center gap-1"><CalendarDays className="h-3 w-3" /> {collection.updated_at}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
