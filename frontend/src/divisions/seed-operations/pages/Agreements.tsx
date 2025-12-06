/**
 * Agreements Page - License agreements
 */
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Plus } from 'lucide-react';

export function Agreements() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">License Agreements</h1>
          <p className="text-gray-500 text-sm">Manage licensing contracts</p>
        </div>
        <Button><Plus className="h-4 w-4 mr-2" />New Agreement</Button>
      </div>
      <Card>
        <CardContent className="py-12 text-center text-gray-500">
          <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>Agreement management coming soon</p>
        </CardContent>
      </Card>
    </div>
  );
}
export default Agreements;
