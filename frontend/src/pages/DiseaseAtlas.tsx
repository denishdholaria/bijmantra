// @ts-nocheck
/**
 * Disease Atlas Page
 * Comprehensive plant disease reference and identification guide
 * Connected to /api/v2/disease/* API
 */
import React, { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

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
    const response = await apiClient.diseaseResistanceService.getDiseases({
      crop: crop !== 'all' ? crop : undefined,
      pathogen_type: pathogenType !== 'all' ? pathogenType : undefined,
    });
    return response.diseases || [];
  } catch {
    return [];
  }
}

// Fetch disease statistics
async function fetchDiseaseStats(): Promise<DiseaseStats> {
  try {
    const response = await apiClient.diseaseResistanceService.getStatistics();
    const stats = response || {};
    return {
      total: stats.totalDiseases || 0,
      fungal: stats.genesByResistanceType?.fungal || 0, // Mapping might be approx
      bacterial: stats.genesByResistanceType?.bacterial || 0,
      viral: stats.genesByResistanceType?.viral || 0,
      highSeverity: 0, // Not provided by API yet
    };
  } catch {
    return { total: 0, fungal: 0, bacterial: 0, viral: 0, highSeverity: 0 };
  }
}

function calculateDiseaseStats(diseases: Disease[]): DiseaseStats {
  return {
    total: diseases.length,
    fungal: diseases.filter(d => (d.pathogenType || d.pathogen_type || d.disease_type)?.toLowerCase() === 'fungal').length,
    bacterial: diseases.filter(d => (d.pathogenType || d.pathogen_type || d.disease_type)?.toLowerCase() === 'bacterial').length,
    viral: diseases.filter(d => (d.pathogenType || d.pathogen_type || d.disease_type)?.toLowerCase() === 'viral').length,
    highSeverity: diseases.filter(d => d.severity === 'high').length,
  }
}

export function DiseaseAtlas() {
  const [activeTab, setActiveTab] = useState('browse')
  const [selectedCrop, setSelectedCrop] = useState('all')
  const [selectedPathogen, setSelectedPathogen] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDisease, setSelectedDisease] = useState<Disease | null>(null)

  // Fetch diseases
  const { data: diseases = [], isLoading: diseasesLoading, error: diseasesError } = useQuery({
    queryKey: ['diseases', selectedCrop, selectedPathogen],
    queryFn: () => fetchDiseases(selectedCrop, selectedPathogen),
    staleTime: 1000 * 60 * 10, // 10 minutes
  })

  // Fetch stats
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['disease-stats'],
    queryFn: fetchDiseaseStats,
    staleTime: 1000 * 60 * 30, // 30 minutes
  })

  // Filter diseases by search query
  const filteredDiseases = useMemo(() => diseases.filter(d => {
    if (searchQuery && !d.name.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  }), [diseases, searchQuery])

  const displayStats = stats || calculateDiseaseStats(diseases)
  const hasNoLiveRecords = !diseasesLoading && diseases.length === 0

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

      {(diseasesError || (statsError && diseases.length === 0)) && (
        <Alert>
          <AlertDescription>
            Live disease registry data is unavailable right now. The atlas is showing only records returned by the API and will remain empty until the service responds.
          </AlertDescription>
        </Alert>
      )}

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
              {filteredDiseases.map((disease) => (
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

          {!diseasesLoading && filteredDiseases.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">
                  {hasNoLiveRecords
                    ? 'No live disease records are currently available for this organization.'
                    : 'No diseases found matching your criteria.'}
                </p>
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
                    {filteredDiseases.map((d) => (
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
  getSeverityBadge: (severity?: string) => React.ReactNode
  getPathogenBadge: (type?: string) => React.ReactNode
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
