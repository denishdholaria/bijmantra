import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Zap,
  Leaf,
  FlaskConical,
  Crosshair,
  Database,
  Save,
  Plus,
  CheckCircle2,
  Clock,
  ArrowRight
} from 'lucide-react'

interface QuickEntryItem {
  type: string
  count: number
  lastEntry: string
}

export function QuickEntry() {
  const [activeTab, setActiveTab] = useState('germplasm')
  const [savedCount, setSavedCount] = useState(0)

  const recentEntries: QuickEntryItem[] = [
    { type: 'Germplasm', count: 12, lastEntry: '5 minutes ago' },
    { type: 'Observations', count: 47, lastEntry: '10 minutes ago' },
    { type: 'Crosses', count: 8, lastEntry: '1 hour ago' }
  ]

  const handleSave = () => {
    setSavedCount(prev => prev + 1)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Zap className="h-8 w-8 text-primary" />
            Quick Entry
          </h1>
          <p className="text-muted-foreground mt-1">Rapid data entry for common breeding tasks</p>
        </div>
        <Badge variant="secondary" className="text-lg py-1 px-3">
          <CheckCircle2 className="h-4 w-4 mr-2" />{savedCount} saved this session
        </Badge>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {recentEntries.map((entry, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    {entry.type === 'Germplasm' ? <Leaf className="h-5 w-5 text-primary" /> :
                     entry.type === 'Observations' ? <Database className="h-5 w-5 text-primary" /> :
                     <Crosshair className="h-5 w-5 text-primary" />}
                  </div>
                  <div>
                    <div className="font-medium">{entry.type}</div>
                    <div className="text-sm text-muted-foreground">{entry.count} entries today</div>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />{entry.lastEntry}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="germplasm"><Leaf className="h-4 w-4 mr-2" />Germplasm</TabsTrigger>
          <TabsTrigger value="observation"><Database className="h-4 w-4 mr-2" />Observation</TabsTrigger>
          <TabsTrigger value="cross"><Crosshair className="h-4 w-4 mr-2" />Cross</TabsTrigger>
          <TabsTrigger value="trial"><FlaskConical className="h-4 w-4 mr-2" />Trial</TabsTrigger>
        </TabsList>

        <TabsContent value="germplasm">
          <Card>
            <CardHeader>
              <CardTitle>Quick Germplasm Entry</CardTitle>
              <CardDescription>Add new germplasm to the database</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Germplasm Name *</Label>
                  <Input placeholder="e.g., IR64-Sub1" />
                </div>
                <div className="space-y-2">
                  <Label>Accession Number</Label>
                  <Input placeholder="e.g., ACC-2025-001" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Species</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select species" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rice">Oryza sativa</SelectItem>
                      <SelectItem value="wheat">Triticum aestivum</SelectItem>
                      <SelectItem value="maize">Zea mays</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Country of Origin</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select country" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PHL">Philippines</SelectItem>
                      <SelectItem value="IND">India</SelectItem>
                      <SelectItem value="CHN">China</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Pedigree</Label>
                <Input placeholder="e.g., IR5657-33-2-1/IR2061-465-1-5-5" />
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea placeholder="Additional information..." rows={3} />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleSave} className="flex-1"><Save className="h-4 w-4 mr-2" />Save</Button>
                <Button variant="outline"><Plus className="h-4 w-4 mr-2" />Save & Add Another</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="observation">
          <Card>
            <CardHeader>
              <CardTitle>Quick Observation Entry</CardTitle>
              <CardDescription>Record phenotypic observations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Study *</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select study" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="s1">Yield Trial 2025</SelectItem>
                      <SelectItem value="s2">Disease Screening</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Observation Unit *</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select unit" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ou1">Plot R1-C1</SelectItem>
                      <SelectItem value="ou2">Plot R1-C2</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Trait *</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select trait" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="yield">Grain Yield (t/ha)</SelectItem>
                      <SelectItem value="height">Plant Height (cm)</SelectItem>
                      <SelectItem value="maturity">Days to Maturity</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Value *</Label>
                  <Input type="number" placeholder="Enter value" />
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleSave} className="flex-1"><Save className="h-4 w-4 mr-2" />Save</Button>
                <Button variant="outline"><ArrowRight className="h-4 w-4 mr-2" />Next Plot</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cross">
          <Card>
            <CardHeader>
              <CardTitle>Quick Cross Entry</CardTitle>
              <CardDescription>Record new crosses</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Female Parent *</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select female" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ir64">IR64</SelectItem>
                      <SelectItem value="swarna">Swarna</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Male Parent *</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select male" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fr13a">FR13A</SelectItem>
                      <SelectItem value="pokkali">Pokkali</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Cross Date</Label>
                  <Input type="date" />
                </div>
                <div className="space-y-2">
                  <Label>Seeds Obtained</Label>
                  <Input type="number" placeholder="Number of seeds" />
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleSave} className="flex-1"><Save className="h-4 w-4 mr-2" />Save Cross</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trial">
          <Card>
            <CardHeader>
              <CardTitle>Quick Trial Entry</CardTitle>
              <CardDescription>Create a new trial</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Trial Name *</Label>
                  <Input placeholder="e.g., Yield Trial Spring 2025" />
                </div>
                <div className="space-y-2">
                  <Label>Program</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select program" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rice">Rice Breeding</SelectItem>
                      <SelectItem value="wheat">Wheat Breeding</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Start Date</Label>
                  <Input type="date" />
                </div>
                <div className="space-y-2">
                  <Label>End Date</Label>
                  <Input type="date" />
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleSave} className="flex-1"><Save className="h-4 w-4 mr-2" />Create Trial</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
