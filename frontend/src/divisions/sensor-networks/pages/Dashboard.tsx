/**
 * Sensor Networks Dashboard
 *
 * IoT sensors and environmental monitoring network.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function Dashboard() {
  const features = [
    { icon: '🌡️', title: 'Environmental Sensors', description: 'Temperature, humidity, soil moisture monitoring' },
    { icon: '📡', title: 'LoRaWAN Network', description: 'Long-range, low-power sensor connectivity' },
    { icon: '🛰️', title: 'Satellite Integration', description: 'Remote sensing data fusion' },
    { icon: '⚡', title: 'Real-time Alerts', description: 'Automated threshold-based notifications' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Sensor Networks</h1>
        <p className="text-gray-600 mt-1">IoT sensors and environmental monitoring network</p>
        <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full bg-teal-100 text-teal-800 text-sm">
          🔧 Conceptual Module
        </div>
      </div>

      <Card className="bg-gradient-to-br from-teal-50 to-cyan-50 border-teal-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <span className="text-4xl">📶</span>
            <div>
              <h3 className="font-semibold text-lg text-teal-900">Smart Field Monitoring</h3>
              <p className="text-teal-700 mt-1">
                This division will enable deployment and management of IoT sensor networks 
                across breeding trials, providing real-time environmental data for 
                precision agriculture and phenotyping.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Planned Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {features.map((feature, i) => (
              <div key={i} className="p-4 border rounded-lg hover:border-teal-300 transition-colors">
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
          <CardTitle>🔌 Integration Points</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-gray-600">
            <li className="flex items-center gap-2">
              <span className="text-teal-500">○</span>
              The Things Network (TTN) for LoRaWAN
            </li>
            <li className="flex items-center gap-2">
              <span className="text-teal-500">○</span>
              MQTT broker for real-time data streaming
            </li>
            <li className="flex items-center gap-2">
              <span className="text-teal-500">○</span>
              TimescaleDB for time-series storage
            </li>
            <li className="flex items-center gap-2">
              <span className="text-teal-500">○</span>
              Grafana dashboards for visualization
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

export default Dashboard;
