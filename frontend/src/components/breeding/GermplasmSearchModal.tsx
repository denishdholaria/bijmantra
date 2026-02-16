import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Search, Leaf, MapPin, Dna, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { cn } from '@/lib/utils'

export interface Germplasm {
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

interface GermplasmSearchModalProps {
  onSelect: (germplasm: Germplasm) => void
  trigger?: React.ReactNode
  title?: string
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function GermplasmSearchModal({ onSelect, trigger, title = "Select Germplasm", open: controlledOpen, onOpenChange: setControlledOpen }: GermplasmSearchModalProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const isControlled = controlledOpen !== undefined
  const open = isControlled ? controlledOpen : internalOpen
  const setOpen = isControlled ? setControlledOpen : setInternalOpen

  const [searchQuery, setSearchQuery] = useState('')

  // Fetch search results
  const { data: searchData, isLoading } = useQuery({
    queryKey: ['germplasm-search', searchQuery],
    queryFn: () => apiClient.germplasmSearchService.search({
      query: searchQuery || undefined,
      pageSize: 20
    }),
    enabled: !!open, // Only search when modal is open
    staleTime: 5000
  })

  const results: Germplasm[] = searchData?.results || []

  const handleSelect = (g: Germplasm) => {
    onSelect(g)
    if (setOpen) setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || <Button variant="outline">Select Germplasm</Button>}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>Search and select germplasm</DialogDescription>
        </DialogHeader>

        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, accession..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <ScrollArea className="flex-1 pr-4">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {searchQuery ? 'No results found' : 'Start typing to search'}
            </div>
          ) : (
            <div className="space-y-2">
              {results.map((item) => (
                <div
                  key={item.id}
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-muted/50 transition-colors",
                  )}
                  onClick={() => handleSelect(item)}
                >
                  <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                    <Leaf className="h-5 w-5 text-green-600 dark:text-green-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">{item.name}</span>
                      <Badge variant="outline" className="text-xs">{item.accession}</Badge>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                      <span className="flex items-center gap-1"><Dna className="h-3 w-3" />{item.species}</span>
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{item.origin}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
