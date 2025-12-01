/**
 * Disease Atlas Page
 * Comprehensive plant disease reference and identification guide
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'

interface Disease {
  id: string
  name: string
  scientificName: string
  crop: string
  pathogen: string
  pathogenType: 'fungal' | 'bacterial' | 'viral' | 'nematode'
  symptoms: string[]
  conditions: string[]
  management: string[]
  severity: 'low' | 'medium' | 'high'
  economicImpact: string
  images: string[]
}

const diseases: Disease[] = [
  {
    id: 'd1',
    name: 'Rice Blast',
    scientificName: 'Magnaporthe oryzae',
    crop: 'Rice',
    pathogen: 'Magnaporthe oryzae',
    pathogenType: 'fungal',
    symptoms: ['Diamond-shaped lesions on leaves', 'Gray center with brown margins', 'Neck rot at panicle base', 'Node blast causing stem breakage'],
    conditions: ['High humidity (>90%)', 'Temperature 25-28°C', 'Prolonged leaf wetness', 'Excess nitrogen fertilization'],
    management: ['Use resistant varieties (Pi genes)', 'Seed treatment with fungicides', 'Balanced nitrogen application', 'Tricyclazole or Isoprothiolane spray', 'Silicon fertilization'],
    severity: 'high',
    economicImpact: 'Can cause 50-90% yield loss in severe epidemics',
    images: [],
  },
  {
    id: 'd2',
    name: 'Bacterial Leaf Blight',
    scientificName: 'Xanthomonas oryzae pv. oryzae',
    crop: 'Rice',
    pathogen: 'Xanthomonas oryzae',
    pathogenType: 'bacterial',
    symptoms: ['Yellow-orange lesions from leaf tip', 'Wavy leaf margins', 'Bacterial ooze on leaves', 'Kresek (seedling wilt)'],
    conditions: ['Warm temperature (25-34°C)', 'High humidity', 'Wounds from wind/insects', 'Flooded conditions'],
    management: ['Resistant varieties (Xa genes)', 'Avoid clipping seedlings', 'Balanced fertilization', 'Copper-based bactericides', 'Proper drainage'],
    severity: 'high',
    economicImpact: 'Yield losses of 20-50% common',
    images: [],
  },
  {
    id: 'd3',
    name: 'Sheath Blight',
    scientificName: 'Rhizoctonia solani',
    crop: 'Rice',
    pathogen: 'Rhizoctonia solani AG1-IA',
    pathogenType: 'fungal',
    symptoms: ['Oval/irregular lesions on sheath', 'Gray-white center', 'Brown margins', 'Sclerotia formation'],
    conditions: ['High humidity', 'Dense planting', 'Excess nitrogen', 'Temperature 28-32°C'],
    management: ['Wider spacing', 'Balanced nitrogen', 'Validamycin application', 'Remove crop residues', 'Biological control (Trichoderma)'],
    severity: 'medium',
    economicImpact: 'Yield reduction of 10-30%',
    images: [],
  },
  {
    id: 'd4',
    name: 'Wheat Rust (Stripe)',
    scientificName: 'Puccinia striiformis',
    crop: 'Wheat',
    pathogen: 'Puccinia striiformis f. sp. tritici',
    pathogenType: 'fungal',
    symptoms: ['Yellow-orange pustules in stripes', 'Parallel to leaf veins', 'Chlorotic streaks', 'Premature leaf death'],
    conditions: ['Cool temperatures (10-15°C)', 'High humidity', 'Dew formation', 'Susceptible varieties'],
    management: ['Resistant varieties (Yr genes)', 'Fungicide application (Propiconazole)', 'Early sowing', 'Remove volunteer wheat', 'Crop rotation'],
    severity: 'high',
    economicImpact: 'Can cause complete crop failure',
    images: [],
  },
  {
    id: 'd5',
    name: 'Powdery Mildew',
    scientificName: 'Blumeria graminis',
    crop: 'Wheat',
    pathogen: 'Blumeria graminis f. sp. tritici',
    pathogenType: 'fungal',
    symptoms: ['White powdery growth on leaves', 'Leaf curling', 'Yellowing', 'Reduced grain filling'],
    conditions: ['Moderate temperature (15-22°C)', 'High humidity', 'Dense canopy', 'Excess nitrogen'],
    management: ['Resistant varieties', 'Sulfur dust application', 'Triadimefon spray', 'Proper spacing', 'Balanced fertilization'],
    severity: 'medium',
    economicImpact: 'Yield loss of 10-25%',
    images: [],
  },
  {
    id: 'd6',
    name: 'Northern Corn Leaf Blight',
    scientificName: 'Exserohilum turcicum',
    crop: 'Maize',
    pathogen: 'Exserohilum turcicum',
    pathogenType: 'fungal',
    symptoms: ['Cigar-shaped lesions', 'Gray-green color', 'Lower leaves affected first', 'Lesions 2-15 cm long'],
    conditions: ['Moderate temperature (18-27°C)', 'Heavy dew', 'Humid weather', 'Susceptible hybrids'],
    management: ['Resistant hybrids (Ht genes)', 'Crop rotation', 'Tillage to bury residue', 'Fungicide application', 'Early planting'],
    severity: 'medium',
    economicImpact: 'Yield loss of 15-30%',
    images: [],
  },
]

export function DiseaseAtlas() {
  const [activeTab, setActiveTab] = useState('browse')
  const [selectedCrop, setSelectedCrop] = useState('all')
  const [selectedPathogen, setSelectedPathogen] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDisease, setSelectedDisease] = useState<Disease | null>(null)

  const filteredDiseases = diseases.filter(d => {
    if (selectedCrop !== 'all' && d.crop.toLowerCase() !== selectedCrop) return false
    if (selectedPathogen !== 'all' && d.pathogenType !== selectedPathogen) return false
    if (searchQuery && !d.name.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'high': return <Badge className="bg-red-100 text-red-700">High Severity</Badge>
      case 'medium': return <Badge className="bg-yellow-100 text-yellow-700">Medium Severity</Badge>
      case 'low': return <Badge className="bg-green-100 text-green-700">Low Severity</Badge>
      default: return <Badge variant="secondary">{severity}</Badge>
    }
  }

  const getPathogenBadge = (type: string) => {
    switch (type) {
      case 'fungal': return <Badge className="bg-purple-100 text-purple-700">🍄 Fungal</Badge>
      case 'bacterial': return <Badge className="bg-blue-100 text-blue-700">🦠 Bacterial</Badge>
      case 'viral': return <Badge className="bg-orange-100 text-orange-700">🧬 Viral</Badge>
      case 'nematode': return <Badge className="bg-brown-100 text-brown-700">🪱 Nematode</Badge>
      default: return <Badge variant="secondary">{type}</Badge>
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">🦠 Disease Atlas</h1>
          <p className="text-muted-foreground mt-1">Comprehensive plant disease reference guide</p>
        </div>
        <div className="flex gap-2">
          <Input 
            placeholder="Search diseases..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-48"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{diseases.length}</p>
            <p className="text-sm text-muted-foreground">Total Diseases</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">{diseases.filter(d => d.pathogenType === 'fungal').length}</p>
            <p className="text-sm text-muted-foreground">Fungal</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{diseases.filter(d => d.pathogenType === 'bacterial').length}</p>
            <p className="text-sm text-muted-foreground">Bacterial</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-red-600">{diseases.filter(d => d.severity === 'high').length}</p>
            <p className="text-sm text-muted-foreground">High Severity</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="browse">📚 Browse</TabsTrigger>
          <TabsTrigger value="detail" disabled={!selectedDisease}>📋 Details</TabsTrigger>
          <TabsTrigger value="compare">⚖️ Compare</TabsTrigger>
        </TabsList>

        <TabsContent value="browse" className="space-y-6 mt-4">
          {/* Filters */}
          <div className="flex gap-4">
            <Select value={selectedCrop} onValueChange={setSelectedCrop}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Crop" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Crops</SelectItem>
                <SelectItem value="rice">Rice</SelectItem>
                <SelectItem value="wheat">Wheat</SelectItem>
                <SelectItem value="maize">Maize</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedPathogen} onValueChange={setSelectedPathogen}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Pathogen" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="fungal">Fungal</SelectItem>
                <SelectItem value="bacterial">Bacterial</SelectItem>
                <SelectItem value="viral">Viral</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Disease Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredDiseases.map((disease) => (
              <Card 
                key={disease.id} 
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => { setSelectedDisease(disease); setActiveTab('detail'); }}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{disease.name}</CardTitle>
                      <CardDescription className="italic">{disease.scientificName}</CardDescription>
                    </div>
                    {getSeverityBadge(disease.severity)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant="outline">{disease.crop}</Badge>
                    {getPathogenBadge(disease.pathogenType)}
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {disease.symptoms[0]}
                  </p>
                  <Button variant="link" className="p-0 h-auto mt-2">View Details →</Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="detail" className="space-y-6 mt-4">
          {selectedDisease && (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-2xl">{selectedDisease.name}</CardTitle>
                      <CardDescription className="text-lg italic">{selectedDisease.scientificName}</CardDescription>
                    </div>
                    <div className="flex gap-2">
                      {getSeverityBadge(selectedDisease.severity)}
                      {getPathogenBadge(selectedDisease.pathogenType)}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Symptoms */}
                    <div>
                      <h4 className="font-bold mb-2 flex items-center gap-2">🔍 Symptoms</h4>
                      <ul className="space-y-1">
                        {selectedDisease.symptoms.map((s, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm">
                            <span className="text-red-500">•</span>
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Favorable Conditions */}
                    <div>
                      <h4 className="font-bold mb-2 flex items-center gap-2">🌡️ Favorable Conditions</h4>
                      <ul className="space-y-1">
                        {selectedDisease.conditions.map((c, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm">
                            <span className="text-yellow-500">•</span>
                            {c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Management */}
                  <div>
                    <h4 className="font-bold mb-2 flex items-center gap-2">💊 Management Strategies</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {selectedDisease.management.map((m, i) => (
                        <div key={i} className="flex items-start gap-2 text-sm p-2 bg-green-50 rounded">
                          <span className="text-green-600">✓</span>
                          {m}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Economic Impact */}
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="font-bold text-red-800 mb-1">💰 Economic Impact</h4>
                    <p className="text-red-700">{selectedDisease.economicImpact}</p>
                  </div>
                </CardContent>
              </Card>

              <Button variant="outline" onClick={() => setActiveTab('browse')}>← Back to Browse</Button>
            </>
          )}
        </TabsContent>

        <TabsContent value="compare" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Disease Comparison</CardTitle>
              <CardDescription>Compare symptoms and management across diseases</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Disease</th>
                      <th className="text-left p-3">Crop</th>
                      <th className="text-left p-3">Type</th>
                      <th className="text-center p-3">Severity</th>
                      <th className="text-left p-3">Key Symptom</th>
                    </tr>
                  </thead>
                  <tbody>
                    {diseases.map((d) => (
                      <tr key={d.id} className="border-b hover:bg-muted/50 cursor-pointer" onClick={() => { setSelectedDisease(d); setActiveTab('detail'); }}>
                        <td className="p-3 font-medium">{d.name}</td>
                        <td className="p-3">{d.crop}</td>
                        <td className="p-3">{getPathogenBadge(d.pathogenType)}</td>
                        <td className="p-3 text-center">{getSeverityBadge(d.severity)}</td>
                        <td className="p-3 text-muted-foreground">{d.symptoms[0]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
