import { useState, useRef, useCallback, useEffect } from 'react';
import { Camera, X, RotateCcw, Download, Zap, Focus, Sun, Moon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface CameraCaptureProps {
  onCapture: (imageData: string, metadata: ImageMetadata) => void;
  onClose?: () => void;
  overlay?: 'grid' | 'leaf' | 'plant' | 'none';
  showGuides?: boolean;
  aspectRatio?: '4:3' | '16:9' | '1:1';
  quality?: number;
  className?: string;
}

interface ImageMetadata {
  timestamp: string;
  width: number;
  height: number;
  facingMode: string;
  location?: { latitude: number; longitude: number };
}

export function CameraCapture({
  onCapture,
  onClose,
  overlay = 'grid',
  showGuides = true,
  aspectRatio = '4:3',
  quality = 0.92,
  className,
}: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [facingMode, setFacingMode] = useState<'user' | 'environment'>('environment');
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [flashEnabled, setFlashEnabled] = useState(false);
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null);

  // Get aspect ratio dimensions
  const getAspectRatioDimensions = () => {
    switch (aspectRatio) {
      case '16:9': return { width: 1920, height: 1080 };
      case '1:1': return { width: 1080, height: 1080 };
      default: return { width: 1280, height: 960 };
    }
  };

  // Initialize camera
  const initCamera = useCallback(async () => {
    try {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }

      const { width, height } = getAspectRatioDimensions();
      const constraints: MediaStreamConstraints = {
        video: {
          facingMode,
          width: { ideal: width },
          height: { ideal: height },
        },
        audio: false,
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setError(null);
    } catch (err) {
      console.error('Camera error:', err);
      setError('Unable to access camera. Please check permissions.');
    }
  }, [facingMode, aspectRatio]);


  // Get location
  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setLocation({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
        () => console.log('Location not available')
      );
    }
  }, []);

  // Initialize camera on mount
  useEffect(() => {
    initCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [initCamera]);

  // Switch camera
  const switchCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
  };

  // Capture image
  const captureImage = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    setIsCapturing(true);
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const imageData = canvas.toDataURL('image/jpeg', quality);
    setCapturedImage(imageData);
    setIsCapturing(false);
  }, [quality]);

  // Confirm capture
  const confirmCapture = () => {
    if (!capturedImage || !canvasRef.current) return;

    const metadata: ImageMetadata = {
      timestamp: new Date().toISOString(),
      width: canvasRef.current.width,
      height: canvasRef.current.height,
      facingMode,
      location: location || undefined,
    };

    onCapture(capturedImage, metadata);
    setCapturedImage(null);
  };

  // Retake photo
  const retake = () => {
    setCapturedImage(null);
  };

  // Render overlay
  const renderOverlay = () => {
    if (overlay === 'none') return null;

    return (
      <div className="absolute inset-0 pointer-events-none">
        {overlay === 'grid' && (
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <line x1="33.33" y1="0" x2="33.33" y2="100" stroke="white" strokeOpacity="0.5" strokeWidth="0.2" />
            <line x1="66.66" y1="0" x2="66.66" y2="100" stroke="white" strokeOpacity="0.5" strokeWidth="0.2" />
            <line x1="0" y1="33.33" x2="100" y2="33.33" stroke="white" strokeOpacity="0.5" strokeWidth="0.2" />
            <line x1="0" y1="66.66" x2="100" y2="66.66" stroke="white" strokeOpacity="0.5" strokeWidth="0.2" />
          </svg>
        )}
        {overlay === 'leaf' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-3/4 h-3/4 border-2 border-dashed border-green-400/60 rounded-[40%]" />
            <span className="absolute bottom-4 text-white/80 text-sm bg-black/40 px-2 py-1 rounded">
              Center leaf in frame
            </span>
          </div>
        )}
        {overlay === 'plant' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-2/3 h-4/5 border-2 border-dashed border-green-400/60 rounded-lg" />
            <span className="absolute bottom-4 text-white/80 text-sm bg-black/40 px-2 py-1 rounded">
              Center plant in frame
            </span>
          </div>
        )}
      </div>
    );
  };

  if (error) {
    return (
      <Card className={cn('w-full max-w-lg mx-auto', className)}>
        <CardContent className="p-6 text-center">
          <Camera className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={initCamera}>Retry</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('relative bg-black rounded-lg overflow-hidden', className)}>
      {/* Video/Preview */}
      <div className="relative aspect-[4/3]">
        {capturedImage ? (
          <img src={capturedImage} alt="Captured" className="w-full h-full object-cover" />
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            {showGuides && renderOverlay()}
          </>
        )}
        <canvas ref={canvasRef} className="hidden" />

        {/* Flash effect */}
        {isCapturing && (
          <div className="absolute inset-0 bg-white animate-pulse" />
        )}
      </div>

      {/* Controls */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
        {capturedImage ? (
          <div className="flex items-center justify-center gap-4">
            <Button variant="outline" size="lg" onClick={retake} className="bg-white/10 border-white/20 text-white">
              <RotateCcw className="h-5 w-5 mr-2" />
              Retake
            </Button>
            <Button size="lg" onClick={confirmCapture} className="bg-green-600 hover:bg-green-700">
              <Download className="h-5 w-5 mr-2" />
              Use Photo
            </Button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setFlashEnabled(!flashEnabled)}
              className="text-white hover:bg-white/20"
              aria-label={flashEnabled ? 'Disable flash' : 'Enable flash'}
            >
              {flashEnabled ? <Sun className="h-6 w-6" /> : <Moon className="h-6 w-6" />}
            </Button>

            <Button
              size="lg"
              onClick={captureImage}
              className="h-16 w-16 rounded-full bg-white hover:bg-gray-200 p-0"
            >
              <div className="h-14 w-14 rounded-full border-4 border-gray-800" />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={switchCamera}
              className="text-white hover:bg-white/20"
              aria-label="Switch camera"
            >
              <RotateCcw className="h-6 w-6" />
            </Button>
          </div>
        )}
      </div>

      {/* Close button */}
      {onClose && (
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="absolute top-2 right-2 text-white hover:bg-white/20"
          aria-label="Close camera"
        >
          <X className="h-6 w-6" />
        </Button>
      )}

      {/* Status badges */}
      <div className="absolute top-2 left-2 flex gap-2">
        {location && (
          <Badge variant="secondary" className="bg-black/50 text-white">
            <Focus className="h-3 w-3 mr-1" />
            GPS
          </Badge>
        )}
        <Badge variant="secondary" className="bg-black/50 text-white">
          <Zap className="h-3 w-3 mr-1" />
          {facingMode === 'environment' ? 'Back' : 'Front'}
        </Badge>
      </div>
    </div>
  );
}
