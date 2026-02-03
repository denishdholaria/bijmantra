import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { FileText, Search, Download, Printer, Globe, Dna, Leaf, Calendar } from 'lucide-react'

interface PassportData {
  id: string
  accessionNumber: string
  name: string
  species: string
  origin: string
  collectionDate: string
  donor: string
  pedigree: string
  characteristics: string[]
  storageLocation: string
  availability: 'available' | 'limited' | 'unavailable'
}

export function GermplasmPassport() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedAccession, setSelectedAccession] = useState<PassportData | null>(null)

  const accessions: PassportData[] = [
    { id: '1', accessionNumber: 'BIJ-R-001', name: 'IR64', species: 'Oryza sativa', origin: 'Philippines', collectionDate: '1985-06-15', donor: 'IRRI', pedigree: 'IR5657-33-2-1/IR2061-465-1-5-5', characteristics: ['Semi-dwarf', 'High yield', 'Good grain quality'], storageLocation: 'Vault A-1', availability: 'available' },
    { id: '2', accessionNumber: 'BIJ-R-002', name: 'Nipponbare', species: 'Oryza sativa', origin: 'Japan', collectionDate: '1990-03-20', donor: 'NIAS', pedigree: 'Landrace selection', characteristics: ['Japonica type', 'Reference genome'], storageLocation: 'Vault A-2', availability: 'available' },
    { id: '3', accessionNumber: 'BIJ-W-001', name: 'Chinese Spring', species: 'Triticum aestivum', origin: 'China', collectionDate: '1978-09-10', donor: 'CIMMYT', pedigree: 'Landrace', characteristics: ['Reference genome', 'Spring type'], storageLocation: 'Vault B-1', availability: 'limited' },
  ]

  const getAvailabilityColor = (availability: string) => {
    const colors: Record<string, string> = { available: 'bg-green-100 text-green-800', limited: 'bg-yellow-100 text-yellow-800', unavailable: 'bg-red-100 text-red-800' }
    return colors[availability] || 'bg-gray-100 text-gray-800'
  }

  const filteredAccessions = accessions.filter(a => 
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.accessionNumber.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Germplasm Passport</h1>
          <p className="text-muted-foreground">Detailed passport data for accessions</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Accessions</CardTitle>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {filteredAccessions.map((acc) => (
                <div key={acc.id} className={`p-3 cursor-pointer hover:bg-accent ${selectedAccession?.id === acc.id ? 'bg-accent' : ''}`} onClick={() => setSelectedAccession(acc)}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{acc.name}</p>
                      <p className="text-sm text-muted-foreground">{acc.accessionNumber}</p>
                    </div>
                    <Badge className={getAvailabilityColor(acc.availability)}>{acc.availability}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{selectedAccession ? selectedAccession.name : 'Select an Accession'}</CardTitle>
                {selectedAccession && <CardDescription>{selectedAccession.accessionNumber}</CardDescription>}
              </div>
              {selectedAccession && (
                <div className="flex gap-2">
                  <Button variant="outline" size="sm"><Printer className="mr-1 h-3 w-3" />Print</Button>
                  <Button variant="outline" size="sm"><Download className="mr-1 h-3 w-3" />Export</Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {selectedAccession ? (
              <div className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2"><Leaf className="h-4 w-4 text-green-500" /><span className="text-sm font-medium">Species:</span><span className="text-sm">{selectedAccession.species}</span></div>
                    <div className="flex items-center gap-2"><Globe className="h-4 w-4 text-blue-500" /><span className="text-sm font-medium">Origin:</span><span className="text-sm">{selectedAccession.origin}</span></div>
                    <div className="flex items-center gap-2"><Calendar className="h-4 w-4 text-orange-500" /><span className="text-sm font-medium">Collection Date:</span><span className="text-sm">{selectedAccession.collectionDate}</span></div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2"><FileText className="h-4 w-4 text-purple-500" /><span className="text-sm font-medium">Donor:</span><span className="text-sm">{selectedAccession.donor}</span></div>
                    <div className="flex items-center gap-2"><Dna className="h-4 w-4 text-pink-500" /><span className="text-sm font-medium">Storage:</span><span className="text-sm">{selectedAccession.storageLocation}</span></div>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium mb-2">Pedigree</p>
                  <p className="text-sm text-muted-foreground p-3 bg-accent rounded-lg font-mono">{selectedAccession.pedigree}</p>
                </div>
                <div>
                  <p className="text-sm font-medium mb-2">Characteristics</p>
                  <div className="flex gap-2 flex-wrap">{selectedAccession.characteristics.map(c => (<Badge key={c} variant="outline">{c}</Badge>))}</div>
                </div>
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">Select an accession to view passport data</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
