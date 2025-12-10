/**
 * Radiation Calculator Page
 *
 * Calculate radiation exposure for space missions and plant effects.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertTriangle, Shield, Rocket } from 'lucide-react';

interface RadiationResult {
  mission_type: string;
  duration_days: number;
  shielding_gcm2: number;
  daily_dose_msv: number;
  total_dose_msv: number;
  plant_effects: string[];
  comparison: {
    earth_annual: number;
    iss_annual: number;
    mars_transit: number;
  };
}

const MISSION_TYPES = [
  { value: 'LEO', label: 'Low Earth Orbit (ISS)', rate: '~0.5 mSv/day' },
  { value: 'lunar', label: 'Lunar (Gateway)', rate: '~1.0 mSv/day' },
  { value: 'mars', label: 'Mars Transit', rate: '~0.7 mSv/day' },
  { value: 'deep_space', label: 'Deep Space', rate: '~1.5 mSv/day' },
];

export function Radiation() {
  const [missionType, setMissionType] = useState('LEO');
  const [duration, setDuration] = useState(180);
  const [shielding, setShielding] = useState(20);
  const [result, setResult] = useState<RadiationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const calculate = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `/api/v2/space/radiation?mission_type=${missionType}&duration_days=${duration}&shielding_gcm2=${shielding}`
      );
      if (res.ok) {
        const data = await res.json();
        setResult(data.data);
      }
    } catch {
      // Calculate locally
      const baseRates: Record<string, number> = { LEO: 0.5, lunar: 1.0, mars: 0.7, deep_space: 1.5 };
      const baseRate = baseRates[missionType] || 0.5;
      const shieldingFactor = Math.exp(-shielding / 30);
      const effectiveRate = baseRate * (0.3 + 0.7 * shieldingFactor);
      const totalDose = effectiveRate * duration;
      
      let effects = ['Minimal impact expected'];
      if (totalDose > 500) effects = ['Severe growth inhibition likely'];
      else if (totalDose > 100) effects = ['Moderate growth reduction expected'];
      else if (totalDose > 50) effects = ['Minor effects on sensitive varieties'];
      
      setResult({
        mission_type: missionType,
        duration_days: duration,
        shielding_gcm2: shielding,
        daily_dose_msv: Math.round(effectiveRate * 1000) / 1000,
        total_dose_msv: Math.round(totalDose * 10) / 10,
        plant_effects: effects,
        comparison: { earth_annual: 2.4, iss_annual: 182.5, mars_transit: 300 },
      });
    } finally {
      setLoading(false);
    }
  };

  const getDoseColor = (dose: number) => {
    if (dose < 50) return 'text-green-600';
    if (dose < 100) return 'text-yellow-600';
    if (dose < 500) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Radiation Calculator</h1>
        <p className="text-gray-600 mt-1">Estimate radiation exposure and effects on plants</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Rocket className="h-5 w-5" />
              Mission Parameters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Mission Type</Label>
              <Select value={missionType} onValueChange={setMissionType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MISSION_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label} ({type.rate})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Duration (days)</Label>
              <Input
                type="number"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value) || 1)}
                min={1}
                max={1000}
              />
            </div>
            <div>
              <Label className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Shielding (g/cm²)
              </Label>
              <Input
                type="number"
                value={shielding}
                onChange={(e) => setShielding(parseFloat(e.target.value) || 0)}
                min={0}
                max={100}
              />
              <p className="text-xs text-gray-500 mt-1">ISS: ~20 g/cm², Spacecraft: 5-30 g/cm²</p>
            </div>
            <Button onClick={calculate} disabled={loading} className="w-full">
              Calculate Exposure
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <Card>
            <CardHeader>
              <CardTitle>Radiation Exposure</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center p-6 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-xl">
                <p className="text-sm text-gray-500">Total Dose</p>
                <p className={`text-5xl font-bold ${getDoseColor(result.total_dose_msv)}`}>
                  {result.total_dose_msv}
                </p>
                <p className="text-lg text-gray-600">mSv</p>
                <p className="text-sm text-gray-500 mt-2">
                  ({result.daily_dose_msv} mSv/day × {result.duration_days} days)
                </p>
              </div>

              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-amber-800">Plant Effects</p>
                    {result.plant_effects.map((effect, i) => (
                      <p key={i} className="text-sm text-amber-700">{effect}</p>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Comparison</h4>
                <div className="space-y-2">
                  {[
                    { label: 'Earth (annual)', value: result.comparison.earth_annual },
                    { label: 'ISS (annual)', value: result.comparison.iss_annual },
                    { label: 'Mars Transit', value: result.comparison.mars_transit },
                    { label: 'This Mission', value: result.total_dose_msv },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center justify-between text-sm">
                      <span>{item.label}</span>
                      <Badge variant="outline">{item.value} mSv</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Radiation Info */}
      <Card>
        <CardHeader>
          <CardTitle>☢️ Radiation Types in Space</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium">Galactic Cosmic Rays (GCR)</h4>
              <p className="text-sm text-gray-600 mt-1">
                High-energy particles from outside solar system. Constant background, hard to shield.
              </p>
            </div>
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium">Solar Particle Events (SPE)</h4>
              <p className="text-sm text-gray-600 mt-1">
                Bursts from solar flares. Sporadic but intense. Can be shielded.
              </p>
            </div>
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium">Trapped Radiation</h4>
              <p className="text-sm text-gray-600 mt-1">
                Van Allen belts around Earth. Brief exposure during transit.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Plant Radiation Effects */}
      <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
        <CardHeader>
          <CardTitle className="text-green-800">🌱 Plant Radiation Responses</CardTitle>
        </CardHeader>
        <CardContent className="text-green-700">
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium">Low Dose (&lt;50 mSv)</h4>
              <ul className="mt-1 space-y-1 list-disc list-inside">
                <li>Minimal visible effects</li>
                <li>Possible hormesis (growth stimulation)</li>
                <li>Increased antioxidant production</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium">High Dose (&gt;500 mSv)</h4>
              <ul className="mt-1 space-y-1 list-disc list-inside">
                <li>DNA damage and mutations</li>
                <li>Growth inhibition</li>
                <li>Reduced seed viability</li>
                <li>Chlorophyll degradation</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Radiation;
