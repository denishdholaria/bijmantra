/**
 * Earth Systems Dashboard
 *
 * Overview of weather, climate, and field conditions.
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface WeatherData {
  temperature: number;
  humidity: number;
  precipitation: number;
  windSpeed: number;
  condition: string;
  forecast: { day: string; high: number; low: number; condition: string }[];
}

export function Dashboard() {
  const { data: weather, isLoading } = useQuery<WeatherData>({
    queryKey: ['earth-systems', 'weather-current'],
    queryFn: async () => ({
      temperature: 28,
      humidity: 65,
      precipitation: 0,
      windSpeed: 12,
      condition: 'Partly Cloudy',
      forecast: [
        { day: 'Today', high: 32, low: 24, condition: '⛅' },
        { day: 'Tomorrow', high: 30, low: 22, condition: '🌤️' },
        { day: 'Wed', high: 28, low: 20, condition: '☀️' },
        { day: 'Thu', high: 31, low: 23, condition: '🌧️' },
        { day: 'Fri', high: 29, low: 21, condition: '⛅' },
      ],
    }),
  });

  const quickLinks = [
    { label: '7-Day Forecast', path: '/earth-systems/weather', icon: '🌤️' },
    { label: 'Climate Trends', path: '/earth-systems/climate', icon: '📊' },
    { label: 'Field Map', path: '/earth-systems/map', icon: '🗺️' },
    { label: 'Soil Data', path: '/earth-systems/soil', icon: '🌱' },
    { label: 'Growing Degrees', path: '/earth-systems/gdd', icon: '🌡️' },
    { label: 'Drought Monitor', path: '/earth-systems/drought', icon: '💧' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Earth Systems</h1>
        <p className="text-gray-600 mt-1">Climate, weather, and GIS for agricultural planning</p>
      </div>

      {/* Current Conditions */}
      <div className="grid md:grid-cols-4 gap-4">
        {isLoading ? (
          Array(4).fill(0).map((_, i) => (
            <Card key={i}><CardContent className="p-4"><Skeleton className="h-16" /></CardContent></Card>
          ))
        ) : (
          <>
            <Card className="bg-gradient-to-br from-orange-50 to-yellow-50">
              <CardContent className="p-4 text-center">
                <div className="text-3xl font-bold text-orange-600">{weather?.temperature}°C</div>
                <div className="text-sm text-gray-600">Temperature</div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-blue-50 to-cyan-50">
              <CardContent className="p-4 text-center">
                <div className="text-3xl font-bold text-blue-600">{weather?.humidity}%</div>
                <div className="text-sm text-gray-600">Humidity</div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-cyan-50 to-blue-50">
              <CardContent className="p-4 text-center">
                <div className="text-3xl font-bold text-cyan-600">{weather?.precipitation}mm</div>
                <div className="text-sm text-gray-600">Precipitation</div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-gray-50 to-slate-50">
              <CardContent className="p-4 text-center">
                <div className="text-3xl font-bold text-gray-600">{weather?.windSpeed}km/h</div>
                <div className="text-sm text-gray-600">Wind Speed</div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* 5-Day Forecast */}
      <Card>
        <CardHeader>
          <CardTitle>5-Day Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-4">
            {weather?.forecast.map((day, i) => (
              <div key={i} className="text-center p-3 rounded-lg bg-gray-50">
                <div className="font-medium text-gray-700">{day.day}</div>
                <div className="text-3xl my-2">{day.condition}</div>
                <div className="text-sm">
                  <span className="text-red-500">{day.high}°</span>
                  {' / '}
                  <span className="text-blue-500">{day.low}°</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <Card>
        <CardHeader>
          <CardTitle>Tools & Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {quickLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className="flex flex-col items-center p-4 rounded-lg border hover:border-green-500 hover:bg-green-50 transition-colors"
              >
                <span className="text-3xl mb-2">{link.icon}</span>
                <span className="text-sm font-medium text-center">{link.label}</span>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Agricultural Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>🚨 Agricultural Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <AlertItem level="warning" title="Heat Advisory" description="High temperatures expected Thu-Fri. Consider irrigation scheduling." />
            <AlertItem level="info" title="Optimal Planting Window" description="Next 3 days ideal for wheat sowing based on soil moisture." />
            <AlertItem level="success" title="Rainfall Expected" description="10-15mm rain forecast Thursday. Delay fertilizer application." />
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
  const icons = { warning: '⚠️', info: 'ℹ️', success: '✅' };

  return (
    <div className={`p-3 rounded-lg border ${styles[level]}`}>
      <div className="flex items-center gap-2 font-medium">
        <span>{icons[level]}</span>
        {title}
      </div>
      <p className="text-sm mt-1 opacity-80">{description}</p>
    </div>
  );
}

export default Dashboard;
