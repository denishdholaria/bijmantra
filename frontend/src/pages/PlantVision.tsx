/**
 * Plant Vision AI Page
 * AI-powered plant phenotyping using computer vision
 */
import { useState, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { 
  plantVision, 
  DiseaseDetection, 
  GrowthStageResult, 
  StressDetection, 
  TraitMeasurement,
  PlantCount 
} from '@/lib/plant-vision'

export function PlantVision() {
  const [activeTab, setActiveTab] = useState('capture')
  const [selectedCrop, setSelectedCrop] = useState('rice')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const [analysisResults, setAnalysisResults] = useState<{
    diseases: DiseaseDetection[]
    growthStage: GrowthStageResult | null
    stress: StressDetection | null
    traits: TraitMeasurement[]
    plantCount: PlantCount | null
  } | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [cameraActive, setCameraActive] = useState(false)

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment', width: 1280, height: 720 } 
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setCameraActive(true)
      }
    } catch (err) {
      console.error('Camera access denied:', err)
      alert('Camera access denied. Please allow camera access or upload an image.')
    }
  }

  // Stop camera
  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
      tracks.forEach(track => track.stop())
      videoRef.current.srcObject = null
      setCameraActive(false)
    }
  }

  // Capture from camera
  const captureFromCamera = () => {
    if (videoRef.current && canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d')
      canvasRef.current.width = videoRef.current.videoWidth
      canvasRef.current.height = videoRef.current.videoHeight
      ctx?.drawImage(videoRef.current, 0, 0)
      const imageUrl = canvasRef.current.toDataURL('image/jpeg')
      setCapturedImage(imageUrl)
      stopCamera()
      analyzeImage(canvasRef.current)
    }
  }

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const imageUrl = event.target?.result as string
        setCapturedImage(imageUrl)
        
        // Create image element for analysis
        const img = new Image()
        img.onload = () => analyzeImage(img)
        img.src = imageUrl
      }
      reader.readAsDataURL(file)
    }
  }

  // Analyze image
  const analyzeImage = async (imageSource: HTMLImageElement | HTMLCanvasElement) => {
    setIsAnalyzing(true)
    setActiveTab('results')

    try {
      // Get image data
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      canvas.width = imageSource.width || 640
      canvas.height = imageSource.height || 480
      ctx?.drawImage(imageSource, 0, 0, canvas.width, canvas.height)
      const imageData = ctx?.getImageData(0, 0, canvas.width, canvas.height)

      if (imageData) {
        // Run all analyses in parallel
        const [diseases, growthStage, stress, traits, plantCount] = await Promise.all([
          plantVision.detectDisease(imageData, selectedCrop),
          plantVision.detectGrowthStage(imageData, selectedCrop),
          plantVision.detectStress(imageData),
          plantVision.measureTraits(imageData),
          plantVision.countPlants(imageData),
        ])

        setAnalysisResults({ diseases, growthStage, stress, traits, plantCount })
      }
    } catch (err) {
      console.error('Analysis failed:', err)
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Reset analysis
  const resetAnalysis = () => {
    setCapturedImage(null)
    setAnalysisResults(null)
    setActiveTab('capture')
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-700'
      case 'medium': return 'bg-yellow-100 text-yellow-700'
      case 'low': return 'bg-green-100 text-green-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">🌿 Plant Vision AI</h1>
          <p className="text-muted-foreground mt-1">AI-powered plant phenotyping and disease detection</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedCrop} onValueChange={setSelectedCrop}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="rice">🌾 Rice</SelectItem>
              <SelectItem value="wheat">🌾 Wheat</SelectItem>
              <SelectItem value="maize">🌽 Maize</SelectItem>
            </SelectContent>
          </Select>
          {capturedImage && (
            <Button variant="outline" onClick={resetAnalysis}>🔄 New Analysis</Button>
          )}
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { icon: '🦠', label: 'Disease Detection', desc: 'Identify plant diseases' },
          { icon: '📈', label: 'Growth Stage', desc: 'BBCH stage classification' },
          { icon: '⚠️', label: 'Stress Detection', desc: 'Drought, nutrient, heat' },
          { icon: '📏', label: 'Trait Measurement', desc: 'LAI, chlorophyll, coverage' },
          { icon: '🔢', label: 'Plant Counting', desc: 'Stand establishment' },
        ].map((feature) => (
          <Card key={feature.label} className="text-center">
            <CardContent className="pt-4">
              <span className="text-2xl">{feature.icon}</span>
              <p className="font-medium text-sm mt-1">{feature.label}</p>
              <p className="text-xs text-muted-foreground">{feature.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="capture">📷 Capture</TabsTrigger>
          <TabsTrigger value="results" disabled={!analysisResults}>📊 Results</TabsTrigger>
          <TabsTrigger value="diseases" disabled={!analysisResults}>🦠 Diseases</TabsTrigger>
          <TabsTrigger value="traits" disabled={!analysisResults}>📏 Traits</TabsTrigger>
          <TabsTrigger value="history">📜 History</TabsTrigger>
        </TabsList>

        <TabsContent value="capture" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Camera Capture */}
            <Card>
              <CardHeader>
                <CardTitle>📷 Camera Capture</CardTitle>
                <CardDescription>Take a photo of your plant</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="aspect-video bg-muted rounded-lg overflow-hidden relative">
                  {cameraActive ? (
                    <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                  ) : capturedImage ? (
                    <img src={capturedImage} alt="Captured" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <span className="text-4xl">📷</span>
                    </div>
                  )}
                  {isAnalyzing && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                      <div className="text-white text-center">
                        <div className="animate-spin text-4xl mb-2">🔄</div>
                        <p>Analyzing...</p>
                      </div>
                    </div>
                  )}
                </div>
                <canvas ref={canvasRef} className="hidden" />
                <div className="flex gap-2">
                  {!cameraActive ? (
                    <Button onClick={startCamera} className="flex-1">📷 Start Camera</Button>
                  ) : (
                    <>
                      <Button onClick={captureFromCamera} className="flex-1">📸 Capture</Button>
                      <Button variant="outline" onClick={stopCamera}>✕ Stop</Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* File Upload */}
            <Card>
              <CardHeader>
                <CardTitle>📁 Upload Image</CardTitle>
                <CardDescription>Upload an existing plant photo</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div 
                  className="aspect-video bg-muted rounded-lg border-2 border-dashed border-muted-foreground/30 flex items-center justify-center cursor-pointer hover:border-primary transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="text-center">
                    <span className="text-4xl">📤</span>
                    <p className="mt-2 text-sm text-muted-foreground">Click to upload or drag & drop</p>
                    <p className="text-xs text-muted-foreground">JPG, PNG up to 10MB</p>
                  </div>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <Button variant="outline" className="w-full" onClick={() => fileInputRef.current?.click()}>
                  📁 Choose File
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Tips */}
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-800">💡 Tips for Best Results</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 space-y-1">
              <p>• Take photos in good lighting conditions (natural daylight preferred)</p>
              <p>• Focus on the affected area for disease detection</p>
              <p>• Include the whole plant for growth stage classification</p>
              <p>• Use overhead shots for plant counting and canopy coverage</p>
              <p>• Avoid shadows and reflections on leaves</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-6 mt-4">
          {analysisResults && (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className={analysisResults.diseases[0]?.confidence > 0.5 ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}>
                  <CardContent className="pt-4 text-center">
                    <span className="text-3xl">{analysisResults.diseases[0]?.confidence > 0.5 ? '🦠' : '✅'}</span>
                    <p className="font-bold mt-1">
                      {analysisResults.diseases[0]?.confidence > 0.5 ? analysisResults.diseases[0].disease : 'Healthy'}
                    </p>
                    <p className="text-xs text-muted-foreground">Disease Status</p>
                  </CardContent>
                </Card>

                <Card className="border-blue-200 bg-blue-50">
                  <CardContent className="pt-4 text-center">
                    <span className="text-3xl">🌱</span>
                    <p className="font-bold mt-1">{analysisResults.growthStage?.stage}</p>
                    <p className="text-xs text-muted-foreground">{analysisResults.growthStage?.stageCode}</p>
                  </CardContent>
                </Card>

                <Card className={analysisResults.stress?.stressType !== 'none' ? 'border-yellow-200 bg-yellow-50' : 'border-green-200 bg-green-50'}>
                  <CardContent className="pt-4 text-center">
                    <span className="text-3xl">{analysisResults.stress?.stressType !== 'none' ? '⚠️' : '💚'}</span>
                    <p className="font-bold mt-1">
                      {analysisResults.stress?.stressType !== 'none' 
                        ? `${analysisResults.stress?.stressType} Stress` 
                        : 'No Stress'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {analysisResults.stress?.severity}% severity
                    </p>
                  </CardContent>
                </Card>

                <Card className="border-purple-200 bg-purple-50">
                  <CardContent className="pt-4 text-center">
                    <span className="text-3xl">🌿</span>
                    <p className="font-bold mt-1">{analysisResults.plantCount?.standEstablishment}%</p>
                    <p className="text-xs text-muted-foreground">Stand Establishment</p>
                  </CardContent>
                </Card>
              </div>

              {/* Captured Image with Analysis */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Analyzed Image</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {capturedImage && (
                      <img src={capturedImage} alt="Analyzed" className="w-full rounded-lg" />
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Key Findings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Growth Stage */}
                    <div className="p-3 bg-muted rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Growth Stage</span>
                        <Badge>{analysisResults.growthStage?.stage}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        ~{analysisResults.growthStage?.daysEstimate} days from sowing
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Next: {analysisResults.growthStage?.nextStage} in ~{analysisResults.growthStage?.daysToNextStage} days
                      </p>
                    </div>

                    {/* Stress */}
                    {analysisResults.stress && (
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">Stress Level</span>
                          <Badge className={analysisResults.stress.stressType !== 'none' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}>
                            {analysisResults.stress.stressType !== 'none' ? analysisResults.stress.stressType : 'None'}
                          </Badge>
                        </div>
                        {analysisResults.stress.indicators.length > 0 && (
                          <ul className="text-sm text-muted-foreground mt-1 list-disc list-inside">
                            {analysisResults.stress.indicators.slice(0, 3).map((ind, i) => (
                              <li key={i}>{ind}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}

                    {/* Top Traits */}
                    <div className="p-3 bg-muted rounded-lg">
                      <span className="font-medium">Key Measurements</span>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        {analysisResults.traits.slice(0, 4).map((trait) => (
                          <div key={trait.trait} className="text-sm">
                            <span className="text-muted-foreground">{trait.trait}:</span>
                            <span className="font-bold ml-1">{trait.value} {trait.unit}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Recommendations */}
              {analysisResults.stress?.recommendations && analysisResults.stress.recommendations.length > 0 && (
                <Card className="border-green-200 bg-green-50">
                  <CardHeader>
                    <CardTitle className="text-green-800">💡 Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {analysisResults.stress.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2 text-green-700">
                          <span>✓</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="diseases" className="space-y-6 mt-4">
          {analysisResults?.diseases && (
            <Card>
              <CardHeader>
                <CardTitle>Disease Detection Results</CardTitle>
                <CardDescription>Potential diseases ranked by confidence</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analysisResults.diseases.map((disease, i) => (
                    <div key={i} className={`p-4 border rounded-lg ${disease.confidence > 0.5 ? 'border-red-200 bg-red-50' : ''}`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">#{i + 1}</Badge>
                          <h4 className="font-bold">{disease.disease}</h4>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={getSeverityColor(disease.severity)}>{disease.severity}</Badge>
                          <span className={`font-bold ${getConfidenceColor(disease.confidence)}`}>
                            {(disease.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <Progress value={disease.confidence * 100} className="h-2 mb-3" />
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="font-medium text-muted-foreground">Symptoms:</p>
                          <ul className="list-disc list-inside">
                            {disease.symptoms.map((s, j) => <li key={j}>{s}</li>)}
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-muted-foreground">Treatment:</p>
                          <ul className="list-disc list-inside">
                            {disease.treatment.map((t, j) => <li key={j}>{t}</li>)}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="traits" className="space-y-6 mt-4">
          {analysisResults?.traits && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Trait Measurements</CardTitle>
                  <CardDescription>Automated phenotypic measurements</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {analysisResults.traits.map((trait) => (
                      <div key={trait.trait} className="flex items-center gap-4">
                        <div className="w-40">
                          <p className="font-medium">{trait.trait}</p>
                          <p className="text-xs text-muted-foreground">{trait.method}</p>
                        </div>
                        <div className="flex-1">
                          <Progress value={trait.confidence * 100} className="h-3" />
                        </div>
                        <div className="w-24 text-right">
                          <p className="font-bold">{trait.value} {trait.unit}</p>
                          <p className="text-xs text-muted-foreground">{(trait.confidence * 100).toFixed(0)}% conf</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {analysisResults.plantCount && (
                <Card>
                  <CardHeader>
                    <CardTitle>Plant Count Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <p className="text-2xl font-bold">{analysisResults.plantCount.totalPlants}</p>
                        <p className="text-xs text-muted-foreground">Total Plants</p>
                      </div>
                      <div className="text-center p-3 bg-green-50 rounded-lg">
                        <p className="text-2xl font-bold text-green-600">{analysisResults.plantCount.healthyPlants}</p>
                        <p className="text-xs text-muted-foreground">Healthy</p>
                      </div>
                      <div className="text-center p-3 bg-yellow-50 rounded-lg">
                        <p className="text-2xl font-bold text-yellow-600">{analysisResults.plantCount.stressedPlants}</p>
                        <p className="text-xs text-muted-foreground">Stressed</p>
                      </div>
                      <div className="text-center p-3 bg-red-50 rounded-lg">
                        <p className="text-2xl font-bold text-red-600">{analysisResults.plantCount.missingSpots}</p>
                        <p className="text-xs text-muted-foreground">Missing</p>
                      </div>
                      <div className="text-center p-3 bg-blue-50 rounded-lg">
                        <p className="text-2xl font-bold text-blue-600">{analysisResults.plantCount.standEstablishment}%</p>
                        <p className="text-xs text-muted-foreground">Stand Est.</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Analysis History</CardTitle>
              <CardDescription>Previous plant analyses (stored locally)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <span className="text-4xl">📜</span>
                <p className="mt-2">No previous analyses</p>
                <p className="text-sm">Your analysis history will appear here</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
