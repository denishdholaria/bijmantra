/**
 * Commercial Dashboard
 *
 * Seed traceability, licensing, and business operations.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function Dashboard() {
  const features = [
    { icon: '📦', title: 'Seed Traceability', description: 'Track seed lots from breeding to market' },
    { icon: '📜', title: 'Licensing Management', description: 'Variety licensing and royalty tracking' },
    { icon: '🔗', title: 'ERP Integration', description: 'Connect with ERPNext and other systems' },
    { icon: '📊', title: 'Market Analytics', description: 'Sales forecasting and demand planning' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Commercial</h1>
        <p className="text-gray-600 mt-1">Seed traceability, licensing, and business operations</p>
        <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm">
          📋 Planned Module
        </div>
      </div>

      <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <span className="text-4xl">💼</span>
            <div>
              <h3 className="font-semibold text-lg text-blue-900">Business Operations Hub</h3>
              <p className="text-blue-700 mt-1">
                This division will bridge breeding operations with commercial activities, 
                enabling seamless tracking from variety development to market release.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Planned Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {features.map((feature, i) => (
              <div key={i} className="p-4 border rounded-lg hover:border-blue-300 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{feature.icon}</span>
                  <div>
                    <h4 className="font-medium">{feature.title}</h4>
                    <p className="text-sm text-gray-600">{feature.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>🔗 Integration Roadmap</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-gray-600">
            <li className="flex items-center gap-2">
              <span className="text-green-500">○</span>
              ERPNext integration for inventory and sales
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">○</span>
              Blockchain-based seed certification
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">○</span>
              QR code generation for lot tracking
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">○</span>
              Regulatory compliance reporting
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

export default Dashboard;
