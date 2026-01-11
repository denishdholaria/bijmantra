/**
 * Weather Forecast Page
 *
 * Detailed weather forecasts for agricultural planning.
 * Connected to /api/v2/weather endpoints.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  CloudSun, Droplets, Wind, Thermometer, RefreshCw,
  AlertTriangle, CheckCircle, Calendar, Sprout
} from 'lucide-react';

interface DailyForecast {
  date: string;
  temp_high_c: number;
  temp_low_c: number;
  humidity_percent: number;
  precipitation_mm: number;
  wind_speed_kmh: number;
  conditions: string;
  uv_index: number;
}

interface WeatherAlert {
  type: string;
  severity: string;
  message: string;
  start_date: string;
  end_date: string;
}

interface ActivityWindow {
  activity: string;
  start: string;
  end: string;
  confidence: number;
  conditions: string;
}

interface GDDData {
  date: string;
  daily_gdd: number;
  cumulative_gdd: number;
}

interface ForecastData {
  location_id: string;
  location_name: string;
  generated_at: string;
  daily_forecasts: DailyForecast[];
  alerts: WeatherAlert[];
  gdd_summary: { accumulated: number; base_temp: number };
}

export function WeatherForecast() {
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [activityWindows, setActivityWindows] = useState<ActivityWindow[]>([]);
  const [gddData, setGddData] = useState<GDDData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLocation, setSelectedLocation] = useState('LOC-001');
  const [selectedCrop, setSelectedCrop] = useState('wheat');

  const locations = [
    { id: 'LOC-001', name: 'Main Station' },
    { id: 'LOC-002', name: 'North Field' },
    { id: 'LOC-003', name: 'South Trial' },
  ];

  const crops = [
    { id: 'wheat', name: 'Wheat', baseTemp: 0 },
    { id: 'rice', name: 'Rice', baseTemp: 10 },
    { id: 'maize', name: 'Maize', baseTemp: 10 },
    { id: 'cotton', name: 'Cotton', baseTemp: 15.5 },
  ];

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    const locationName = locations.find(l => l.id === selectedLocation)?.name || 'Location';
    
    try {
      const [forecastRes, windowsRes, gddRes] = await Promise.all([
        fetch(`/api/v2/weather/forecast/${selectedLocation}?location_name=${encodeURIComponent(locationName)}&days=14&crop=${selectedCrop}`),
        fetch(`/api/v2/weather/activity-windows/${selectedLocation}?location_name=${encodeURIComponent(locationName)}&days=14`),
        fetch(`/api/v2/weather/gdd/${selectedLocation}?location_name=${encodeURIComponent(locationName)}&crop=${selectedCrop}&days=14`),
      ]);

      if (forecastRes.ok) {
        const data = await forecastRes.json();
        setForecast(data);
      } else {
        throw new Error('Failed to fetch forecast');
      }

      if (windowsRes.ok) {
        const data = await windowsRes.json();
        setActivityWindows(data.windows || []);
      }

      if (gddRes.ok) {
        const data = await gddRes.json();
        setGddData(data.gdd_data || []);
      }
    } catch (err) {
      setError('Weather service unavailable');
      // Demo fallback
      setForecast({
        location_id: selectedLocation,
        location_name: locationName,
        generated_at: new Date().toISOString(),
        daily_forecasts: Array.from({ length: 14 }, (_, i) => ({
          date: new Date(Date.now() + i * 86400000).toISOString(),
          temp_high_c: 28 + Math.sin(i / 3) * 5,
          temp_low_c: 18 + Math.sin(i / 3) * 3,
          humidity_percent: 60 + Math.cos(i / 2) * 15,
          precipitation_mm: i % 4 === 3 ? Math.random() * 15 : 0,
          wind_speed_kmh: 8 + Math.random() * 10,
          conditions: ['Sunny', 'Partly Cloudy', 'Cloudy', 'Rain'][i % 4],
          uv_index: 6 + Math.floor(Math.random() * 4),
        })),
        alerts: [
          { type: 'heat', severity: 'warning', message: 'High temperatures expected', start_date: new Date().toISOString(), end_date: new Date(Date.now() + 172800000).toISOString() },
        ],
        gdd_summary: { accumulated: 850, base_temp: crops.find(c => c.id === selectedCrop)?.baseTemp || 10 },
      });
      setActivityWindows([
        { activity: 'planting', start: new Date().toISOString(), end: new Date(Date.now() + 259200000).toISOString(), confidence: 0.85, conditions: 'Good soil moisture' },
        { activity: 'spraying', start: new Date(Date.now() + 86400000).toISOString(), end: new Date(Date.now() + 172800000).toISOString(), confidence: 0.92, conditions: 'Low wind' },
        { activity: 'harvesting', start: new Date(Date.now() + 432000000).toISOString(), end: new Date(Date.now() + 604800000).toISOString(), confidence: 0.78, conditions: 'Dry period' },
      ]);
      setGddData(Array.from({ length: 14 }, (_, i) => ({
        date: new Date(Date.now() + i * 86400000).toISOString(),
        daily_gdd: 15 + Math.random() * 10,
        cumulative_gdd: 850 + (i + 1) * 18,
      })));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedLocation, selectedCrop]);

  const getConditionEmoji = (condition: string) => {
    const map: Record<string, string> = {
      'Sunny': '☀️', 'Clear': '☀️', 'Partly Cloudy': '⛅', 'Cloudy': '☁️',
      'Rain': '🌧️', 'Thunderstorm': '⛈️', 'Snow': '❄️', 'Fog': '🌫️',
    };
    return map[condition] || '🌤️';
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">Weather Forecast</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">14-day agricultural weather outlook</p>
          {error && <Badge variant="outline" className="mt-1 text-yellow-600">{error} - Demo Mode</Badge>}
        </div>
        <div className="flex gap-2">
          <Select value={selectedLocation} onValueChange={setSelectedLocation}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Location" />
            </SelectTrigger>
            <SelectContent>
              {locations.map(loc => (
                <SelectItem key={loc.id} value={loc.id}>{loc.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedCrop} onValueChange={setSelectedCrop}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Crop" />
            </SelectTrigger>
            <SelectContent>
              {crops.map(crop => (
                <SelectItem key={crop.id} value={crop.id}>{crop.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={fetchData} disabled={loading} aria-label="Refresh weather forecast">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* 14-Day Forecast */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CloudSun className="h-5 w-5" />
            14-Day Forecast
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-48" />
          ) : (
            <div className="grid grid-cols-7 gap-2">
              {forecast?.daily_forecasts.slice(0, 7).map((day, i) => (
                <div key={i} className="text-center p-3 rounded-lg bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors">
                  <div className="font-medium text-sm">{i === 0 ? 'Today' : formatDate(day.date).split(' ')[0]}</div>
                  <div className="text-3xl my-2">{getConditionEmoji(day.conditions)}</div>
                  <div className="text-lg font-bold text-red-500">{day.temp_high_c.toFixed(0)}°</div>
                  <div className="text-sm text-blue-500">{day.temp_low_c.toFixed(0)}°</div>
                  {day.precipitation_mm > 0 && (
                    <div className="text-xs text-blue-600 mt-1 flex items-center justify-center gap-1">
                      <Droplets className="h-3 w-3" />
                      {day.precipitation_mm.toFixed(0)}mm
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          {/* Week 2 */}
          {!loading && forecast && (
            <div className="mt-4 pt-4 border-t">
              <div className="text-sm text-muted-foreground mb-2">Week 2</div>
              <div className="grid grid-cols-7 gap-2">
                {forecast.daily_forecasts.slice(7, 14).map((day, i) => (
                  <div key={i} className="text-center p-2 rounded-lg bg-gray-50/50 dark:bg-slate-800/50">
                    <div className="text-xs text-muted-foreground">{formatDate(day.date).split(' ')[0]}</div>
                    <div className="text-xl my-1">{getConditionEmoji(day.conditions)}</div>
                    <div className="text-sm">
                      <span className="text-red-500">{day.temp_high_c.toFixed(0)}°</span>
                      <span className="text-gray-400">/</span>
                      <span className="text-blue-500">{day.temp_low_c.toFixed(0)}°</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Activity Windows */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Optimal Activity Windows
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-32" />
            ) : activityWindows.length === 0 ? (
              <p className="text-muted-foreground">No optimal windows found</p>
            ) : (
              <div className="space-y-3">
                {activityWindows.map((window, i) => (
                  <div key={i} className="p-3 rounded-lg border bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <span className="font-medium capitalize">{window.activity}</span>
                      </div>
                      <Badge variant="outline" className="bg-green-100 text-green-700">
                        {(window.confidence * 100).toFixed(0)}% confidence
                      </Badge>
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {formatDate(window.start)} - {formatDate(window.end)}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">{window.conditions}</div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* GDD Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sprout className="h-5 w-5" />
              Growing Degree Days ({selectedCrop})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-32" />
            ) : (
              <>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
                    <div className="text-2xl font-bold text-green-700 dark:text-green-400">
                      {forecast?.gdd_summary.accumulated || gddData[gddData.length - 1]?.cumulative_gdd.toFixed(0) || 0}
                    </div>
                    <div className="text-sm text-green-600 dark:text-green-400">Accumulated GDD</div>
                  </div>
                  <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                    <div className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                      {forecast?.gdd_summary.base_temp || crops.find(c => c.id === selectedCrop)?.baseTemp}°C
                    </div>
                    <div className="text-sm text-blue-600 dark:text-blue-400">Base Temperature</div>
                  </div>
                </div>
                <div className="h-24 flex items-end gap-1">
                  {gddData.slice(0, 14).map((day, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-green-500 rounded-t hover:bg-green-600 transition-colors"
                      style={{ height: `${Math.min(100, (day.daily_gdd / 30) * 100)}%` }}
                      title={`${formatDate(day.date)}: ${day.daily_gdd.toFixed(1)} GDD`}
                    />
                  ))}
                </div>
                <div className="text-xs text-muted-foreground mt-2 text-center">Daily GDD (14 days)</div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Weather Alerts */}
      {forecast?.alerts && forecast.alerts.length > 0 && (
        <Card className="border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-800 dark:text-yellow-300">
              <AlertTriangle className="h-5 w-5" />
              Weather Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {forecast.alerts.map((alert, i) => (
                <div key={i} className="p-3 rounded-lg bg-white dark:bg-slate-800 border border-yellow-200 dark:border-yellow-800">
                  <div className="flex items-center gap-2">
                    <Badge variant={alert.severity === 'warning' ? 'destructive' : 'secondary'}>
                      {alert.severity}
                    </Badge>
                    <span className="font-medium capitalize">{alert.type}</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{alert.message}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    {formatDate(alert.start_date)} - {formatDate(alert.end_date)}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agricultural Impact */}
      <Card>
        <CardHeader>
          <CardTitle>🌾 Agricultural Impact Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <ImpactCard 
              title="Irrigation" 
              status={forecast?.daily_forecasts.some(d => d.precipitation_mm > 10) ? 'good' : 'moderate'} 
              description={forecast?.daily_forecasts.some(d => d.precipitation_mm > 10) 
                ? "Reduce irrigation due to expected rainfall" 
                : "Normal irrigation schedule recommended"} 
            />
            <ImpactCard 
              title="Spraying" 
              status={activityWindows.some(w => w.activity === 'spraying') ? 'good' : 'caution'} 
              description={activityWindows.find(w => w.activity === 'spraying')?.conditions || "Check wind conditions before spraying"} 
            />
            <ImpactCard 
              title="Harvesting" 
              status={activityWindows.some(w => w.activity === 'harvesting') ? 'good' : 'moderate'} 
              description={activityWindows.find(w => w.activity === 'harvesting')?.conditions || "Monitor weather for dry windows"} 
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ImpactCard({ title, status, description }: { title: string; status: 'good' | 'moderate' | 'caution'; description: string }) {
  const colors = { 
    good: 'border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-900/20', 
    moderate: 'border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20', 
    caution: 'border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20' 
  };
  const icons = { good: '✅', moderate: '⚠️', caution: '🚨' };
  return (
    <div className={`p-4 rounded-lg border-2 ${colors[status]}`}>
      <div className="flex items-center gap-2 font-medium mb-2">{icons[status]} {title}</div>
      <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
    </div>
  );
}

export default WeatherForecast;
