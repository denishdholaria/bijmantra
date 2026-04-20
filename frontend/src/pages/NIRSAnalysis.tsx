import { useRef, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2, Upload, FileBarChart, Zap, Download } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { Link } from 'react-router-dom'

interface NIRSModel {
  id: string;
  name: string;
  target_trait: string;
  r_squared?: number;
  status?: string;
}

interface PredictionResult {
  id: string;
  trait: string;
  value: number;
  unit: string;
  confidence: number;
}

interface UploadReceipt {
  dataset_id: string;
  filename: string;
  size_bytes: number;
  status: string;
  message: string;
}

interface PredictionStatus {
  model_id: string;
  model_name?: string;
  target_trait?: string;
  sample_count?: number;
  status?: string;
  message?: string;
  timestamp?: string;
  predictions?: PredictionResult[];
}

export function NIRSAnalysis() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedDevice, setSelectedDevice] = useState<string>('dev-01')
  const [predictionResults, setPredictionResults] = useState<PredictionResult[] | null>(null)
  const [uploadReceipt, setUploadReceipt] = useState<UploadReceipt | null>(null)
  const [predictionStatus, setPredictionStatus] = useState<PredictionStatus | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Fetch Models
  const { data: modelsData = [], isLoading: modelsLoading } = useQuery<NIRSModel[]>({
    queryKey: ['nirs-models'],
    queryFn: () => apiClient.phenomicSelectionService.getModels({ status: 'deployed' })
  })

  // Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.phenomicSelectionService.uploadSpectralData(file, undefined, undefined, 'NIRS'),
    onSuccess: (data) => {
      setUploadReceipt(data)
      setPredictionStatus(null)
      setPredictionResults(null)
      toast.success('Spectral data uploaded successfully')
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
      const predictions = Array.isArray(data?.predictions) ? data.predictions as PredictionResult[] : null
      setPredictionResults(predictions)
      setPredictionStatus(data)
      toast.success(predictions?.length ? 'Prediction completed' : 'Prediction request accepted')
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
    if (selectedModel && uploadReceipt) {
      predictMutation.mutate({
        modelId: selectedModel,
        sampleIds: [uploadReceipt.dataset_id]
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
                {modelsLoading ? (
                  <div className="flex justify-center p-4"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
                ) : modelsData.map((model) => (
                  <div key={model.id} className="flex justify-between items-center p-3 border rounded-md">
                    <div>
                      <p className="font-medium">{model.name}</p>
                      <p className="text-xs text-muted-foreground">{model.target_trait} (R²={model.r_squared})</p>
                    </div>
                    <Badge variant="outline" className="bg-green-50 text-green-700">Ready</Badge>
                  </div>
                ))}
                {!modelsLoading && !modelsData.length && (
                  <Alert>
                    <AlertTitle>No deployed NIRS models</AlertTitle>
                    <AlertDescription>
                      Trait prediction is unavailable until a deployed phenomic model is registered for this organization.
                    </AlertDescription>
                  </Alert>
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
              <CardDescription>Live spectral traces appear only when the backend publishes full spectral payloads.</CardDescription>
            </CardHeader>
            <CardContent>
              {uploadReceipt ? (
                <div className="space-y-4">
                  <Alert>
                    <AlertTitle>Metadata registered</AlertTitle>
                    <AlertDescription>
                      {uploadReceipt.message}
                    </AlertDescription>
                  </Alert>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="rounded-lg border p-4">
                      <p className="text-muted-foreground mb-1">Dataset ID</p>
                      <p className="font-medium">{uploadReceipt.dataset_id}</p>
                    </div>
                    <div className="rounded-lg border p-4">
                      <p className="text-muted-foreground mb-1">Upload Status</p>
                      <p className="font-medium capitalize">{uploadReceipt.status}</p>
                    </div>
                    <div className="rounded-lg border p-4">
                      <p className="text-muted-foreground mb-1">Filename</p>
                      <p className="font-medium">{uploadReceipt.filename}</p>
                    </div>
                    <div className="rounded-lg border p-4">
                      <p className="text-muted-foreground mb-1">Payload Size</p>
                      <p className="font-medium">{uploadReceipt.size_bytes.toLocaleString()} bytes</p>
                    </div>
                  </div>
                </div>
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
                      {modelsData.map((m) => (
                        <SelectItem key={m.id} value={m.id}>{m.name} ({m.target_trait})</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handlePredict} disabled={!selectedModel || !uploadReceipt || predictMutation.isPending}>
                  {predictMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <Zap className="mr-2 h-4 w-4" /> Predict Traits
                </Button>
              </div>

              {!uploadReceipt && (
                <Alert className="mb-6">
                  <AlertDescription>
                    Upload a spectral file first. Prediction requests are issued only against registered upload jobs.
                  </AlertDescription>
                </Alert>
              )}

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

              {predictionStatus && !predictionResults && (
                <Alert>
                  <AlertTitle>{predictionStatus.status === 'pending' ? 'Prediction queued' : 'Prediction status updated'}</AlertTitle>
                  <AlertDescription>
                    {predictionStatus.message || 'The backend acknowledged the request but did not return trait values yet.'}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
