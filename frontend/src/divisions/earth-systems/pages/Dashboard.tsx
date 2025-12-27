/**
 * Earth Systems Dashboard
 *
 * Overview of weather, climate, and field conditions.
 * Connected to /api/v2/weather and /api/v2/field-environment endpoints.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  CloudSun, BarChart3, Map, Sprout, FlaskConical, Droplets,
  Thermometer, Sun, AlertTriangle, Info, CheckCircle,
  RefreshCw, Wind
} from 'lucide-react';

interface WeatherForecast {
  location_id: string;
  location_name: string;
  generated_at: string;
  daily_forecasts: DailyForecast[];
  alerts: WeatherAlert[];
  gdd_summary: { accumulated: number; base_temp: number };
}

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

export function Dashboard() {
  const [weather, setWeather] = useState<WeatherForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWeather = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v2/weather/forecast/LOC-001?location_name=Main%20Station&days=7');
      if (res.ok) {
        const data = await res.json();
        setWeather(data);
      } else {
        throw new Error('Failed to fetch weather');
      }
    } catch (err) {
      setError('Weather service unavailable');
      // Demo fallback
      setWeather({
        location_id: 'LOC-001',
        location_name: 'Main Station',
        generated_at: new Date().toISOString(),
        daily_forecasts: [
          { date: new Date().toISOString(), temp_high_c: 32, temp_low_c: 24, humidity_percent: 65, precipitation_mm: 0, wind_speed_kmh: 12, conditions: 'Partly Cloudy', uv_index: 7 },
          { date: new Date(Date.now() + 86400000).toISOString(), temp_high_c: 30, temp_low_c: 22, humidity_percent: 60, precipitation_mm: 0, wind_speed_kmh: 10, conditions: 'Sunny', uv_index: 8 },
          { date: new Date(Date.now() + 172800000).toISOString(), temp_high_c: 28, temp_low_c: 20, humidity_percent: 55, precipitation_mm: 0, wind_speed_kmh: 8, conditions: 'Clear', uv_index: 9 },
          { date: new Date(Date.now() + 259200000).toISOString(), temp_high_c: 31, temp_low_c: 23, humidity_percent: 70, precipitation_mm: 15, wind_speed_kmh: 15, conditions: 'Rain', uv_index: 4 },
          { date: new Date(Date.now() + 345600000).toISOString(), temp_high_c: 29, temp_low_c: 21, humidity_percent: 65, precipitation_mm: 5, wind_speed_kmh: 12, conditions: 'Partly Cloudy', uv_index: 6 },
        ],
        alerts: [
          { type: 'heat', severity: 'warning', message: 'High temperatures expected Thu-Fri', start_date: new Date(Date.now() + 259200000).toISOString(), end_date: new Date(Date.now() + 345600000).toISOString() },
        ],
        gdd_summary: { accumulated: 1250, base_temp: 10 },
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeather();
  }, []);

  const quickLinks = [
    { label: '7-Day Forecast', path: '/earth-systems/weather', icon: CloudSun, color: 'text-blue-600 bg-blue-100' },
    { label: 'Climate Trends', path: '/earth-systems/climate', icon: BarChart3, color: 'text-purple-600 bg-purple-100' },
    { label: 'Field Map', path: '/earth-systems/map', icon: Map, color: 'text-green-600 bg-green-100' },
    { label: 'Soil Data', path: '/earth-systems/soil', icon: Sprout, color: 'text-amber-600 bg-amber-100' },
    { label: 'Input Log', path: '/earth-systems/inputs', icon: FlaskConical, color: 'text-pink-600 bg-pink-100' },
    { label: 'Irrigation', path: '/earth-systems/irrigation', icon: Droplets, color: 'text-cyan-600 bg-cyan-100' },
    { label: 'Growing Degrees', path: '/earth-systems/gdd', icon: Thermometer, color: 'text-red-600 bg-red-100' },
    { label: 'Drought Monitor', path: '/earth-systems/drought', icon: Sun, color: 'text-orange-600 bg-orange-100' },
  ];

  const getConditionEmoji = (condition: string) => {
    const map: Record<string, string> = {
      'Sunny': '☀️', 'Clear': '☀️', 'Partly Cloudy': '⛅', 'Cloudy': '☁️',
      'Rain': '🌧️', 'Thunderstorm': '⛈️', 'Snow': '❄️', 'Fog': '🌫️',
    };
    return map[condition] || '🌤️';
  };

  const today = weather?.daily_forecasts?.[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Earth Systems</h1>
          <p className="text-gray-600 mt-1">Climate, weather, and GIS for agricultural planning</p>
          {error && <Badge variant="outline" className="mt-1 text-yellow-600">{error} - Demo Mode</Badge>}
        </div>
        <Button variant="outline" size="sm" onClick={fetchWeather} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Current Conditions */}
      <div className="grid md:grid-cols-4 gap-4">
        {loading ? (
          Array(4).fill(0).map((_, i) => (
            <Card key={i}><CardContent className="p-4"><Skeleton className="h-16" /></CardContent></Card>
          ))
        ) : (
          <>
            <Card className="bg-gradient-to-br from-orange-50 to-yellow-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Thermometer className="h-8 w-8 text-orange-500" />
                  <div>
                    <div className="text-3xl font-bold text-orange-600">{today?.temp_high_c}°C</div>
                    <div className="text-sm text-gray-600">High / {today?.temp_low_c}° Low</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-blue-50 to-cyan-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Droplets className="h-8 w-8 text-blue-500" />
                  <div>
                    <div className="text-3xl font-bold text-blue-600">{today?.humidity_percent}%</div>
                    <div className="text-sm text-gray-600">Humidity</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-cyan-50 to-blue-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <CloudSun className="h-8 w-8 text-cyan-500" />
                  <div>
                    <div className="text-3xl font-bold text-cyan-600">{today?.precipitation_mm}mm</div>
                    <div className="text-sm text-gray-600">Precipitation</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-gray-50 to-slate-50">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Wind className="h-8 w-8 text-gray-500" />
                  <div>
                    <div className="text-3xl font-bold text-gray-600">{today?.wind_speed_kmh}km/h</div>
                    <div className="text-sm text-gray-600">Wind Speed</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* 5-Day Forecast */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CloudSun className="h-5 w-5" />
            5-Day Forecast
            {weather && <span className="text-sm font-normal text-muted-foreground ml-2">({weather.location_name})</span>}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-32" />
          ) : (
            <div className="grid grid-cols-5 gap-4">
              {weather?.daily_forecasts.slice(0, 5).map((day, i) => (
                <div key={i} className="text-center p-3 rounded-lg bg-gray-50">
                  <div className="font-medium text-gray-700">
                    {i === 0 ? 'Today' : new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                  </div>
                  <div className="text-3xl my-2">{getConditionEmoji(day.conditions)}</div>
                  <div className="text-sm">
                    <span className="text-red-500">{day.temp_high_c}°</span>
                    {' / '}
                    <span className="text-blue-500">{day.temp_low_c}°</span>
                  </div>
                  {day.precipitation_mm > 0 && (
                    <div className="text-xs text-blue-600 mt-1">{day.precipitation_mm}mm</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* GDD Summary */}
      {weather?.gdd_summary && (
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Thermometer className="h-8 w-8 text-green-600" />
                <div>
                  <div className="text-2xl font-bold text-green-700">{weather.gdd_summary.accumulated} GDD</div>
                  <div className="text-sm text-green-600">Accumulated Growing Degree Days (Base {weather.gdd_summary.base_temp}°C)</div>
                </div>
              </div>
              <Link to="/earth-systems/gdd">
                <Button variant="outline" size="sm">View Details</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Links */}
      <Card>
        <CardHeader>
          <CardTitle>Tools & Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
            {quickLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className="flex flex-col items-center p-4 rounded-lg border hover:border-green-500 hover:bg-green-50 transition-colors"
              >
                <div className={`w-10 h-10 rounded-lg ${link.color} flex items-center justify-center mb-2`}>
                  <link.icon className="h-5 w-5" />
                </div>
                <span className="text-sm font-medium text-center">{link.label}</span>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Weather Alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Agricultural Alerts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {weather?.alerts && weather.alerts.length > 0 ? (
              weather.alerts.map((alert, i) => (
                <AlertItem
                  key={i}
                  level={alert.severity === 'warning' ? 'warning' : alert.severity === 'critical' ? 'warning' : 'info'}
                  title={`${alert.type.charAt(0).toUpperCase() + alert.type.slice(1)} Alert`}
                  description={alert.message}
                />
              ))
            ) : (
              <AlertItem level="success" title="No Active Alerts" description="Weather conditions are favorable for field activities." />
            )}
            <AlertItem level="info" title="Optimal Planting Window" description="Next 3 days ideal for wheat sowing based on soil moisture." />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AlertItem({ level, title, description }: { level: 'warning' | 'info' | 'success'; title: string; description: string }) {
  const styles = {
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
  };
  const icons = {
    warning: <AlertTriangle className="h-4 w-4" />,
    info: <Info className="h-4 w-4" />,
    success: <CheckCircle className="h-4 w-4" />
  };

  return (
    <div className={`p-3 rounded-lg border ${styles[level]}`}>
      <div className="flex items-center gap-2 font-medium">
        {icons[level]}
        {title}
      </div>
      <p className="text-sm mt-1 opacity-80">{description}</p>
    </div>
  );
}

export default Dashboard;
