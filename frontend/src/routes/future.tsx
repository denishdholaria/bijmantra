import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';
import { wrapWithAppShell } from './routeShell';

// Integration Hub
const IntegrationsHub = lazy(() => import('@/divisions/integrations/pages/Dashboard'));

// Sun-Earth Systems Division
const SunEarthDashboard = lazy(() => import('@/divisions/sun-earth-systems/pages/Dashboard'));
const SunEarthSolarActivity = lazy(() => import('@/divisions/sun-earth-systems/pages/SolarActivity'));
const SunEarthPhotoperiod = lazy(() => import('@/divisions/sun-earth-systems/pages/Photoperiod'));
const SunEarthUVIndex = lazy(() => import('@/divisions/sun-earth-systems/pages/UVIndex'));

// Space Research Division
const SpaceResearchDashboard = lazy(() => import('@/divisions/space-research/pages/Dashboard'));
const SpaceResearchCrops = lazy(() => import('@/divisions/space-research/pages/SpaceCrops'));
const SpaceResearchRadiation = lazy(() => import('@/divisions/space-research/pages/Radiation'));
const SpaceResearchLifeSupport = lazy(() => import('@/divisions/space-research/pages/LifeSupport'));

// Sensor Networks Division
const SensorNetworksDashboard = lazy(() => import('@/divisions/sensor-networks/pages/Dashboard'));
const SensorNetworksDevices = lazy(() => import('@/divisions/sensor-networks/pages/Devices'));
const SensorNetworksLiveData = lazy(() => import('@/divisions/sensor-networks/pages/LiveData'));
const SensorNetworksAlerts = lazy(() => import('@/divisions/sensor-networks/pages/Alerts'));

const SoilAnalysis = lazy(() => import('@/pages/SoilAnalysis').then(m => ({ default: m.SoilAnalysis })));
const FertilizerCalculator = lazy(() => import('@/pages/FertilizerCalculator').then(m => ({ default: m.FertilizerCalculator })));

const CropIntelligenceGDDTracker = lazy(() => import('@/divisions/crop-intelligence/pages/GDDTracker').then(m => ({ default: m.GDDTracker })));

const AbioticStress = lazy(() => import('@/pages/AbioticStress').then(m => ({ default: m.AbioticStress })));

const IrrigationPlanner = lazy(() => import('@/pages/IrrigationPlanner').then(m => ({ default: m.IrrigationPlanner })));
const Weather = lazy(() => import('@/pages/Weather').then(m => ({ default: m.Weather })));
const WeatherForecast = lazy(() => import('@/pages/WeatherForecast').then(m => ({ default: m.WeatherForecast })));

// Plant Sciences Hub
const PlantSciencesHub = lazy(() => import('@/divisions/plant-sciences/pages/PlantSciencesHub').then(m => ({ default: m.PlantSciencesHub })));

export const futureRoutes: RouteObject[] = [
  // Integrations
  { path: '/integrations', element: wrapWithAppShell(IntegrationsHub) },

  // Earth Systems compatibility aliases
  { path: '/earth-systems', element: wrapWithAppShell(SoilAnalysis) },
  { path: '/earth-systems/weather', element: wrapWithAppShell(Weather) },
  { path: '/earth-systems/climate', element: wrapWithAppShell(WeatherForecast) },
  { path: '/earth-systems/gdd', element: wrapWithAppShell(CropIntelligenceGDDTracker) },
  { path: '/earth-systems/drought', element: wrapWithAppShell(AbioticStress) },
  { path: '/earth-systems/soil', element: wrapWithAppShell(SoilAnalysis) },
  { path: '/earth-systems/inputs', element: wrapWithAppShell(FertilizerCalculator) },
  { path: '/earth-systems/irrigation', element: wrapWithAppShell(IrrigationPlanner) },
  { path: '/earth-systems/map', element: wrapWithAppShell(Weather) },

  // Sun-Earth
  { path: '/sun-earth-systems', element: wrapWithAppShell(SunEarthDashboard) },
  { path: '/sun-earth-systems/dashboard', element: wrapWithAppShell(SunEarthDashboard) },
  { path: '/sun-earth-systems/solar-activity', element: wrapWithAppShell(SunEarthSolarActivity) },
  { path: '/sun-earth-systems/photoperiod', element: wrapWithAppShell(SunEarthPhotoperiod) },
  { path: '/sun-earth-systems/uv-index', element: wrapWithAppShell(SunEarthUVIndex) },

  // Space Research
  { path: '/space-research', element: wrapWithAppShell(SpaceResearchDashboard) },
  { path: '/space-research/dashboard', element: wrapWithAppShell(SpaceResearchDashboard) },
  { path: '/space-research/crops', element: wrapWithAppShell(SpaceResearchCrops) },
  { path: '/space-research/radiation', element: wrapWithAppShell(SpaceResearchRadiation) },
  { path: '/space-research/life-support', element: wrapWithAppShell(SpaceResearchLifeSupport) },

  // Sensor Networks
  { path: '/sensor-networks', element: wrapWithAppShell(SensorNetworksDashboard) },
  { path: '/sensor-networks/dashboard', element: wrapWithAppShell(SensorNetworksDashboard) },
  { path: '/sensor-networks/devices', element: wrapWithAppShell(SensorNetworksDevices) },
  { path: '/sensor-networks/live', element: wrapWithAppShell(SensorNetworksLiveData) },
  { path: '/sensor-networks/alerts', element: wrapWithAppShell(SensorNetworksAlerts) },
  { path: '/sensor-networks/telemetry', element: wrapWithAppShell(SensorNetworksLiveData) },
  { path: '/sensor-networks/aggregates', element: wrapWithAppShell(SensorNetworksDashboard) },
  { path: '/sensor-networks/environment-link', element: wrapWithAppShell(SensorNetworksDevices) },

  // Plant Sciences Hub
  { path: '/plant-sciences', element: wrapWithAppShell(PlantSciencesHub) },
];
