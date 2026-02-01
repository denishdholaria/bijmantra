import { lazy, Suspense } from 'react';
import { RouteObject, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Layout } from '@/components/Layout';

// Core Pages
// const Landing = lazy(() => import('@/pages/Landing'));
const Login = lazy(() => import('@/pages/Login').then(m => ({ default: m.Login })));
const Dashboard = lazy(() => import('@/pages/Dashboard').then(m => ({ default: m.Dashboard })));
const WorkspaceGateway = lazy(() => import('@/pages/WorkspaceGateway').then(m => ({ default: m.WorkspaceGateway })));
const Profile = lazy(() => import('@/pages/Profile').then(m => ({ default: m.Profile })));
const Settings = lazy(() => import('@/pages/Settings').then(m => ({ default: m.Settings })));
const Help = lazy(() => import('@/pages/Help').then(m => ({ default: m.Help })));
const Search = lazy(() => import('@/pages/Search').then(m => ({ default: m.Search })));
const Notifications = lazy(() => import('@/pages/Notifications').then(m => ({ default: m.Notifications })));

// Lists & Resources
const Images = lazy(() => import('@/pages/Images').then(m => ({ default: m.Images })));
const People = lazy(() => import('@/pages/People').then(m => ({ default: m.People })));
const PersonForm = lazy(() => import('@/pages/PersonForm').then(m => ({ default: m.PersonForm })));
const PersonDetail = lazy(() => import('@/pages/PersonDetail').then(m => ({ default: m.PersonDetail })));
const Lists = lazy(() => import('@/pages/Lists').then(m => ({ default: m.Lists })));
const ListDetail = lazy(() => import('@/pages/ListDetail').then(m => ({ default: m.ListDetail })));
const Seasons = lazy(() => import('@/pages/Seasons').then(m => ({ default: m.Seasons })));
const Reports = lazy(() => import('@/pages/Reports').then(m => ({ default: m.Reports })));
const CommonCropNames = lazy(() => import('@/pages/CommonCropNames').then(m => ({ default: m.CommonCropNames })));
const Ontologies = lazy(() => import('@/pages/Ontologies').then(m => ({ default: m.Ontologies })));

// Misc
const About = lazy(() => import('@/pages/About').then(m => ({ default: m.About })));
const Vision = lazy(() => import('@/pages/Vision').then(m => ({ default: m.Vision })));
const Inspiration = lazy(() => import('@/pages/Inspiration').then(m => ({ default: m.Inspiration })));
const HelpCenter = lazy(() => import('@/pages/HelpCenter').then(m => ({ default: m.HelpCenter })));
const QuickGuide = lazy(() => import('@/pages/QuickGuide').then(m => ({ default: m.QuickGuide })));
const Glossary = lazy(() => import('@/pages/Glossary').then(m => ({ default: m.Glossary })));
const FAQ = lazy(() => import('@/pages/FAQ').then(m => ({ default: m.FAQ })));
const KeyboardShortcuts = lazy(() => import('@/pages/KeyboardShortcuts').then(m => ({ default: m.KeyboardShortcuts })));
const WhatsNew = lazy(() => import('@/pages/WhatsNew').then(m => ({ default: m.WhatsNew })));
const Feedback = lazy(() => import('@/pages/Feedback').then(m => ({ default: m.Feedback })));
const Tips = lazy(() => import('@/pages/Tips').then(m => ({ default: m.Tips })));
const Changelog = lazy(() => import('@/pages/Changelog').then(m => ({ default: m.Changelog })));
const Contact = lazy(() => import('@/pages/Contact').then(m => ({ default: m.Contact })));
const Privacy = lazy(() => import('@/pages/Privacy').then(m => ({ default: m.Privacy })));
const Terms = lazy(() => import('@/pages/Terms').then(m => ({ default: m.Terms })));

