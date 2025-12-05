/**
 * Space Research Dashboard
 *
 * Visionary module for interplanetary plant research and space agriculture.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function Dashboard() {
  const concepts = [
    { icon: '🚀', title: 'Microgravity Breeding', description: 'Plant adaptation studies for zero-G environments' },
    { icon: '☀️', title: 'Radiation Tolerance', description: 'Developing crops resistant to cosmic radiation' },
    { icon: '🌱', title: 'Closed-Loop Systems', description: 'Self-sustaining agricultural ecosystems' },
    { icon: '🔴', title: 'Mars Agriculture', description: 'Crop varieties for Martian soil conditions' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Space Research</h1>
        <p className="text-gray-600 mt-1">Foundation for interplanetary plant research and space agriculture</p>
        <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full bg-purple-100 text-purple-800 text-sm">
          🔮 Visionary Module
        </div>
      </div>

      <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-purple-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <span className="text-4xl">🛸</span>
            <div>
              <h3 className="font-semibold text-lg text-purple-900">Future Vision</h3>
              <p className="text-purple-700 mt-1">
                This division will support research collaborations with space agencies (ISRO, NASA, ESA) 
                for developing crops suitable for long-duration space missions and planetary colonization.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Research Concepts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {concepts.map((concept, i) => (
              <div key={i} className="p-4 border rounded-lg hover:border-purple-300 transition-colors">
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
          <CardTitle>🎯 Planned Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-gray-600">
            <li className="flex items-center gap-2">
              <span className="text-green-500">○</span>
              Controlled environment experiment tracking
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">○</span>
              Space agency collaboration portal
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">○</span>
              Radiation exposure simulation models
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">○</span>
              Microgravity phenotype database
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

export default Dashboard;
