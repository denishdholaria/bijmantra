/**
 * Disease Atlas Page
 * Comprehensive plant disease reference and identification guide
 * Connected to /api/v2/disease/* API
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Loader2 } from 'lucide-react'
import { diseaseAPI } from '@/lib/api-client'

interface Disease {
  id: string
  name: string
  scientific_name?: string
  scientificName?: string
  crop: string
  pathogen: string
  pathogen_type?: string
  pathogenType?: 'fungal' | 'bacterial' | 'viral' | 'nematode'
  symptoms?: string[] | string
  conditions?: string[]
  management?: string[]
  severity?: 'low' | 'medium' | 'high'
  economic_impact?: string
  economicImpact?: string
  disease_type?: string
}

interface DiseaseStats {
  total: number
  fungal: number
  bacterial: number
  viral: number
  highSeverity: number
}

// Fetch diseases from API
async function fetchDiseases(crop?: string, pathogenType?: string): Promise<Disease[]> {
  try {
    const response = await diseaseAPI.getDiseases({
      crop: crop !== 'all' ? crop : undefined,
      disease_type: pathogenType !== 'all' ? pathogenType : undefined,
    });
    return response.data || [];
  } catch {
    return [];
  }
}

// Fetch disease statistics
async function fetchDiseaseStats(): Promise<DiseaseStats> {
  try {
    const response = await diseaseAPI.getStatistics();
    const stats = response.data || {};
    return {
      total: stats.total_diseases || 0,
      fungal: stats.by_type?.fungal || 0,
      bacterial: stats.by_type?.bacterial || 0,
      viral: stats.by_type?.viral || 0,
      highSeverity: stats.high_severity || 0,
    };
  } catch {
    return { total: 0, fungal: 0, bacterial: 0, viral: 0, highSeverity: 0 };
  }
}

// Fetch single disease details
async function fetchDiseaseDetails(diseaseId: string): Promise<Disease | null> {
  try {
    const response = await diseaseAPI.getDisease(diseaseId);
    return response.data || null;
  } catch {
    return null;
  }
}

export function DiseaseAtlas() {
  const [activeTab, setActiveTab] = useState('browse')
  const [selectedCrop, setSelectedCrop] = useState('all')
  const [selectedPathogen, setSelectedPathogen] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDisease, setSelectedDisease] = useState<Disease | null>(null)

  // Fetch diseases
  const { data: diseases = [], isLoading: diseasesLoading } = useQuery({
    queryKey: ['diseases', selectedCrop, selectedPathogen],
    queryFn: () => fetchDiseases(selectedCrop, selectedPathogen),
    staleTime: 1000 * 60 * 10, // 10 minutes
  })

  // Fetch stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['disease-stats'],
    queryFn: fetchDiseaseStats,
    staleTime: 1000 * 60 * 30, // 30 minutes
  })

  // Filter diseases by search query
  const filteredDiseases = diseases.filter(d => {
    if (searchQuery && !d.name.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  // Use fallback data if API returns empty
  const displayDiseases = filteredDiseases.length > 0 ? filteredDiseases : getFallbackDiseases(selectedCrop, selectedPathogen, searchQuery)
  const displayStats = stats || calculateFallbackStats(displayDiseases)

  const getSeverityBadge = (severity?: string) => {
    switch (severity) {
      case 'high': return <Badge className="bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300">High Severity</Badge>
      case 'medium': return <Badge className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300">Medium Severity</Badge>
      case 'low': return <Badge className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">Low Severity</Badge>
      default: return <Badge variant="secondary">{severity || 'Unknown'}</Badge>
    }
  }

  const getPathogenBadge = (type?: string) => {
    const pathogenType = type?.toLowerCase()
    switch (pathogenType) {
      case 'fungal': return <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">🍄 Fungal</Badge>
      case 'bacterial': return <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">🦠 Bacterial</Badge>
      case 'viral': return <Badge className="bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300">🧬 Viral</Badge>
      case 'nematode': return <Badge className="bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300">🪱 Nematode</Badge>
      default: return <Badge variant="secondary">{type || 'Unknown'}</Badge>
    }
  }

  const handleDiseaseSelect = (disease: Disease) => {
    setSelectedDisease(disease)
    setActiveTab('detail')
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
            {statsLoading ? (
              <Loader2 className="h-6 w-6 animate-spin mx-auto" />
            ) : (
              <p className="text-3xl font-bold text-primary">{displayStats.total}</p>
            )}
            <p className="text-sm text-muted-foreground">Total Diseases</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            {statsLoading ? (
              <Loader2 className="h-6 w-6 animate-spin mx-auto" />
            ) : (
              <p className="text-3xl font-bold text-purple-600">{displayStats.fungal}</p>
            )}
            <p className="text-sm text-muted-foreground">Fungal</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            {statsLoading ? (
              <Loader2 className="h-6 w-6 animate-spin mx-auto" />
            ) : (
              <p className="text-3xl font-bold text-blue-600">{displayStats.bacterial}</p>
            )}
            <p className="text-sm text-muted-foreground">Bacterial</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            {statsLoading ? (
              <Loader2 className="h-6 w-6 animate-spin mx-auto" />
            ) : (
              <p className="text-3xl font-bold text-red-600">{displayStats.highSeverity}</p>
            )}
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
                <SelectItem value="Rice">Rice</SelectItem>
                <SelectItem value="Wheat">Wheat</SelectItem>
                <SelectItem value="Maize">Maize</SelectItem>
                <SelectItem value="Soybean">Soybean</SelectItem>
                <SelectItem value="Cotton">Cotton</SelectItem>
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
                <SelectItem value="nematode">Nematode</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Disease Grid */}
          {diseasesLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {displayDiseases.map((disease) => (
                <Card 
                  key={disease.id} 
                  className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => handleDiseaseSelect(disease)}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{disease.name}</CardTitle>
                        <CardDescription className="italic">
                          {disease.scientific_name || disease.scientificName || disease.pathogen}
                        </CardDescription>
                      </div>
                      {getSeverityBadge(disease.severity)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2 mb-3">
                      <Badge variant="outline">{disease.crop}</Badge>
                      {getPathogenBadge(disease.pathogen_type || disease.pathogenType || disease.disease_type)}
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {Array.isArray(disease.symptoms) ? disease.symptoms[0] : disease.symptoms || 'No symptoms listed'}
                    </p>
                    <Button variant="link" className="p-0 h-auto mt-2">View Details →</Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {!diseasesLoading && displayDiseases.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">No diseases found matching your criteria</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="detail" className="space-y-6 mt-4">
          {selectedDisease && (
            <DiseaseDetail 
              disease={selectedDisease} 
              onBack={() => setActiveTab('browse')}
              getSeverityBadge={getSeverityBadge}
              getPathogenBadge={getPathogenBadge}
            />
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
                    {displayDiseases.map((d) => (
                      <tr 
                        key={d.id} 
                        className="border-b hover:bg-muted/50 cursor-pointer" 
                        onClick={() => handleDiseaseSelect(d)}
                      >
                        <td className="p-3 font-medium">{d.name}</td>
                        <td className="p-3">{d.crop}</td>
                        <td className="p-3">{getPathogenBadge(d.pathogen_type || d.pathogenType || d.disease_type)}</td>
                        <td className="p-3 text-center">{getSeverityBadge(d.severity)}</td>
                        <td className="p-3 text-muted-foreground">
                          {Array.isArray(d.symptoms) ? d.symptoms[0] : d.symptoms || '-'}
                        </td>
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

// Disease Detail Component
function DiseaseDetail({ 
  disease, 
  onBack,
  getSeverityBadge,
  getPathogenBadge,
}: { 
  disease: Disease
  onBack: () => void
  getSeverityBadge: (severity?: string) => JSX.Element
  getPathogenBadge: (type?: string) => JSX.Element
}) {
  const symptoms = Array.isArray(disease.symptoms) 
    ? disease.symptoms 
    : disease.symptoms ? [disease.symptoms] : []
  
  const conditions = disease.conditions || []
  const management = disease.management || []
  const economicImpact = disease.economic_impact || disease.economicImpact || 'Impact data not available'

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-2xl">{disease.name}</CardTitle>
              <CardDescription className="text-lg italic">
                {disease.scientific_name || disease.scientificName || disease.pathogen}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {getSeverityBadge(disease.severity)}
              {getPathogenBadge(disease.pathogen_type || disease.pathogenType || disease.disease_type)}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Symptoms */}
            <div>
              <h4 className="font-bold mb-2 flex items-center gap-2">🔍 Symptoms</h4>
              {symptoms.length > 0 ? (
                <ul className="space-y-1">
                  {symptoms.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="text-red-500">•</span>
                      {s}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No symptoms data available</p>
              )}
            </div>

            {/* Favorable Conditions */}
            <div>
              <h4 className="font-bold mb-2 flex items-center gap-2">🌡️ Favorable Conditions</h4>
              {conditions.length > 0 ? (
                <ul className="space-y-1">
                  {conditions.map((c, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="text-yellow-500">•</span>
                      {c}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No conditions data available</p>
              )}
            </div>
          </div>

          {/* Management */}
          <div>
            <h4 className="font-bold mb-2 flex items-center gap-2">💊 Management Strategies</h4>
            {management.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {management.map((m, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm p-2 bg-green-50 dark:bg-green-950 rounded">
                    <span className="text-green-600">✓</span>
                    {m}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No management data available</p>
            )}
          </div>

          {/* Economic Impact */}
          <div className="p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
            <h4 className="font-bold text-red-800 dark:text-red-300 mb-1">💰 Economic Impact</h4>
            <p className="text-red-700 dark:text-red-400">{economicImpact}</p>
          </div>
        </CardContent>
      </Card>

      <Button variant="outline" onClick={onBack}>← Back to Browse</Button>
    </>
  )
}

// Fallback data when API is unavailable
function getFallbackDiseases(crop: string, pathogenType: string, searchQuery: string): Disease[] {
  const fallbackDiseases: Disease[] = [
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
    },
  ]

  return fallbackDiseases.filter(d => {
    if (crop !== 'all' && d.crop.toLowerCase() !== crop.toLowerCase()) return false
    if (pathogenType !== 'all' && d.pathogenType !== pathogenType) return false
    if (searchQuery && !d.name.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })
}

function calculateFallbackStats(diseases: Disease[]): DiseaseStats {
  return {
    total: diseases.length,
    fungal: diseases.filter(d => d.pathogenType === 'fungal' || d.pathogen_type === 'fungal').length,
    bacterial: diseases.filter(d => d.pathogenType === 'bacterial' || d.pathogen_type === 'bacterial').length,
    viral: diseases.filter(d => d.pathogenType === 'viral' || d.pathogen_type === 'viral').length,
    highSeverity: diseases.filter(d => d.severity === 'high').length,
  }
}
