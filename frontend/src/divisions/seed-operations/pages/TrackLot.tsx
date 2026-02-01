/**
 * Track Lot Page - QR lookup for traceability
 * Connected to /api/v2/traceability endpoints
 */

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  QrCode, Search, Package, MapPin, Calendar, User, 
  ArrowRight, CheckCircle, Truck, FlaskConical, FileCheck,
  History, Loader2, AlertCircle, ChevronDown, ChevronUp, RefreshCw
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface LotDetails {
  lot_id: string;
  variety_id: string;
  variety_name: string;
  crop: string;
  seed_class: string;
  production_year: number;
  production_season: string;
  production_location: string;
  producer_name: string;
  quantity_kg: number;
  germination_percent?: number;
  purity_percent?: number;
  moisture_percent?: number;
  status: string;
  created_at: string;
}

interface TraceEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  details: Record<string, any>;
  operator_name?: string;
  location?: string;
}

interface Certification {
  cert_id: string;
  cert_type: string;
  cert_number: string;
  issuing_authority: string;
  issue_date: string;
  expiry_date: string;
}

export function TrackLot() {
  const [lotNumber, setLotNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lotDetails, setLotDetails] = useState<LotDetails | null>(null);
  const [history, setHistory] = useState<TraceEvent[]>([]);
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [lineage, setLineage] = useState<any>(null);
  const [showFullHistory, setShowFullHistory] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleTrack = async () => {
    if (!lotNumber.trim()) return;
    
    setLoading(true);
    setError(null);
    setLotDetails(null);
    setHistory([]);
    setCertifications([]);
    setLineage(null);
    
    try {
      // Fetch lot details
      const lotRes = await apiClient.traceabilityService.getTraceabilityLot(lotNumber);
      if (lotRes.status !== 'success' || !lotRes.data) {
        throw new Error('Lot not found');
      }
      setLotDetails(lotRes.data);
      
      // Fetch history, certifications, and lineage in parallel
      const [historyRes, certsRes, lineageRes] = await Promise.all([
        apiClient.traceabilityService.getLotHistory(lotNumber).catch(() => ({ data: [] })),
        apiClient.traceabilityService.getLotCertifications(lotNumber).catch(() => ({ data: [] })),
        apiClient.traceabilityService.traceLotLineage(lotNumber).catch(() => ({ data: null })),
      ]);
      
      setHistory(historyRes.data || []);
      setCertifications(certsRes.data || []);
      setLineage(lineageRes.data);
    } catch (err: any) {
      setError(err.message || 'Lot not found. Please check the lot number and try again.');
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setLotNumber('');
    setLotDetails(null);
    setHistory([]);
    setCertifications([]);
    setLineage(null);
    setError(null);
    inputRef.current?.focus();
  };

  const getEventIcon = (eventType: string) => {
    const icons: Record<string, any> = {
      harvest: Package,
      processing: ArrowRight,
      testing: FlaskConical,
      certification: FileCheck,
      packaging: Package,
      dispatch: Truck,
      quality_check: CheckCircle,
      transfer: ArrowRight,
    };
    const Icon = icons[eventType] || History;
    return <Icon className="h-4 w-4" />;
  };

  const formatEventType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const displayedHistory = showFullHistory ? history : history.slice(0, 5);

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <QrCode className="h-6 w-6 text-blue-600" />
          Track Lot
        </h1>
        <p className="text-gray-500 text-sm mt-1">Scan or enter lot number to view complete chain of custody</p>
      </div>

      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Lot Lookup</CardTitle>
          <CardDescription>Enter lot number or scan QR code to trace history</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input 
              ref={inputRef}
              placeholder="Enter lot number (e.g., LOT-2024-001)..."
              value={lotNumber}
              onChange={(e) => setLotNumber(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleTrack()}
              autoFocus
            />
            <Button onClick={handleTrack} disabled={loading || !lotNumber.trim()}>
              {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
              Track
            </Button>
          </div>
          
          {!lotDetails && !loading && !error && (
            <div className="py-8 text-center text-gray-500">
              <QrCode className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Enter a lot number to view its complete history</p>
              <p className="text-sm mt-1">Try: LOT-2024-001</p>
            </div>
          )}
        </CardContent>
      </Card>

      {error && !lotDetails && (
        <div className="flex items-center justify-between p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={handleTrack}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      )}

      {/* Lot Details */}
      {lotDetails && (
        <>
          <Card>
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl">{lotDetails.lot_id}</CardTitle>
                  <CardDescription>{lotDetails.variety_name} - {lotDetails.crop}</CardDescription>
                </div>
                <Badge className={lotDetails.seed_class === 'foundation' ? 'bg-white border border-gray-300' : lotDetails.seed_class === 'certified' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'}>
                  {lotDetails.seed_class}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">Producer</p>
                    <p className="text-sm font-medium">{lotDetails.producer_name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">Location</p>
                    <p className="text-sm font-medium">{lotDetails.production_location}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">Season</p>
                    <p className="text-sm font-medium">{lotDetails.production_season} {lotDetails.production_year}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Package className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">Quantity</p>
                    <p className="text-sm font-medium">{lotDetails.quantity_kg} kg</p>
                  </div>
                </div>
              </div>

              {/* Quality Metrics */}
              {(lotDetails.germination_percent || lotDetails.purity_percent || lotDetails.moisture_percent) && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm font-medium text-gray-700 mb-2">Quality Metrics</p>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    {lotDetails.germination_percent && (
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className={`text-xl font-bold ${lotDetails.germination_percent >= 80 ? 'text-green-600' : 'text-red-600'}`}>
                          {lotDetails.germination_percent}%
                        </p>
                        <p className="text-xs text-gray-500">Germination</p>
                      </div>
                    )}
                    {lotDetails.purity_percent && (
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className={`text-xl font-bold ${lotDetails.purity_percent >= 95 ? 'text-green-600' : 'text-red-600'}`}>
                          {lotDetails.purity_percent}%
                        </p>
                        <p className="text-xs text-gray-500">Purity</p>
                      </div>
                    )}
                    {lotDetails.moisture_percent && (
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className={`text-xl font-bold ${lotDetails.moisture_percent <= 12 ? 'text-green-600' : 'text-red-600'}`}>
                          {lotDetails.moisture_percent}%
                        </p>
                        <p className="text-xs text-gray-500">Moisture</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Certifications */}
          {certifications.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <FileCheck className="h-5 w-5 text-green-600" />
                  Certifications
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {certifications.map((cert) => (
                    <div key={cert.cert_id} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <div>
                        <p className="font-medium">{cert.cert_number}</p>
                        <p className="text-sm text-gray-600">{cert.issuing_authority}</p>
                      </div>
                      <div className="text-right text-sm">
                        <p className="text-gray-500">Valid until</p>
                        <p className="font-medium">{cert.expiry_date}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Event History */}
          {history.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <History className="h-5 w-5 text-blue-600" />
                  Chain of Custody ({history.length} events)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative">
                  {/* Timeline line */}
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
                  
                  <div className="space-y-4">
                    {displayedHistory.map((event, index) => (
                      <div key={event.event_id} className="relative flex gap-4 pl-10">
                        {/* Timeline dot */}
                        <div className="absolute left-2 w-5 h-5 rounded-full bg-blue-100 border-2 border-blue-500 flex items-center justify-center">
                          {getEventIcon(event.event_type)}
                        </div>
                        
                        <div className="flex-1 pb-4">
                          <div className="flex items-center justify-between">
                            <p className="font-medium">{formatEventType(event.event_type)}</p>
                            <p className="text-sm text-gray-500">
                              {new Date(event.timestamp).toLocaleDateString()}
                            </p>
                          </div>
                          {event.operator_name && (
                            <p className="text-sm text-gray-600">{event.operator_name}</p>
                          )}
                          {event.location && (
                            <p className="text-sm text-gray-500 flex items-center gap-1">
                              <MapPin className="h-3 w-3" /> {event.location}
                            </p>
                          )}
                          {Object.keys(event.details).length > 0 && (
                            <div className="mt-1 text-xs text-gray-500">
                              {Object.entries(event.details).map(([k, v]) => (
                                <span key={k} className="mr-3">{k}: {String(v)}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {history.length > 5 && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="w-full mt-2"
                      onClick={() => setShowFullHistory(!showFullHistory)}
                    >
                      {showFullHistory ? (
                        <><ChevronUp className="h-4 w-4 mr-1" /> Show Less</>
                      ) : (
                        <><ChevronDown className="h-4 w-4 mr-1" /> Show All {history.length} Events</>
                      )}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex justify-center gap-2">
            <Button variant="outline" onClick={clearSearch}>
              Track Another Lot
            </Button>
            <Button variant="outline">
              <QrCode className="h-4 w-4 mr-2" />
              Print QR Label
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

export default TrackLot;
