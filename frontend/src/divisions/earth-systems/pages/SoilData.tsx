/**
 * Soil Data Page
 *
 * Soil analysis and nutrient management.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function SoilData() {
  const soilSamples = [
    { id: 'S001', field: 'North Block A', date: '2024-11-15', ph: 6.8, nitrogen: 45, phosphorus: 32, potassium: 180, organic: 2.4 },
    { id: 'S002', field: 'North Block B', date: '2024-11-14', ph: 7.2, nitrogen: 38, phosphorus: 28, potassium: 165, organic: 2.1 },
    { id: 'S003', field: 'South Block', date: '2024-11-12', ph: 6.5, nitrogen: 52, phosphorus: 35, potassium: 195, organic: 2.8 },
  ];

  const getNutrientStatus = (value: number, type: string) => {
    const thresholds: Record<string, [number, number]> = {
      nitrogen: [40, 60],
      phosphorus: [25, 40],
      potassium: [150, 200],
    };
    const [low, high] = thresholds[type] || [0, 100];
    if (value < low) return { status: 'Low', color: 'text-red-600 bg-red-50' };
    if (value > high) return { status: 'High', color: 'text-blue-600 bg-blue-50' };
    return { status: 'Optimal', color: 'text-green-600 bg-green-50' };
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Soil Data</h1>
        <p className="text-gray-600 mt-1">Soil analysis and nutrient management</p>
      </div>

      {/* Soil Samples Table */}
      <Card>
        <CardHeader><CardTitle>📊 Recent Soil Analyses</CardTitle></CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Field</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">pH</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">N (kg/ha)</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">P (kg/ha)</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">K (kg/ha)</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">OM %</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {soilSamples.map((sample) => (
                <tr key={sample.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{sample.field}</td>
                  <td className="px-4 py-3 text-gray-600">{sample.date}</td>
                  <td className="px-4 py-3 text-center">{sample.ph}</td>
                  <td className="px-4 py-3 text-center">
                    <NutrientBadge value={sample.nitrogen} type="nitrogen" />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <NutrientBadge value={sample.phosphorus} type="phosphorus" />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <NutrientBadge value={sample.potassium} type="potassium" />
                  </td>
                  <td className="px-4 py-3 text-center">{sample.organic}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Fertilizer Recommendations */}
      <Card>
        <CardHeader><CardTitle>🌱 Fertilizer Recommendations</CardTitle></CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <RecommendationCard nutrient="Nitrogen" current={45} target={55} recommendation="Apply 25 kg/ha urea before next irrigation" />
            <RecommendationCard nutrient="Phosphorus" current={32} target={35} recommendation="Adequate levels - maintain with DAP at sowing" />
            <RecommendationCard nutrient="Potassium" current={180} target={175} recommendation="Sufficient - no additional K required" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function NutrientBadge({ value, type }: { value: number; type: string }) {
  const thresholds: Record<string, [number, number]> = {
    nitrogen: [40, 60], phosphorus: [25, 40], potassium: [150, 200],
  };
  const [low, high] = thresholds[type] || [0, 100];
  const color = value < low ? 'bg-red-100 text-red-700' : value > high ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700';
  return <span className={`px-2 py-1 rounded text-sm font-medium ${color}`}>{value}</span>;
}

function RecommendationCard({ nutrient, current, target, recommendation }: { nutrient: string; current: number; target: number; recommendation: string }) {
  const diff = target - current;
  return (
    <div className="p-4 border rounded-lg">
      <div className="font-medium text-lg">{nutrient}</div>
      <div className="flex items-center gap-2 my-2">
        <span className="text-2xl font-bold">{current}</span>
        <span className="text-gray-400">→</span>
        <span className="text-green-600 font-medium">{target}</span>
        <span className="text-xs text-gray-500">kg/ha</span>
      </div>
      <p className="text-sm text-gray-600">{recommendation}</p>
    </div>
  );
}

export default SoilData;
