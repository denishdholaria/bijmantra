/**
 * Quality Gate Scanner Page
 * Pre-processing verification with QR/barcode scanning
 * Connected to /api/v2/quality and /api/v2/traceability endpoints
 */

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Shield, QrCode, CheckCircle, XCircle, AlertTriangle, 
  FlaskConical, History, Loader2, Camera, X
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useToast } from '@/hooks/use-toast';
import { useAuthStore } from '@/store/auth';
import { Html5Qrcode } from 'html5-qrcode';

type QualityStatus = 'PASS' | 'FAIL' | 'PENDING' | 'UNKNOWN' | null;

interface ScanResult {
  status: QualityStatus;
  lotNumber: string;
  variety?: string;
  crop?: string;
  testResults?: { 
    germination?: number; 
    purity?: number; 
    moisture?: number;
    vigor?: number;
    health?: number;
  };
  issues: string[];
  recommendation: string;
  certifications?: any[];
  lastEvent?: string;
}

export function QualityGate() {
  const [lotNumber, setLotNumber] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [recentScans, setRecentScans] = useState<string[]>([]);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [decisionState, setDecisionState] = useState<'idle' | 'approving' | 'rejecting'>('idle');
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const html5QrCodeRef = useRef<Html5Qrcode | null>(null);
  const qrCodeRegionId = 'qr-reader';
  const { toast } = useToast();
  const user = useAuthStore((state) => state.user);

  // Focus input on mount for barcode scanner
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Cleanup camera on unmount
  useEffect(() => {
    return () => {
      if (html5QrCodeRef.current?.isScanning) {
        html5QrCodeRef.current.stop().catch(console.error);
      }
    };
  }, []);

  const startCamera = async () => {
    setCameraError(null);
    setIsCameraActive(true);

    try {
      if (!html5QrCodeRef.current) {
        html5QrCodeRef.current = new Html5Qrcode(qrCodeRegionId);
      }

      const qrCodeScanner = html5QrCodeRef.current;

      await qrCodeScanner.start(
        { facingMode: 'environment' }, // Use back camera
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
        },
        (decodedText) => {
          // Successfully scanned QR code
          setLotNumber(decodedText);
          stopCamera();
          // Auto-trigger scan
          setTimeout(() => handleScan(decodedText), 100);
        },
        (errorMessage) => {
          // Scanning error (can be ignored, happens frequently)
          console.debug('QR scan error:', errorMessage);
        }
      );
    } catch (err) {
      console.error('Camera error:', err);
      setCameraError('Failed to access camera. Please check permissions.');
      setIsCameraActive(false);
    }
  };

  const stopCamera = async () => {
    if (html5QrCodeRef.current?.isScanning) {
      try {
        await html5QrCodeRef.current.stop();
      } catch (err) {
        console.error('Error stopping camera:', err);
      }
    }
    setIsCameraActive(false);
  };

  const handleScan = async (scannedLot?: string) => {
    const lotToScan = scannedLot || lotNumber;
    if (!lotToScan.trim()) return;
    
    setIsScanning(true);
    
    try {
      // Try to get lot from traceability API first
      const lotRes = await apiClient.traceabilityService.getTraceabilityLot(lotToScan);
      
      if (lotRes.status === 'success' && lotRes.data) {
        const lot = lotRes.data;
        const issues: string[] = [];
        let status: QualityStatus = 'PASS';
        
        // Check quality thresholds
        if (lot.germination_percent !== undefined && lot.germination_percent < 80) {
          issues.push(`Germination ${lot.germination_percent}% below 80% threshold`);
          status = 'FAIL';
        }
        if (lot.purity_percent !== undefined && lot.purity_percent < 95) {
          issues.push(`Purity ${lot.purity_percent}% below 95% threshold`);
          status = 'FAIL';
        }
        if (lot.moisture_percent !== undefined && lot.moisture_percent > 12) {
          issues.push(`Moisture ${lot.moisture_percent}% above 12% limit`);
          status = 'FAIL';
        }
        
        // If no test results, mark as pending
        if (lot.germination_percent === undefined && lot.purity_percent === undefined) {
          status = 'PENDING';
          issues.push('Quality tests not yet completed');
        }

        setScanResult({
          status,
          lotNumber: lot.lot_id,
          variety: lot.variety_name,
          crop: lot.crop,
          testResults: {
            germination: lot.germination_percent,
            purity: lot.purity_percent,
            moisture: lot.moisture_percent,
          },
          issues,
          recommendation: status === 'PASS' 
            ? 'Approved for processing' 
            : status === 'FAIL' 
              ? 'Reject - Quality standards not met'
              : 'Testing required before processing',
        });
        setDecisionError(null);
        
        // Add to recent scans
        setRecentScans(prev => [lotToScan, ...prev.filter(l => l !== lotToScan)].slice(0, 5));
      } else {
        throw new Error('Lot not found');
      }
    } catch (err) {
      // Fall back to the QC sample record for the scanned lot.
      try {
        const qcRes = await apiClient.qualityControlService.getQCSamples(undefined, lotToScan);
        const sample = qcRes.samples?.find((entry: { lot_id?: string }) => entry.lot_id === lotToScan);
        if (sample) {
          setScanResult({
            status: sample.status === 'passed' ? 'PASS' : sample.status === 'failed' ? 'FAIL' : 'PENDING',
            lotNumber: sample.lot_id,
            variety: sample.variety,
            testResults: {},
            issues: sample.status === 'pending' ? ['Quality tests in progress'] : [],
            recommendation: sample.status === 'passed' 
              ? 'Approved for processing' 
              : sample.status === 'failed'
                ? 'Reject - Quality standards not met'
                : 'Testing in progress',
          });
          setDecisionError(null);
          setRecentScans(prev => [lotToScan, ...prev.filter(l => l !== lotToScan)].slice(0, 5));
        } else {
          throw new Error('Not found');
        }
      } catch {
        // Show unknown status
        setScanResult({
          status: 'UNKNOWN',
          lotNumber: lotToScan,
          issues: ['No records found for this lot number'],
          recommendation: 'Register lot and complete testing before processing',
        });
        setDecisionError(null);
      }
    } finally {
      setIsScanning(false);
    }
  };

  const clearResult = () => {
    setScanResult(null);
    setLotNumber('');
    setDecisionError(null);
    setDecisionState('idle');
    if (isCameraActive) {
      void stopCamera();
    }
    inputRef.current?.focus();
  };

  const operatorName = user?.full_name || user?.email || 'Quality Gate';

  const handleApprove = async () => {
    if (!scanResult) return;
    setDecisionState('approving');
    setDecisionError(null);
    try {
      await apiClient.traceabilityService.recordTraceabilityEvent(scanResult.lotNumber, {
        event_type: 'quality_check',
        details: { 
          decision: 'approved',
          test_results: scanResult.testResults,
        },
        operator_name: operatorName,
        location: 'Processing Plant',
      });
      toast({ title: 'Approved', description: 'Lot approved for processing' });
      clearResult();
    } catch {
      setDecisionError('Approval was not recorded. The lot remains visible until the server confirms the traceability event.')
      toast({
        title: 'Approval failed',
        description: 'The traceability event was not recorded. Review the lot and retry once the backend is available.',
        variant: 'destructive',
      });
    } finally {
      setDecisionState('idle');
    }
  };

  const handleReject = async () => {
    if (!scanResult) return;
    setDecisionState('rejecting');
    setDecisionError(null);
    try {
      await apiClient.traceabilityService.recordTraceabilityEvent(scanResult.lotNumber, {
        event_type: 'quality_check',
        details: { 
          decision: 'rejected',
          issues: scanResult.issues,
        },
        operator_name: operatorName,
        location: 'Processing Plant',
      });
      toast({ title: 'Rejected', description: 'Lot rejected and quarantined' });
      clearResult();
    } catch {
      setDecisionError('Rejection was not recorded. The lot remains visible until the server confirms the quarantine event.')
      toast({
        title: 'Rejection failed',
        description: 'The traceability event was not recorded. Review the lot and retry once the backend is available.',
        variant: 'destructive',
      });
    } finally {
      setDecisionState('idle');
    }
  };

  const getStatusColor = (status: QualityStatus) => {
    switch (status) {
      case 'PASS': return 'border-green-500 bg-green-50 text-green-700';
      case 'FAIL': return 'border-red-500 bg-red-50 text-red-700';
      case 'PENDING': return 'border-yellow-500 bg-yellow-50 text-yellow-700';
      default: return 'border-gray-500 bg-gray-50 text-gray-700';
    }
  };

  const getStatusIcon = (status: QualityStatus) => {
    switch (status) {
      case 'PASS': return <CheckCircle className="h-8 w-8 text-green-600" />;
      case 'FAIL': return <XCircle className="h-8 w-8 text-red-600" />;
      case 'PENDING': return <AlertTriangle className="h-8 w-8 text-yellow-600" />;
      default: return <QrCode className="h-8 w-8 text-gray-600" />;
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Shield className="h-6 w-6 text-blue-600" />
          Quality Gate Scanner
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Verify seed lot quality before processing to prevent contamination
        </p>
      </div>

      {/* Scanner Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Scan Lot</CardTitle>
          <CardDescription>
            Scan QR code or enter lot number to verify quality status
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!scanResult ? (
            <>
              {/* Scanner Interface */}
              <div className="text-center space-y-4">
                {!isCameraActive ? (
                  <>
                    <div className="w-32 h-32 mx-auto border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
                      {isScanning ? (
                        <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
                      ) : (
                        <QrCode className="h-12 w-12 text-gray-400" />
                      )}
                    </div>
                    
                    <div className="flex gap-2 max-w-md mx-auto">
                      <Input
                        ref={inputRef}
                        placeholder="Enter lot number or scan QR..."
                        value={lotNumber}
                        onChange={(e) => setLotNumber(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleScan()}
                        autoFocus
                        disabled={isCameraActive}
                      />
                      <Button onClick={() => handleScan()} disabled={isScanning || !lotNumber.trim() || isCameraActive}>
                        {isScanning ? 'Scanning...' : 'Scan'}
                      </Button>
                    </div>

                    <div className="flex justify-center">
                      <Button 
                        variant="outline" 
                        onClick={startCamera}
                        disabled={isScanning}
                        className="gap-2"
                      >
                        <Camera className="h-4 w-4" />
                        Open Camera to Scan QR
                      </Button>
                    </div>

                    {cameraError && (
                      <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                        {cameraError}
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    {/* Camera View */}
                    <div className="relative max-w-md mx-auto">
                      <div 
                        id={qrCodeRegionId} 
                        className="rounded-lg overflow-hidden border-2 border-blue-500"
                      />
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={stopCamera}
                        className="absolute top-2 right-2 gap-1"
                      >
                        <X className="h-4 w-4" />
                        Close Camera
                      </Button>
                    </div>
                    <p className="text-sm text-gray-600">
                      Position QR code within the frame to scan
                    </p>
                  </>
                )}

                {/* Recent Scans */}
                {!isCameraActive && recentScans.length > 0 && (
                  <div className="pt-4">
                    <p className="text-xs text-gray-500 mb-2 flex items-center justify-center gap-1">
                      <History className="h-3 w-3" /> Recent Scans
                    </p>
                    <div className="flex flex-wrap justify-center gap-2">
                      {recentScans.map((lot) => (
                        <Button 
                          key={lot}
                          variant="outline" 
                          size="sm"
                          onClick={() => { setLotNumber(lot); }}
                        >
                          {lot}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                {!isCameraActive && (
                  <p className="text-xs text-gray-500">
                    💡 Hardware barcode scanners work automatically
                  </p>
                )}
              </div>
            </>
          ) : (
            <>
              {/* Results Display */}
              <div className={`p-6 rounded-lg border-2 ${getStatusColor(scanResult.status)}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(scanResult.status)}
                    <div>
                      <h3 className="text-lg font-semibold">Lot: {scanResult.lotNumber}</h3>
                      {scanResult.variety && (
                        <p className="text-sm opacity-80">{scanResult.crop} - {scanResult.variety}</p>
                      )}
                      <p className="font-medium">{scanResult.recommendation}</p>
                    </div>
                  </div>
                  <Badge 
                    variant={scanResult.status === 'PASS' ? 'default' : scanResult.status === 'FAIL' ? 'destructive' : 'secondary'}
                    className="text-sm px-3 py-1"
                  >
                    {scanResult.status}
                  </Badge>
                </div>
              </div>

              {/* Test Results */}
              {scanResult.testResults && Object.keys(scanResult.testResults).some(k => scanResult.testResults![k as keyof typeof scanResult.testResults] !== undefined) && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <FlaskConical className="h-4 w-4" />
                      Quality Test Results
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      {scanResult.testResults.germination !== undefined && (
                        <div>
                          <p className={`text-2xl font-bold ${scanResult.testResults.germination < 80 ? 'text-red-600' : 'text-green-600'}`}>
                            {scanResult.testResults.germination}%
                          </p>
                          <p className="text-xs text-gray-500">Germination (≥80%)</p>
                        </div>
                      )}
                      {scanResult.testResults.purity !== undefined && (
                        <div>
                          <p className={`text-2xl font-bold ${scanResult.testResults.purity < 95 ? 'text-red-600' : 'text-green-600'}`}>
                            {scanResult.testResults.purity}%
                          </p>
                          <p className="text-xs text-gray-500">Purity (≥95%)</p>
                        </div>
                      )}
                      {scanResult.testResults.moisture !== undefined && (
                        <div>
                          <p className={`text-2xl font-bold ${scanResult.testResults.moisture > 12 ? 'text-red-600' : 'text-green-600'}`}>
                            {scanResult.testResults.moisture}%
                          </p>
                          <p className="text-xs text-gray-500">Moisture (≤12%)</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Issues */}
              {scanResult.issues.length > 0 && (
                <Card className="border-red-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-red-600">Quality Issues</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-1">
                      {scanResult.issues.map((issue, i) => (
                        <li key={i} className="text-sm flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                          <span>{issue}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {decisionError && (
                <Card className="border-amber-300 bg-amber-50">
                  <CardContent className="pt-6 text-sm text-amber-900">
                    {decisionError}
                  </CardContent>
                </Card>
              )}

              {/* Actions */}
              <div className="flex justify-center gap-2">
                <Button variant="outline" onClick={clearResult} disabled={decisionState !== 'idle'}>
                  Scan Another Lot
                </Button>
                {scanResult.status === 'PASS' && (
                  <Button
                    className="bg-green-600 hover:bg-green-700"
                    onClick={handleApprove}
                    disabled={decisionState !== 'idle'}
                  >
                    {decisionState === 'approving' ? 'Approving...' : 'Approve for Processing'}
                  </Button>
                )}
                {scanResult.status === 'FAIL' && (
                  <Button
                    variant="destructive"
                    onClick={handleReject}
                    disabled={decisionState !== 'idle'}
                  >
                    {decisionState === 'rejecting' ? 'Rejecting...' : 'Reject & Quarantine'}
                  </Button>
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Status Legend */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Status Guide</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span><strong>PASS:</strong> Approved</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full" />
              <span><strong>FAIL:</strong> Rejected</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full" />
              <span><strong>PENDING:</strong> Review</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-gray-500 rounded-full" />
              <span><strong>UNKNOWN:</strong> Test needed</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default QualityGate;