// Field & Operations (Misc)
const FieldLayout = lazy(() => import('@/pages/FieldLayout').then(m => ({ default: m.FieldLayout })));
const TrialDesign = lazy(() => import('@/pages/TrialDesign').then(m => ({ default: m.TrialDesign })));
const Weather = lazy(() => import('@/pages/Weather').then(m => ({ default: m.Weather })));
const HarvestPlanner = lazy(() => import('@/pages/HarvestPlanner').then(m => ({ default: m.HarvestPlanner })));
const PhenotypeComparison = lazy(() => import('@/pages/PhenotypeComparison').then(m => ({ default: m.PhenotypeComparison })));
const Statistics = lazy(() => import('@/pages/Statistics').then(m => ({ default: m.Statistics })));
const NurseryManagement = lazy(() => import('@/pages/NurseryManagement').then(m => ({ default: m.NurseryManagement })));
const LabelPrinting = lazy(() => import('@/pages/LabelPrinting').then(m => ({ default: m.LabelPrinting })));
const TraitCalculator = lazy(() => import('@/pages/TraitCalculator').then(m => ({ default: m.TraitCalculator })));
const PhenologyTracker = lazy(() => import('@/pages/PhenologyTracker').then(m => ({ default: m.PhenologyTracker })));
const FieldBook = lazy(() => import('@/pages/FieldBook').then(m => ({ default: m.FieldBook })));
const YieldMap = lazy(() => import('@/pages/YieldMap').then(m => ({ default: m.YieldMap })));
const TrialPlanning = lazy(() => import('@/pages/TrialPlanning').then(m => ({ default: m.TrialPlanning })));
const DevProgress = lazy(() => import('@/pages/DevProgress').then(m => ({ default: m.DevProgress })));
const PedigreeAnalysis = lazy(() => import('@/pages/PedigreeAnalysis').then(m => ({ default: m.PedigreeAnalysis })));
const PhenotypeAnalysis = lazy(() => import('@/pages/PhenotypeAnalysis').then(m => ({ default: m.PhenotypeAnalysis })));
const FieldScanner = lazy(() => import('@/pages/FieldScanner').then(m => ({ default: m.FieldScanner })));
const CollaborationHub = lazy(() => import('@/pages/CollaborationHub').then(m => ({ default: m.CollaborationHub })));
const AdvancedReports = lazy(() => import('@/pages/AdvancedReports').then(m => ({ default: m.AdvancedReports })));
const ExperimentDesigner = lazy(() => import('@/pages/ExperimentDesigner').then(m => ({ default: m.ExperimentDesigner })));
const EnvironmentMonitor = lazy(() => import('@/pages/EnvironmentMonitor').then(m => ({ default: m.EnvironmentMonitor })));
const PublicationTracker = lazy(() => import('@/pages/PublicationTracker').then(m => ({ default: m.PublicationTracker })));
const TrainingHub = lazy(() => import('@/pages/TrainingHub').then(m => ({ default: m.TrainingHub })));
const BreedingGoals = lazy(() => import('@/pages/BreedingGoals').then(m => ({ default: m.BreedingGoals })));
const TrialComparison = lazy(() => import('@/pages/TrialComparison').then(m => ({ default: m.TrialComparison })));
const DataVisualization = lazy(() => import('@/pages/DataVisualization').then(m => ({ default: m.DataVisualization })));
const FieldMap = lazy(() => import('@/pages/FieldMap').then(m => ({ default: m.FieldMap })));
const PlotHistory = lazy(() => import('@/pages/PlotHistory').then(m => ({ default: m.PlotHistory })));
const GrowthTracker = lazy(() => import('@/pages/GrowthTracker').then(m => ({ default: m.GrowthTracker })));
const HarvestLog = lazy(() => import('@/pages/HarvestLog').then(m => ({ default: m.HarvestLog })));
const DroneIntegration = lazy(() => import('@/pages/DroneIntegration').then(m => ({ default: m.DroneIntegration })));
const IoTSensors = lazy(() => import('@/pages/IoTSensors').then(m => ({ default: m.IoTSensors })));
const BlockchainTraceability = lazy(() => import('@/pages/BlockchainTraceability').then(m => ({ default: m.BlockchainTraceability })));
const AnalyticsDashboard = lazy(() => import('@/pages/AnalyticsDashboard').then(m => ({ default: m.AnalyticsDashboard })));
const WeatherForecast = lazy(() => import('@/pages/WeatherForecast').then(m => ({ default: m.WeatherForecast })));
const NotificationCenter = lazy(() => import('@/pages/NotificationCenter').then(m => ({ default: m.NotificationCenter })));
const TrialNetwork = lazy(() => import('@/pages/TrialNetwork').then(m => ({ default: m.TrialNetwork })));
const ParentSelection = lazy(() => import('@/pages/ParentSelection').then(m => ({ default: m.ParentSelection })));
const ActivityTimeline = lazy(() => import('@/pages/ActivityTimeline').then(m => ({ default: m.ActivityTimeline })));
const FieldPlanning = lazy(() => import('@/pages/FieldPlanning').then(m => ({ default: m.FieldPlanning })));
const QuickEntry = lazy(() => import('@/pages/QuickEntry').then(m => ({ default: m.QuickEntry })));
const TrialSummary = lazy(() => import('@/pages/TrialSummary').then(m => ({ default: m.TrialSummary })));
const SelectionDecision = lazy(() => import('@/pages/SelectionDecision').then(m => ({ default: m.SelectionDecision })));
const SeasonPlanning = lazy(() => import('@/pages/SeasonPlanning').then(m => ({ default: m.SeasonPlanning })));
const HarvestManagement = lazy(() => import('@/pages/HarvestManagement').then(m => ({ default: m.HarvestManagement })));
const Events = lazy(() => import('@/pages/Events').then(m => ({ default: m.Events })));

// Helper
const wrap = (Component: React.LazyExoticComponent<any> | React.ComponentType) => (
  <ProtectedRoute>
    <Layout>
      <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
        <Component />
      </Suspense>
    </Layout>
  </ProtectedRoute>
);

