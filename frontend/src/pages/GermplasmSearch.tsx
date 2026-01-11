/**
 * Germplasm Search Page
 * Advanced germplasm search and discovery
 * Connected to /api/v2/germplasm-search/* endpoints
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Search, Leaf, MapPin, Dna, Star, Download, Plus, Eye, SlidersHorizontal, X, AlertCircle } from 'lucide-react'
import { germplasmSearchAPI } from '@/lib/api-client'

interface GermplasmResult {
  id: string
  name: string
  accession: string
  species: string
  subspecies?: string
  origin: string
  traits: string[]
  status: string
  collection: string
  year?: number
}

interface Filters {
  species: string[]
  origins: string[]
  collections: string[]
  traits: string[]
}

export function GermplasmSearch() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedItems, setSelectedItems] = useState<string[]>([])
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({ species: 'all', origin: 'all', collection: 'all' })

  // Fetch search results
  const { data: searchData, isLoading: searchLoading, error: searchError } = useQuery({
    queryKey: ['germplasm-search', searchQuery, filters],
    queryFn: () => germplasmSearchAPI.search({
      query: searchQuery || undefined,
      species: filters.species !== 'all' ? filters.species : undefined,
      origin: filters.origin !== 'all' ? filters.origin : undefined,
      collection: filters.collection !== 'all' ? filters.collection : undefined,
    }),
    retry: 1,
  })

  // Fetch filter options
  const { data: filterData } = useQuery({
    queryKey: ['germplasm-search-filters'],
    queryFn: () => germplasmSearchAPI.getFilters(),
    retry: 1,
  })

  // Use API data
  const results: GermplasmResult[] = searchData?.results || []
  const filterOptions: Filters = filterData?.data || { species: [], origins: [], collections: [], traits: [] }

  const toggleSelect = (id: string) => {
    setSelectedItems(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id])
  }

  if (searchLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-20" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Search className="h-8 w-8 text-primary" />
            Germplasm Search
          </h1>
          <p className="text-muted-foreground mt-1">Search and discover genetic resources</p>
        </div>
        <div className="flex gap-2">
          {selectedItems.length > 0 && (
            <>
              <Button variant="outline"><Plus className="h-4 w-4 mr-2" />Add to List ({selectedItems.length})</Button>
              <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
            </>
          )}
        </div>
      </div>

      {searchError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load germplasm data. Please try again.</AlertDescription>
        </Alert>
      )}

      {/* Search Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input placeholder="Search by name, accession, or trait..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-12 h-12 text-lg" />
            </div>
            <Button variant="outline" onClick={() => setShowFilters(!showFilters)}>
              <SlidersHorizontal className="h-4 w-4 mr-2" />Filters
              {Object.values(filters).some(f => f !== 'all') && <Badge variant="secondary" className="ml-2">Active</Badge>}
            </Button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t grid grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Species</label>
                <Select value={filters.species} onValueChange={(v) => setFilters({...filters, species: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Species</SelectItem>
                    {filterOptions.species.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Country of Origin</label>
                <Select value={filters.origin} onValueChange={(v) => setFilters({...filters, origin: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Countries</SelectItem>
                    {filterOptions.origins.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Collection</label>
                <Select value={filters.collection} onValueChange={(v) => setFilters({...filters, collection: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Collections</SelectItem>
                    {filterOptions.collections.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end">
                <Button variant="ghost" onClick={() => setFilters({ species: 'all', origin: 'all', collection: 'all' })}>
                  <X className="h-4 w-4 mr-2" />Clear Filters
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Search Results</CardTitle>
              <CardDescription>{results.length} germplasm found</CardDescription>
            </div>
            {selectedItems.length > 0 && (
              <Button variant="ghost" size="sm" onClick={() => setSelectedItems([])}>Clear Selection</Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="space-y-3">
              {results.map((item) => (
                <div key={item.id} className={`flex items-center gap-4 p-4 border rounded-lg cursor-pointer transition-colors ${selectedItems.includes(item.id) ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'}`} onClick={() => toggleSelect(item.id)}>
                  <Checkbox checked={selectedItems.includes(item.id)} />
                  <div className="p-3 bg-green-100 rounded-lg"><Leaf className="h-6 w-6 text-green-600" /></div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{item.name}</h3>
                      <Badge variant="outline">{item.accession}</Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                      <span className="flex items-center gap-1"><Dna className="h-3 w-3" />{item.species}</span>
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{item.origin}</span>
                      <span>{item.collection}</span>
                    </div>
                    <div className="flex gap-1 mt-2">
                      {item.traits.map((trait, i) => <Badge key={i} variant="secondary" className="text-xs">{trait}</Badge>)}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon" aria-label="Add to favorites"><Star className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="icon" aria-label="View details"><Eye className="h-4 w-4" /></Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
