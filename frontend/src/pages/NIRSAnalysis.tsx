import { useState, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import ReactECharts from 'echarts-for-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2, Upload, FileBarChart, Zap, CheckCircle2, AlertTriangle, Download, HardDrive } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { Link } from 'react-router-dom'

export function NIRSAnalysis() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedDevice, setSelectedDevice] = useState<string>('dev-01')
  const [predictionResults, setPredictionResults] = useState<any[] | null>(null)
  const [spectralData, setSpectralData] = useState<any>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Fetch Models
  const { data: modelsData } = useQuery({
    queryKey: ['nirs-models'],
    queryFn: () => apiClient.phenomicSelectionService.getModels({ status: 'deployed' })
  })

  // Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.phenomicSelectionService.uploadSpectralData(file, undefined, undefined, 'NIRS'),
    onSuccess: (data) => {
      toast.success('Spectral data uploaded successfully')
      // Simulate spectral data for visualization since backend returns simulated response
      generateMockSpectralData()
    },
    onError: (err) => {
      toast.error('Failed to upload file')
      console.error(err)
    }
  })

  // Predict Mutation
  const predictMutation = useMutation({
    mutationFn: (data: { modelId: string, sampleIds: string[] }) =>
      apiClient.phenomicSelectionService.predictTraits(data.modelId, data.sampleIds),
    onSuccess: (data) => {
      toast.success('Prediction completed')
      // Simulate results
      setPredictionResults([
        { id: 'S-001', trait: 'Protein', value: 12.5, unit: '%', confidence: 0.95 },
        { id: 'S-002', trait: 'Protein', value: 11.8, unit: '%', confidence: 0.92 },
        { id: 'S-003', trait: 'Protein', value: 13.1, unit: '%', confidence: 0.96 },
        { id: 'S-004', trait: 'Protein', value: 12.2, unit: '%', confidence: 0.94 },
        { id: 'S-005', trait: 'Protein', value: 11.5, unit: '%', confidence: 0.91 },
      ])
    }
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile)
    }
  }

  const handlePredict = () => {
    if (selectedModel) {
      predictMutation.mutate({
        modelId: selectedModel,
        sampleIds: ['S-001', 'S-002', 'S-003', 'S-004', 'S-005']
      })
    }
  }

  const handleExport = () => {
    if (!predictionResults) return

    const csvContent = "data:text/csv;charset=utf-8,"
      + "Sample ID,Trait,Value,Unit,Confidence\n"
      + predictionResults.map(r => `${r.id},${r.trait},${r.value},${r.unit},${r.confidence}`).join("\n")

    const encodedUri = encodeURI(csvContent)
    const link = document.createElement("a")
    link.setAttribute("href", encodedUri)
    link.setAttribute("download", "nirs_predictions.csv")
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const generateMockSpectralData = () => {
    const wavelengths = Array.from({ length: 100 }, (_, i) => 400 + i * 10)
    const samples = Array.from({ length: 5 }, (_, s) => ({
      name: `Sample ${s+1}`,
      data: wavelengths.map(w => Math.sin(w/100) * 0.5 + Math.random() * 0.1 + s * 0.1)
    }))

    setSpectralData({ wavelengths, samples })
  }

  const getChartOption = () => {
    if (!spectralData) return {}

    return {
      title: { text: 'Spectral Absorbance' },
      tooltip: { trigger: 'axis' },
      legend: { data: spectralData.samples.map((s: any) => s.name) },
      xAxis: { type: 'category', data: spectralData.wavelengths, name: 'Wavelength (nm)' },
      yAxis: { type: 'value', name: 'Absorbance' },
      series: spectralData.samples.map((s: any) => ({
        name: s.name,
        type: 'line',
        data: s.data,
        smooth: true,
        showSymbol: false
      })),
      dataZoom: [{ type: 'inside' }, { type: 'slider' }]
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileBarChart className="h-7 w-7 text-primary" />
            NIRS Analysis
          </h1>
          <p className="text-muted-foreground">Spectral data processing and trait prediction</p>
        </div>
        <Button variant="outline"><Download className="h-4 w-4 mr-2" />Download Template</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Upload & Calibration */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Data Upload</CardTitle>
              <CardDescription>Upload .dx, .spc, or .csv files</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Select Device</Label>
                <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dev-01">NIRS-DS2500 (Lab 1)</SelectItem>
                    <SelectItem value="dev-02">NIRS-DA1650 (Field)</SelectItem>
                    <SelectItem value="dev-03">SpectraStar-XT (Lab 2)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center hover:bg-muted/50 transition-colors cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                <Upload className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-sm font-medium">Click to upload or drag and drop</p>
                <p className="text-xs text-muted-foreground">Supported: JCAMP-DX, SPC, CSV</p>
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  accept=".csv,.dx,.spc"
                  onChange={handleFileChange}
                />
              </div>

              {selectedFile && (
                <div className="flex items-center justify-between p-3 bg-muted rounded-md text-sm">
                  <span className="truncate max-w-[200px]">{selectedFile.name}</span>
                  <Button size="sm" onClick={handleUpload} disabled={uploadMutation.isPending}>
                    {uploadMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Upload
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Calibration Status</CardTitle>
              <CardDescription>Available prediction models</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {modelsData?.map((model: any) => (
                  <div key={model.id} className="flex justify-between items-center p-3 border rounded-md">
                    <div>
                      <p className="font-medium">{model.name}</p>
                      <p className="text-xs text-muted-foreground">{model.target_trait} (R²={model.r_squared})</p>
                    </div>
                    <Badge variant="outline" className="bg-green-50 text-green-700">Ready</Badge>
                  </div>
                ))}
                {!modelsData?.length && (
                  <div className="text-center p-4 text-muted-foreground text-sm">No models deployed.</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Visualization & Prediction */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Spectral Visualization</CardTitle>
            </CardHeader>
            <CardContent>
              {spectralData ? (
                <ReactECharts option={getChartOption()} style={{ height: '400px' }} />
              ) : (
                <div className="h-[400px] flex items-center justify-center bg-muted/20 rounded-lg text-muted-foreground">
                  Upload data to view spectra
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Trait Prediction</CardTitle>
              <CardDescription>Apply calibration models to uploaded spectra</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-4 mb-6">
                <div className="flex-1 space-y-2">
                  <Label>Select Model</Label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose a model..." />
                    </SelectTrigger>
                    <SelectContent>
                      {modelsData?.map((m: any) => (
                        <SelectItem key={m.id} value={m.id}>{m.name} ({m.target_trait})</SelectItem>
                      ))}
                      {/* Fallback for demo if no data */}
                      {!modelsData?.length && <SelectItem value="demo-model">Wheat Protein (PLSR)</SelectItem>}
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handlePredict} disabled={!selectedModel || !spectralData || predictMutation.isPending}>
                  {predictMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <Zap className="mr-2 h-4 w-4" /> Predict Traits
                </Button>
              </div>

              {predictionResults && (
                <div className="space-y-4">
                  <div className="flex justify-end">
                    <Button variant="outline" size="sm" onClick={handleExport}>
                      <Download className="h-4 w-4 mr-2" /> Export CSV
                    </Button>
                  </div>
                  <div className="border rounded-md">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Sample ID</TableHead>
                          <TableHead>Trait</TableHead>
                          <TableHead>Predicted Value</TableHead>
                          <TableHead>Confidence</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {predictionResults.map((res, i) => (
                          <TableRow key={i}>
                            <TableCell className="font-medium">
                              <Link to={`/samples/${res.id}`} className="hover:underline text-primary">
                                {res.id}
                              </Link>
                            </TableCell>
                            <TableCell>{res.trait}</TableCell>
                            <TableCell>{res.value} {res.unit}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                                  <div className="h-full bg-green-500" style={{ width: `${res.confidence * 100}%` }} />
                                </div>
                                <span className="text-xs text-muted-foreground">{(res.confidence * 100).toFixed(0)}%</span>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
