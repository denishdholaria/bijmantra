/**
 * Field Scanner Page
 * Real-time field scanning and plot-level analysis
 */
import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { plantVision, PlantAnalysisResult } from '@/lib/plant-vision'

interface ScanResult {
  id: string
  timestamp: Date
  plotId: string
  location: { lat: number; lng: number } | null
  results: PlantAnalysisResult[]
  thumbnail: string
  notes: string
}

export function FieldScanner() {
  const [activeTab, setActiveTab] = useState('scan')
  const [isScanning, setIsScanning] = useState(false)
  const [scanMode, setScanMode] = useState<'single' | 'continuous'>('single')
  const [scanResults, setScanResults] = useState<ScanResult[]>([])
  const [currentResults, setCurrentResults] = useState<PlantAnalysisResult[]>([])
  const [plotId, setPlotId] = useState('')
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const scanIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment', width: 1280, height: 720 } 
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    } catch (err) {
      console.error('Camera access denied:', err)
      alert('Camera access required for field scanning')
    }
  }

  // Stop camera
  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
      tracks.forEach(track => track.stop())
      videoRef.current.srcObject = null
    }
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current)
      scanIntervalRef.current = null
    }
    setIsScanning(false)
  }

  // Start scanning
  const startScanning = async () => {
    await startCamera()
    setIsScanning(true)

    if (scanMode === 'continuous') {
      // Continuous scanning every 2 seconds
      scanIntervalRef.current = setInterval(async () => {
        await performScan()
      }, 2000)
    }
  }

  // Perform single scan
  const performScan = async () => {
    if (!videoRef.current || !canvasRef.current) return

    const ctx = canvasRef.current.getContext('2d')
    canvasRef.current.width = videoRef.current.videoWidth || 640
    canvasRef.current.height = videoRef.current.videoHeight || 480
    ctx?.drawImage(videoRef.current, 0, 0)

    const results = await plantVision.processVideoFrame(videoRef.current)
    setCurrentResults(results)

    // Save scan result
    const thumbnail = canvasRef.current.toDataURL('image/jpeg', 0.5)
    const scanResult: ScanResult = {
      id: `scan-${Date.now()}`,
      timestamp: new Date(),
      plotId: plotId || `Plot-${scanResults.length + 1}`,
      location: null, // Would use geolocation API
      results,
      thumbnail,
      notes: '',
    }
    setScanResults(prev => [scanResult, ...prev])

    if (scanMode === 'single') {
      stopCamera()
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => stopCamera()
  }, [])

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'disease': return '🦠'
      case 'stress': return '⚠️'
      case 'trait': return '📏'
      case 'growth_stage': return '🌱'
      default: return '📊'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500'
    if (confidence >= 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">📱 Field Scanner</h1>
          <p className="text-muted-foreground mt-1">Real-time field scanning and plot analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={scanMode} onValueChange={(v) => setScanMode(v as 'single' | 'continuous')}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="single">Single Scan</SelectItem>
              <SelectItem value="continuous">Continuous</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{scanResults.length}</p>
            <p className="text-sm text-muted-foreground">Scans Today</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">
              {scanResults.filter(s => !s.results.some(r => r.type === 'disease' && r.confidence > 0.5)).length}
            </p>
            <p className="text-sm text-muted-foreground">Healthy Plots</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-red-600">
              {scanResults.filter(s => s.results.some(r => r.type === 'disease' && r.confidence > 0.5)).length}
            </p>
            <p className="text-sm text-muted-foreground">Issues Found</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">
              {new Set(scanResults.map(s => s.plotId)).size}
            </p>
            <p className="text-sm text-muted-foreground">Plots Scanned</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="scan">📷 Scan</TabsTrigger>
          <TabsTrigger value="results">📊 Results ({scanResults.length})</TabsTrigger>
          <TabsTrigger value="map">🗺️ Field Map</TabsTrigger>
          <TabsTrigger value="export">📤 Export</TabsTrigger>
        </TabsList>

        <TabsContent value="scan" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Scanner View */}
            <Card>
              <CardHeader>
                <CardTitle>Scanner View</CardTitle>
                <CardDescription>Point camera at plants to analyze</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="aspect-video bg-black rounded-lg overflow-hidden relative">
                  <video 
                    ref={videoRef} 
                    autoPlay 
                    playsInline 
                    className="w-full h-full object-cover"
                  />
                  {isScanning && (
                    <div className="absolute top-2 right-2">
                      <Badge className="bg-red-500 text-white animate-pulse">● LIVE</Badge>
                    </div>
                  )}
                  {isScanning && scanMode === 'continuous' && (
                    <div className="absolute bottom-2 left-2 right-2">
                      <Progress value={100} className="h-1 animate-pulse" />
                    </div>
                  )}
                </div>
                <canvas ref={canvasRef} className="hidden" />
                
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Plot ID (optional)"
                    value={plotId}
                    onChange={(e) => setPlotId(e.target.value)}
                    className="flex-1 px-3 py-2 border rounded-md text-sm"
                  />
                </div>

                <div className="flex gap-2">
                  {!isScanning ? (
                    <Button onClick={startScanning} className="flex-1">
                      📷 Start {scanMode === 'continuous' ? 'Continuous ' : ''}Scanning
                    </Button>
                  ) : (
                    <>
                      {scanMode === 'single' && (
                        <Button onClick={performScan} className="flex-1">📸 Capture & Analyze</Button>
                      )}
                      <Button variant="destructive" onClick={stopCamera}>⏹ Stop</Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Live Results */}
            <Card>
              <CardHeader>
                <CardTitle>Live Analysis</CardTitle>
                <CardDescription>Real-time detection results</CardDescription>
              </CardHeader>
              <CardContent>
                {currentResults.length > 0 ? (
                  <div className="space-y-3">
                    {currentResults.map((result, i) => (
                      <div key={i} className="p-3 bg-muted rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{getResultIcon(result.type)}</span>
                            <span className="font-medium">{result.label}</span>
                          </div>
                          <Badge className={`${getConfidenceColor(result.confidence)} text-white`}>
                            {(result.confidence * 100).toFixed(0)}%
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{result.description}</p>
                        {result.recommendations && result.recommendations.length > 0 && (
                          <div className="mt-2 text-xs">
                            <span className="text-green-600">💡 {result.recommendations[0]}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <span className="text-4xl">📷</span>
                    <p className="mt-2">Start scanning to see results</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Tips */}
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="pt-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">💡</span>
                <div className="text-sm text-blue-700">
                  <p className="font-medium mb-1">Scanning Tips:</p>
                  <ul className="space-y-1">
                    <li>• Hold camera steady at 30-50cm from plants</li>
                    <li>• Ensure good lighting (avoid harsh shadows)</li>
                    <li>• Focus on symptomatic areas for disease detection</li>
                    <li>• Use continuous mode for rapid plot surveys</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Scan History</CardTitle>
              <CardDescription>All scans from this session</CardDescription>
            </CardHeader>
            <CardContent>
              {scanResults.length > 0 ? (
                <div className="space-y-4">
                  {scanResults.map((scan) => (
                    <div key={scan.id} className="flex gap-4 p-4 border rounded-lg">
                      <img 
                        src={scan.thumbnail} 
                        alt={scan.plotId}
                        className="w-24 h-24 object-cover rounded"
                      />
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-bold">{scan.plotId}</h4>
                          <span className="text-xs text-muted-foreground">
                            {scan.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {scan.results.map((r, i) => (
                            <Badge key={i} variant="outline" className="text-xs">
                              {getResultIcon(r.type)} {r.label}
                            </Badge>
                          ))}
                        </div>
                        {scan.results.some(r => r.type === 'disease' && r.confidence > 0.5) && (
                          <Badge className="mt-2 bg-red-100 text-red-700">⚠️ Issue Detected</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <span className="text-4xl">📋</span>
                  <p className="mt-2">No scans yet</p>
                  <p className="text-sm">Start scanning to collect data</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="map" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Field Map</CardTitle>
              <CardDescription>Spatial view of scan locations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">🗺️</span>
                  <p className="mt-2 text-muted-foreground">Field Map View</p>
                  <p className="text-xs text-muted-foreground">GPS-tagged scans will appear here</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="export" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Export Data</CardTitle>
              <CardDescription>Download scan results</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button variant="outline" className="h-20">
                  <div className="text-center">
                    <span className="text-2xl">📊</span>
                    <p className="text-sm mt-1">Export CSV</p>
                  </div>
                </Button>
                <Button variant="outline" className="h-20">
                  <div className="text-center">
                    <span className="text-2xl">📋</span>
                    <p className="text-sm mt-1">Export PDF Report</p>
                  </div>
                </Button>
                <Button variant="outline" className="h-20">
                  <div className="text-center">
                    <span className="text-2xl">🖼️</span>
                    <p className="text-sm mt-1">Export Images</p>
                  </div>
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                {scanResults.length} scans ready for export
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
