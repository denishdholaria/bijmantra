import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Users,
  Search,
  Filter,
  Star,
  Dna,
  Target,
  TrendingUp,
  CheckCircle2,
  Plus,
  Download,
  ArrowRight,
  Sparkles
} from 'lucide-react'

interface Parent {
  id: string
  name: string
  type: 'elite' | 'donor' | 'landrace'
  traits: string[]
  gebv: number
  heterosis: number
  selected: boolean
  pedigree: string
}

export function ParentSelection() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedParents, setSelectedParents] = useState<string[]>([])
  const [traitFilter, setTraitFilter] = useState('all')

  const parents: Parent[] = [
    { id: '1', name: 'IR64', type: 'elite', traits: ['High yield', 'Good quality'], gebv: 2.45, heterosis: 15.2, selected: false, pedigree: 'IR5657-33-2-1/IR2061-465-1-5-5' },
    { id: '2', name: 'Swarna', type: 'elite', traits: ['High yield', 'Wide adaptation'], gebv: 2.38, heterosis: 12.8, selected: false, pedigree: 'Vasistha/Mahsuri' },
    { id: '3', name: 'FR13A', type: 'donor', traits: ['Submergence tolerance'], gebv: 1.85, heterosis: 8.5, selected: false, pedigree: 'Landrace selection' },
    { id: '4', name: 'Pokkali', type: 'donor', traits: ['Salt tolerance'], gebv: 1.72, heterosis: 7.2, selected: false, pedigree: 'Kerala landrace' },
    { id: '5', name: 'Kasalath', type: 'landrace', traits: ['Drought tolerance', 'Deep roots'], gebv: 1.65, heterosis: 6.8, selected: false, pedigree: 'Aus landrace' },
    { id: '6', name: 'N22', type: 'donor', traits: ['Heat tolerance', 'Drought tolerance'], gebv: 1.58, heterosis: 9.1, selected: false, pedigree: 'Aus variety' },
    { id: '7', name: 'IRBB60', type: 'donor', traits: ['Bacterial blight resistance'], gebv: 1.92, heterosis: 5.4, selected: false, pedigree: 'IR24 NIL' },
    { id: '8', name: 'Tetep', type: 'donor', traits: ['Blast resistance'], gebv: 1.78, heterosis: 6.2, selected: false, pedigree: 'Vietnamese variety' }
  ]

  const toggleParent = (id: string) => {
    setSelectedParents(prev => prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id])
  }

  const filteredParents = parents.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesTrait = traitFilter === 'all' || p.traits.some(t => t.toLowerCase().includes(traitFilter.toLowerCase()))
    return matchesSearch && matchesTrait
  })

  const selectedParentData = parents.filter(p => selectedParents.includes(p.id))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users className="h-8 w-8 text-primary" />
            Parent Selection
          </h1>
          <p className="text-muted-foreground mt-1">Select optimal parents for crossing based on breeding values</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
          <Button disabled={selectedParents.length < 2}><Plus className="h-4 w-4 mr-2" />Create Cross Plan</Button>
        </div>
      </div>

      {/* Selection Summary */}
      {selectedParents.length > 0 && (
        <Card className="bg-primary/5 border-primary">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <CheckCircle2 className="h-6 w-6 text-primary" />
                <div>
                  <div className="font-medium">{selectedParents.length} Parents Selected</div>
                  <div className="text-sm text-muted-foreground">
                    {selectedParentData.map(p => p.name).join(' × ')}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-sm text-muted-foreground">Predicted Heterosis</div>
                  <div className="font-bold text-green-600">+{(selectedParentData.reduce((sum, p) => sum + p.heterosis, 0) / selectedParentData.length).toFixed(1)}%</div>
                </div>
                <Button variant="outline" size="sm" onClick={() => setSelectedParents([])}>Clear</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Parent List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Available Parents</CardTitle>
            <CardDescription>Select parents based on breeding objectives</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search parents..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
              </div>
              <Select value={traitFilter} onValueChange={setTraitFilter}>
                <SelectTrigger className="w-[180px]"><Filter className="h-4 w-4 mr-2" /><SelectValue placeholder="Filter by trait" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Traits</SelectItem>
                  <SelectItem value="yield">High Yield</SelectItem>
                  <SelectItem value="drought">Drought Tolerance</SelectItem>
                  <SelectItem value="disease">Disease Resistance</SelectItem>
                  <SelectItem value="quality">Grain Quality</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {filteredParents.map((parent) => (
                  <div key={parent.id} className={`flex items-center gap-4 p-4 rounded-lg border cursor-pointer transition-colors ${selectedParents.includes(parent.id) ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'}`} onClick={() => toggleParent(parent.id)}>
                    <Checkbox checked={selectedParents.includes(parent.id)} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{parent.name}</span>
                        <Badge variant={parent.type === 'elite' ? 'default' : parent.type === 'donor' ? 'secondary' : 'outline'}>{parent.type}</Badge>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {parent.traits.map((trait, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{trait}</Badge>
                        ))}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">{parent.pedigree}</div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-green-600">
                        <TrendingUp className="h-4 w-4" />
                        <span className="font-bold">{parent.gebv.toFixed(2)}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">GEBV</div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Selection Criteria */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Target className="h-5 w-5" />Breeding Objectives</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { trait: 'Yield', weight: 40, icon: <TrendingUp className="h-4 w-4" /> },
                  { trait: 'Disease Resistance', weight: 25, icon: <Dna className="h-4 w-4" /> },
                  { trait: 'Drought Tolerance', weight: 20, icon: <Star className="h-4 w-4" /> },
                  { trait: 'Grain Quality', weight: 15, icon: <Sparkles className="h-4 w-4" /> }
                ].map((obj, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {obj.icon}
                      <span className="text-sm">{obj.trait}</span>
                    </div>
                    <Badge variant="secondary">{obj.weight}%</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5" />AI Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { cross: 'IR64 × FR13A', reason: 'High yield + submergence tolerance', score: 92 },
                  { cross: 'Swarna × Pokkali', reason: 'Adaptation + salt tolerance', score: 88 },
                  { cross: 'IR64 × N22', reason: 'Yield + heat tolerance', score: 85 }
                ].map((rec, i) => (
                  <div key={i} className="p-3 border rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm">{rec.cross}</span>
                      <Badge variant="default">{rec.score}%</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{rec.reason}</p>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-4"><Sparkles className="h-4 w-4 mr-2" />Get More Suggestions</Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Cross Prediction */}
      {selectedParents.length >= 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Cross Prediction</CardTitle>
            <CardDescription>Predicted performance of selected cross</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center gap-4 mb-6">
              {selectedParentData.map((p, i) => (
                <div key={p.id} className="flex items-center gap-2">
                  <div className="p-4 bg-primary/10 rounded-lg text-center">
                    <div className="font-bold">{p.name}</div>
                    <div className="text-sm text-muted-foreground">{p.type}</div>
                  </div>
                  {i < selectedParentData.length - 1 && <ArrowRight className="h-6 w-6 text-muted-foreground" />}
                </div>
              ))}
            </div>
            <div className="grid grid-cols-4 gap-4">
              {[
                { label: 'Expected GEBV', value: (selectedParentData.reduce((sum, p) => sum + p.gebv, 0) / 2).toFixed(2) },
                { label: 'Heterosis', value: `+${(selectedParentData.reduce((sum, p) => sum + p.heterosis, 0) / selectedParentData.length).toFixed(1)}%` },
                { label: 'Genetic Distance', value: '0.42' },
                { label: 'Success Probability', value: '78%' }
              ].map((stat, i) => (
                <div key={i} className="text-center p-4 bg-muted rounded-lg">
                  <div className="text-2xl font-bold text-primary">{stat.value}</div>
                  <div className="text-sm text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
