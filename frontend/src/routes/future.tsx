import { lazy, Suspense } from 'react';
import { RouteObject } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
// Lazy Layout import to prevent circular dependency
const Layout = lazy(() => import('@/components/Layout').then(m => ({ default: m.Layout })));

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

// Soil & Nutrients Division
const SoilNutrientsDashboard = lazy(() => import('@/divisions/future/soil-nutrients/pages/Dashboard').then(m => ({ default: m.Dashboard })));
const SoilNutrientsSoilTests = lazy(() => import('@/divisions/future/soil-nutrients/pages/SoilTests').then(m => ({ default: m.SoilTests })));
const SoilNutrientsSoilHealth = lazy(() => import('@/divisions/future/soil-nutrients/pages/SoilHealth').then(m => ({ default: m.SoilHealth })));
const SoilNutrientsNutrientCalculator = lazy(() => import('@/divisions/future/soil-nutrients/pages/NutrientCalculator').then(m => ({ default: m.NutrientCalculator })));
const SoilNutrientsCarbonTracker = lazy(() => import('@/divisions/future/soil-nutrients/pages/CarbonTracker').then(m => ({ default: m.CarbonTracker })));
const SoilAnalysis = lazy(() => import('@/pages/SoilAnalysis').then(m => ({ default: m.SoilAnalysis })));
const FertilizerCalculator = lazy(() => import('@/pages/FertilizerCalculator').then(m => ({ default: m.FertilizerCalculator })));

// Crop Intelligence
const CropIntelligenceCropSuitability = lazy(() => import('@/divisions/future/crop-intelligence/pages/CropSuitability').then(m => ({ default: m.CropSuitability })));
const CropIntelligenceGDDTracker = lazy(() => import('@/divisions/future/crop-intelligence/pages/GDDTracker').then(m => ({ default: m.GDDTracker })));
const CropIntelligenceCropCalendar = lazy(() => import('@/divisions/future/crop-intelligence/pages/CropCalendar').then(m => ({ default: m.CropCalendar })));
const CropIntelligenceYieldPrediction = lazy(() => import('@/divisions/future/crop-intelligence/pages/YieldPrediction').then(m => ({ default: m.YieldPrediction })));
const CropCalendar = lazy(() => import('@/pages/CropCalendar').then(m => ({ default: m.CropCalendar })));
const YieldPredictor = lazy(() => import('@/pages/YieldPredictor').then(m => ({ default: m.YieldPredictor })));

// Crop Protection
const CropProtectionDashboard = lazy(() => import('@/divisions/future/crop-protection/pages/Dashboard').then(m => ({ default: m.CropProtectionDashboard })));
const CropProtectionPestObservations = lazy(() => import('@/divisions/future/crop-protection/pages/PestObservations').then(m => ({ default: m.PestObservations })));
const CropProtectionDiseaseRiskForecast = lazy(() => import('@/divisions/future/crop-protection/pages/DiseaseRiskForecast').then(m => ({ default: m.DiseaseRiskForecastPage })));
const CropProtectionSprayApplications = lazy(() => import('@/divisions/future/crop-protection/pages/SprayApplication').then(m => ({ default: m.SprayApplication })));
const CropProtectionIPMStrategies = lazy(() => import('@/divisions/future/crop-protection/pages/IPMStrategies').then(m => ({ default: m.IPMStrategies })));
const DiseaseAtlas = lazy(() => import('@/pages/DiseaseAtlas').then(m => ({ default: m.DiseaseAtlas })));
const DiseaseResistance = lazy(() => import('@/pages/DiseaseResistance').then(m => ({ default: m.DiseaseResistance })));
const AbioticStress = lazy(() => import('@/pages/AbioticStress').then(m => ({ default: m.AbioticStress })));
const PestMonitor = lazy(() => import('@/pages/PestMonitor').then(m => ({ default: m.PestMonitor })));
const CropHealthDashboard = lazy(() => import('@/pages/CropHealthDashboard').then(m => ({ default: m.CropHealthDashboard })));

// Water & Irrigation Division
const WaterIrrigationDashboard = lazy(() => import('@/divisions/future/water-irrigation/pages/Dashboard').then(m => ({ default: m.Dashboard })));
const WaterIrrigationSchedules = lazy(() => import('@/divisions/future/water-irrigation/pages/IrrigationSchedules').then(m => ({ default: m.IrrigationSchedules })));
const WaterIrrigationBalance = lazy(() => import('@/divisions/future/water-irrigation/pages/WaterBalance').then(m => ({ default: m.WaterBalance })));
const WaterIrrigationMoisture = lazy(() => import('@/divisions/future/water-irrigation/pages/SoilMoisture').then(m => ({ default: m.SoilMoisture })));
const IrrigationPlanner = lazy(() => import('@/pages/IrrigationPlanner').then(m => ({ default: m.IrrigationPlanner })));

// Plant Sciences Hub
const PlantSciencesHub = lazy(() => import('@/divisions/plant-sciences/pages/PlantSciencesHub').then(m => ({ default: m.PlantSciencesHub })));

// Future Placeholders
const FuturePlaceholder = lazy(() => import('@/archive/pages/FuturePlaceholder'));

