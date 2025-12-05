/**
 * Sun-Earth Systems Dashboard
 *
 * Solar radiation, magnetic field monitoring, and space weather impacts on agriculture.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function Dashboard() {
  const concepts = [
    { icon: '☀️', title: 'Solar Activity', description: 'Monitor solar cycles and their agricultural impacts' },
    { icon: '🧲', title: 'Geomagnetic Field', description: 'Earth magnetic field variations and plant responses' },
    { icon: '🌌', title: 'Cosmic Radiation', description: 'Galactic cosmic ray flux and mutation rates' },
    { icon: '🌍', title: 'Ionosphere', description: 'Atmospheric electrical conditions affecting growth' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Sun-Earth Systems</h1>
        <p className="text-gray-600 mt-1">Understanding cosmic influences on agriculture</p>
        <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full bg-amber-100 text-amber-800 text-sm">
          🔮 Visionary Module
        </div>
      </div>

      <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <span className="text-4xl">🌞</span>
            <div>
              <h3 className="font-semibold text-lg text-amber-900">Cosmic Agriculture Research</h3>
              <p className="text-amber-700 mt-1">
                This visionary division explores the relationship between solar activity, 
                Earth's magnetic field, and agricultural outcomes — bridging ancient wisdom 
                with modern heliobiology research.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Research Areas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {concepts.map((concept, i) => (
              <div key={i} className="p-4 border rounded-lg hover:border-amber-300 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{concept.icon}</span>
                  <div>
                    <h4 className="font-medium">{concept.title}</h4>
                    <p className="text-sm text-gray-600">{concept.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>🎯 Future Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-gray-600">
            <li className="flex items-center gap-2">
              <span className="text-amber-500">○</span>
              Real-time solar wind data integration
            </li>
            <li className="flex items-center gap-2">
              <span className="text-amber-500">○</span>
              Geomagnetic storm alerts for field operations
            </li>
            <li className="flex items-center gap-2">
              <span className="text-amber-500">○</span>
              Correlation analysis: solar cycles vs crop yields
            </li>
            <li className="flex items-center gap-2">
              <span className="text-amber-500">○</span>
              Biodynamic calendar integration
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

export default Dashboard;
