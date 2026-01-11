/**
 * Solar Activity Page
 *
 * Real-time solar conditions and space weather monitoring.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Sun, Wind, Activity, AlertTriangle } from 'lucide-react';

interface SolarConditions {
  timestamp: string;
  sunspot_number: number;
  solar_flux_f107: number;
  solar_flux_unit: string;
  solar_wind_speed: number;
  solar_wind_unit: string;
  kp_index: number;
  geomagnetic_storm: boolean;
  solar_flare_probability: {
    C_class: number;
    M_class: number;
    X_class: number;
  };
  cycle_phase: string;
  cycle_number: number;
}

interface ForecastDay {
  date: string;
  sunspot_number: number;
  kp_index_forecast: number;
  geomagnetic_activity: string;
  aurora_probability: number;
}

interface GeomagneticData {
  timestamp: string;
  kp_index: number;
  kp_category: string;
  dst_index: number;
  dst_unit: string;
  bz_component: number;
  bz_unit: string;
  aurora_oval: string;
  radio_blackout_risk: string;
}

export function SolarActivity() {
  const [conditions, setConditions] = useState<SolarConditions | null>(null);
  const [forecast, setForecast] = useState<ForecastDay[]>([]);
  const [magnetic, setMagnetic] = useState<GeomagneticData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [condRes, forecastRes, magRes] = await Promise.all([
        fetch('/api/v2/solar/current'),
        fetch('/api/v2/solar/forecast?days=7'),
        fetch('/api/v2/solar/magnetic'),
      ]);

      if (condRes.ok) {
        const data = await condRes.json();
        setConditions(data.data);
      }
      if (forecastRes.ok) {
        const data = await forecastRes.json();
        setForecast(data.data);
      }
      if (magRes.ok) {
        const data = await magRes.json();
        setMagnetic(data.data);
      }
    } catch (err) {
      setError('Failed to fetch solar data - backend unavailable');
      // Zero Mock Data Policy - show empty state
      setConditions(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const getKpColor = (kp: number) => {
    if (kp < 2) return 'bg-green-500';
    if (kp < 4) return 'bg-yellow-500';
    if (kp < 6) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Solar Activity</h1>
          <p className="text-gray-600 mt-1">Real-time solar and space weather conditions</p>
        </div>
        <Button onClick={fetchData} disabled={loading} variant="outline">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-yellow-600" />
          <span className="text-yellow-800">{error} - Showing demo data</span>
        </div>
      )}

      {/* Current Conditions */}
      {conditions && (
        <div className="grid md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-100 rounded-lg">
                  <Sun className="h-6 w-6 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Sunspot Number</p>
                  <p className="text-2xl font-bold">{conditions.sunspot_number}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Activity className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Solar Flux (F10.7)</p>
                  <p className="text-2xl font-bold">{conditions.solar_flux_f107} <span className="text-sm font-normal">sfu</span></p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Wind className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Solar Wind</p>
                  <p className="text-2xl font-bold">{conditions.solar_wind_speed} <span className="text-sm font-normal">km/s</span></p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${getKpColor(conditions.kp_index)} bg-opacity-20`}>
                  <Activity className={`h-6 w-6 ${conditions.kp_index >= 4 ? 'text-orange-600' : 'text-green-600'}`} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Kp Index</p>
                  <p className="text-2xl font-bold">{conditions.kp_index}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Solar Cycle Info */}
        {conditions && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sun className="h-5 w-5" />
                Solar Cycle {conditions.cycle_number}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Current Phase</span>
                <Badge variant="outline" className="bg-amber-50">{conditions.cycle_phase}</Badge>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">Solar Flare Probability (24h)</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">C-class</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-yellow-500"
                          style={{ width: `${conditions.solar_flare_probability.C_class * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">{(conditions.solar_flare_probability.C_class * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">M-class</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-orange-500"
                          style={{ width: `${conditions.solar_flare_probability.M_class * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">{(conditions.solar_flare_probability.M_class * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">X-class</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-red-500"
                          style={{ width: `${conditions.solar_flare_probability.X_class * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">{(conditions.solar_flare_probability.X_class * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Geomagnetic Data */}
        {magnetic && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                🧲 Geomagnetic Conditions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Kp Index</span>
                <Badge className={getKpColor(magnetic.kp_index)}>{magnetic.kp_index} - {magnetic.kp_category}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Dst Index</span>
                <span className="font-medium">{magnetic.dst_index} {magnetic.dst_unit}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Bz Component</span>
                <span className="font-medium">{magnetic.bz_component} {magnetic.bz_unit}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Aurora Oval</span>
                <Badge variant="outline">{magnetic.aurora_oval}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Radio Blackout Risk</span>
                <Badge variant={magnetic.radio_blackout_risk === 'Low' ? 'outline' : 'destructive'}>
                  {magnetic.radio_blackout_risk}
                </Badge>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 7-Day Forecast */}
      <Card>
        <CardHeader>
          <CardTitle>7-Day Solar Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-2">
            {forecast.map((day, i) => (
              <div key={i} className="text-center p-3 border rounded-lg">
                <p className="text-xs text-gray-500">
                  {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                </p>
                <p className="text-sm font-medium mt-1">
                  {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </p>
                <div className="mt-2">
                  <p className="text-lg font-bold">{day.sunspot_number}</p>
                  <p className="text-xs text-gray-500">sunspots</p>
                </div>
                <Badge
                  variant="outline"
                  className={`mt-2 text-xs ${day.geomagnetic_activity === 'Quiet' ? 'bg-green-50' : 'bg-yellow-50'}`}
                >
                  {day.geomagnetic_activity}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Agricultural Relevance */}
      <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
        <CardHeader>
          <CardTitle className="text-green-800">🌱 Agricultural Relevance</CardTitle>
        </CardHeader>
        <CardContent className="text-green-700 space-y-2">
          <p>Solar activity affects agriculture through:</p>
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li>UV radiation levels impacting plant stress and secondary metabolites</li>
            <li>Cosmic ray flux variations affecting natural mutation rates</li>
            <li>Geomagnetic disturbances potentially influencing plant orientation</li>
            <li>Solar cycle correlations with climate patterns and crop yields</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

export default SolarActivity;