// Helper
const wrap = (Component: React.LazyExoticComponent<any> | React.ComponentType) => (
  <ProtectedRoute>
    <Suspense fallback={null}>
      <Layout>
        <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
          <Component />
        </Suspense>
      </Layout>
    </Suspense>
  </ProtectedRoute>
);

export const futureRoutes: RouteObject[] = [
  // Integrations
  { path: '/integrations', element: wrap(IntegrationsHub) },

  // Sun-Earth
  { path: '/sun-earth-systems', element: wrap(SunEarthDashboard) },
  { path: '/sun-earth-systems/dashboard', element: wrap(SunEarthDashboard) },
  { path: '/sun-earth-systems/solar-activity', element: wrap(SunEarthSolarActivity) },
  { path: '/sun-earth-systems/photoperiod', element: wrap(SunEarthPhotoperiod) },
  { path: '/sun-earth-systems/uv-index', element: wrap(SunEarthUVIndex) },

  // Space Research
  { path: '/space-research', element: wrap(SpaceResearchDashboard) },
  { path: '/space-research/dashboard', element: wrap(SpaceResearchDashboard) },
  { path: '/space-research/crops', element: wrap(SpaceResearchCrops) },
  { path: '/space-research/radiation', element: wrap(SpaceResearchRadiation) },
  { path: '/space-research/life-support', element: wrap(SpaceResearchLifeSupport) },

  // Sensor Networks
  { path: '/sensor-networks', element: wrap(SensorNetworksDashboard) },
  { path: '/sensor-networks/dashboard', element: wrap(SensorNetworksDashboard) },
  { path: '/sensor-networks/devices', element: wrap(SensorNetworksDevices) },
  { path: '/sensor-networks/live', element: wrap(SensorNetworksLiveData) },
  { path: '/sensor-networks/alerts', element: wrap(SensorNetworksAlerts) },

  // Soil & Nutrients
  { path: '/soil-nutrients', element: wrap(SoilNutrientsDashboard) },
  { path: '/soil-nutrients/soil-tests', element: wrap(SoilNutrientsSoilTests) },
  { path: '/soil-nutrients/soil-health', element: wrap(SoilNutrientsSoilHealth) },
  { path: '/soil-nutrients/prescriptions', element: wrap(SoilNutrientsNutrientCalculator) },
  { path: '/soil-nutrients/carbon', element: wrap(SoilNutrientsCarbonTracker) },
  { path: '/soil', element: wrap(SoilAnalysis) },
  { path: '/fertilizer', element: wrap(FertilizerCalculator) },

  // Crop Intelligence
  { path: '/crop-intelligence/crop-suitability', element: wrap(CropIntelligenceCropSuitability) },
  { path: '/crop-intelligence/gdd-tracker', element: wrap(CropIntelligenceGDDTracker) },
  { path: '/crop-intelligence/crop-calendar', element: wrap(CropIntelligenceCropCalendar) },
  { path: '/crop-intelligence/yield-prediction', element: wrap(CropIntelligenceYieldPrediction) },
  { path: '/crop-calendar', element: wrap(CropCalendar) },
  { path: '/yield-predictor', element: wrap(YieldPredictor) },

  // Crop Protection
  { path: '/crop-protection', element: wrap(CropProtectionDashboard) },
  { path: '/crop-protection/pest-observations', element: wrap(CropProtectionPestObservations) },
  { path: '/crop-protection/disease-risk-forecast', element: wrap(CropProtectionDiseaseRiskForecast) },
  { path: '/crop-protection/spray-applications', element: wrap(CropProtectionSprayApplications) },
  { path: '/crop-protection/ipm-strategies', element: wrap(CropProtectionIPMStrategies) },
  { path: '/disease-atlas', element: wrap(DiseaseAtlas) },
  { path: '/disease-resistance', element: wrap(DiseaseResistance) },
  { path: '/abiotic-stress', element: wrap(AbioticStress) },
  { path: '/pest-monitor', element: wrap(PestMonitor) },
  { path: '/crop-health', element: wrap(CropHealthDashboard) },

  // Water & Irrigation
  { path: '/water-irrigation', element: wrap(WaterIrrigationDashboard) },
  { path: '/water-irrigation/schedules', element: wrap(WaterIrrigationSchedules) },
  { path: '/water-irrigation/balance', element: wrap(WaterIrrigationBalance) },
  { path: '/water-irrigation/moisture', element: wrap(WaterIrrigationMoisture) },
  { path: '/irrigation', element: wrap(IrrigationPlanner) },

  // Plant Sciences Hub
  { path: '/plant-sciences', element: wrap(PlantSciencesHub) },

  // Placeholders
  { path: '/market-economics/*', element: wrap(FuturePlaceholder) },
  { path: '/sustainability/*', element: wrap(FuturePlaceholder) },
  { path: '/farm-operations/*', element: wrap(FuturePlaceholder) },
  { path: '/robotics/*', element: wrap(FuturePlaceholder) },
  { path: '/post-harvest/*', element: wrap(FuturePlaceholder) },
  { path: '/livestock/*', element: wrap(FuturePlaceholder) },
  { path: '/aquaculture/*', element: wrap(FuturePlaceholder) },
];
