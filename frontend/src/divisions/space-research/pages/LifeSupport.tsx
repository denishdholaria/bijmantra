/**
 * Life Support Calculator Page
 *
 * Calculate life support requirements and crop contributions for space missions.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Users, Calendar, Leaf, Droplets, Wind, Apple } from 'lucide-react';

interface LifeSupportResult {
  crew_size: number;
  mission_days: number;
  crop_area_m2: number;
  requirements: {
    oxygen_kg: number;
    water_kg: number;
    food_kg: number;
  };
  crop_contribution: {
    oxygen_kg: number;
    oxygen_percent: number;
    co2_absorbed_kg: number;
    co2_percent: number;
    water_recycled_kg: number;
    water_percent: number;
    food_kg: number;
    food_percent: number;
  };
  self_sufficiency_score: number;
}

export function LifeSupport() {
  const [crewSize, setCrewSize] = useState(4);
  const [missionDays, setMissionDays] = useState(180);
  const [cropArea, setCropArea] = useState(20);
  const [result, setResult] = useState<LifeSupportResult | null>(null);
  const [loading, setLoading] = useState(false);

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `/api/v2/space/life-support?crew_size=${crewSize}&mission_days=${missionDays}&crop_area_m2=${cropArea}`
      );
      if (res.ok) {
        const data = await res.json();
        setResult(data.data);
      }
    } catch {
      // Calculate locally
      const dailyO2 = 0.84 * crewSize;
      const dailyCO2 = 1.0 * crewSize;
      const dailyWater = 2.5 * crewSize;
      const dailyFood = 1.8 * crewSize;
      
      const cropO2 = 0.02 * cropArea * missionDays;
      const cropCO2 = 0.025 * cropArea * missionDays;
      const cropWater = 0.1 * cropArea * missionDays;
      const cropFood = 0.015 * cropArea * missionDays;
      
      const totalO2 = dailyO2 * missionDays;
      const totalCO2 = dailyCO2 * missionDays;
      const totalWater = dailyWater * missionDays;
      const totalFood = dailyFood * missionDays;
      
      setResult({
        crew_size: crewSize,
        mission_days: missionDays,
        crop_area_m2: cropArea,
        requirements: {
          oxygen_kg: Math.round(totalO2 * 10) / 10,
          water_kg: Math.round(totalWater * 10) / 10,
          food_kg: Math.round(totalFood * 10) / 10,
        },
        crop_contribution: {
          oxygen_kg: Math.round(cropO2 * 10) / 10,
          oxygen_percent: Math.round(cropO2 / totalO2 * 1000) / 10,
          co2_absorbed_kg: Math.round(cropCO2 * 10) / 10,
          co2_percent: Math.round(cropCO2 / totalCO2 * 1000) / 10,
          water_recycled_kg: Math.round(cropWater * 10) / 10,
          water_percent: Math.round(cropWater / totalWater * 1000) / 10,
          food_kg: Math.round(cropFood * 10) / 10,
          food_percent: Math.round(cropFood / totalFood * 1000) / 10,
        },
        self_sufficiency_score: Math.round((cropO2 / totalO2 + cropFood / totalFood) / 2 * 1000) / 10,
      });
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 50) return 'text-green-600';
    if (score >= 25) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Life Support Calculator</h1>
        <p className="text-gray-600 mt-1">Calculate crop contributions to closed-loop life support</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Mission Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="flex items-center gap-2">
                <Users className="h-4 w-4" /> Crew Size
              </Label>
              <Input
                type="number"
                value={crewSize}
                onChange={(e) => setCrewSize(parseInt(e.target.value) || 1)}
                min={1}
                max={20}
              />
            </div>
            <div>
              <Label className="flex items-center gap-2">
                <Calendar className="h-4 w-4" /> Mission Duration (days)
              </Label>
              <Input
                type="number"
                value={missionDays}
                onChange={(e) => setMissionDays(parseInt(e.target.value) || 1)}
                min={1}
                max={1000}
              />
            </div>
            <div>
              <Label className="flex items-center gap-2">
                <Leaf className="h-4 w-4" /> Crop Growing Area (m²)
              </Label>
              <Input
                type="number"
                value={cropArea}
                onChange={(e) => setCropArea(parseFloat(e.target.value) || 0)}
                min={0}
                max={1000}
              />
              <p className="text-xs text-gray-500 mt-1">ISS Veggie: ~0.13 m², APH: ~0.18 m²</p>
            </div>
            <Button onClick={calculate} disabled={loading} className="w-full">
              Calculate Requirements
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Results
                <Badge className={getScoreColor(result.self_sufficiency_score)}>
                  {result.self_sufficiency_score}% Self-Sufficient
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Wind className="h-6 w-6 mx-auto text-blue-500" />
                  <p className="text-lg font-bold">{result.requirements.oxygen_kg}</p>
                  <p className="text-xs text-gray-500">kg O₂ needed</p>
                </div>
                <div className="p-3 bg-cyan-50 rounded-lg">
                  <Droplets className="h-6 w-6 mx-auto text-cyan-500" />
                  <p className="text-lg font-bold">{result.requirements.water_kg}</p>
                  <p className="text-xs text-gray-500">kg H₂O needed</p>
                </div>
                <div className="p-3 bg-orange-50 rounded-lg">
                  <Apple className="h-6 w-6 mx-auto text-orange-500" />
                  <p className="text-lg font-bold">{result.requirements.food_kg}</p>
                  <p className="text-xs text-gray-500">kg food needed</p>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium">Crop Contributions</h4>
                {[
                  { label: 'Oxygen', value: result.crop_contribution.oxygen_percent, color: 'bg-blue-500' },
                  { label: 'CO₂ Absorbed', value: result.crop_contribution.co2_percent, color: 'bg-green-500' },
                  { label: 'Water Recycled', value: result.crop_contribution.water_percent, color: 'bg-cyan-500' },
                  { label: 'Food', value: result.crop_contribution.food_percent, color: 'bg-orange-500' },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{item.label}</span>
                      <span>{item.value}%</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${item.color}`}
                        style={{ width: `${Math.min(item.value, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Reference Info */}
      <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
        <CardHeader>
          <CardTitle className="text-purple-800">📊 Reference Data</CardTitle>
        </CardHeader>
        <CardContent className="text-purple-700">
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-medium">Daily Human Needs</h4>
              <ul className="mt-1 space-y-1">
                <li>• Oxygen: 0.84 kg</li>
                <li>• Water: 2.5 kg</li>
                <li>• Food: 1.8 kg</li>
                <li>• CO₂ produced: 1.0 kg</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium">Crop Production (per m²/day)</h4>
              <ul className="mt-1 space-y-1">
                <li>• O₂: ~0.02 kg</li>
                <li>• CO₂ absorbed: ~0.025 kg</li>
                <li>• Edible biomass: ~0.015 kg</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium">Target for Mars</h4>
              <ul className="mt-1 space-y-1">
                <li>• 50-100 m² per person</li>
                <li>• 50%+ food self-sufficiency</li>
                <li>• Full O₂/CO₂ cycling</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default LifeSupport;
