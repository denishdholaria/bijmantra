import { useState, useEffect, useCallback, useRef } from 'react';

type MinimalGattServer = {
  connected: boolean;
  disconnect: () => void;
  getPrimaryService: (service: string) => Promise<{ getCharacteristic: (char: string) => Promise<{ startNotifications: () => Promise<void>; addEventListener: (event: string, handler: (event: Event) => void) => void }> }>;
};

type MinimalBluetoothDevice = {
  gatt?: { connect: () => Promise<MinimalGattServer | null> };
  addEventListener: (event: string, handler: () => void) => void;
};

type MinimalBluetoothNavigator = Navigator & {
  bluetooth?: {
    requestDevice: (options: {
      filters: Array<{ services: string[] }>;
      optionalServices?: string[];
    }) => Promise<MinimalBluetoothDevice>;
  };
};

/**
 * Interface for the weight data returned by the scale.
 */
export interface ScaleData {
  weight: number;
  unit: 'kg' | 'lb';
  timestamp?: Date;
}

/**
 * Connection status of the Bluetooth scale.
 */
export type BluetoothStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

/**
 * Return type for the BluetoothScaleListenerHook.
 */
export interface UseBluetoothScaleReturn {
  data: ScaleData | null;
  status: BluetoothStatus;
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  isSupported: boolean;
}

/**
 * Bluetooth UUIDs for Weight Scale Service and Characteristics.
 * Standard GATT UUIDs:
 * Weight Scale Service: 0x181D
 * Weight Measurement: 0x2A9D
 */
const WEIGHT_SCALE_SERVICE_UUID = 'weight_scale'; // Or 0x181D
const WEIGHT_MEASUREMENT_CHAR_UUID = 'weight_measurement'; // Or 0x2A9D

/**
 * Hook to listen to a Bluetooth Scale using the Web Bluetooth API.
 *
 * @returns {UseBluetoothScaleReturn} The current scale data, connection status, and control functions.
 */
export const useBluetoothScale = (): UseBluetoothScaleReturn => {
  const [data, setData] = useState<ScaleData | null>(null);
  const [status, setStatus] = useState<BluetoothStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);

  const gattServerRef = useRef<MinimalGattServer | BluetoothRemoteGATTServer | null>(null);
  const deviceRef = useRef<MinimalBluetoothDevice | BluetoothDevice | null>(null);

  const bluetoothNavigator =
    typeof navigator !== 'undefined' ? (navigator as MinimalBluetoothNavigator) : null;
  const isSupported = !!bluetoothNavigator?.bluetooth;

  /**
   * Parses the weight measurement data from the Bluetooth characteristic.
   * GATT Weight Measurement (0x2A9D) format parsing.
   */
  const handleCharacteristicValueChanged = useCallback((event: Event) => {
    const characteristic = event.target as unknown as { value: DataView | null };
    const value = characteristic.value;

    if (!value) return;

    // Flags: Bit 0 = Units (0: kg, 1: lb)
    const flags = value.getUint8(0);
    const isLbs = (flags & 0x01) !== 0;
    const unit = isLbs ? 'lb' : 'kg';

    // Weight value starts at byte 1 (Uint16)
    // Resolution: kg = 0.005, lb = 0.01
    const rawWeight = value.getUint16(1, true);
    const weight = rawWeight * (isLbs ? 0.01 : 0.005);

    // Optional: Parse timestamp if Bit 1 is set
    let timestamp: Date | undefined;
    if ((flags & 0x02) !== 0 && value.byteLength >= 10) {
      const year = value.getUint16(3, true);
      const month = value.getUint8(5) - 1;
      const day = value.getUint8(6);
      const hours = value.getUint8(7);
      const minutes = value.getUint8(8);
      const seconds = value.getUint8(9);
      timestamp = new Date(year, month, day, hours, minutes, seconds);
    }

    setData({
      weight: parseFloat(weight.toFixed(2)),
      unit,
      timestamp
    });
  }, []);

  const handleDisconnected = useCallback(() => {
    setStatus('disconnected');
    setData(null);
    gattServerRef.current = null;
    deviceRef.current = null;
  }, []);

  const disconnect = useCallback(() => {
    if (gattServerRef.current && gattServerRef.current.connected) {
      gattServerRef.current.disconnect();
    }
    handleDisconnected();
  }, [handleDisconnected]);

  const connect = useCallback(async () => {
    if (!isSupported) {
      setError('Web Bluetooth is not supported in this browser.');
      return;
    }

    try {
      setStatus('connecting');
      setError(null);

      const device = await bluetoothNavigator!.bluetooth!.requestDevice({
        filters: [{ services: [WEIGHT_SCALE_SERVICE_UUID] }],
        optionalServices: [WEIGHT_SCALE_SERVICE_UUID]
      });

      deviceRef.current = device;
      device.addEventListener('gattserverdisconnected', handleDisconnected);

      const server = await device.gatt?.connect();
      if (!server) throw new Error('Could not connect to GATT server.');

      gattServerRef.current = server;

      const service = await server.getPrimaryService(WEIGHT_SCALE_SERVICE_UUID);
      const characteristic = await service.getCharacteristic(WEIGHT_MEASUREMENT_CHAR_UUID);

      await characteristic.startNotifications();
      characteristic.addEventListener('characteristicvaluechanged', handleCharacteristicValueChanged);

      setStatus('connected');
    } catch (err: unknown) {
      console.error('Bluetooth Connection Error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to Bluetooth scale.';
      setError(errorMessage);
      setStatus('error');
      handleDisconnected();
    }
  }, [bluetoothNavigator, isSupported, handleCharacteristicValueChanged, handleDisconnected]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (gattServerRef.current) {
        disconnect();
      }
    };
  }, [disconnect]);

  return {
    data,
    status,
    error,
    connect,
    disconnect,
    isSupported
  };
};

export default useBluetoothScale;
