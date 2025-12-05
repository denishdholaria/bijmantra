/**
 * Growing Degree Days Page
 *
 * Track accumulated heat units for crop development.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function GrowingDegrees() {
  const crops = [
    { name: 'Wheat', baseTemp: 4, accumulated: 1250, target: 1500, stage: 'Grain Fill', progress: 83 },
    { name: 'Maize', baseTemp: 10, accumulated: 980, target: 1400, stage: 'Silking', progress: 70 },
    { name: 'Rice', baseTemp: 10, accumulated: 1100, target: 1200, stage: 'Heading', progress: 92 },
    { name: 'Soybean', baseTemp: 10, accumulated: 850, target: 1300, stage: 'Pod Fill', progress: 65 },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Growing Degree Days</h1>
        <p className="text-gray-600 mt-1">Track accumulated heat units for crop development</p>
      </div>

      {/* Current Season Summary */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-orange-50 to-yellow-50">
          <CardContent className="p-6 text-center">
            <div className="text-4xl font-bold text-orange-600">1,250</div>
            <div className="text-sm text-gray-600 mt-1">Season GDD (Base 10°C)</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-emerald-50">
          <CardContent className="p-6 text-center">
            <div className="text-4xl font-bold text-green-600">+45</div>
            <div className="text-sm text-gray-600 mt-1">GDD This Week</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-50 to-cyan-50">
          <CardContent className="p-6 text-center">
            <div className="text-4xl font-bold text-blue-600">+8%</div>
            <div className="text-sm text-gray-600 mt-1">vs. 10-Year Average</div>
          </CardContent>
        </Card>
      </div>

      {/* Crop Progress */}
      <Card>
        <CardHeader><CardTitle>🌾 Crop Development Progress</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-6">
            {crops.map((crop) => (
              <div key={crop.name} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">{crop.name}</span>
                    <span className="text-sm text-gray-500 ml-2">(Base: {crop.baseTemp}°C)</span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold">{crop.accumulated}</span>
                    <span className="text-gray-400"> / {crop.target} GDD</span>
                  </div>
                </div>
                <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${crop.progress >= 90 ? 'bg-green-500' : crop.progress >= 70 ? 'bg-yellow-500' : 'bg-blue-500'}`}
                    style={{ width: `${crop.progress}%` }}
                  />
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Current Stage: <span className="font-medium text-gray-700">{crop.stage}</span></span>
                  <span className="text-gray-500">{crop.progress}% to maturity</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Phenology Predictions */}
      <Card>
        <CardHeader><CardTitle>📅 Phenology Predictions</CardTitle></CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            <PredictionCard crop="Wheat" event="Physiological Maturity" date="Dec 18-22" gddRemaining={250} />
            <PredictionCard crop="Maize" event="Black Layer" date="Dec 28 - Jan 2" gddRemaining={420} />
            <PredictionCard crop="Rice" event="Harvest Ready" date="Dec 12-15" gddRemaining={100} />
            <PredictionCard crop="Soybean" event="Full Maturity" date="Jan 5-10" gddRemaining={450} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function PredictionCard({ crop, event, date, gddRemaining }: { crop: string; event: string; date: string; gddRemaining: number }) {
  return (
    <div className="p-4 border rounded-lg">
      <div className="font-medium">{crop}</div>
      <div className="text-lg font-bold text-green-600 mt-1">{event}</div>
      <div className="flex justify-between mt-2 text-sm text-gray-600">
        <span>📅 {date}</span>
        <span>{gddRemaining} GDD remaining</span>
      </div>
    </div>
  );
}

export default GrowingDegrees;
