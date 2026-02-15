import { BarcodeScanner } from '@/components/BarcodeScanner';

interface ScannerProps {
  onScan: (result: any) => void;
  className?: string;
}

export function Scanner({ onScan, className }: ScannerProps) {
  return (
    <div className={`scanner-wrapper ${className}`}>
      <BarcodeScanner 
        onScan={onScan}
        autoStart={true}
        showHistory={false}
        showManualInput={true}
        className="mobile-scanner"
      />
    </div>
  );
}

export default Scanner;
