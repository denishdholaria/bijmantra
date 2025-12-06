/**
 * Varieties Page - Registered varieties for licensing
 */
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sprout, Plus } from 'lucide-react';

export function Varieties() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Registered Varieties</h1>
          <p className="text-gray-500 text-sm">Manage variety registrations and protection</p>
        </div>
        <Button><Plus className="h-4 w-4 mr-2" />Register Variety</Button>
      </div>
      <Card>
        <CardContent className="py-12 text-center text-gray-500">
          <Sprout className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>Variety registration coming soon</p>
          <p className="text-sm mt-1">PVP, PBR, patent tracking</p>
        </CardContent>
      </Card>
    </div>
  );
}
export default Varieties;
