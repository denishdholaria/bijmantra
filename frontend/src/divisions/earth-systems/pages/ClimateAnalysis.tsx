/**
 * Climate Analysis Page
 *
 * Long-term climate trends and historical data analysis.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function ClimateAnalysis() {
  const climateData = {
    avgTemp: { current: 26.5, historical: 25.2, change: '+1.3°C' },
    rainfall: { current: 850, historical: 920, change: '-7.6%' },
    growingSeason: { current: 245, historical: 230, change: '+15 days' },
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Climate Analysis</h1>
        <p className="text-gray-600 mt-1">Long-term climate trends and historical patterns</p>
      </div>

      {/* Climate Indicators */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-4xl mb-2">🌡️</div>
            <div className="text-2xl font-bold">{climateData.avgTemp.current}°C</div>
            <div className="text-sm text-gray-500">Avg Temperature</div>
            <div className="text-sm text-red-500 mt-2">{climateData.avgTemp.change} vs 30-yr avg</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-4xl mb-2">🌧️</div>
            <div className="text-2xl font-bold">{climateData.rainfall.current}mm</div>
            <div className="text-sm text-gray-500">Annual Rainfall</div>
            <div className="text-sm text-orange-500 mt-2">{climateData.rainfall.change} vs 30-yr avg</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-4xl mb-2">🌱</div>
            <div className="text-2xl font-bold">{climateData.growingSeason.current}</div>
            <div className="text-sm text-gray-500">Growing Season (days)</div>
            <div className="text-sm text-green-500 mt-2">{climateData.growingSeason.change}</div>
          </CardContent>
        </Card>
      </div>

      {/* Climate Trends */}
      <Card>
        <CardHeader><CardTitle>📈 Climate Trends (30 Years)</CardTitle></CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <p className="text-gray-500">Climate trend visualization would render here</p>
          </div>
        </CardContent>
      </Card>

      {/* Adaptation Recommendations */}
      <Card>
        <CardHeader><CardTitle>🎯 Adaptation Recommendations</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            <RecommendationItem icon="💧" title="Water Management" description="Consider drought-tolerant varieties and improved irrigation efficiency" />
            <RecommendationItem icon="📅" title="Planting Dates" description="Shift sowing dates 1-2 weeks earlier to optimize growing season" />
            <RecommendationItem icon="🌾" title="Crop Selection" description="Evaluate heat-tolerant cultivars for changing temperature patterns" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function RecommendationItem({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
      <span className="text-2xl">{icon}</span>
      <div>
        <div className="font-medium">{title}</div>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </div>
  );
}

export default ClimateAnalysis;
