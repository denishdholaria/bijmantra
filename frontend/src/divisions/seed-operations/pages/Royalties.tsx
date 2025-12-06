/**
 * Royalties Page - Payment tracking
 */
import { Card, CardContent } from '@/components/ui/card';
import { DollarSign } from 'lucide-react';

export function Royalties() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Royalties</h1>
        <p className="text-gray-500 text-sm">Track royalty payments and revenue</p>
      </div>
      <Card>
        <CardContent className="py-12 text-center text-gray-500">
          <DollarSign className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>Royalty tracking coming soon</p>
        </CardContent>
      </Card>
    </div>
  );
}
export default Royalties;
