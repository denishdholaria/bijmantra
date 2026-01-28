/**
 * Sun-Earth Systems Dashboard
 *
 * Solar radiation, photoperiod, UV index, and space weather impacts on agriculture.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Sun, 
  Clock, 
  Shield, 
  Activity, 
  ArrowRight, 
  Sprout, 
  FlaskConical,
  Orbit,
  Magnet,
  Sparkles,
  Globe
} from 'lucide-react';

interface SolarConditions {
  sunspot_number: number;
  kp_index: number;
  solar_wind_speed: number;
  cycle_phase: string;
}

export function Dashboard() {
  const [conditions, setConditions] = useState<SolarConditions | null>(null);

  useEffect(() => {
    fetch('/api/v2/solar/current')
      .then(res => res.ok ? res.json() : null)
      .then(data => data && setConditions(data.data))
      .catch(() => setConditions({
        sunspot_number: 142,
        kp_index: 3.2,
        solar_wind_speed: 385,
        cycle_phase: 'Solar Maximum',
      }));
  }, []);

  const modules = [
    {
      icon: Activity,
      title: 'Solar Activity',
      description: 'Real-time solar conditions and space weather',
      route: '/sun-earth-systems/solar-activity',
      color: 'bg-amber-100 text-amber-600',
    },
    {
      icon: Clock,
      title: 'Photoperiod',
      description: 'Day length calculator for crop planning',
      route: '/sun-earth-systems/photoperiod',
      color: 'bg-blue-100 text-blue-600',
    },
    {
      icon: Shield,
      title: 'UV Index',
      description: 'UV radiation levels and field work safety',
      route: '/sun-earth-systems/uv-index',
      color: 'bg-purple-100 text-purple-600',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Sun-Earth Systems</h1>
        <p className="text-gray-600 mt-1">Solar radiation, photoperiod, and space weather for agriculture</p>
        <Badge className="mt-2 bg-green-100 text-green-800">Active Module</Badge>
      </div>

      {/* Current Conditions Summary */}
      {conditions && (
        <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Sun className="h-12 w-12 text-amber-500" />
                <div>
                  <h3 className="font-semibold text-lg text-amber-900">Current Solar Conditions</h3>
                  <p className="text-amber-700">{conditions.cycle_phase} • Cycle 25</p>
                </div>
              </div>
              <div className="flex gap-6 text-center">
                <div>
                  <p className="text-2xl font-bold text-amber-800">{conditions.sunspot_number}</p>
                  <p className="text-xs text-amber-600">Sunspots</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-amber-800">{conditions.kp_index}</p>
                  <p className="text-xs text-amber-600">Kp Index</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-amber-800">{conditions.solar_wind_speed}</p>
                  <p className="text-xs text-amber-600">km/s</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Module Cards */}
      <div className="grid md:grid-cols-3 gap-4">
        {modules.map((mod) => (
          <Card key={mod.title} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className={`inline-flex p-3 rounded-lg ${mod.color} mb-4`}>
                <mod.icon className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-lg">{mod.title}</h3>
              <p className="text-sm text-gray-600 mt-1 mb-4">{mod.description}</p>
              <Link to={mod.route}>
                <Button variant="outline" size="sm" className="w-full">
                  Open <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Agricultural Relevance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
              <Sprout className="h-5 w-5 text-green-600" />
            </div>
            Agricultural Applications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-2">Photoperiod & Flowering</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Short-day crops: Rice, Soybean, Cotton</li>
                <li>• Long-day crops: Wheat, Barley, Spinach</li>
                <li>• Day-neutral: Tomato, Corn, Cucumber</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Solar Radiation Effects</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• PAR drives photosynthesis rates</li>
                <li>• UV-B affects secondary metabolites</li>
                <li>• Solar cycles correlate with yields</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Research Areas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
              <FlaskConical className="h-5 w-5 text-purple-600" />
            </div>
            Research Areas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-4">
            {[
              { icon: Sun, title: 'Solar Cycles', desc: '11-year activity patterns', color: 'bg-amber-100 text-amber-600' },
              { icon: Orbit, title: 'Geomagnetic', desc: 'Earth field variations', color: 'bg-blue-100 text-blue-600' },
              { icon: Sparkles, title: 'Cosmic Rays', desc: 'Natural mutation source', color: 'bg-purple-100 text-purple-600' },
              { icon: Globe, title: 'Ionosphere', desc: 'Atmospheric conditions', color: 'bg-green-100 text-green-600' },
            ].map((item) => (
              <div key={item.title} className="p-4 border rounded-lg text-center">
                <div className={`w-12 h-12 rounded-lg ${item.color} flex items-center justify-center mx-auto`}>
                  <item.icon className="h-6 w-6" />
                </div>
                <h4 className="font-medium mt-2">{item.title}</h4>
                <p className="text-xs text-gray-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Dashboard;
