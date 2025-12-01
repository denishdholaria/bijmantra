/**
 * Field Book Page
 * Digital field book for data collection
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

interface FieldEntry {
  plotId: string
  germplasm: string
  rep: string
  row: number
  col: number
  traits: Record<string, string | number>
}

const sampleTraits = ['Plant Height', 'Days to Flowering', 'Disease Score', 'Yield']

const sampleEntries: FieldEntry[] = [
  { plotId: 'A-01-01', germplasm: 'Elite Variety 2024', rep: 'R1', row: 1, col: 1, traits: { 'Plant Height': 95, 'Days to Flowering': 65, 'Disease Score': 2, 'Yield': '' } },
  { plotId: 'A-01-02', germplasm: 'High Yield Line A', rep: 'R1', row: 1, col: 2, traits: { 'Plant Height': 102, 'Days to Flowering': 68, 'Disease Score': 3, 'Yield': '' } },
  { plotId: 'A-01-03', germplasm: 'Disease Resistant B', rep: 'R1', row: 1, col: 3, traits: { 'Plant Height': 88, 'Days to Flowering': 62, 'Disease Score': 1, 'Yield': '' } },
  { plotId: 'A-02-01', germplasm: 'Elite Variety 2024', rep: 'R2', row: 2, col: 1, traits: { 'Plant Height': 92, 'Days to Flowering': 64, 'Disease Score': 2, 'Yield': '' } },
  { plotId: 'A-02-02', germplasm: 'High Yield Line A', rep: 'R2', row: 2, col: 2, traits: { 'Plant Height': '', 'Days to Flowering': '', 'Disease Score': '', 'Yield': '' } },
  { plotId: 'A-02-03', germplasm: 'Disease Resistant B', rep: 'R2', row: 2, col: 3, traits: { 'Plant Height': '', 'Days to Flowering': '', 'Disease Score': '', 'Yield': '' } },
]

export function FieldBook() {
  const [entries, setEntries] = useState<FieldEntry[]>(sampleEntries)
  const [selectedTrait, setSelectedTrait] = useState('Plant Height')
  const [currentIndex, setCurrentIndex] = useState(0)

  const currentEntry = entries[currentIndex]
  const completedCount = entries.filter(e => e.traits[selectedTrait] !== '').length
  const progress = (completedCount / entries.length) * 100

  const updateValue = (value: string) => {
    setEntries(prev => prev.map((e, i) => 
      i === currentIndex ? { ...e, traits: { ...e.traits, [selectedTrait]: value } } : e
    ))
  }

  const goNext = () => {
    if (currentIndex < entries.length - 1) {
      setCurrentIndex(currentIndex + 1)
    } else {
      toast.success('Reached end of field book')
    }
  }

  const goPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    }
  }

  const saveData = () => {
    toast.success(`Saved ${completedCount} observations for ${selectedTrait}`)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Field Book</h1>
          <p className="text-muted-foreground mt-1">Digital data collection</p>
        </div>
        <Button onClick={saveData}>💾 Save All</Button>
      </div>

      <Tabs defaultValue="collect">
        <TabsList>
          <TabsTrigger value="collect">Collect</TabsTrigger>
          <TabsTrigger value="grid">Grid View</TabsTrigger>
          <TabsTrigger value="summary">Summary</TabsTrigger>
        </TabsList>

        <TabsContent value="collect" className="space-y-4 mt-4">
          {/* Trait Selection */}
          <Card>
            <CardContent className="pt-4">
              <div className="flex flex-col sm:flex-row gap-4 items-end">
                <div className="flex-1 space-y-2">
                  <Label>Trait</Label>
                  <Select value={selectedTrait} onValueChange={setSelectedTrait}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {sampleTraits.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="text-sm text-muted-foreground">
                  Progress: {completedCount}/{entries.length} ({progress.toFixed(0)}%)
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Data Entry Card */}
          <Card className="border-2 border-primary">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{currentEntry.plotId}</CardTitle>
                  <CardDescription>{currentEntry.germplasm}</CardDescription>
                </div>
                <Badge>{currentEntry.rep}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>Row: <span className="font-bold">{currentEntry.row}</span></div>
                <div>Column: <span className="font-bold">{currentEntry.col}</span></div>
              </div>

              <div className="space-y-2">
                <Label className="text-lg">{selectedTrait}</Label>
                <Input
                  type="number"
                  value={currentEntry.traits[selectedTrait] || ''}
                  onChange={(e) => updateValue(e.target.value)}
                  placeholder={`Enter ${selectedTrait}`}
                  className="text-2xl h-16 text-center"
                  autoFocus
                />
              </div>

              <div className="flex gap-2">
                <Button variant="outline" onClick={goPrev} disabled={currentIndex === 0} className="flex-1">
                  ← Previous
                </Button>
                <Button onClick={goNext} disabled={currentIndex === entries.length - 1} className="flex-1">
                  Next →
                </Button>
              </div>

              <div className="text-center text-sm text-muted-foreground">
                Entry {currentIndex + 1} of {entries.length}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="grid" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Grid View - {selectedTrait}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="p-2 text-left">Plot</th>
                      <th className="p-2 text-left">Germplasm</th>
                      <th className="p-2 text-left">Rep</th>
                      <th className="p-2 text-right">{selectedTrait}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((entry, i) => (
                      <tr 
                        key={entry.plotId} 
                        className={`border-b cursor-pointer hover:bg-muted/50 ${i === currentIndex ? 'bg-primary/10' : ''}`}
                        onClick={() => setCurrentIndex(i)}
                      >
                        <td className="p-2 font-mono">{entry.plotId}</td>
                        <td className="p-2">{entry.germplasm}</td>
                        <td className="p-2">{entry.rep}</td>
                        <td className="p-2 text-right">
                          {entry.traits[selectedTrait] || <span className="text-muted-foreground">-</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="summary" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Collection Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {sampleTraits.map(trait => {
                  const collected = entries.filter(e => e.traits[trait] !== '').length
                  return (
                    <div key={trait} className="p-4 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{collected}/{entries.length}</p>
                      <p className="text-sm text-muted-foreground">{trait}</p>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
