import React from 'react';
import { useBluetoothScale } from '../../hooks/BluetoothScaleListenerHook';
import { Bluetooth, BluetoothOff, Weight, AlertCircle, CheckCircle2 } from 'lucide-react';

/**
 * ScaleTest Component
 * A standalone component to test and demonstrate the BluetoothScaleListenerHook.
 * This is isolated from the main app structure as per directives.
 */
export const ScaleTest: React.FC = () => {
  const { data, status, error, connect, disconnect, isSupported } = useBluetoothScale();

  if (!isSupported) {
    return (
      <div className="p-6 max-w-md mx-auto bg-destructive/10 border border-destructive/20 rounded-xl flex items-center gap-4">
        <AlertCircle className="text-destructive h-8 w-8" />
        <div>
          <h3 className="font-bold text-destructive">Web Bluetooth Not Supported</h3>
          <p className="text-sm text-destructive/80">
            Please use a modern browser (Chrome, Edge) to test Bluetooth features.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-xl mx-auto space-y-6 bg-card border border-border rounded-2xl shadow-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${
            status === 'connected' ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'
          }`}>
            {status === 'connected' ? <Bluetooth className="h-6 w-6" /> : <BluetoothOff className="h-6 w-6" />}
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight">Bluetooth Scale</h2>
            <p className="text-sm text-muted-foreground flex items-center gap-1.5">
              Status:
              <span className={`capitalize font-medium ${
                status === 'connected' ? 'text-green-500' :
                status === 'error' ? 'text-destructive' :
                'text-muted-foreground'
              }`}>
                {status}
              </span>
              {status === 'connected' && <CheckCircle2 className="h-3 w-3 text-green-500" />}
            </p>
          </div>
        </div>

        <button
          onClick={status === 'connected' ? disconnect : connect}
          disabled={status === 'connecting'}
          className={`px-4 py-2 rounded-md font-medium transition-colors ${
            status === 'connected'
              ? 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          } disabled:opacity-50`}
        >
          {status === 'connected' ? 'Disconnect' : status === 'connecting' ? 'Connecting...' : 'Connect Scale'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 p-6 bg-accent/30 rounded-xl border border-accent/50 min-h-[160px] flex items-center justify-center text-center">
        {status === 'connected' && data ? (
          <div className="space-y-2">
            <div className="flex items-center justify-center gap-3">
              <Weight className="h-10 w-10 text-primary" />
              <span className="text-6xl font-black tabular-nums">
                {data.weight}
              </span>
              <span className="text-2xl font-semibold text-muted-foreground uppercase self-end mb-2">
                {data.unit}
              </span>
            </div>
            {data.timestamp && (
              <p className="text-xs text-muted-foreground">
                Last updated: {data.timestamp.toLocaleTimeString()}
              </p>
            )}
          </div>
        ) : status === 'connected' ? (
          <div className="text-muted-foreground animate-pulse">
            <p className="text-lg">Waiting for data...</p>
            <p className="text-sm">Step on the scale to start measurement</p>
          </div>
        ) : (
          <div className="text-muted-foreground/60 italic">
            <Weight className="h-12 w-12 mx-auto mb-2 opacity-20" />
            <p>Scale not connected</p>
          </div>
        )}
      </div>

      {error && (
        <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md flex items-start gap-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      <div className="pt-4 border-t border-border space-y-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">About this integration</h4>
        <p className="text-xs text-muted-foreground leading-relaxed">
          This component uses the standard Web Bluetooth API to connect to devices implementing the
          <strong> Weight Scale Service (0x181D)</strong>. Data is parsed in real-time using the
          GATT Weight Measurement specification.
        </p>
      </div>
    </div>
  );
};

export default ScaleTest;
