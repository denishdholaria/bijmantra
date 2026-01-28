import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  BookOpen, FileText, Users, Calendar, ExternalLink,
  Plus, Search, Filter, Star, Download, Award
} from 'lucide-react'

interface Publication {
  id: string
  title: string
  authors: string[]
  journal: string
  year: number
  doi?: string
  status: 'published' | 'in-review' | 'draft' | 'submitted'
  citations: number
  relatedTrials: string[]
}

export function PublicationTracker() {
  const [activeTab, setActiveTab] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  const publications: Publication[] = [
    { id: '1', title: 'Genomic Selection for Yield Improvement in Rice', authors: ['Chen S', 'Patel R', 'Garcia M'], journal: 'Theoretical and Applied Genetics', year: 2025, doi: '10.1007/xxx', status: 'published', citations: 12, relatedTrials: ['RT-2024-001'] },
    { id: '2', title: 'QTL Mapping of Drought Tolerance in Wheat', authors: ['Smith J', 'Okonkwo A'], journal: 'Crop Science', year: 2025, doi: '10.1002/xxx', status: 'published', citations: 8, relatedTrials: ['WT-2024-003'] },
    { id: '3', title: 'GWAS for Disease Resistance in Maize', authors: ['Patel R', 'Chen S'], journal: 'Plant Genome', year: 2025, status: 'in-review', citations: 0, relatedTrials: ['MZ-2024-002'] },
    { id: '4', title: 'Speed Breeding Protocols for Cereals', authors: ['Garcia M', 'Wei C'], journal: 'Plant Methods', year: 2025, status: 'submitted', citations: 0, relatedTrials: [] },
    { id: '5', title: 'Phenomic Selection in Plant Breeding', authors: ['Chen S', 'Smith J', 'Patel R'], journal: 'Frontiers in Plant Science', year: 2025, status: 'draft', citations: 0, relatedTrials: ['RT-2025-001'] },
  ]

  const stats = {
    total: publications.length,
    published: publications.filter(p => p.status === 'published').length,
    inReview: publications.filter(p => p.status === 'in-review' || p.status === 'submitted').length,
    totalCitations: publications.reduce((sum, p) => sum + p.citations, 0)
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { published: 'bg-green-100 text-green-800', 'in-review': 'bg-yellow-100 text-yellow-800', submitted: 'bg-blue-100 text-blue-800', draft: 'bg-gray-100 text-gray-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const filteredPubs = publications.filter(p => 
    (activeTab === 'all' || p.status === activeTab) &&
    (searchQuery === '' || p.title.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Publication Tracker</h1>
          <p className="text-muted-foreground">Track research outputs and citations</p>
        </div>
        <Button><Plus className="mr-2 h-4 w-4" />Add Publication</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Publications</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Published</CardTitle>
            <FileText className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.published}</div>
            <p className="text-xs text-muted-foreground">Peer-reviewed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Review</CardTitle>
            <Calendar className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.inReview}</div>
            <p className="text-xs text-muted-foreground">Under review</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Citations</CardTitle>
            <Award className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalCitations}</div>
            <p className="text-xs text-muted-foreground">Total citations</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search publications..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
        </div>
        <Button variant="outline"><Filter className="mr-2 h-4 w-4" />Filter</Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All ({publications.length})</TabsTrigger>
          <TabsTrigger value="published">Published ({stats.published})</TabsTrigger>
          <TabsTrigger value="in-review">In Review</TabsTrigger>
          <TabsTrigger value="draft">Drafts</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          {filteredPubs.map((pub) => (
            <Card key={pub.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{pub.title}</CardTitle>
                    <CardDescription className="flex items-center gap-2 mt-1">
                      <Users className="h-3 w-3" />{pub.authors.join(', ')}
                    </CardDescription>
                  </div>
                  <Badge className={getStatusColor(pub.status)}>{pub.status}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>{pub.journal}</span>
                    <span>{pub.year}</span>
                    {pub.citations > 0 && <span className="flex items-center gap-1"><Star className="h-3 w-3" />{pub.citations} citations</span>}
                  </div>
                  <div className="flex gap-2">
                    {pub.doi && <Button variant="outline" size="sm"><ExternalLink className="mr-1 h-3 w-3" />DOI</Button>}
                    <Button variant="outline" size="sm"><Download className="mr-1 h-3 w-3" />PDF</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}
