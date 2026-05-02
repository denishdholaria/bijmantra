import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';
import { cropIntelligenceRoutes } from '@/divisions/crop-intelligence';
import { cropProtectionRoutes } from '@/divisions/crop-protection';
import { soilNutrientsRoutes } from '@/divisions/soil-nutrients';
import { waterIrrigationRoutes } from '@/divisions/water-irrigation';
import { wrapWithAppShell } from './routeShell';

const CropIntelligenceDivision = lazy(() => import('@/divisions/crop-intelligence'));
const CropProtectionDivision = lazy(() => import('@/divisions/crop-protection'));
const SoilNutrientsDivision = lazy(() => import('@/divisions/soil-nutrients'));
const WaterIrrigationDivision = lazy(() => import('@/divisions/water-irrigation'));

const SoilNutrientsCarbonTracker = lazy(() => import('@/divisions/soil-nutrients/pages/CarbonTracker').then(m => ({ default: m.CarbonTracker })));
const SoilAnalysis = lazy(() => import('@/pages/SoilAnalysis').then(m => ({ default: m.SoilAnalysis })));
const FertilizerCalculator = lazy(() => import('@/pages/FertilizerCalculator').then(m => ({ default: m.FertilizerCalculator })));
const CropCalendar = lazy(() => import('@/pages/CropCalendar').then(m => ({ default: m.CropCalendar })));
const YieldPredictor = lazy(() => import('@/pages/YieldPredictor').then(m => ({ default: m.YieldPredictor })));
const DiseaseAtlas = lazy(() => import('@/pages/DiseaseAtlas').then(m => ({ default: m.DiseaseAtlas })));
const DiseaseResistance = lazy(() => import('@/pages/DiseaseResistance').then(m => ({ default: m.DiseaseResistance })));
const AbioticStress = lazy(() => import('@/pages/AbioticStress').then(m => ({ default: m.AbioticStress })));
const PestMonitor = lazy(() => import('@/pages/PestMonitor').then(m => ({ default: m.PestMonitor })));
const CropHealthDashboard = lazy(() => import('@/pages/CropHealthDashboard').then(m => ({ default: m.CropHealthDashboard })));
const IrrigationPlanner = lazy(() => import('@/pages/IrrigationPlanner').then(m => ({ default: m.IrrigationPlanner })));

export const cropSystemsRoutes: RouteObject[] = [
  { path: '/soil-nutrients', element: wrapWithAppShell(SoilNutrientsDivision), children: soilNutrientsRoutes },
  { path: '/crop-intelligence', element: wrapWithAppShell(CropIntelligenceDivision), children: cropIntelligenceRoutes },
  { path: '/crop-protection', element: wrapWithAppShell(CropProtectionDivision), children: cropProtectionRoutes },
  { path: '/water-irrigation', element: wrapWithAppShell(WaterIrrigationDivision), children: waterIrrigationRoutes },
  { path: '/soil', element: wrapWithAppShell(SoilAnalysis) },
  { path: '/fertilizer', element: wrapWithAppShell(FertilizerCalculator) },
  { path: '/crop-calendar', element: wrapWithAppShell(CropCalendar) },
  { path: '/yield-predictor', element: wrapWithAppShell(YieldPredictor) },
  { path: '/disease-atlas', element: wrapWithAppShell(DiseaseAtlas) },
  { path: '/disease-resistance', element: wrapWithAppShell(DiseaseResistance) },
  { path: '/abiotic-stress', element: wrapWithAppShell(AbioticStress) },
  { path: '/pest-monitor', element: wrapWithAppShell(PestMonitor) },
  { path: '/crop-health', element: wrapWithAppShell(CropHealthDashboard) },
  { path: '/irrigation', element: wrapWithAppShell(IrrigationPlanner) },
  { path: '/sustainability', element: wrapWithAppShell(SoilNutrientsCarbonTracker) },
];