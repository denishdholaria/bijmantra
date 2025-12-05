/**
 * Weather Forecast Page
 *
 * Detailed weather forecasts for agricultural planning.
 */

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function WeatherForecast() {
  const { data: forecast } = useQuery({
    queryKey: ['earth-systems', 'weather-forecast'],
    queryFn: async () => ({
      hourly: Array.from({ length: 24 }, (_, i) => ({
        hour: `${i}:00`,
        temp: 20 + Math.sin(i / 4) * 8,
        humidity: 60 + Math.cos(i / 3) * 15,
        precip: i >= 14 && i <= 18 ? Math.random() * 5 : 0,
      })),
      daily: Array.from({ length: 7 }, (_, i) => ({
        day: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][(new Date().getDay() + i) % 7],
        high: 28 + Math.random() * 6,
        low: 18 + Math.random() * 4,
        precip: Math.random() * 20,
        humidity: 55 + Math.random() * 25,
        condition: ['☀️', '⛅', '🌤️', '🌧️', '⛈️'][Math.floor(Math.random() * 5)],
      })),
    }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Weather Forecast</h1>
        <p className="text-gray-600 mt-1">7-day agricultural weather outlook</p>
      </div>

      {/* 7-Day Forecast */}
      <Card>
        <CardHeader><CardTitle>7-Day Forecast</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-2">
            {forecast?.daily.map((day, i) => (
              <div key={i} className="text-center p-3 rounded-lg bg-gray-50 hover:bg-gray-100">
                <div className="font-medium">{day.day}</div>
                <div className="text-4xl my-3">{day.condition}</div>
                <div className="text-lg font-bold text-red-500">{day.high.toFixed(0)}°</div>
                <div className="text-sm text-blue-500">{day.low.toFixed(0)}°</div>
                <div className="text-xs text-gray-500 mt-2">💧 {day.precip.toFixed(0)}mm</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Agricultural Impact */}
      <Card>
        <CardHeader><CardTitle>🌾 Agricultural Impact</CardTitle></CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <ImpactCard title="Irrigation" status="moderate" description="Reduce irrigation mid-week due to expected rainfall" />
            <ImpactCard title="Spraying" status="good" description="Optimal conditions Mon-Wed for pesticide application" />
            <ImpactCard title="Harvesting" status="caution" description="Complete harvest before Thursday rain event" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ImpactCard({ title, status, description }: { title: string; status: 'good' | 'moderate' | 'caution'; description: string }) {
  const colors = { good: 'border-green-300 bg-green-50', moderate: 'border-yellow-300 bg-yellow-50', caution: 'border-red-300 bg-red-50' };
  const icons = { good: '✅', moderate: '⚠️', caution: '🚨' };
  return (
    <div className={`p-4 rounded-lg border-2 ${colors[status]}`}>
      <div className="flex items-center gap-2 font-medium mb-2">{icons[status]} {title}</div>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}

export default WeatherForecast;
