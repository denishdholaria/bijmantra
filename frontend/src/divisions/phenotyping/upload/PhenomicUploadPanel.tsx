/**
 * PhenomicUploadPanel
 * Division-owned UI panel for phenomic data upload
 * Implements all 4 states: loading, empty, error, success
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Upload, FileText, CheckCircle2, AlertTriangle,
  Database, Sparkles, X, FileCheck
} from 'lucide-react';
import { usePhenomicUpload } from './usePhenomicUpload';
import { useCallback } from 'react';

export function PhenomicUploadPanel() {
  const {
    isUploading,
    uploadProgress,
    uploadMessage,
    uploadReceipt,
    selectedFile,
    datasetName,
    crop,
    platform,
    update,
    selectFile,
    uploadFile,
    reset,
  } = usePhenomicUpload();

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    selectFile(file);
  }, [selectFile]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0] || null;
    selectFile(file);
  }, [selectFile]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  }, []);

  // State: Loading (upload in progress)
  if (isUploading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Upload className="h-8 w-8 text-blue-500" />
              Phenomic Data Upload
            </h1>
            <p className="text-muted-foreground mt-1">
              High-throughput phenotyping data ingestion
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 animate-pulse text-blue-500" />
              Uploading Spectral Data...
            </CardTitle>
            <CardDescription>
              Processing {selectedFile?.name}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Upload Progress</span>
                <span className="font-medium">{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="h-2" />
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Database className="h-4 w-4" />
              <span>Creating persistent import job and upload receipt...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // State: Success (upload complete with receipt)
  if (uploadReceipt) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Upload className="h-8 w-8 text-blue-500" />
              Phenomic Data Upload
            </h1>
            <p className="text-muted-foreground mt-1">
              High-throughput phenotyping data ingestion
            </p>
          </div>
          <Badge variant="default" className="bg-green-500">
            <CheckCircle2 className="h-4 w-4 mr-1" />
            Upload Complete
          </Badge>
        </div>

        <Card className="border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-900 dark:text-green-100">
              <CheckCircle2 className="h-6 w-6" />
              Upload Successful
            </CardTitle>
            <CardDescription className="text-green-700 dark:text-green-300">
              {uploadReceipt.message}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label className="text-sm text-green-700 dark:text-green-300">Job ID</Label>
                <div className="font-mono text-lg font-bold text-green-900 dark:text-green-100">
                  #{uploadReceipt.job_id}
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-sm text-green-700 dark:text-green-300">Status</Label>
                <Badge variant="outline" className="text-green-900 dark:text-green-100">
                  {uploadReceipt.status}
                </Badge>
              </div>
              <div className="space-y-1">
                <Label className="text-sm text-green-700 dark:text-green-300">Filename</Label>
                <div className="flex items-center gap-2 text-green-900 dark:text-green-100">
                  <FileCheck className="h-4 w-4" />
                  <span className="font-medium">{uploadReceipt.filename}</span>
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-sm text-green-700 dark:text-green-300">File Size</Label>
                <div className="text-green-900 dark:text-green-100">
                  {(uploadReceipt.size_bytes / 1024).toFixed(2)} KB
                </div>
              </div>
              {uploadReceipt.dataset_name && (
                <div className="space-y-1">
                  <Label className="text-sm text-green-700 dark:text-green-300">Dataset</Label>
                  <div className="text-green-900 dark:text-green-100">
                    {uploadReceipt.dataset_name}
                  </div>
                </div>
              )}
              {uploadReceipt.crop && (
                <div className="space-y-1">
                  <Label className="text-sm text-green-700 dark:text-green-300">Crop</Label>
                  <div className="text-green-900 dark:text-green-100">
                    {uploadReceipt.crop}
                  </div>
                </div>
              )}
              <div className="space-y-1">
                <Label className="text-sm text-green-700 dark:text-green-300">Platform</Label>
                <div className="text-green-900 dark:text-green-100">
                  {uploadReceipt.platform}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-green-200 dark:border-green-900">
              <Button onClick={reset} className="w-full">
                <Upload className="h-4 w-4 mr-2" />
                Upload Another File
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // State: Empty (no file selected) or Error (validation/upload error)
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Upload className="h-8 w-8 text-blue-500" />
            Phenomic Data Upload
          </h1>
          <p className="text-muted-foreground mt-1">
            High-throughput phenotyping data ingestion
          </p>
        </div>
      </div>

      {/* Error State Alert */}
      {uploadMessage && !uploadReceipt && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{uploadMessage}</AlertDescription>
        </Alert>
      )}

      {/* File Upload Card */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Spectral Data</CardTitle>
          <CardDescription>
            Supported formats: CSV, DX, SPC (max 100MB)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Drag-Drop Zone (Empty State) */}
          {!selectedFile ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-12 text-center hover:border-muted-foreground/50 transition-colors cursor-pointer"
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <div className="flex flex-col items-center gap-4">
                <div className="rounded-full bg-muted p-4">
                  <Upload className="h-8 w-8 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-lg font-medium">Drop your file here</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    or click to browse
                  </p>
                </div>
                <Badge variant="outline">CSV, DX, SPC</Badge>
              </div>
              <input
                id="file-input"
                type="file"
                accept=".csv,.dx,.spc"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          ) : (
            /* Selected File Display */
            <div className="border rounded-lg p-4 bg-muted/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="font-medium">{selectedFile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => selectFile(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Upload Parameters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="dataset-name">Dataset Name (Optional)</Label>
              <Input
                id="dataset-name"
                value={datasetName}
                onChange={(e) => update({ datasetName: e.target.value })}
                placeholder="e.g., Trial 2024 NIRS"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="crop">Crop (Optional)</Label>
              <Input
                id="crop"
                value={crop}
                onChange={(e) => update({ crop: e.target.value })}
                placeholder="e.g., Wheat"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="platform">Platform</Label>
              <Select value={platform} onValueChange={(v) => update({ platform: v })}>
                <SelectTrigger id="platform">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="NIRS">NIRS</SelectItem>
                  <SelectItem value="Hyperspectral">Hyperspectral</SelectItem>
                  <SelectItem value="RGB">RGB</SelectItem>
                  <SelectItem value="Multispectral">Multispectral</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Upload Button */}
          <div className="pt-4">
            <Button
              onClick={uploadFile}
              disabled={!selectedFile}
              className="w-full"
              size="lg"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              Upload Spectral Data
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">About Phenomic Upload</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            Upload high-throughput phenotyping data for downstream analysis and prediction modeling.
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Spectral data is validated and queued for processing</li>
            <li>A persistent import job tracks ingestion status</li>
            <li>Upload receipts provide durable audit trails</li>
            <li>Processed data becomes available for phenomic selection workflows</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

export default PhenomicUploadPanel;
