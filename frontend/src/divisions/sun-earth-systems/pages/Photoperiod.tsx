/**
 * Photoperiod Calculator Page
 *
 * Calculate day length for any location and understand crop photoperiod responses.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Sun, Sunrise, Sunset, Calendar, MapPin } from 'lucide-react';

interface PhotoperiodData {
  date: string;
  latitude: number;
  day_length_hours: number;
  sunrise: string;
  sunset: string;
  solar_declination: number;
  day_of_year: number;
  is_long_day: boolean;
  photoperiod_class: string;
}

const PRESET_LOCATIONS = [
  { name: 'New Delhi, India', lat: 28.6 },
  { name: 'Hyderabad, India', lat: 17.4 },
  { name: 'Chennai, India', lat: 13.1 },
  { name: 'Mumbai, India', lat: 19.1 },
  { name: 'Kolkata, India', lat: 22.6 },
  { name: 'Singapore', lat: 1.3 },
  { name: 'Tokyo, Japan', lat: 35.7 },
  { name: 'London, UK', lat: 51.5 },
  { name: 'New York, USA', lat: 40.7 },
  { name: 'Sydney, Australia', lat: -33.9 },
];

const CROP_RESPONSES = [
  {
    type: 'Short-Day Plants',
    description: 'Flower when day length is shorter than critical photoperiod',
    crops: ['Rice', 'Soybean', 'Cotton', 'Sorghum', 'Chrysanthemum'],
    critical: '< 12-14 hours',
    color: 'bg-orange-100 text-orange-800',
  },
  {
    type: 'Long-Day Plants',
    description: 'Flower when day length exceeds critical photoperiod',
    crops: ['Wheat', 'Barley', 'Oats', 'Spinach', 'Lettuce', 'Radish'],
    critical: '> 14-16 hours',
    color: 'bg-blue-100 text-blue-800',
  },
  {
    type: 'Day-Neutral Plants',
    description: 'Flowering independent of day length',
    crops: ['Tomato', 'Corn', 'Cucumber', 'Sunflower', 'Pepper'],
    critical: 'Any',
    color: 'bg-green-100 text-green-800',
  },
];

export function Photoperiod() {
  const [latitude, setLatitude] = useState(28.6);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [data, setData] = useState<PhotoperiodData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchPhotoperiod = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v2/solar/photoperiod?latitude=${latitude}&date=${selectedDate}`);
      if (res.ok) {
        const json = await res.json();
        setData(json.data);
      }
    } catch {
      // Calculate locally as fallback
      const doy = Math.floor((new Date(selectedDate).getTime() - new Date(new Date(selectedDate).getFullYear(), 0, 0).getTime()) / 86400000);
      const declination = 23.45 * Math.sin((360 * (284 + doy) / 365) * Math.PI / 180);
      const latRad = latitude * Math.PI / 180;
      const decRad = declination * Math.PI / 180;
      const cosHourAngle = -Math.tan(latRad) * Math.tan(decRad);
      let dayLength = 12;
      if (cosHourAngle < -1) dayLength = 24;
      else if (cosHourAngle > 1) dayLength = 0;
      else dayLength = 2 * Math.acos(cosHourAngle) * 180 / Math.PI / 15;

      setData({
        date: selectedDate,
        latitude,
        day_length_hours: Math.round(dayLength * 100) / 100,
        sunrise: `${Math.floor(12 - dayLength / 2)}:${Math.floor(((12 - dayLength / 2) % 1) * 60).toString().padStart(2, '0')}`,
        sunset: `${Math.floor(12 + dayLength / 2)}:${Math.floor(((12 + dayLength / 2) % 1) * 60).toString().padStart(2, '0')}`,
        solar_declination: Math.round(declination * 100) / 100,
        day_of_year: doy,
        is_long_day: dayLength > 12,
        photoperiod_class: dayLength >= 14 ? 'Long Day (>14h)' : dayLength >= 12 ? 'Intermediate (12-14h)' : dayLength >= 10 ? 'Short Day (10-12h)' : 'Very Short (<10h)',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPhotoperiod();
  }, [latitude, selectedDate]);

  const getDayLengthColor = (hours: number) => {
    if (hours >= 14) return 'text-blue-600';
    if (hours >= 12) return 'text-green-600';
    if (hours >= 10) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Photoperiod Calculator</h1>
        <p className="text-gray-600 mt-1">Calculate day length and understand crop photoperiod responses</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              Location & Date
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Latitude (°)</Label>
              <Input
                type="number"
                value={latitude}
                onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                min={-90}
                max={90}
                step={0.1}
              />
              <p className="text-xs text-gray-500 mt-1">Positive = North, Negative = South</p>
            </div>

            <div>
              <Label>Date</Label>
              <Input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
              />
            </div>

            <div>
              <Label className="text-sm text-gray-500">Quick Select</Label>
              <div className="flex flex-wrap gap-1 mt-1">
                {PRESET_LOCATIONS.slice(0, 6).map((loc) => (
                  <Button
                    key={loc.name}
                    variant={latitude === loc.lat ? 'default' : 'outline'}
                    size="sm"
                    className="text-xs"
                    onClick={() => setLatitude(loc.lat)}
                  >
                    {loc.name.split(',')[0]}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sun className="h-5 w-5" />
              Day Length Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data && (
              <div className="space-y-6">
                <div className="text-center p-6 bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl">
                  <p className="text-sm text-gray-500">Day Length</p>
                  <p className={`text-5xl font-bold ${getDayLengthColor(data.day_length_hours)}`}>
                    {data.day_length_hours.toFixed(2)}
                  </p>
                  <p className="text-lg text-gray-600">hours</p>
                  <Badge className="mt-2" variant="outline">
                    {data.photoperiod_class}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-3 p-3 bg-orange-50 rounded-lg">
                    <Sunrise className="h-8 w-8 text-orange-500" />
                    <div>
                      <p className="text-sm text-gray-500">Sunrise</p>
                      <p className="text-xl font-semibold">{data.sunrise}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                    <Sunset className="h-8 w-8 text-purple-500" />
                    <div>
                      <p className="text-sm text-gray-500">Sunset</p>
                      <p className="text-xl font-semibold">{data.sunset}</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-sm text-gray-500">Day of Year</p>
                    <p className="text-lg font-medium">{data.day_of_year}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Solar Declination</p>
                    <p className="text-lg font-medium">{data.solar_declination}°</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Day Type</p>
                    <p className="text-lg font-medium">{data.is_long_day ? 'Long' : 'Short'}</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Crop Photoperiod Responses */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🌱 Crop Photoperiod Responses
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            {CROP_RESPONSES.map((response) => (
              <div key={response.type} className={`p-4 rounded-lg ${response.color.split(' ')[0]}`}>
                <h4 className={`font-semibold ${response.color.split(' ')[1]}`}>{response.type}</h4>
                <p className="text-sm text-gray-600 mt-1">{response.description}</p>
                <p className="text-sm mt-2">
                  <span className="font-medium">Critical:</span> {response.critical}
                </p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {response.crops.map((crop) => (
                    <Badge key={crop} variant="outline" className="text-xs">
                      {crop}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Practical Applications */}
      <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
        <CardHeader>
          <CardTitle className="text-green-800">🎯 Practical Applications</CardTitle>
        </CardHeader>
        <CardContent className="text-green-700">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium">Planting Decisions</h4>
              <ul className="text-sm list-disc list-inside mt-1 space-y-1">
                <li>Time sowing to match crop photoperiod requirements</li>
                <li>Avoid premature flowering in long-day crops</li>
                <li>Optimize vegetative growth period</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium">Breeding Applications</h4>
              <ul className="text-sm list-disc list-inside mt-1 space-y-1">
                <li>Select photoperiod-insensitive varieties for wider adaptation</li>
                <li>Plan crossing blocks for synchronized flowering</li>
                <li>Use artificial lighting for off-season breeding</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Photoperiod;