export const coreRoutes: RouteObject[] = [
  // Public
  { path: '/', element: <Navigate to="/gateway" replace /> },
  { path: '/login', element: <Login /> },
  { path: '/gateway', element: <ProtectedRoute><WorkspaceGateway /></ProtectedRoute> },
  
  // Dashboard & Profile
  { path: '/dashboard', element: wrap(Dashboard) },
  { path: '/profile', element: wrap(Profile) },
  { path: '/settings', element: wrap(Settings) },
  { path: '/help', element: wrap(Help) },
  { path: '/search', element: wrap(Search) },
  { path: '/notifications', element: wrap(Notifications) },

  // Lists & Entities
  { path: '/events', element: wrap(Events) }, // Moved from Breeding? It was "Events routes" but generic
  { path: '/images', element: wrap(Images) },
  { path: '/people', element: wrap(People) },
  { path: '/people/new', element: wrap(PersonForm) },
  { path: '/people/:id', element: wrap(PersonDetail) },
  { path: '/people/:id/edit', element: wrap(PersonForm) },
  { path: '/lists', element: wrap(Lists) },
  { path: '/lists/:id', element: wrap(ListDetail) },
  { path: '/seasons', element: wrap(Seasons) },
  { path: '/reports', element: wrap(Reports) },
  { path: '/crops', element: wrap(CommonCropNames) },
  { path: '/ontologies', element: wrap(Ontologies) },

  // Info & Docs
  { path: '/about', element: wrap(About) },
  { path: '/vision', element: wrap(Vision) },
  { path: '/inspiration', element: wrap(Inspiration) },
  { path: '/help', element: wrap(HelpCenter) }, // Help duplicate? Keeping specific HelpCenter one
  { path: '/quick-guide', element: wrap(QuickGuide) },
  { path: '/glossary', element: wrap(Glossary) },
  { path: '/faq', element: wrap(FAQ) },
  { path: '/keyboard-shortcuts', element: wrap(KeyboardShortcuts) },
  { path: '/whats-new', element: wrap(WhatsNew) },
  { path: '/feedback', element: wrap(Feedback) },
  { path: '/tips', element: wrap(Tips) },
  { path: '/changelog', element: wrap(Changelog) },
  { path: '/contact', element: wrap(Contact) },
  { path: '/privacy', element: wrap(Privacy) },
  { path: '/terms', element: wrap(Terms) },

  // Misc Operations (Legacy/Other)
  { path: '/fieldlayout', element: wrap(FieldLayout) },
  { path: '/trialdesign', element: wrap(TrialDesign) },
  { path: '/weather', element: wrap(Weather) },
  { path: '/harvest', element: wrap(HarvestPlanner) },
  { path: '/comparison', element: wrap(PhenotypeComparison) },
  { path: '/statistics', element: wrap(Statistics) },
  { path: '/nursery', element: wrap(NurseryManagement) },
  { path: '/labels', element: wrap(LabelPrinting) },
  { path: '/calculator', element: wrap(TraitCalculator) },
  { path: '/phenology', element: wrap(PhenologyTracker) },
  { path: '/fieldbook', element: wrap(FieldBook) },
  { path: '/yieldmap', element: wrap(YieldMap) },
  { path: '/trialplanning', element: wrap(TrialPlanning) },
  { path: '/dev-progress', element: wrap(DevProgress) },
  { path: '/pedigree-analysis', element: wrap(PedigreeAnalysis) },
  { path: '/phenotype-analysis', element: wrap(PhenotypeAnalysis) },
  { path: '/field-scanner', element: wrap(FieldScanner) },
  { path: '/collaboration', element: wrap(CollaborationHub) },
  { path: '/advanced-reports', element: wrap(AdvancedReports) },
  { path: '/experiment-designer', element: wrap(ExperimentDesigner) },
  { path: '/environment-monitor', element: wrap(EnvironmentMonitor) },
  { path: '/publications', element: wrap(PublicationTracker) },
  { path: '/training', element: wrap(TrainingHub) },
  { path: '/breeding-goals', element: wrap(BreedingGoals) },
  { path: '/trial-comparison', element: wrap(TrialComparison) },
  { path: '/visualization', element: wrap(DataVisualization) },
  { path: '/field-map', element: wrap(FieldMap) },
  { path: '/plot-history', element: wrap(PlotHistory) },
  { path: '/growth-tracker', element: wrap(GrowthTracker) },
  { path: '/harvest-log', element: wrap(HarvestLog) },
  { path: '/drones', element: wrap(DroneIntegration) },
  { path: '/iot-sensors', element: wrap(IoTSensors) },
  { path: '/blockchain', element: wrap(BlockchainTraceability) },
  { path: '/analytics', element: wrap(AnalyticsDashboard) },
  { path: '/weather-forecast', element: wrap(WeatherForecast) },
  { path: '/notification-center', element: wrap(NotificationCenter) },
  { path: '/trial-network', element: wrap(TrialNetwork) },
  { path: '/parent-selection', element: wrap(ParentSelection) },
  { path: '/activity', element: wrap(ActivityTimeline) },
  { path: '/field-planning', element: wrap(FieldPlanning) },
  { path: '/quick-entry', element: wrap(QuickEntry) },
  { path: '/trial-summary', element: wrap(TrialSummary) },
  { path: '/selection-decision', element: wrap(SelectionDecision) },
  { path: '/season-planning', element: wrap(SeasonPlanning) },
  { path: '/harvest-management', element: wrap(HarvestManagement) },
];
