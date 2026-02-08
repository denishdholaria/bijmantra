/**
 * UV Index Page
 *
 * UV radiation monitoring and protection recommendations.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Sun, Shield, AlertTriangle, MapPin } from 'lucide-react';

interface UVData {
  date: string;
  latitude: number;
  elevation: number;
  cloud_cover: number;
  uv_index: number;
  category: string;
  protection_needed: boolean;
  peak_hours: string;
}

const UV_CATEGORIES = [
  { range: '0-2', label: 'Low', color: 'bg-green-500', advice: 'No protection needed' },
  { range: '3-5', label: 'Moderate', color: 'bg-yellow-500', advice: 'Seek shade during midday' },
  { range: '6-7', label: 'High', color: 'bg-orange-500', advice: 'Protection essential' },
  { range: '8-10', label: 'Very High', color: 'bg-red-500', advice: 'Extra protection needed' },
  { range: '11+', label: 'Extreme', color: 'bg-purple-500', advice: 'Avoid sun exposure' },
];


export function UVIndex() {
  const [latitude, setLatitude] = useState(28.6);
  const [elevation, setElevation] = useState(200);
  const [cloudCover, setCloudCover] = useState(0.3);
  const [data, setData] = useState<UVData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchUVIndex = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `/api/v2/solar/uv-index?latitude=${latitude}&elevation=${elevation}&cloud_cover=${cloudCover}`
      );
      if (res.ok) {
        const json = await res.json();
        setData(json.data);
      }
    } catch {
      // Calculate locally as fallback
      const doy = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) / 86400000);
      const latFactor = Math.cos(latitude * Math.PI / 180);
      const seasonFactor = 1 + 0.3 * Math.cos(2 * Math.PI * (doy - 172) / 365);
      const baseUV = 12 * latFactor * seasonFactor;
      const elevFactor = 1 + 0.04 * (elevation / 300);
      const cloudFactor = 1 - 0.7 * cloudCover;
      const uvIndex = Math.max(0, Math.min(15, baseUV * elevFactor * cloudFactor));
      
      setData({
        date: new Date().toISOString().split('T')[0],
        latitude,
        elevation,
        cloud_cover: cloudCover,
        uv_index: Math.round(uvIndex * 10) / 10,
        category: uvIndex < 3 ? 'Low' : uvIndex < 6 ? 'Moderate' : uvIndex < 8 ? 'High' : uvIndex < 11 ? 'Very High' : 'Extreme',
        protection_needed: uvIndex >= 3,
        peak_hours: '10:00 - 14:00',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUVIndex();
  }, [latitude, elevation, cloudCover]);

  const getUVColor = (uv: number) => {
    if (uv < 3) return 'bg-green-500';
    if (uv < 6) return 'bg-yellow-500';
    if (uv < 8) return 'bg-orange-500';
    if (uv < 11) return 'bg-red-500';
    return 'bg-purple-500';
  };

  const getUVTextColor = (uv: number) => {
    if (uv < 3) return 'text-green-600';
    if (uv < 6) return 'text-yellow-600';
    if (uv < 8) return 'text-orange-600';
    if (uv < 11) return 'text-red-600';
    return 'text-purple-600';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">UV Index</h1>
        <p className="text-gray-600 mt-1">UV radiation levels and field work recommendations</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              Location Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Latitude (°)</Label>
              <Input
                type="number"
                value={latitude}
                onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                min={-90}
                max={90}
                step={0.1}
              />
            </div>
            <div>
              <Label>Elevation (m)</Label>
              <Input
                type="number"
                value={elevation}
                onChange={(e) => setElevation(parseFloat(e.target.value) || 0)}
                min={0}
                max={8848}
              />
              <p className="text-xs text-gray-500 mt-1">UV increases ~4% per 300m</p>
            </div>
            <div>
              <Label>Cloud Cover ({(cloudCover * 100).toFixed(0)}%)</Label>
              <input
                type="range"
                value={cloudCover}
                onChange={(e) => setCloudCover(parseFloat(e.target.value))}
                min={0}
                max={1}
                step={0.1}
                className="w-full"
              />
            </div>
            <Button onClick={fetchUVIndex} disabled={loading} className="w-full">
              Calculate UV Index
            </Button>
          </CardContent>
        </Card>

        {/* UV Index Display */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sun className="h-5 w-5" />
              Current UV Index
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data && (
              <div className="space-y-6">
                <div className="text-center p-8 bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl">
                  <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full ${getUVColor(data.uv_index)} bg-opacity-20`}>
                    <span className={`text-5xl font-bold ${getUVTextColor(data.uv_index)}`}>
                      {data.uv_index}
                    </span>
                  </div>
                  <p className="text-xl font-semibold mt-4">{data.category}</p>
                  <Badge className={`mt-2 ${getUVColor(data.uv_index)}`}>
                    {data.protection_needed ? 'Protection Needed' : 'Safe'}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Peak UV Hours</p>
                    <p className="text-lg font-semibold">{data.peak_hours}</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Date</p>
                    <p className="text-lg font-semibold">{data.date}</p>
                  </div>
                </div>

                {data.protection_needed && (
                  <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-amber-800">Field Work Advisory</p>
                      <p className="text-sm text-amber-700 mt-1">
                        Schedule outdoor activities before 10 AM or after 4 PM. 
                        Use protective clothing and sunscreen for extended field work.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* UV Scale Reference */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            UV Index Scale
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-2">
            {UV_CATEGORIES.map((cat) => (
              <div key={cat.label} className="text-center">
                <div className={`h-4 ${cat.color} rounded-t-lg`} />
                <div className="p-3 border border-t-0 rounded-b-lg">
                  <p className="font-semibold">{cat.label}</p>
                  <p className="text-sm text-gray-500">{cat.range}</p>
                  <p className="text-xs text-gray-600 mt-1">{cat.advice}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Plant UV Effects */}
      <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
        <CardHeader>
          <CardTitle className="text-green-800">🌱 UV Effects on Plants</CardTitle>
        </CardHeader>
        <CardContent className="text-green-700">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium">Beneficial Effects</h4>
              <ul className="text-sm list-disc list-inside mt-1 space-y-1">
                <li>Increased flavonoid and anthocyanin production</li>
                <li>Enhanced disease resistance compounds</li>
                <li>Improved nutritional quality in some crops</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium">Stress Responses</h4>
              <ul className="text-sm list-disc list-inside mt-1 space-y-1">
                <li>DNA damage at high UV-B levels</li>
                <li>Reduced photosynthesis efficiency</li>
                <li>Leaf curling and thickness changes</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default UVIndex;
