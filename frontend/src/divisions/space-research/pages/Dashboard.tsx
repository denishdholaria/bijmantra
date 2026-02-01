/**
 * Space Research Dashboard
 *
 * Interplanetary plant research and space agriculture.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Rocket, 
  Leaf, 
  Shield, 
  Users, 
  ArrowRight, 
  FlaskConical,
  Atom,
  RefreshCw,
  Globe
} from 'lucide-react';
import { GoogleMapWrapper } from '@/components/maps/GoogleMapWrapper';

interface Mission {
  id: string;
  name: string;
  type: string;
  duration_days: number;
  gravity_g: number;
  current_crops?: string[];
  planned_crops?: string[];
}

export function Dashboard() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [agencies, setAgencies] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/v2/space/missions')
      .then(res => res.ok ? res.json() : null)
      .then(data => data && setMissions(data.data))
      .catch(() => setMissions([
        { id: 'ISS', name: 'International Space Station', type: 'LEO', duration_days: 180, gravity_g: 0, current_crops: ['Lettuce', 'Mizuna'] },
        { id: 'MARS_SURFACE', name: 'Mars Surface Habitat', type: 'mars', duration_days: 500, gravity_g: 0.38, planned_crops: ['Wheat', 'Potato'] },
      ]));
    
    fetch('/api/v2/space/agencies')
      .then(res => res.ok ? res.json() : null)
      .then(data => data && setAgencies(data.data))
      .catch(() => {});
  }, []);

  const modules = [
    { icon: Leaf, title: 'Space Crops', description: 'Crops proven for space agriculture', route: '/space-research/crops', color: 'bg-green-100 text-green-600' },
    { icon: Shield, title: 'Radiation', description: 'Radiation exposure calculator', route: '/space-research/radiation', color: 'bg-yellow-100 text-yellow-600' },
    { icon: Users, title: 'Life Support', description: 'Closed-loop system calculator', route: '/space-research/life-support', color: 'bg-blue-100 text-blue-600' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Space Research</h1>
        <p className="text-gray-600 mt-1">Interplanetary agriculture and space agency collaborations</p>
        <Badge className="mt-2 bg-green-100 text-green-800">Active Module</Badge>
      </div>

      {/* Satellite Intelligence Map */}
      <div className="bg-slate-900 rounded-xl p-0 overflow-hidden border border-slate-700 shadow-xl">
        <GoogleMapWrapper height="500px" />
      </div>



      {/* Hero Card */}
      <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-purple-200">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <Rocket className="h-12 w-12 text-purple-500" />
            <div>
              <h3 className="font-semibold text-lg text-purple-900">Space Agriculture Research</h3>
              <p className="text-purple-700">
                Tools for developing crops suitable for long-duration space missions and planetary colonization.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

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

      {/* Mission Profiles */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
              <Rocket className="h-5 w-5 text-indigo-600" />
            </div>
            Mission Profiles
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {missions.map((mission) => (
              <div key={mission.id} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{mission.name}</h4>
                  <Badge variant="outline">{mission.type.toUpperCase()}</Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                  <p>Duration: {mission.duration_days} days</p>
                  <p>Gravity: {mission.gravity_g}g</p>
                </div>
                {(mission.current_crops || mission.planned_crops) && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(mission.current_crops || mission.planned_crops)?.map((crop) => (
                      <Badge key={crop} variant="secondary" className="text-xs">{crop}</Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Space Agencies */}
      {agencies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
                <Globe className="h-5 w-5 text-blue-600" />
              </div>
              Space Agencies with Agriculture Programs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              {agencies.slice(0, 6).map((agency) => (
                <div key={agency.id} className="p-3 border rounded-lg">
                  <h4 className="font-medium">{agency.id}</h4>
                  <p className="text-xs text-gray-500">{agency.country}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {agency.programs?.slice(0, 2).map((prog: string) => (
                      <Badge key={prog} variant="outline" className="text-xs">{prog}</Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

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
              { icon: Rocket, title: 'Microgravity', desc: 'Zero-G plant adaptation', color: 'bg-indigo-100 text-indigo-600' },
              { icon: Atom, title: 'Radiation', desc: 'Cosmic ray tolerance', color: 'bg-yellow-100 text-yellow-600' },
              { icon: RefreshCw, title: 'Life Support', desc: 'Closed-loop systems', color: 'bg-green-100 text-green-600' },
              { icon: Globe, title: 'Mars Soil', desc: 'Regolith agriculture', color: 'bg-red-100 text-red-600' },
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
