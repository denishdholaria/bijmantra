/**
 * Space Crops Page
 *
 * Catalog of crops suitable for space agriculture.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Rocket, Leaf, Clock, Shield, Zap } from 'lucide-react';

interface SpaceCrop {
  id: string;
  name: string;
  species: string;
  space_heritage: string;
  growth_cycle_days: number;
  radiation_tolerance: string;
  microgravity_adaptation: string;
  caloric_yield: number;
  notes: string;
}

export function SpaceCrops() {
  const [crops, setCrops] = useState<SpaceCrop[]>([]);
  const [selectedCrop, setSelectedCrop] = useState<SpaceCrop | null>(null);
  const [environment, setEnvironment] = useState<any>(null);

  useEffect(() => {
    fetch('/api/v2/space/crops')
      .then(res => res.ok ? res.json() : null)
      .then(data => data && setCrops(data.data || []))
      .catch(() => {
        // No data available - show empty state
        setCrops([]);
      });
  }, []);

  const fetchEnvironment = async (cropId: string) => {
    try {
      const res = await fetch(`/api/v2/space/crops/${cropId}/environment`);
      if (res.ok) {
        const data = await res.json();
        setEnvironment(data.data);
      }
    } catch {
      // No environment data available
      setEnvironment(null);
    }
  };

  const handleSelectCrop = (crop: SpaceCrop) => {
    setSelectedCrop(crop);
    fetchEnvironment(crop.id);
  };

  const getToleranceBadge = (level: string) => {
    const colors: Record<string, string> = {
      'Excellent': 'bg-green-100 text-green-800',
      'Good': 'bg-blue-100 text-blue-800',
      'Moderate': 'bg-yellow-100 text-yellow-800',
      'Low': 'bg-red-100 text-red-800',
    };
    return colors[level] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Space Crops</h1>
        <p className="text-gray-600 mt-1">Crops proven or planned for space agriculture</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Crop List */}
        <div className="lg:col-span-2 space-y-4">
          {crops.map((crop) => (
            <Card
              key={crop.id}
              className={`cursor-pointer transition-all ${selectedCrop?.id === crop.id ? 'ring-2 ring-purple-500' : 'hover:shadow-md'}`}
              onClick={() => handleSelectCrop(crop)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <Leaf className="h-6 w-6 text-green-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{crop.name}</h3>
                      <p className="text-sm text-gray-500 italic">{crop.species}</p>
                    </div>
                  </div>
                  <Badge variant="outline">{crop.id}</Badge>
                </div>
                
                <div className="mt-4 grid grid-cols-4 gap-2 text-center text-sm">
                  <div>
                    <Clock className="h-4 w-4 mx-auto text-gray-400" />
                    <p className="font-medium">{crop.growth_cycle_days}d</p>
                    <p className="text-xs text-gray-500">Cycle</p>
                  </div>
                  <div>
                    <Shield className="h-4 w-4 mx-auto text-gray-400" />
                    <Badge className={`text-xs ${getToleranceBadge(crop.radiation_tolerance)}`}>
                      {crop.radiation_tolerance}
                    </Badge>
                    <p className="text-xs text-gray-500">Radiation</p>
                  </div>
                  <div>
                    <Rocket className="h-4 w-4 mx-auto text-gray-400" />
                    <Badge className={`text-xs ${getToleranceBadge(crop.microgravity_adaptation)}`}>
                      {crop.microgravity_adaptation}
                    </Badge>
                    <p className="text-xs text-gray-500">Microgravity</p>
                  </div>
                  <div>
                    <Zap className="h-4 w-4 mx-auto text-gray-400" />
                    <p className="font-medium">{crop.caloric_yield}</p>
                    <p className="text-xs text-gray-500">kcal/kg</p>
                  </div>
                </div>

                <p className="mt-3 text-sm text-gray-600">
                  <span className="font-medium">Heritage:</span> {crop.space_heritage}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Environment Panel */}
        <div>
          {selectedCrop && environment ? (
            <Card className="sticky top-4">
              <CardHeader>
                <CardTitle className="text-lg">Optimal Environment</CardTitle>
                <p className="text-sm text-gray-500">{selectedCrop.name}</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium text-sm text-gray-500">Light</h4>
                  <div className="mt-1 space-y-1 text-sm">
                    <p>Photoperiod: {environment.light?.photoperiod_hours}h</p>
                    <p>PPFD: {environment.light?.ppfd_umol} µmol/m²/s</p>
                    <p>Spectrum: {environment.light?.spectrum}</p>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium text-sm text-gray-500">Atmosphere</h4>
                  <div className="mt-1 space-y-1 text-sm">
                    <p>CO₂: {environment.atmosphere?.co2_ppm} ppm</p>
                    <p>Humidity: {environment.atmosphere?.humidity_percent}%</p>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium text-sm text-gray-500">Temperature</h4>
                  <div className="mt-1 space-y-1 text-sm">
                    <p>Day: {environment.temperature?.day_c}°C</p>
                    <p>Night: {environment.temperature?.night_c}°C</p>
                  </div>
                </div>
                <p className="text-sm text-gray-600 pt-2 border-t">
                  {selectedCrop.notes}
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-gray-50">
              <CardContent className="p-6 text-center text-gray-500">
                <Leaf className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Select a crop to view optimal environment parameters</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export default SpaceCrops;
