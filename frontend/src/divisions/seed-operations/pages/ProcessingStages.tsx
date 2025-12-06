/**
 * Processing Stages Page
 */
import { Card, CardContent } from '@/components/ui/card';
import { Cog } from 'lucide-react';

export function ProcessingStages() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Processing Stages</h1>
        <p className="text-gray-500 text-sm">Cleaning, grading, treatment workflows</p>
      </div>
      <Card>
        <CardContent className="py-12 text-center text-gray-500">
          <Cog className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>Processing stages coming soon</p>
        </CardContent>
      </Card>
    </div>
  );
}
export default ProcessingStages;
