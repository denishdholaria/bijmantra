import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  BookOpen, Plus, Search, Clock, CheckCircle, 
  FileText, Download, Share2, Star, Filter,
  Beaker, Leaf, Dna, Microscope, FlaskConical
} from 'lucide-react'

interface Protocol {
  id: string
  name: string
  category: string
  description: string
  version: string
  author: string
  lastUpdated: string
  steps: number
  starred: boolean
  status: 'approved' | 'draft' | 'archived'
}

export function ProtocolLibrary() {
  const [activeTab, setActiveTab] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  const protocols: Protocol[] = [
    { id: '1', name: 'DNA Extraction - CTAB Method', category: 'molecular', description: 'Standard CTAB protocol for plant DNA extraction', version: '2.1', author: 'Dr. Sarah Chen', lastUpdated: '2 weeks ago', steps: 12, starred: true, status: 'approved' },
    { id: '2', name: 'Crossing Block Setup', category: 'breeding', description: 'Guidelines for establishing crossing blocks', version: '1.5', author: 'Raj Patel', lastUpdated: '1 month ago', steps: 8, starred: true, status: 'approved' },
    { id: '3', name: 'Phenotyping - Plant Height', category: 'phenotyping', description: 'Standard method for measuring plant height', version: '1.2', author: 'Maria Garcia', lastUpdated: '3 months ago', steps: 5, starred: false, status: 'approved' },
    { id: '4', name: 'Seed Germination Test', category: 'quality', description: 'Protocol for testing seed viability', version: '1.0', author: 'John Smith', lastUpdated: '6 months ago', steps: 7, starred: false, status: 'approved' },
    { id: '5', name: 'PCR Amplification', category: 'molecular', description: 'Standard PCR protocol for marker analysis', version: '3.0', author: 'Dr. Sarah Chen', lastUpdated: '1 week ago', steps: 10, starred: true, status: 'approved' },
    { id: '6', name: 'Disease Scoring - Blast', category: 'phenotyping', description: 'Visual scoring scale for rice blast', version: '1.1', author: 'Aisha Okonkwo', lastUpdated: '2 months ago', steps: 6, starred: false, status: 'approved' },
    { id: '7', name: 'Doubled Haploid Production', category: 'breeding', description: 'Anther culture protocol for DH lines', version: '0.9', author: 'Chen Wei', lastUpdated: '1 week ago', steps: 15, starred: false, status: 'draft' },
    { id: '8', name: 'Leaf Sampling for Genotyping', category: 'molecular', description: 'Best practices for tissue collection', version: '1.3', author: 'Raj Patel', lastUpdated: '4 months ago', steps: 4, starred: false, status: 'approved' },
  ]

  const categories = [
    { id: 'all', name: 'All Protocols', icon: BookOpen, count: protocols.length },
    { id: 'breeding', name: 'Breeding', icon: Leaf, count: protocols.filter(p => p.category === 'breeding').length },
    { id: 'molecular', name: 'Molecular', icon: Dna, count: protocols.filter(p => p.category === 'molecular').length },
    { id: 'phenotyping', name: 'Phenotyping', icon: Microscope, count: protocols.filter(p => p.category === 'phenotyping').length },
    { id: 'quality', name: 'Quality', icon: FlaskConical, count: protocols.filter(p => p.category === 'quality').length },
  ]

  const filteredProtocols = protocols.filter(p => 
    (activeTab === 'all' || p.category === activeTab) &&
    (searchQuery === '' || p.name.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, any> = { breeding: Leaf, molecular: Dna, phenotyping: Microscope, quality: FlaskConical }
    const Icon = icons[category] || Beaker
    return <Icon className="h-5 w-5" />
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { approved: 'bg-green-100 text-green-800', draft: 'bg-yellow-100 text-yellow-800', archived: 'bg-gray-100 text-gray-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Protocol Library</h1>
          <p className="text-muted-foreground">Standard operating procedures and methods</p>
        </div>
        <Button><Plus className="mr-2 h-4 w-4" />New Protocol</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        {categories.map((cat) => (
          <Card key={cat.id} className={`cursor-pointer transition-colors ${activeTab === cat.id ? 'border-primary' : ''}`} onClick={() => setActiveTab(cat.id)}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <cat.icon className={`h-5 w-5 ${activeTab === cat.id ? 'text-primary' : 'text-muted-foreground'}`} />
                <div>
                  <p className="font-medium text-sm">{cat.name}</p>
                  <p className="text-xs text-muted-foreground">{cat.count} protocols</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search protocols..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
        </div>
        <Button variant="outline"><Filter className="mr-2 h-4 w-4" />Filter</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {filteredProtocols.map((protocol) => (
          <Card key={protocol.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {getCategoryIcon(protocol.category)}
                  <div>
                    <CardTitle className="text-lg">{protocol.name}</CardTitle>
                    <CardDescription>{protocol.description}</CardDescription>
                  </div>
                </div>
                <Button variant="ghost" size="icon" className={protocol.starred ? 'text-yellow-500' : ''} aria-label={protocol.starred ? 'Unstar protocol' : 'Star protocol'}>
                  <Star className="h-4 w-4" fill={protocol.starred ? 'currentColor' : 'none'} />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>v{protocol.version}</span>
                  <span>{protocol.steps} steps</span>
                  <span>Updated {protocol.lastUpdated}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={getStatusColor(protocol.status)}>{protocol.status}</Badge>
                  <Button variant="outline" size="sm"><FileText className="mr-1 h-3 w-3" />View</Button>
                  <Button variant="ghost" size="icon" aria-label="Download protocol"><Download className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="icon" aria-label="Share protocol"><Share2 className="h-4 w-4" /></Button>
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">By {protocol.author}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
