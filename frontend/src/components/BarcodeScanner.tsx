/**
 * Barcode/QR Scanner Component
 * 
 * Uses html5-qrcode for camera-based scanning.
 * Supports QR codes, Code128, DataMatrix, and more.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Html5Qrcode, Html5QrcodeScannerState } from 'html5-qrcode';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  Camera, CameraOff, QrCode, Search, Volume2, VolumeX,
  RotateCcw, Flashlight, CheckCircle2, XCircle, Package,
} from 'lucide-react';

interface ScanResult {
  barcode_value: string;
  found: boolean;
  entity_type?: string;
  entity_id?: string;
  entity_name?: string;
  data?: Record<string, unknown>;
}

interface BarcodeScannerProps {
  onScan?: (result: ScanResult) => void;
  onLookup?: (barcode: string) => Promise<ScanResult | null>;
  autoStart?: boolean;
  showManualInput?: boolean;
  showHistory?: boolean;
  className?: string;
}

const API_BASE = '/api/v2/barcode';

export function BarcodeScanner({
  onScan,
  onLookup,
  autoStart = false,
  showManualInput = true,
  showHistory = true,
  className = '',
}: BarcodeScannerProps) {
  const [isScanning, setIsScanning] = useState(false);
  const [manualCode, setManualCode] = useState('');
  const [lastResult, setLastResult] = useState<ScanResult | null>(null);
  const [scanHistory, setScanHistory] = useState<ScanResult[]>([]);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [cameraId, setCameraId] = useState<string | null>(null);
  const [cameras, setCameras] = useState<{ id: string; label: string }[]>([]);
  
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();


  // Play beep sound on successful scan
  const playBeep = useCallback(() => {
    if (!soundEnabled) return;
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      oscillator.frequency.value = 1000;
      oscillator.type = 'sine';
      gainNode.gain.value = 0.3;
      oscillator.start();
      setTimeout(() => oscillator.stop(), 100);
    } catch (e) {
      console.log('Audio not available');
    }
  }, [soundEnabled]);

  // Handle scan result
  const handleScan = useCallback(async (decodedText: string) => {
    playBeep();
    
    // Look up the barcode
    let result: ScanResult = {
      barcode_value: decodedText,
      found: false,
    };

    try {
      if (onLookup) {
        const lookupResult = await onLookup(decodedText);
        if (lookupResult) {
          result = lookupResult;
        }
      } else {
        // Default API lookup
        const res = await fetch(`${API_BASE}/scan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ barcode_value: decodedText }),
        });
        const data = await res.json();
        if (data.entity) {
          result = {
            barcode_value: decodedText,
            found: true,
            entity_type: data.entity.entity_type,
            entity_id: data.entity.entity_id,
            entity_name: data.entity.entity_name,
            data: data.entity.data,
          };
        }
      }
    } catch (error) {
      console.error('Lookup error:', error);
    }

    setLastResult(result);
    setScanHistory(prev => [result, ...prev.slice(0, 9)]);
    
    if (onScan) {
      onScan(result);
    }

    toast({
      title: result.found ? 'Barcode Found' : 'Unknown Barcode',
      description: result.found 
        ? `${result.entity_name} (${result.entity_type})`
        : `Code: ${decodedText}`,
      variant: result.found ? 'default' : 'destructive',
    });
  }, [onScan, onLookup, playBeep, toast]);

  // Initialize scanner
  useEffect(() => {
    Html5Qrcode.getCameras().then(devices => {
      if (devices && devices.length) {
        setCameras(devices.map(d => ({ id: d.id, label: d.label || `Camera ${d.id}` })));
        setCameraId(devices[0].id);
      }
    }).catch(err => {
      console.error('Camera error:', err);
    });

    return () => {
      if (scannerRef.current) {
        scannerRef.current.stop().catch(() => {});
      }
    };
  }, []);

  // Auto-start if enabled
  useEffect(() => {
    if (autoStart && cameraId && !isScanning) {
      startScanning();
    }
  }, [autoStart, cameraId]);

  const startScanning = async () => {
    if (!cameraId || !containerRef.current) return;

    try {
      if (!scannerRef.current) {
        scannerRef.current = new Html5Qrcode('barcode-scanner-container');
      }

      await scannerRef.current.start(
        cameraId,
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
        },
        handleScan,
        () => {} // Ignore errors during scanning
      );
      setIsScanning(true);
    } catch (err) {
      console.error('Failed to start scanner:', err);
      toast({
        title: 'Camera Error',
        description: 'Failed to access camera. Please check permissions.',
        variant: 'destructive',
      });
    }
  };

  const stopScanning = async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop();
        setIsScanning(false);
      } catch (err) {
        console.error('Failed to stop scanner:', err);
      }
    }
  };

  const handleManualSubmit = () => {
    if (manualCode.trim()) {
      handleScan(manualCode.trim());
      setManualCode('');
    }
  };

  const getEntityIcon = (type?: string) => {
    switch (type) {
      case 'seed_lot': return <Package className="w-4 h-4" />;
      case 'accession': return <QrCode className="w-4 h-4" />;
      default: return <QrCode className="w-4 h-4" />;
    }
  };


  return (
    <div className={`space-y-4 ${className}`}>
      {/* Scanner Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        <Button
          onClick={isScanning ? stopScanning : startScanning}
          variant={isScanning ? 'destructive' : 'default'}
          className="gap-2"
        >
          {isScanning ? <CameraOff className="w-4 h-4" /> : <Camera className="w-4 h-4" />}
          {isScanning ? 'Stop Scanner' : 'Start Scanner'}
        </Button>
        
        <Button
          variant="outline"
          size="icon"
          onClick={() => setSoundEnabled(!soundEnabled)}
          title={soundEnabled ? 'Mute' : 'Unmute'}
          aria-label={soundEnabled ? 'Mute scan sound' : 'Unmute scan sound'}
        >
          {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
        </Button>

        {cameras.length > 1 && (
          <select
            className="px-3 py-2 border rounded-md text-sm"
            value={cameraId || ''}
            onChange={(e) => {
              setCameraId(e.target.value);
              if (isScanning) {
                stopScanning().then(() => startScanning());
              }
            }}
          >
            {cameras.map(cam => (
              <option key={cam.id} value={cam.id}>{cam.label}</option>
            ))}
          </select>
        )}
      </div>

      {/* Scanner View */}
      <Card>
        <CardContent className="p-4">
          <div
            id="barcode-scanner-container"
            ref={containerRef}
            className={`w-full aspect-video bg-gray-900 rounded-lg overflow-hidden ${!isScanning ? 'flex items-center justify-center' : ''}`}
          >
            {!isScanning && (
              <div className="text-center text-gray-400">
                <QrCode className="w-16 h-16 mx-auto mb-2 opacity-50" />
                <p>Click "Start Scanner" to begin</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Manual Input */}
      {showManualInput && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Search className="w-4 h-4" />
              Manual Entry
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                placeholder="Enter barcode manually..."
                value={manualCode}
                onChange={(e) => setManualCode(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleManualSubmit()}
              />
              <Button onClick={handleManualSubmit}>Lookup</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Last Result */}
      {lastResult && (
        <Card className={lastResult.found ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              {lastResult.found ? (
                <CheckCircle2 className="w-4 h-4 text-green-600" />
              ) : (
                <XCircle className="w-4 h-4 text-red-600" />
              )}
              Last Scan
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono">{lastResult.barcode_value}</Badge>
                {lastResult.entity_type && (
                  <Badge className="bg-blue-100 text-blue-800">{lastResult.entity_type}</Badge>
                )}
              </div>
              {lastResult.found && (
                <>
                  <p className="font-medium">{lastResult.entity_name}</p>
                  {lastResult.data && Object.keys(lastResult.data).length > 0 && (
                    <div className="text-sm text-gray-600 grid grid-cols-2 gap-1">
                      {Object.entries(lastResult.data).map(([key, value]) => (
                        <div key={key}>
                          <span className="text-gray-400">{key}:</span> {String(value)}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scan History */}
      {showHistory && scanHistory.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Recent Scans</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setScanHistory([])}>
                <RotateCcw className="w-3 h-3 mr-1" /> Clear
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {scanHistory.slice(0, 5).map((scan, i) => (
                <div key={i} className="flex items-center justify-between text-sm py-1 border-b last:border-0">
                  <div className="flex items-center gap-2">
                    {scan.found ? (
                      <CheckCircle2 className="w-3 h-3 text-green-500" />
                    ) : (
                      <XCircle className="w-3 h-3 text-red-500" />
                    )}
                    <span className="font-mono text-xs">{scan.barcode_value}</span>
                  </div>
                  {scan.entity_name && (
                    <span className="text-gray-600 truncate max-w-[150px]">{scan.entity_name}</span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default BarcodeScanner;
