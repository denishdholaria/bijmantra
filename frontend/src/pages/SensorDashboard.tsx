/**
 * Sensor Dashboard Page - Thin Adapter
 * Delegates to divisions/environment/sensor-dashboard/SensorDashboardWorkspace
 */
import { SensorDashboardWorkspace } from '@/divisions/environment/sensor-dashboard';

export function SensorDashboard() {
  return <SensorDashboardWorkspace />;
}
