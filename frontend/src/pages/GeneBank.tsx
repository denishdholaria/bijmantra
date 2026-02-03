import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Database, Search, Filter, Download, Upload,
  MapPin, Thermometer, Calendar, Package, Globe
} from 'lucide-react'

interface Accession {
  id: string
  accessionNumber: string
  name: string
  species: string
  origin: string
  collectionDate: string
  storageLocation: string
  status: 'active' | 'depleted' | 'regenerating'
  quantity: number
  viability: number
}

export function GeneBank() {
  const [activeTab, setActiveTab] = useState('collection')
  const [searchQuery, setSearchQuery] = useState('')

  const accessions: Accession[] = [
    { id: '1', accessionNumber: 'GB-R-001', name: 'IR64', species: 'Oryza sativa', origin: 'Philippines', collectionDate: '1985-06-15', storageLocation: 'Vault A-1', status: 'active', quantity: 5000, viability: 95 },
    { id: '2', accessionNumber: 'GB-R-002', name: 'Nipponbare', species: 'Oryza sativa', origin: 'Japan', collectionDate: '1990-03-20', storageLocation: 'Vault A-2', status: 'active', quantity: 3500, viability: 92 },
    { id: '3', accessionNumber: 'GB-W-001', name: 'Chinese Spring', species: 'Triticum aestivum', origin: 'China', collectionDate: '1978-09-10', storageLocation: 'Vault B-1', status: 'regenerating', quantity: 500, viability: 78 },
    { id: '4', accessionNumber: 'GB-M-001', name: 'B73', species: 'Zea mays', origin: 'USA', collectionDate: '1972-07-25', storageLocation: 'Vault C-1', status: 'active', quantity: 8000, viability: 88 },
    { id: '5', accessionNumber: 'GB-R-003', name: 'Kasalath', species: 'Oryza sativa', origin: 'India', collectionDate: '1988-11-05', storageLocation: 'Vault A-3', status: 'depleted', quantity: 50, viability: 65 },
  ]

  const stats = {
    total: accessions.length,
    active: accessions.filter(a => a.status === 'active').length,
    regenerating: accessions.filter(a => a.status === 'regenerating').length,
    avgViability: Math.round(accessions.reduce((sum, a) => sum + a.viability, 0) / accessions.length)
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { active: 'bg-green-100 text-green-800', depleted: 'bg-red-100 text-red-800', regenerating: 'bg-yellow-100 text-yellow-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const filteredAccessions = accessions.filter(a => 
    searchQuery === '' || 
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.accessionNumber.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Gene Bank</h1>
          <p className="text-muted-foreground">Manage genetic resources and accessions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export</Button>
          <Button><Upload className="mr-2 h-4 w-4" />Add Accession</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Accessions</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">In collection</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <Package className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.active}</div>
            <p className="text-xs text-muted-foreground">Available for distribution</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Regenerating</CardTitle>
            <Calendar className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.regenerating}</div>
            <p className="text-xs text-muted-foreground">Under multiplication</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Viability</CardTitle>
            <Thermometer className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avgViability}%</div>
            <p className="text-xs text-muted-foreground">Germination rate</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search accessions..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
        </div>
        <Button variant="outline"><Filter className="mr-2 h-4 w-4" />Filter</Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="collection"><Database className="mr-2 h-4 w-4" />Collection</TabsTrigger>
          <TabsTrigger value="storage"><Thermometer className="mr-2 h-4 w-4" />Storage</TabsTrigger>
          <TabsTrigger value="distribution"><Globe className="mr-2 h-4 w-4" />Distribution</TabsTrigger>
        </TabsList>

        <TabsContent value="collection" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <div className="divide-y">
                {filteredAccessions.map((acc) => (
                  <div key={acc.id} className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center font-mono text-sm">{acc.accessionNumber.split('-')[1]}</div>
                      <div>
                        <p className="font-medium">{acc.name}</p>
                        <p className="text-sm text-muted-foreground">{acc.accessionNumber} • {acc.species}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right text-sm">
                        <p className="flex items-center gap-1"><MapPin className="h-3 w-3" />{acc.origin}</p>
                        <p className="text-muted-foreground">{acc.quantity.toLocaleString()} seeds • {acc.viability}% viable</p>
                      </div>
                      <Badge className={getStatusColor(acc.status)}>{acc.status}</Badge>
                      <Button variant="outline" size="sm">View</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="storage"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Storage conditions and monitoring</p></CardContent></Card></TabsContent>
        <TabsContent value="distribution"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Seed distribution requests</p></CardContent></Card></TabsContent>
      </Tabs>
    </div>
  )
}
