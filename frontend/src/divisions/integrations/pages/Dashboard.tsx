/**
 * Integrations Dashboard
 *
 * Third-party API connections and external service integrations.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function Dashboard() {
  const integrations = [
    { icon: '🧬', title: 'NCBI/GenBank', description: 'Genomic sequence databases', status: 'planned' },
    { icon: '🌾', title: 'BrAPI', description: 'Breeding API interoperability', status: 'active' },
    { icon: '📊', title: 'ERPNext', description: 'Enterprise resource planning', status: 'planned' },
    { icon: '🗺️', title: 'GIS Services', description: 'Mapping and spatial data', status: 'planned' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Integration Hub</h1>
        <p className="text-gray-600 mt-1">Connect with external systems and services</p>
        <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full bg-green-100 text-green-800 text-sm">
          ✅ Active Module
        </div>
      </div>

      <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <span className="text-4xl">🔗</span>
            <div>
              <h3 className="font-semibold text-lg text-green-900">External Connections</h3>
              <p className="text-green-700 mt-1">
                This division manages integrations with external databases, APIs, and services.
                Following the principle of "integrate, don't rebuild."
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Available Integrations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {integrations.map((integration, i) => (
              <div key={i} className="p-4 border rounded-lg hover:border-green-300 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{integration.icon}</span>
                    <div>
                      <h4 className="font-medium">{integration.title}</h4>
                      <p className="text-sm text-gray-600">{integration.description}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    integration.status === 'active' 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {integration.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Dashboard;
