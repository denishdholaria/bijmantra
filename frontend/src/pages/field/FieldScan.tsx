import { FieldLayout } from '@/components/layouts/FieldLayout';
import { Scanner } from '@/components/ui/Scanner';
import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ObservationEntryForm } from './ObservationEntryForm';
import { db } from '@/lib/db';
import { useToast } from '@/hooks/use-toast';

export function FieldScan() {
  const [scannedPlotId, setScannedPlotId] = useState<string | null>(null);
  const { toast } = useToast();

  const handleScan = async (result: any) => {
    // result.barcode_value or result might be the string directly depending on Scanner implementation
    // The Scanner component calls onScan with a 'result' object from BarcodeScanner
    // { barcode_value: string, found: boolean, entity_type... }
    
    const code = result.barcode_value || result;
    console.log('Scanned:', code);

    // 1. Lookup Plot in Local DB
    // We assume barcode == plotId for now, or we lookup by some other field
    // In real world, might be a UUID or a shorter code.
    // Let's try to find a plot where id matches OR plotNumber matches (if numeric)
    
    let plot = await db.plots.get(code); 
    
    if (!plot) {
        // Fallback: try finding by plotNumber if numeric
        if (!isNaN(Number(code))) {
            const num = Number(code);
            // This is ambiguous if multiple trials, but for now take the first match
            // or specific to active trial if we had that context.
            const plotByNum = await db.plots.where({ plotNumber: num }).first();
            if (plotByNum) plot = plotByNum;
        }
    }

    if (plot) {
        setScannedPlotId(plot.id);
        toast({ title: 'Plot Found', description: `Plot ${plot.plotNumber} - ${plot.accessionName}` });
    } else {
        toast({ title: 'Not Found', description: `No offline plot found for ${code}`, variant: 'destructive' });
    }
  };

  return (
    <FieldLayout title={scannedPlotId ? "Entry" : "Scan Plot"}>
      <div className="space-y-4">
        
        {!scannedPlotId ? (
            <>
                <Scanner onScan={handleScan} className="mb-4" />
                <p className="text-center text-sm text-gray-500">
                    Scan a plot barcode or QR code to enter observations.
                </p>
            </>
        ) : (
            <ObservationEntryForm 
                plotId={scannedPlotId} 
                onClose={() => setScannedPlotId(null)} 
            />
        )}

      </div>
    </FieldLayout>
  );
}

export default FieldScan;
