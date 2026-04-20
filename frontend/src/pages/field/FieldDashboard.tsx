import { FieldLayout } from '@/components/layouts/FieldLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Download } from 'lucide-react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '@/lib/db';
import { Link } from 'react-router-dom';

export function FieldDashboard() {
  const trialCount = useLiveQuery(() => db.trials.count());
  const plotCount = useLiveQuery(() => db.plots.count());
  const obsCount = useLiveQuery(() => db.observations.count());
  const pendingSync = useLiveQuery(() => db.observations.where('synced').equals(0).count());

  return (
    <FieldLayout title="Dashboard">
      <div className="space-y-4">
        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Trials</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{trialCount ?? 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Observations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{obsCount ?? 0}</div>
              <p className="text-xs text-gray-500">{pendingSync ?? 0} pending sync</p>
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
             <Link to="/field/scan">
              <Button className="w-full h-12 text-lg">
                <Plus className="mr-2 h-5 w-5" /> New Observation
              </Button>
            </Link>
            
            <Button variant="outline" className="w-full">
              <Download className="mr-2 h-4 w-4" /> Download Trials (Offline)
            </Button>
          </CardContent>
        </Card>
      </div>
    </FieldLayout>
  );
}

export default FieldDashboard;
