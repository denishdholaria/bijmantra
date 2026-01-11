/**
 * Field Scanner Page
 * Real-time field scanning and plot-level analysis
 * Connected to /api/v2/field-scanner endpoints
 */
import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { plantVision, PlantAnalysisResult } from '@/lib/plant-vision';
import { apiClient } from '@/lib/api-client';

interface ScanResult {
  id: string;
  plot_id: string;
  study_id?: string;
  timestamp: string;
  location: { lat: number; lng: number } | null;
  crop: string;
  results: PlantAnalysisResult[];
  thumbnail: string | null;
  notes: string;
  weather?: { temp?: number; humidity?: number; conditions?: string };
}

export function FieldScanner() {
  const [activeTab, setActiveTab] = useState('scan');
  const [isScanning, setIsScanning] = useState(false);
  const [scanMode, setScanMode] = useState<'single' | 'continuous'>('single');
  const [currentResults, setCurrentResults] = useState<PlantAnalysisResult[]>([]);
  const [plotId, setPlotId] = useState('');
  const [selectedCrop, setSelectedCrop] = useState('rice');
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const scanIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const queryClient = useQueryClient();

  // Fetch scan stats
  const { data: stats } = useQuery({
    queryKey: ['field-scanner', 'stats'],
    queryFn: () => apiClient.getFieldScanStats(),
  });

  // Fetch scan history
  const { data: scansData, isLoading: loadingScans } = useQuery({
    queryKey: ['field-scanner', 'scans'],
    queryFn: () => apiClient.getFieldScans({ limit: 50 }),
  });

  // Create scan mutation
  const createScan = useMutation({
    mutationFn: (data: {
      plot_id?: string;
      study_id?: string;
      crop?: string;
      location?: { lat: number; lng: number };
      results?: any[];
      thumbnail?: string;
      notes?: string;
    }) => apiClient.createFieldScan(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['field-scanner'] });
    },
  });

  // Delete scan mutation
  const deleteScan = useMutation({
    mutationFn: (scanId: string) => apiClient.deleteFieldScan(scanId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['field-scanner'] });
    },
  });

  const scanResults: ScanResult[] = scansData?.scans || [];

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment', width: 1280, height: 720 } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error('Camera access denied:', err);
      alert('Camera access required for field scanning');
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    setIsScanning(false);
  };

  // Start scanning
  const startScanning = async () => {
    await startCamera();
    setIsScanning(true);

    if (scanMode === 'continuous') {
      scanIntervalRef.current = setInterval(async () => {
        await performScan();
      }, 2000);
    }
  };

  // Perform single scan
  const performScan = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const ctx = canvasRef.current.getContext('2d');
    canvasRef.current.width = videoRef.current.videoWidth || 640;
    canvasRef.current.height = videoRef.current.videoHeight || 480;
    ctx?.drawImage(videoRef.current, 0, 0);

    const results = await plantVision.processVideoFrame(videoRef.current);
    setCurrentResults(results);

    // Get thumbnail
    const thumbnail = canvasRef.current.toDataURL('image/jpeg', 0.5);
    
    // Get location if available
    let location: { lat: number; lng: number } | null = null;
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
      });
      location = { lat: pos.coords.latitude, lng: pos.coords.longitude };
    } catch {
      // Location not available
    }

    // Save to backend
    createScan.mutate({
      plot_id: plotId || `Plot-${(scansData?.total || 0) + 1}`,
      crop: selectedCrop,
      location: location || undefined,
      results: results.map(r => ({
        type: r.type,
        label: r.label,
        confidence: r.confidence,
        description: r.description,
        value: r.measurements ? Object.values(r.measurements)[0] : undefined,
        unit: r.description?.split(' ').pop(),
      })),
      thumbnail: thumbnail || undefined,
      notes: '',
    });

    if (scanMode === 'single') {
      stopCamera();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => stopCamera();
  }, []);

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'disease': return '🦠';
      case 'stress': return '⚠️';
      case 'trait': return '📏';
      case 'growth_stage': return '🌱';
      default: return '📊';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const data = await apiClient.exportFieldScans(format);
      const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `field-scans-${new Date().toISOString().split('T')[0]}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Field Scanner</h1>
          <p className="text-muted-foreground mt-1">Real-time field scanning and plot analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedCrop} onValueChange={setSelectedCrop}>
            <SelectTrigger className="w-28">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="rice">Rice</SelectItem>
              <SelectItem value="wheat">Wheat</SelectItem>
              <SelectItem value="maize">Maize</SelectItem>
            </SelectContent>
          </Select>
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
            <p className="text-3xl font-bold text-primary">{stats?.total_scans || 0}</p>
            <p className="text-sm text-muted-foreground">Total Scans</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">{stats?.healthy_plots || 0}</p>
            <p className="text-sm text-muted-foreground">Healthy Plots</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-red-600">{stats?.issues_found || 0}</p>
            <p className="text-sm text-muted-foreground">Issues Found</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{stats?.plots_scanned || 0}</p>
            <p className="text-sm text-muted-foreground">Plots Scanned</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="scan">Scan</TabsTrigger>
          <TabsTrigger value="results">Results ({scansData?.total || 0})</TabsTrigger>
          <TabsTrigger value="map">Field Map</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
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
                      Start {scanMode === 'continuous' ? 'Continuous ' : ''}Scanning
                    </Button>
                  ) : (
                    <>
                      {scanMode === 'single' && (
                        <Button onClick={performScan} className="flex-1" disabled={createScan.isPending}>
                          {createScan.isPending ? 'Saving...' : 'Capture & Analyze'}
                        </Button>
                      )}
                      <Button variant="destructive" onClick={stopCamera}>Stop</Button>
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
          <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950/20">
            <CardContent className="pt-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">💡</span>
                <div className="text-sm text-blue-700 dark:text-blue-300">
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
              <CardDescription>All scans saved to database</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingScans ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 w-full" />)}
                </div>
              ) : scanResults.length > 0 ? (
                <div className="space-y-4">
                  {scanResults.map((scan) => (
                    <div key={scan.id} className="flex gap-4 p-4 border rounded-lg">
                      {scan.thumbnail && (
                        <img 
                          src={scan.thumbnail} 
                          alt={scan.plot_id}
                          className="w-24 h-24 object-cover rounded"
                        />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-bold">{scan.plot_id}</h4>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{scan.crop}</Badge>
                            <span className="text-xs text-muted-foreground">
                              {new Date(scan.timestamp).toLocaleString()}
                            </span>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {scan.results.map((r: any, i: number) => (
                            <Badge key={i} variant="outline" className="text-xs">
                              {getResultIcon(r.type)} {r.label}
                            </Badge>
                          ))}
                        </div>
                        {scan.results.some((r: any) => r.type === 'disease' && r.confidence > 0.5) && (
                          <Badge className="mt-2 bg-red-100 text-red-700">⚠️ Issue Detected</Badge>
                        )}
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => deleteScan.mutate(scan.id)}
                        disabled={deleteScan.isPending}
                      >
                        🗑️
                      </Button>
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
              <div className="h-64 bg-muted rounded-lg p-4">
                {scanResults.filter(s => s.location).length > 0 ? (
                  <div className="h-full flex flex-col">
                    <p className="text-sm text-muted-foreground mb-2">
                      {scanResults.filter(s => s.location).length} GPS-tagged scans
                    </p>
                    <div className="flex-1 grid grid-cols-4 gap-2">
                      {scanResults.filter(s => s.location).slice(0, 8).map((scan, i) => (
                        <div key={scan.id} className="p-2 bg-background rounded text-xs">
                          <p className="font-medium">{scan.plot_id}</p>
                          <p className="text-muted-foreground">
                            {scan.location?.lat.toFixed(4)}, {scan.location?.lng.toFixed(4)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <span className="text-4xl">🗺️</span>
                      <p className="mt-2 text-muted-foreground">Field Map View</p>
                      <p className="text-xs text-muted-foreground">GPS-tagged scans will appear here</p>
                    </div>
                  </div>
                )}
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
                <Button variant="outline" className="h-20" onClick={() => handleExport('csv')}>
                  <div className="text-center">
                    <span className="text-2xl">📊</span>
                    <p className="text-sm mt-1">Export CSV</p>
                  </div>
                </Button>
                <Button variant="outline" className="h-20" onClick={() => handleExport('json')}>
                  <div className="text-center">
                    <span className="text-2xl">📋</span>
                    <p className="text-sm mt-1">Export JSON</p>
                  </div>
                </Button>
                <Button variant="outline" className="h-20" disabled>
                  <div className="text-center">
                    <span className="text-2xl">🖼️</span>
                    <p className="text-sm mt-1">Export Images</p>
                  </div>
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                {scansData?.total || 0} scans ready for export
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
