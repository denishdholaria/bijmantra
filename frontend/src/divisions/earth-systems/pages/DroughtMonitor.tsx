/**
 * Drought Monitor Page
 *
 * Monitor drought conditions and water stress indicators.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function DroughtMonitor() {
  const indicators = [
    { name: 'Soil Moisture Index', value: 0.65, status: 'Moderate', trend: 'declining' },
    { name: 'Vegetation Health (NDVI)', value: 0.72, status: 'Good', trend: 'stable' },
    { name: 'Evapotranspiration', value: 5.2, unit: 'mm/day', status: 'High', trend: 'increasing' },
    { name: 'Days Since Rain', value: 12, unit: 'days', status: 'Watch', trend: 'increasing' },
  ];

  const regions = [
    { name: 'North Block', status: 'D0', description: 'Abnormally Dry', color: 'bg-yellow-200' },
    { name: 'South Block', status: 'D1', description: 'Moderate Drought', color: 'bg-orange-300' },
    { name: 'East Field', status: 'None', description: 'No Drought', color: 'bg-green-200' },
    { name: 'Trial Plots', status: 'D0', description: 'Abnormally Dry', color: 'bg-yellow-200' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Drought Monitor</h1>
        <p className="text-gray-600 mt-1">Monitor drought conditions and water stress</p>
      </div>

      {/* Current Status */}
      <Card className="border-orange-200 bg-orange-50">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="text-5xl">⚠️</div>
            <div>
              <div className="text-xl font-bold text-orange-800">Drought Watch Active</div>
              <p className="text-orange-700">Below-normal rainfall for 2 consecutive weeks. Monitor soil moisture closely.</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Indicators Grid */}
      <div className="grid md:grid-cols-4 gap-4">
        {indicators.map((ind) => (
          <Card key={ind.name}>
            <CardContent className="p-4">
              <div className="text-sm text-gray-500">{ind.name}</div>
              <div className="text-2xl font-bold mt-1">
                {ind.value}{ind.unit && <span className="text-sm font-normal text-gray-500 ml-1">{ind.unit}</span>}
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className={`text-xs px-2 py-0.5 rounded ${
                  ind.status === 'Good' ? 'bg-green-100 text-green-700' :
                  ind.status === 'Moderate' ? 'bg-yellow-100 text-yellow-700' :
                  ind.status === 'High' || ind.status === 'Watch' ? 'bg-orange-100 text-orange-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{ind.status}</span>
                <span className="text-xs text-gray-500">
                  {ind.trend === 'increasing' ? '📈' : ind.trend === 'declining' ? '📉' : '➡️'} {ind.trend}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Regional Status */}
      <Card>
        <CardHeader><CardTitle>🗺️ Regional Drought Status</CardTitle></CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {regions.map((region) => (
              <div key={region.name} className={`p-4 rounded-lg ${region.color}`}>
                <div className="flex items-center justify-between">
                  <span className="font-medium">{region.name}</span>
                  <span className="font-bold">{region.status}</span>
                </div>
                <p className="text-sm mt-1 opacity-80">{region.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Drought Scale Legend */}
      <Card>
        <CardHeader><CardTitle>📊 Drought Intensity Scale</CardTitle></CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <div className="flex-1 p-2 bg-green-200 rounded text-center text-sm">None</div>
            <div className="flex-1 p-2 bg-yellow-200 rounded text-center text-sm">D0 - Abnormal</div>
            <div className="flex-1 p-2 bg-orange-300 rounded text-center text-sm">D1 - Moderate</div>
            <div className="flex-1 p-2 bg-orange-500 text-white rounded text-center text-sm">D2 - Severe</div>
            <div className="flex-1 p-2 bg-red-500 text-white rounded text-center text-sm">D3 - Extreme</div>
            <div className="flex-1 p-2 bg-red-800 text-white rounded text-center text-sm">D4 - Exceptional</div>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader><CardTitle>💧 Water Management Recommendations</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            <RecommendationItem priority="high" action="Increase irrigation frequency for South Block (D1 status)" />
            <RecommendationItem priority="medium" action="Apply mulch to reduce evaporation in North Block" />
            <RecommendationItem priority="low" action="Monitor soil moisture sensors daily until rain event" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function RecommendationItem({ priority, action }: { priority: 'high' | 'medium' | 'low'; action: string }) {
  const colors = { high: 'border-red-300 bg-red-50', medium: 'border-yellow-300 bg-yellow-50', low: 'border-blue-300 bg-blue-50' };
  const icons = { high: '🔴', medium: '🟡', low: '🔵' };
  return (
    <div className={`p-3 border rounded-lg ${colors[priority]}`}>
      <span className="mr-2">{icons[priority]}</span>
      {action}
    </div>
  );
}

export default DroughtMonitor;
