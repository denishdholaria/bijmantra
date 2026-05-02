/**
 * Barcode & QR Code Scanner Page
 * Uses html5-qrcode for camera-based scanning
 * Supports: QR Code, Code 128, EAN, UPC, Code 39, and more
 */
import { useState, useEffect, useRef } from 'react'
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'
import { SmartIcon } from '@/lib/icons'

interface ScanResult {
  code: string
  format: string
  timestamp: string
  matchStatus: 'unmatched'
}

export function BarcodeScanner() {
  const [isScanning, setIsScanning] = useState(false)
  const [manualCode, setManualCode] = useState('')
  const [scanHistory, setScanHistory] = useState<ScanResult[]>([])
  const [lastResult, setLastResult] = useState<ScanResult | undefined>(undefined)
  const [selectedCamera, setSelectedCamera] = useState<string>('')
  const [cameras, setCameras] = useState<{ id: string; label: string }[]>([])
  const [scanMode, setScanMode] = useState<'qr' | 'barcode' | 'all'>('all')
  const scannerRef = useRef<Html5Qrcode | null>(null)
  const scannerContainerId = 'qr-reader'

  // Get supported formats based on mode
  const getFormats = () => {
    if (scanMode === 'qr') {
      return [Html5QrcodeSupportedFormats.QR_CODE]
    }
    if (scanMode === 'barcode') {
      return [
        Html5QrcodeSupportedFormats.CODE_128,
        Html5QrcodeSupportedFormats.CODE_39,
        Html5QrcodeSupportedFormats.EAN_13,
        Html5QrcodeSupportedFormats.EAN_8,
        Html5QrcodeSupportedFormats.UPC_A,
        Html5QrcodeSupportedFormats.UPC_E,
      ]
    }
    // All formats
    return [
      Html5QrcodeSupportedFormats.QR_CODE,
      Html5QrcodeSupportedFormats.CODE_128,
      Html5QrcodeSupportedFormats.CODE_39,
      Html5QrcodeSupportedFormats.EAN_13,
      Html5QrcodeSupportedFormats.EAN_8,
      Html5QrcodeSupportedFormats.UPC_A,
      Html5QrcodeSupportedFormats.UPC_E,
      Html5QrcodeSupportedFormats.DATA_MATRIX,
      Html5QrcodeSupportedFormats.AZTEC,
    ]
  }

  // Initialize cameras list
  useEffect(() => {
    Html5Qrcode.getCameras()
      .then(devices => {
        if (devices && devices.length) {
          setCameras(devices.map(d => ({ id: d.id, label: d.label || `Camera ${d.id}` })))
          setSelectedCamera(devices[0].id)
        }
      })
      .catch(err => {
        console.error('Error getting cameras:', err)
        toast.error('Could not access cameras')
      })

    return () => {
      stopScanning()
    }
  }, [])

  const startScanning = async () => {
    if (!selectedCamera) {
      toast.error('No camera selected')
      return
    }

    try {
      const scanner = new Html5Qrcode(scannerContainerId, { formatsToSupport: getFormats(), verbose: false })
      scannerRef.current = scanner

      await scanner.start(
        selectedCamera,
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
        },
        async (decodedText, decodedResult) => {
          // Success callback
          const format = decodedResult.result.format?.formatName || 'Unknown'
          await handleScanSuccess(decodedText, format)
        },
        (errorMessage) => {
          // Error callback - ignore, scanning continues
        }
      )

      setIsScanning(true)
      toast.success('Scanner started')
    } catch (err) {
      console.error('Error starting scanner:', err)
      toast.error('Failed to start scanner')
    }
  }

  const stopScanning = async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop()
        scannerRef.current = null
      } catch (err) {
        console.error('Error stopping scanner:', err)
      }
    }
    setIsScanning(false)
  }

  const handleScanSuccess = async (code: string, format: string) => {
    // Pause scanning briefly to prevent duplicate scans
    if (scannerRef.current) {
      await scannerRef.current.pause()
    }

    const result: ScanResult = {
      code,
      format,
      timestamp: new Date().toISOString(),
            matchStatus: 'unmatched',
    }

    setLastResult(result)
    setScanHistory(prev => [result, ...prev.slice(0, 19)])

    toast.info(`Captured scan: ${code}`)

    // Resume scanning after a short delay
    setTimeout(async () => {
      if (scannerRef.current) {
        try {
          await scannerRef.current.resume()
        } catch (err) {
          // Scanner might have been stopped
        }
      }
    }, 1500)
  }

  const handleManualSearch = async () => {
    if (!manualCode.trim()) {
      toast.error('Please enter a code')
      return
    }

    const result: ScanResult = {
      code: manualCode,
      format: 'Manual',
      timestamp: new Date().toISOString(),
      matchStatus: 'unmatched',
    }

    setLastResult(result)
    setScanHistory(prev => [result, ...prev.slice(0, 19)])
    setManualCode('')

    toast.info('Recorded code. Database matching is not connected yet.')
  }

  const getFormatBadge = (format: string) => {
    const colors: Record<string, string> = {
      QR_CODE: 'bg-purple-100 text-purple-800',
      CODE_128: 'bg-blue-100 text-blue-800',
      CODE_39: 'bg-blue-100 text-blue-800',
      EAN_13: 'bg-green-100 text-green-800',
      EAN_8: 'bg-green-100 text-green-800',
      Manual: 'bg-gray-100 text-gray-800',
    }
    return colors[format] || 'bg-gray-100 text-gray-800'
  }

  const formatTime = (timestamp: string) => new Date(timestamp).toLocaleTimeString()

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">Scanner</h1>
        <p className="text-muted-foreground mt-1">Capture QR codes and barcodes without fabricated record matching</p>
      </div>

      <Card className="border-amber-300 bg-amber-50/60">
        <CardHeader>
          <CardTitle>Database lookup not connected</CardTitle>
          <CardDescription>
            Scans are captured as raw codes only. This route does not invent germplasm, plot, sample, or seed-lot matches.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-amber-950">
          <p>
            Use this surface to capture codes from the camera or keyboard for now. Link resolution should be enabled only after a tenant-safe lookup API is available.
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">Raw code capture only</Badge>
            <Badge variant="secondary">No mock entity lookup</Badge>
            <Badge variant="secondary">Lookup API required</Badge>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="camera">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="camera"><SmartIcon icon="camera" size="sm" className="mr-2" />Camera Scan</TabsTrigger>
          <TabsTrigger value="manual"><SmartIcon icon="keyboard" size="sm" className="mr-2" />Manual Entry</TabsTrigger>
        </TabsList>

        <TabsContent value="camera" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Camera Scanner</CardTitle>
              <CardDescription>Point camera at QR code or barcode</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Scanner Controls */}
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <Label>Camera</Label>
                  <Select value={selectedCamera} onValueChange={setSelectedCamera} disabled={isScanning}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select camera..." />
                    </SelectTrigger>
                    <SelectContent>
                      {cameras.map(cam => (
                        <SelectItem key={cam.id} value={cam.id}>{cam.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex-1">
                  <Label>Scan Mode</Label>
                  <Select value={scanMode} onValueChange={(v: any) => setScanMode(v)} disabled={isScanning}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Formats</SelectItem>
                      <SelectItem value="qr">QR Code Only</SelectItem>
                      <SelectItem value="barcode">Barcode Only</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Scanner View */}
              <div 
                id={scannerContainerId}
                className="w-full aspect-video bg-gray-900 rounded-lg overflow-hidden"
                style={{ minHeight: '300px' }}
              >
                {!isScanning && (
                  <div className="w-full h-full flex items-center justify-center text-white">
                    <div className="text-center">
                      <p className="text-4xl mb-2">📷</p>
                      <p>Click Start to begin scanning</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Start/Stop Button */}
              <Button 
                onClick={isScanning ? stopScanning : startScanning}
                className="w-full"
                size="lg"
                variant={isScanning ? 'destructive' : 'default'}
              >
                {isScanning ? '⏹️ Stop Scanner' : '▶️ Start Scanner'}
              </Button>

              {/* Supported Formats */}
              <div className="text-xs text-muted-foreground">
                <p className="font-medium mb-1">Supported formats:</p>
                <div className="flex flex-wrap gap-1">
                  {scanMode === 'all' && <Badge variant="outline">QR Code</Badge>}
                  {scanMode === 'qr' && <Badge variant="outline">QR Code</Badge>}
                  {(scanMode === 'all' || scanMode === 'barcode') && (
                    <>
                      <Badge variant="outline">Code 128</Badge>
                      <Badge variant="outline">Code 39</Badge>
                      <Badge variant="outline">EAN-13</Badge>
                      <Badge variant="outline">EAN-8</Badge>
                      <Badge variant="outline">UPC-A</Badge>
                    </>
                  )}
                  {scanMode === 'all' && (
                    <>
                      <Badge variant="outline">Data Matrix</Badge>
                      <Badge variant="outline">Aztec</Badge>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manual" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Manual Entry</CardTitle>
              <CardDescription>Enter code manually</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Enter code (e.g., G-ABC123, GERM-001)"
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value.toUpperCase())}
                  onKeyDown={(e) => e.key === 'Enter' && handleManualSearch()}
                />
                <Button onClick={handleManualSearch}>Search</Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Enter a code to capture it in the local scan history. Match resolution is disabled until the database lookup path is implemented.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Last Scan Result */}
      {lastResult && (
        <Card className="border-yellow-200 bg-yellow-50/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <SmartIcon icon="clipboard" size="xl" className="text-primary" />
                Captured Scan
              </CardTitle>
              <Badge className={getFormatBadge(lastResult.format)}>{lastResult.format}</Badge>
            </div>
            <CardDescription>
              Code: {lastResult.code} • Scanned at {formatTime(lastResult.timestamp)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Database matching is not connected for this route yet, so BijMantra stores the raw scan without claiming a linked entity.
            </p>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">Status: unmatched</Badge>
              <Badge variant="outline">Code: {lastResult.code}</Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scan History */}
      {scanHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Scan History</CardTitle>
            <CardDescription>Last {scanHistory.length} scans</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {scanHistory.map((scan, index) => (
                <div 
                  key={`${scan.code}-${index}`}
                  className="flex items-center justify-between p-3 bg-muted rounded-lg cursor-pointer hover:bg-muted/80"
                  onClick={() => setLastResult(scan)}
                >
                  <div className="flex items-center gap-3">
                    <SmartIcon icon="clipboard" size="lg" className="text-primary" />
                    <div>
                      <p className="font-medium text-sm">{scan.code}</p>
                      <p className="text-xs text-muted-foreground">Awaiting connected lookup</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className={getFormatBadge(scan.format)} variant="secondary">{scan.format}</Badge>
                    <p className="text-xs text-muted-foreground mt-1">{formatTime(scan.timestamp)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
