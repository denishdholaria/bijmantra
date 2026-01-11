import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useEffect, lazy, Suspense } from 'react'
import { useAuthStore } from '@/store/auth'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Login } from '@/pages/Login'
import { Dashboard } from '@/pages/Dashboard'
// Lazy load Gateway page
const WorkspaceGateway = lazy(() => import('@/pages/WorkspaceGateway'))
// Lazy load Design Preview (temporary)
const DesignPreview = lazy(() => import('@/pages/DesignPreview'))
// Lazy load Workspace Dashboards
const BreedingDashboard = lazy(() => import('@/pages/workspaces/BreedingDashboard'))
const SeedBusinessDashboard = lazy(() => import('@/pages/workspaces/SeedOpsDashboard'))
const ResearchDashboard = lazy(() => import('@/pages/workspaces/ResearchDashboard'))
const GeneBankDashboard = lazy(() => import('@/pages/workspaces/GeneBankDashboard'))
const AdminDashboard = lazy(() => import('@/pages/workspaces/AdminDashboard'))
// Lazy load Veena full page chat
const VeenaChat = lazy(() => import('@/pages/VeenaChat'))
// Lazy load REEVA experimental agent
const ReevaChat = lazy(() => import('@/pages/ReevaChat'))
import { Programs } from '@/pages/Programs'
import { ProgramForm } from '@/pages/ProgramForm'
import { ProgramDetail } from '@/pages/ProgramDetail'
import { ProgramEdit } from '@/pages/ProgramEdit'
import { Trials } from '@/pages/Trials'
import { TrialForm } from '@/pages/TrialForm'
import { TrialDetail } from '@/pages/TrialDetail'
import { TrialEdit } from '@/pages/TrialEdit'
import { Studies } from '@/pages/Studies'
import { StudyForm } from '@/pages/StudyForm'
import { StudyDetail } from '@/pages/StudyDetail'
import { StudyEdit } from '@/pages/StudyEdit'
import { Locations } from '@/pages/Locations'
import { LocationForm } from '@/pages/LocationForm'
import { LocationDetail } from '@/pages/LocationDetail'
import { LocationEdit } from '@/pages/LocationEdit'
import { Germplasm } from '@/pages/Germplasm'
import { GermplasmForm } from '@/pages/GermplasmForm'
import { GermplasmDetail } from '@/pages/GermplasmDetail'
import { Traits } from '@/pages/Traits'
import { TraitForm } from '@/pages/TraitForm'
import { TraitDetail } from '@/pages/TraitDetail'
import { TraitEdit } from '@/pages/TraitEdit'
import { Observations } from '@/pages/Observations'
import { ObservationUnits } from '@/pages/ObservationUnits'
import { DataCollect } from '@/pages/DataCollect'
import { SeedLots } from '@/pages/SeedLots'
import { SeedLotDetail } from '@/pages/SeedLotDetail'
import { SeedLotForm } from '@/pages/SeedLotForm'
import { Crosses } from '@/pages/Crosses'
import { CrossForm } from '@/pages/CrossForm'
import { People } from '@/pages/People'
import { Events } from '@/pages/Events'
import { GermplasmEdit } from '@/pages/GermplasmEdit'
import { GermplasmComparison } from '@/pages/GermplasmComparison'
import { Samples } from '@/pages/Samples'
import { Images } from '@/pages/Images'
import { PersonForm } from '@/pages/PersonForm'
import { Search } from '@/pages/Search'
import { Lists } from '@/pages/Lists'
import { ListDetail } from '@/pages/ListDetail'
import { Seasons } from '@/pages/Seasons'
import { ImportExport } from '@/pages/ImportExport'
import { Settings } from '@/pages/Settings'
import { Reports } from '@/pages/Reports'
import { CrossDetail } from '@/pages/CrossDetail'
import { PersonDetail } from '@/pages/PersonDetail'
import { ObservationUnitForm } from '@/pages/ObservationUnitForm'
import { Help } from '@/pages/Help'
import { SampleDetail } from '@/pages/SampleDetail'
import { SampleForm } from '@/pages/SampleForm'
import { Variants } from '@/pages/Variants'
import { VariantDetail } from '@/pages/VariantDetail'
import { VariantSets } from '@/pages/VariantSets'
import { Calls } from '@/pages/Calls'
import { CallSets } from '@/pages/CallSets'
import { AlleleMatrix } from '@/pages/AlleleMatrix'
import { Plates } from '@/pages/Plates'
import { References } from '@/pages/References'
import { GenomeMaps } from '@/pages/GenomeMaps'
import { MarkerPositions } from '@/pages/MarkerPositions'
import { VendorOrders } from '@/pages/VendorOrders'
import { CrossingProjects } from '@/pages/CrossingProjects'
import { PlannedCrosses } from '@/pages/PlannedCrosses'
import { Ontologies } from '@/pages/Ontologies'
import { CommonCropNames } from '@/pages/CommonCropNames'
import { FieldLayout } from '@/pages/FieldLayout'
import { Notifications } from '@/pages/Notifications'
import { AuditLog } from '@/pages/AuditLog'
import { Weather } from '@/pages/Weather'
import { BarcodeScanner } from '@/pages/BarcodeScanner'
import { UserManagement } from '@/pages/UserManagement'
import { SystemSettings } from '@/pages/SystemSettings'
import { SystemHealth } from '@/pages/SystemHealth'
import { SecurityDashboard } from '@/pages/SecurityDashboard'
import { DevProgress } from '@/pages/DevProgress'
import { BackupRestore } from '@/pages/BackupRestore'
import { DataQuality } from '@/pages/DataQuality'
import { ServerInfo } from '@/pages/ServerInfo'
import { GermplasmAttributes } from '@/pages/GermplasmAttributes'
import { GermplasmAttributeValues } from '@/pages/GermplasmAttributeValues'
import { Progeny } from '@/pages/Progeny'
import { TrialDesign } from '@/pages/TrialDesign'
import { SelectionIndex } from '@/pages/SelectionIndex'
import { GeneticGain } from '@/pages/GeneticGain'
import { SelectionIndexCalculator } from '@/pages/SelectionIndexCalculator'
import { GeneticGainTracker } from '@/pages/GeneticGainTracker'
import { HarvestManagement } from '@/pages/HarvestManagement'
import { BreedingValueCalculator } from '@/pages/BreedingValueCalculator'
import { PedigreeViewer } from '@/pages/PedigreeViewer'
// Lazy load Three.js pages to prevent blocking app startup
const Pedigree3D = lazy(() => import('@/pages/Pedigree3D').then(m => ({ default: m.Pedigree3D })).catch(() => ({ default: () => <div className="p-8 text-center text-gray-500">3D Pedigree unavailable</div> })))
import { BreedingPipeline } from '@/pages/BreedingPipeline'
import { HarvestPlanner } from '@/pages/HarvestPlanner'
import { SeedInventory } from '@/pages/SeedInventory'
import { CrossingPlanner } from '@/pages/CrossingPlanner'
import { PhenotypeComparison } from '@/pages/PhenotypeComparison'
import { Statistics } from '@/pages/Statistics'
import { NurseryManagement } from '@/pages/NurseryManagement'
import { LabelPrinting } from '@/pages/LabelPrinting'
import { TraitCalculator } from '@/pages/TraitCalculator'
import { GermplasmCollection } from '@/pages/GermplasmCollection'
import { PhenologyTracker } from '@/pages/PhenologyTracker'
import { SoilAnalysis } from '@/pages/SoilAnalysis'
import { FertilizerCalculator } from '@/pages/FertilizerCalculator'
import { FieldBook } from '@/pages/FieldBook'
import { VarietyComparison } from '@/pages/VarietyComparison'
import { YieldMap } from '@/pages/YieldMap'
import { SeedRequest } from '@/pages/SeedRequest'
import { TrialPlanning } from '@/pages/TrialPlanning'
import { AISettings } from '@/pages/AISettings'
import { AIAssistant } from '@/pages/AIAssistant'
import { ChromeAI } from '@/pages/ChromeAI'
import { About } from '@/pages/About'
import { Vision } from '@/pages/Vision'
import { Inspiration } from '@/pages/Inspiration'
// Lazy load DevGuru page
const DevGuru = lazy(() => import('@/pages/DevGuru'))
import { Profile } from '@/pages/Profile'
import { NotFound } from '@/pages/NotFound'
import { HelpCenter } from '@/pages/HelpCenter'
import { QuickGuide } from '@/pages/QuickGuide'
import { Glossary } from '@/pages/Glossary'
import { FAQ } from '@/pages/FAQ'
import { KeyboardShortcuts } from '@/pages/KeyboardShortcuts'
import { WhatsNew } from '@/pages/WhatsNew'
import { Feedback } from '@/pages/Feedback'
import { Tips } from '@/pages/Tips'
import { Changelog } from '@/pages/Changelog'
import { Contact } from '@/pages/Contact'
import { Privacy } from '@/pages/Privacy'
import { Terms } from '@/pages/Terms'
import { GeneticDiversity } from '@/pages/GeneticDiversity'
import { BreedingValues } from '@/pages/BreedingValues'
import { QTLMapping } from '@/pages/QTLMapping'
import { GenomicSelection } from '@/pages/GenomicSelection'
import { MarkerAssistedSelection } from '@/pages/MarkerAssistedSelection'
import { HaplotypeAnalysis } from '@/pages/HaplotypeAnalysis'
import { LinkageDisequilibrium } from '@/pages/LinkageDisequilibrium'
import { PopulationGenetics } from '@/pages/PopulationGenetics'
import { ParentageAnalysis } from '@/pages/ParentageAnalysis'
import { GeneticCorrelation } from '@/pages/GeneticCorrelation'
import { GxEInteraction } from '@/pages/GxEInteraction'
import { StabilityAnalysis } from '@/pages/StabilityAnalysis'
import { MolecularBreeding } from '@/pages/MolecularBreeding'
import { PhenomicSelection } from '@/pages/PhenomicSelection'
import { SpeedBreeding } from '@/pages/SpeedBreeding'
import { DoubledHaploid } from '@/pages/DoubledHaploid'
import { PlantVision } from '@/pages/PlantVision'
const PlantVisionStrategy = lazy(() => import('@/divisions/plant-sciences/pages/PlantVisionStrategy'))
import { VisionDashboard } from '@/pages/VisionDashboard'
import { VisionDatasets } from '@/pages/VisionDatasets'
import { VisionTraining } from '@/pages/VisionTraining'
import { VisionRegistry } from '@/pages/VisionRegistry'
import { VisionAnnotate } from '@/pages/VisionAnnotate'
import { DiseaseAtlas } from '@/pages/DiseaseAtlas'
import { DiseaseResistance } from '@/pages/DiseaseResistance'
import { AbioticStress } from '@/pages/AbioticStress'
import { Bioinformatics } from '@/pages/Bioinformatics'
import { CropCalendar } from '@/pages/CropCalendar'
import { SpatialAnalysis } from '@/pages/SpatialAnalysis'
import { PedigreeAnalysis } from '@/pages/PedigreeAnalysis'
import { PhenotypeAnalysis } from '@/pages/PhenotypeAnalysis'
import { FieldScanner } from '@/pages/FieldScanner'
import { CropHealthDashboard } from '@/pages/CropHealthDashboard'
import { YieldPredictor } from '@/pages/YieldPredictor'
import { CollaborationHub } from '@/pages/CollaborationHub'
import { AdvancedReports } from '@/pages/AdvancedReports'
import { DataSync } from '@/pages/DataSync'
import { TeamManagement } from '@/pages/TeamManagement'
import { ProtocolLibrary } from '@/pages/ProtocolLibrary'
import { ExperimentDesigner } from '@/pages/ExperimentDesigner'
import { ResourceCalendar } from '@/pages/ResourceCalendar'
import { EnvironmentMonitor } from '@/pages/EnvironmentMonitor'
import { CostAnalysis } from '@/pages/CostAnalysis'
import { PublicationTracker } from '@/pages/PublicationTracker'
import { TrainingHub } from '@/pages/TrainingHub'
import { VarietyRelease } from '@/pages/VarietyRelease'
import { ComplianceTracker } from '@/pages/ComplianceTracker'
import { GeneBank } from '@/pages/GeneBank'
import { BreedingGoals } from '@/pages/BreedingGoals'
import { MarketAnalysis } from '@/pages/MarketAnalysis'
import { StakeholderPortal } from '@/pages/StakeholderPortal'
import { TrialComparison } from '@/pages/TrialComparison'
import { DataVisualization } from '@/pages/DataVisualization'
import { APIExplorer } from '@/pages/APIExplorer'
import { BatchOperations } from '@/pages/BatchOperations'
import { FieldMap } from '@/pages/FieldMap'
import { PlotHistory } from '@/pages/PlotHistory'
import { GermplasmPassport } from '@/pages/GermplasmPassport'
import { SampleTracking } from '@/pages/SampleTracking'
import { IrrigationPlanner } from '@/pages/IrrigationPlanner'
import { PestMonitor } from '@/pages/PestMonitor'
import { GrowthTracker } from '@/pages/GrowthTracker'
import { HarvestLog } from '@/pages/HarvestLog'
import { DroneIntegration } from '@/pages/DroneIntegration'
import { IoTSensors } from '@/pages/IoTSensors'
import { BlockchainTraceability } from '@/pages/BlockchainTraceability'
import { AnalyticsDashboard } from '@/pages/AnalyticsDashboard'
import { WeatherForecast } from '@/pages/WeatherForecast'
import { WorkflowAutomation } from '@/pages/WorkflowAutomation'
import { DataExportTemplates } from '@/pages/DataExportTemplates'
import { NotificationCenter } from '@/pages/NotificationCenter'
import { LanguageSettings } from '@/pages/LanguageSettings'
import { GeneticGainCalculator } from '@/pages/GeneticGainCalculator'
import { TrialNetwork } from '@/pages/TrialNetwork'
import { ParentSelection } from '@/pages/ParentSelection'
import { OfflineMode } from '@/pages/OfflineMode'
import { MobileApp } from '@/pages/MobileApp'
// Lazy load Three.js pages to prevent blocking app startup
const BreedingSimulator = lazy(() => import('@/pages/BreedingSimulator').then(m => ({ default: m.BreedingSimulator })).catch(() => ({ default: () => <div className="p-8 text-center text-gray-500">3D Simulator unavailable</div> })))
import { DataDictionary } from '@/pages/DataDictionary'
import { ActivityTimeline } from '@/pages/ActivityTimeline'
import { GermplasmSearch } from '@/pages/GermplasmSearch'
import { FieldPlanning } from '@/pages/FieldPlanning'
import { QuickEntry } from '@/pages/QuickEntry'
import { CrossPrediction } from '@/pages/CrossPrediction'
import { TrialSummary } from '@/pages/TrialSummary'
import { SelectionDecision } from '@/pages/SelectionDecision'
import { SeasonPlanning } from '@/pages/SeasonPlanning'
import { DataValidation } from '@/pages/DataValidation'
import { BreedingHistory } from '@/pages/BreedingHistory'
import { ResourceAllocation } from '@/pages/ResourceAllocation'
import { GeneticMap } from '@/pages/GeneticMap'
import { PerformanceRanking } from '@/pages/PerformanceRanking'
import { WasmGenomics } from '@/pages/WasmGenomics'
import { WasmGBLUP } from '@/pages/WasmGBLUP'
import { WasmPopGen } from '@/pages/WasmPopGen'
import { WasmLDAnalysis } from '@/pages/WasmLDAnalysis'
import { WasmSelectionIndex } from '@/pages/WasmSelectionIndex'
import InsightsDashboard from '@/pages/InsightsDashboard'
import ApexAnalytics from '@/pages/ApexAnalytics'

// Earth Systems Division - lazy loaded
const EarthSystemsDashboard = lazy(() => import('@/divisions/earth-systems/pages/Dashboard'))
const EarthSystemsWeather = lazy(() => import('@/divisions/earth-systems/pages/WeatherForecast'))
const EarthSystemsClimate = lazy(() => import('@/divisions/earth-systems/pages/ClimateAnalysis'))
const EarthSystemsSoil = lazy(() => import('@/divisions/earth-systems/pages/SoilData'))
const EarthSystemsInputs = lazy(() => import('@/divisions/earth-systems/pages/InputLog'))
const EarthSystemsIrrigation = lazy(() => import('@/divisions/earth-systems/pages/Irrigation'))
const EarthSystemsGDD = lazy(() => import('@/divisions/earth-systems/pages/GrowingDegrees'))
const EarthSystemsDrought = lazy(() => import('@/divisions/earth-systems/pages/DroughtMonitor'))
const EarthSystemsMap = lazy(() => import('@/divisions/earth-systems/pages/FieldMap'))

// Integration Hub
const IntegrationsHub = lazy(() => import('@/divisions/integrations/pages/Dashboard'))

// Seed Operations Division - lazy loaded
const SeedOpsDashboard = lazy(() => import('@/divisions/seed-operations/pages/Dashboard'))
const SeedOpsLabSamples = lazy(() => import('@/divisions/seed-operations/pages/LabSamples'))
const SeedOpsLabTesting = lazy(() => import('@/divisions/seed-operations/pages/LabTesting'))
const SeedOpsCertificates = lazy(() => import('@/divisions/seed-operations/pages/Certificates'))
const SeedOpsQualityGate = lazy(() => import('@/divisions/seed-operations/pages/QualityGate'))
const SeedOpsBatches = lazy(() => import('@/divisions/seed-operations/pages/ProcessingBatches'))
const SeedOpsStages = lazy(() => import('@/divisions/seed-operations/pages/ProcessingStages'))
const SeedOpsLots = lazy(() => import('@/divisions/seed-operations/pages/SeedLots'))
const SeedOpsWarehouse = lazy(() => import('@/divisions/seed-operations/pages/Warehouse'))
const SeedOpsAlerts = lazy(() => import('@/divisions/seed-operations/pages/StockAlerts'))
const SeedOpsDispatch = lazy(() => import('@/divisions/seed-operations/pages/CreateDispatch'))
const SeedOpsDispatchHistory = lazy(() => import('@/divisions/seed-operations/pages/DispatchHistory'))
const SeedOpsFirms = lazy(() => import('@/divisions/seed-operations/pages/Firms'))
const SeedOpsTrack = lazy(() => import('@/divisions/seed-operations/pages/TrackLot'))
const SeedOpsLineage = lazy(() => import('@/divisions/seed-operations/pages/Lineage'))
const SeedOpsVarieties = lazy(() => import('@/divisions/seed-operations/pages/Varieties'))
const SeedOpsAgreements = lazy(() => import('@/divisions/seed-operations/pages/Agreements'))

// Barcode Management
const BarcodeManagement = lazy(() => import('@/pages/BarcodeManagement'))

// Seed Bank Division - lazy loaded
const SeedBankDashboard = lazy(() => import('@/divisions/seed-bank/pages/Dashboard'))
const SeedBankVault = lazy(() => import('@/divisions/seed-bank/pages/VaultManagement'))
const SeedBankAccessions = lazy(() => import('@/divisions/seed-bank/pages/Accessions'))
const SeedBankAccessionNew = lazy(() => import('@/divisions/seed-bank/pages/AccessionNew'))
const SeedBankAccessionDetail = lazy(() => import('@/divisions/seed-bank/pages/AccessionDetail'))
const SeedBankConservation = lazy(() => import('@/divisions/seed-bank/pages/Conservation'))
const SeedBankExchange = lazy(() => import('@/divisions/seed-bank/pages/GermplasmExchange'))
const SeedBankViability = lazy(() => import('@/divisions/seed-bank/pages/ViabilityTesting'))
const SeedBankRegeneration = lazy(() => import('@/divisions/seed-bank/pages/RegenerationPlanning'))
const SeedBankMCPD = lazy(() => import('@/divisions/seed-bank/pages/MCPDExchange'))
const SeedBankGRINSearch = lazy(() => import('@/divisions/seed-bank/pages/GRINSearch'))
const SeedBankTaxonomy = lazy(() => import('@/divisions/seed-bank/pages/TaxonomyValidator'))
const SeedBankMTA = lazy(() => import('@/divisions/seed-bank/pages/MTAManagement'))
const SeedBankVaultMonitoring = lazy(() => import('@/divisions/seed-bank/pages/VaultMonitoring'))
const SeedBankOfflineEntry = lazy(() => import('@/divisions/seed-bank/pages/OfflineDataEntry'))

// Commercial Division - DUS Testing
const CommercialDashboard = lazy(() => import('@/divisions/commercial/pages/Dashboard'))
const DUSTrials = lazy(() => import('@/divisions/commercial/pages/DUSTrials'))
const DUSCrops = lazy(() => import('@/divisions/commercial/pages/DUSCrops'))
const DUSTrialDetail = lazy(() => import('@/divisions/commercial/pages/DUSTrialDetail'))

// Sun-Earth Systems Division - lazy loaded
const SunEarthDashboard = lazy(() => import('@/divisions/sun-earth-systems/pages/Dashboard'))
const SunEarthSolarActivity = lazy(() => import('@/divisions/sun-earth-systems/pages/SolarActivity'))
const SunEarthPhotoperiod = lazy(() => import('@/divisions/sun-earth-systems/pages/Photoperiod'))
const SunEarthUVIndex = lazy(() => import('@/divisions/sun-earth-systems/pages/UVIndex'))

// Space Research Division - lazy loaded
const SpaceResearchDashboard = lazy(() => import('@/divisions/space-research/pages/Dashboard'))
const SpaceResearchCrops = lazy(() => import('@/divisions/space-research/pages/SpaceCrops'))
const SpaceResearchRadiation = lazy(() => import('@/divisions/space-research/pages/Radiation'))
const SpaceResearchLifeSupport = lazy(() => import('@/divisions/space-research/pages/LifeSupport'))

// Sensor Networks Division - lazy loaded
const SensorNetworksDashboard = lazy(() => import('@/divisions/sensor-networks/pages/Dashboard'))
const SensorNetworksDevices = lazy(() => import('@/divisions/sensor-networks/pages/Devices'))
const SensorNetworksLiveData = lazy(() => import('@/divisions/sensor-networks/pages/LiveData'))
const SensorNetworksAlerts = lazy(() => import('@/divisions/sensor-networks/pages/Alerts'))

// Knowledge Division - lazy loaded
const KnowledgeForums = lazy(() => import('@/divisions/knowledge/pages/Forums'))
const KnowledgeForumTopic = lazy(() => import('@/divisions/knowledge/pages/ForumTopic'))
const KnowledgeNewTopic = lazy(() => import('@/divisions/knowledge/pages/NewTopic'))
const KnowledgeTrainingHub = lazy(() => import('@/divisions/knowledge/pages/TrainingHub'))

// Future Divisions - Placeholder pages for roadmap modules
const FuturePlaceholder = lazy(() => import('@/pages/FuturePlaceholder'))

// Inner component that uses router hooks
function AppRoutes() {
  const navigate = useNavigate()
  const { logout } = useAuthStore()

  const { preferences } = useWorkspaceStore()

  // Apply theme
  useEffect(() => {
    const theme = preferences.theme || 'prakruti'
    document.documentElement.setAttribute('data-theme', theme)

    // Aerospace implies dark mode
    if (theme === 'aerospace') {
      document.documentElement.classList.add('dark')
    } else {
      // For Prakruti, we might want to respect system preference or separate toggle
      // For now, removing 'dark' class if switching back to Prakruti to default to light
      // unless user has a separate dark mode toggle (which we don't see yet)
      document.documentElement.classList.remove('dark')
    }
  }, [preferences.theme])

  // Listen for unauthorized events (401 responses)
  useEffect(() => {
    const handleUnauthorized = () => {
      logout()
      navigate('/login', { replace: true })
    }
    
    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [logout, navigate])

  return (
    <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        
        {/* Workspace Gateway - Protected but without Layout */}
        <Route
          path="/gateway"
          element={
            <ProtectedRoute>
              <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin h-8 w-8 border-4 border-green-500 border-t-transparent rounded-full" /></div>}>
                <WorkspaceGateway />
              </Suspense>
            </ProtectedRoute>
          }
        />
        
        {/* Workspace-Specific Dashboards */}
        <Route
          path="/breeding/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <BreedingDashboard />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/seed-ops/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <SeedBusinessDashboard />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/research/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <ResearchDashboard />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/genebank/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <GeneBankDashboard />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <AdminDashboard />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Protected Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/programs"
          element={
            <ProtectedRoute>
              <Layout>
                <Programs />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/programs/new"
          element={
            <ProtectedRoute>
              <Layout>
                <ProgramForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/programs/:programDbId"
          element={
            <ProtectedRoute>
              <Layout>
                <ProgramDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/programs/:programDbId/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <ProgramEdit />
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Trial routes */}
        <Route
          path="/trials"
          element={
            <ProtectedRoute>
              <Layout>
                <Trials />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trials/new"
          element={
            <ProtectedRoute>
              <Layout>
                <TrialForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trials/:trialDbId"
          element={
            <ProtectedRoute>
              <Layout>
                <TrialDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trials/:trialDbId/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <TrialEdit />
              </Layout>
            </ProtectedRoute>
          }
        />
        {/* Study routes */}
        <Route
          path="/studies"
          element={
            <ProtectedRoute>
              <Layout>
                <Studies />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/studies/new"
          element={
            <ProtectedRoute>
              <Layout>
                <StudyForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/studies/:studyDbId"
          element={
            <ProtectedRoute>
              <Layout>
                <StudyDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/studies/:studyDbId/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <StudyEdit />
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Location routes */}
        <Route
          path="/locations"
          element={
            <ProtectedRoute>
              <Layout>
                <Locations />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/locations/new"
          element={
            <ProtectedRoute>
              <Layout>
                <LocationForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/locations/:locationDbId"
          element={
            <ProtectedRoute>
              <Layout>
                <LocationDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/locations/:locationDbId/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <LocationEdit />
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Traits/Observation Variables routes */}
        <Route
          path="/traits"
          element={
            <ProtectedRoute>
              <Layout>
                <Traits />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/traits/new"
          element={
            <ProtectedRoute>
              <Layout>
                <TraitForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/traits/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <TraitDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/traits/:id/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <TraitEdit />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Observations routes */}
        <Route
          path="/observations"
          element={
            <ProtectedRoute>
              <Layout>
                <Observations />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/observations/collect"
          element={
            <ProtectedRoute>
              <Layout>
                <DataCollect />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Observation Units routes */}
        <Route
          path="/observationunits"
          element={
            <ProtectedRoute>
              <Layout>
                <ObservationUnits />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/observationunits/new"
          element={
            <ProtectedRoute>
              <Layout>
                <ObservationUnitForm />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Seed Lots routes */}
        <Route
          path="/seedlots"
          element={
            <ProtectedRoute>
              <Layout>
                <SeedLots />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/seedlots/new"
          element={
            <ProtectedRoute>
              <Layout>
                <SeedLotForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/seedlots/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <SeedLotDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/seedlots/:id/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <SeedLotForm />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Crosses routes */}
        <Route
          path="/crosses"
          element={
            <ProtectedRoute>
              <Layout>
                <Crosses />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/crosses/new"
          element={
            <ProtectedRoute>
              <Layout>
                <CrossForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/crosses/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <CrossDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/crosses/:id/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <CrossForm />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Events routes */}
        <Route
          path="/events"
          element={
            <ProtectedRoute>
              <Layout>
                <Events />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Samples routes (Genotyping) */}
        <Route
          path="/samples"
          element={
            <ProtectedRoute>
              <Layout>
                <Samples />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/samples/new"
          element={
            <ProtectedRoute>
              <Layout>
                <SampleForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/samples/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <SampleDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/samples/:id/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <SampleForm />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Variants routes (Genotyping) */}
        <Route
          path="/variants"
          element={
            <ProtectedRoute>
              <Layout>
                <Variants />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/variants/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <VariantDetail />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Variant Sets routes */}
        <Route
          path="/variantsets"
          element={
            <ProtectedRoute>
              <Layout>
                <VariantSets />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Calls routes */}
        <Route
          path="/calls"
          element={
            <ProtectedRoute>
              <Layout>
                <Calls />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Call Sets routes */}
        <Route
          path="/callsets"
          element={
            <ProtectedRoute>
              <Layout>
                <CallSets />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Allele Matrix */}
        <Route
          path="/allelematrix"
          element={
            <ProtectedRoute>
              <Layout>
                <AlleleMatrix />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Plates routes */}
        <Route
          path="/plates"
          element={
            <ProtectedRoute>
              <Layout>
                <Plates />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* References routes */}
        <Route
          path="/references"
          element={
            <ProtectedRoute>
              <Layout>
                <References />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Genome Maps routes */}
        <Route
          path="/genomemaps"
          element={
            <ProtectedRoute>
              <Layout>
                <GenomeMaps />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Marker Positions routes */}
        <Route
          path="/markerpositions"
          element={
            <ProtectedRoute>
              <Layout>
                <MarkerPositions />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Vendor Orders routes */}
        <Route
          path="/vendororders"
          element={
            <ProtectedRoute>
              <Layout>
                <VendorOrders />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Crossing Projects routes */}
        <Route
          path="/crossingprojects"
          element={
            <ProtectedRoute>
              <Layout>
                <CrossingProjects />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Planned Crosses routes */}
        <Route
          path="/plannedcrosses"
          element={
            <ProtectedRoute>
              <Layout>
                <PlannedCrosses />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Ontologies routes */}
        <Route
          path="/ontologies"
          element={
            <ProtectedRoute>
              <Layout>
                <Ontologies />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Common Crop Names routes */}
        <Route
          path="/crops"
          element={
            <ProtectedRoute>
              <Layout>
                <CommonCropNames />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Server Info routes */}
        <Route
          path="/serverinfo"
          element={
            <ProtectedRoute>
              <Layout>
                <ServerInfo />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Germplasm Attributes routes */}
        <Route
          path="/germplasmattributes"
          element={
            <ProtectedRoute>
              <Layout>
                <GermplasmAttributes />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Germplasm Attribute Values routes */}
        <Route
          path="/attributevalues"
          element={
            <ProtectedRoute>
              <Layout>
                <GermplasmAttributeValues />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Progeny routes */}
        <Route
          path="/progeny"
          element={
            <ProtectedRoute>
              <Layout>
                <Progeny />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Trial Design routes */}
        <Route
          path="/trialdesign"
          element={
            <ProtectedRoute>
              <Layout>
                <TrialDesign />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Selection Index routes */}
        <Route
          path="/selectionindex"
          element={
            <ProtectedRoute>
              <Layout>
                <SelectionIndex />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Field Layout routes */}
        <Route
          path="/fieldlayout"
          element={
            <ProtectedRoute>
              <Layout>
                <FieldLayout />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Notifications routes */}
        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <Layout>
                <Notifications />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Audit Log routes */}
        <Route
          path="/auditlog"
          element={
            <ProtectedRoute>
              <Layout>
                <AuditLog />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Weather routes */}
        <Route
          path="/weather"
          element={
            <ProtectedRoute>
              <Layout>
                <Weather />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Earth Systems Division routes */}
        <Route
          path="/earth-systems"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsDashboard />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/earth-systems/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsDashboard />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/earth-systems/weather"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsWeather />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/earth-systems/climate"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsClimate />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/earth-systems/soil"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsSoil />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/earth-systems/inputs"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsInputs />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/earth-systems/irrigation"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsIrrigation />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/earth-systems/gdd"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsGDD />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/earth-systems/drought"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsDrought />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/earth-systems/map"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <EarthSystemsMap />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Seed Operations Division routes */}
        <Route path="/seed-operations" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/dashboard" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/samples" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsLabSamples /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/testing" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsLabTesting /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/certificates" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsCertificates /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/quality-gate" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsQualityGate /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/batches" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsBatches /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/stages" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsStages /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/lots" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsLots /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/warehouse" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsWarehouse /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/alerts" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsAlerts /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/dispatch" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsDispatch /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/dispatch-history" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsDispatchHistory /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/firms" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsFirms /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/track" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsTrack /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/lineage" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsLineage /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/varieties" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsVarieties /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-operations/agreements" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedOpsAgreements /></Suspense></Layout></ProtectedRoute>} />

        {/* Barcode Management */}
        <Route path="/barcode" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><BarcodeManagement /></Suspense></Layout></ProtectedRoute>} />

        {/* Seed Bank Division routes */}
        <Route path="/seed-bank" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/dashboard" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/vault" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankVault /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/accessions" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankAccessions /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/accessions/new" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankAccessionNew /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/accessions/:id" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankAccessionDetail /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/conservation" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankConservation /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/viability" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankViability /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/regeneration" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankRegeneration /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/exchange" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankExchange /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/mcpd" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankMCPD /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/grin-search" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankGRINSearch /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/taxonomy" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankTaxonomy /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/mta" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankMTA /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/monitoring" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankVaultMonitoring /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/seed-bank/offline" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SeedBankOfflineEntry /></Suspense></Layout></ProtectedRoute>} />

        {/* Commercial Division - DUS Testing */}
        <Route path="/commercial" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><CommercialDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/commercial/dus-trials" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><DUSTrials /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/commercial/dus-crops" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><DUSCrops /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/commercial/dus-trials/:id" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><DUSTrialDetail /></Suspense></Layout></ProtectedRoute>} />

        {/* Sun-Earth Systems Division routes */}
        <Route path="/sun-earth-systems" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SunEarthDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/sun-earth-systems/dashboard" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SunEarthDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/sun-earth-systems/solar-activity" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SunEarthSolarActivity /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/sun-earth-systems/photoperiod" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SunEarthPhotoperiod /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/sun-earth-systems/uv-index" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SunEarthUVIndex /></Suspense></Layout></ProtectedRoute>} />

        {/* Space Research Division routes */}
        <Route path="/space-research" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SpaceResearchDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/space-research/dashboard" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SpaceResearchDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/space-research/crops" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SpaceResearchCrops /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/space-research/radiation" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SpaceResearchRadiation /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/space-research/life-support" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SpaceResearchLifeSupport /></Suspense></Layout></ProtectedRoute>} />

        {/* Sensor Networks Division routes */}
        <Route path="/sensor-networks" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SensorNetworksDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/sensor-networks/dashboard" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SensorNetworksDashboard /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/sensor-networks/devices" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SensorNetworksDevices /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/sensor-networks/live" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SensorNetworksLiveData /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/sensor-networks/alerts" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><SensorNetworksAlerts /></Suspense></Layout></ProtectedRoute>} />

        {/* Knowledge Division routes */}
        <Route path="/knowledge/training" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><KnowledgeTrainingHub /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/knowledge/forums" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><KnowledgeForums /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/knowledge/forums/new" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><KnowledgeNewTopic /></Suspense></Layout></ProtectedRoute>} />
        <Route path="/knowledge/forums/:topicId" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><KnowledgeForumTopic /></Suspense></Layout></ProtectedRoute>} />

        {/* Integration Hub routes */}
        <Route
          path="/integrations"
          element={
            <ProtectedRoute>
              <Layout>
                <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                  <IntegrationsHub />
                </Suspense>
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Barcode Scanner routes */}
        <Route
          path="/scanner"
          element={
            <ProtectedRoute>
              <Layout>
                <BarcodeScanner />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* User Management routes */}
        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <Layout>
                <UserManagement />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* System Settings routes */}
        <Route
          path="/system-settings"
          element={
            <ProtectedRoute>
              <Layout>
                <SystemSettings />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/system-health"
          element={
            <ProtectedRoute>
              <Layout>
                <SystemHealth />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Security Dashboard - ASHTA-STAMBHA Command Center */}
        <Route
          path="/security"
          element={
            <ProtectedRoute>
              <Layout>
                <SecurityDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Dev Progress - Development tracking dashboard */}
        <Route
          path="/dev-progress"
          element={
            <ProtectedRoute>
              <Layout>
                <DevProgress />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Backup & Restore routes */}
        <Route
          path="/backup"
          element={
            <ProtectedRoute>
              <Layout>
                <BackupRestore />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Data Quality routes */}
        <Route
          path="/dataquality"
          element={
            <ProtectedRoute>
              <Layout>
                <DataQuality />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Images routes */}
        <Route
          path="/images"
          element={
            <ProtectedRoute>
              <Layout>
                <Images />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* People routes */}
        <Route
          path="/people"
          element={
            <ProtectedRoute>
              <Layout>
                <People />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/people/new"
          element={
            <ProtectedRoute>
              <Layout>
                <PersonForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/people/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <PersonDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/people/:id/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <PersonForm />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Search */}
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <Layout>
                <Search />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Lists */}
        <Route
          path="/lists"
          element={
            <ProtectedRoute>
              <Layout>
                <Lists />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/lists/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <ListDetail />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Seasons */}
        <Route
          path="/seasons"
          element={
            <ProtectedRoute>
              <Layout>
                <Seasons />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Import/Export */}
        <Route
          path="/import-export"
          element={
            <ProtectedRoute>
              <Layout>
                <ImportExport />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Reports */}
        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <Layout>
                <Reports />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Germplasm routes */}
        <Route
          path="/germplasm"
          element={
            <ProtectedRoute>
              <Layout>
                <Germplasm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/germplasm/new"
          element={
            <ProtectedRoute>
              <Layout>
                <GermplasmForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/germplasm/:germplasmDbId"
          element={
            <ProtectedRoute>
              <Layout>
                <GermplasmDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/germplasm/:germplasmDbId/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <GermplasmEdit />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/germplasm-comparison"
          element={
            <ProtectedRoute>
              <Layout>
                <GermplasmComparison />
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Help */}
        <Route
          path="/help"
          element={
            <ProtectedRoute>
              <Layout>
                <Help />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Profile */}
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Layout>
                <Profile />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Settings */}
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Layout>
                <Settings />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Genetic Gain */}
        <Route
          path="/geneticgain"
          element={
            <ProtectedRoute>
              <Layout>
                <GeneticGain />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Pedigree Viewer */}
        <Route
          path="/pedigree"
          element={
            <ProtectedRoute>
              <Layout>
                <PedigreeViewer />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* 3D Pedigree Explorer */}
        <Route
          path="/pedigree-3d"
          element={
            <ProtectedRoute>
              <Layout>
                <Pedigree3D />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Breeding Pipeline */}
        <Route
          path="/pipeline"
          element={
            <ProtectedRoute>
              <Layout>
                <BreedingPipeline />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Harvest Planner */}
        <Route
          path="/harvest"
          element={
            <ProtectedRoute>
              <Layout>
                <HarvestPlanner />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Seed Inventory */}
        <Route
          path="/inventory"
          element={
            <ProtectedRoute>
              <Layout>
                <SeedInventory />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Crossing Planner */}
        <Route
          path="/crossingplanner"
          element={
            <ProtectedRoute>
              <Layout>
                <CrossingPlanner />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Phenotype Comparison */}
        <Route
          path="/comparison"
          element={
            <ProtectedRoute>
              <Layout>
                <PhenotypeComparison />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Statistics */}
        <Route
          path="/statistics"
          element={
            <ProtectedRoute>
              <Layout>
                <Statistics />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Nursery Management */}
        <Route
          path="/nursery"
          element={
            <ProtectedRoute>
              <Layout>
                <NurseryManagement />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Label Printing */}
        <Route
          path="/labels"
          element={
            <ProtectedRoute>
              <Layout>
                <LabelPrinting />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Trait Calculator */}
        <Route
          path="/calculator"
          element={
            <ProtectedRoute>
              <Layout>
                <TraitCalculator />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Germplasm Collection */}
        <Route
          path="/collections"
          element={
            <ProtectedRoute>
              <Layout>
                <GermplasmCollection />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Phenology Tracker */}
        <Route
          path="/phenology"
          element={
            <ProtectedRoute>
              <Layout>
                <PhenologyTracker />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Soil Analysis */}
        <Route
          path="/soil"
          element={
            <ProtectedRoute>
              <Layout>
                <SoilAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Fertilizer Calculator */}
        <Route
          path="/fertilizer"
          element={
            <ProtectedRoute>
              <Layout>
                <FertilizerCalculator />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Field Book */}
        <Route
          path="/fieldbook"
          element={
            <ProtectedRoute>
              <Layout>
                <FieldBook />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Variety Comparison */}
        <Route
          path="/varietycomparison"
          element={
            <ProtectedRoute>
              <Layout>
                <VarietyComparison />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Yield Map */}
        <Route
          path="/yieldmap"
          element={
            <ProtectedRoute>
              <Layout>
                <YieldMap />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Seed Request */}
        <Route
          path="/seedrequest"
          element={
            <ProtectedRoute>
              <Layout>
                <SeedRequest />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Trial Planning */}
        <Route
          path="/trialplanning"
          element={
            <ProtectedRoute>
              <Layout>
                <TrialPlanning />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* AI Settings */}
        <Route
          path="/ai-settings"
          element={
            <ProtectedRoute>
              <Layout>
                <AISettings />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Veena Full Page Chat */}
        <Route
          path="/veena"
          element={
            <ProtectedRoute>
              <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin h-8 w-8 border-4 border-amber-500 border-t-transparent rounded-full" /></div>}>
                <VeenaChat />
              </Suspense>
            </ProtectedRoute>
          }
        />

        {/* REEVA Experimental Agent */}
        <Route
          path="/reeva"
          element={
            <ProtectedRoute>
              <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin h-8 w-8 border-4 border-violet-500 border-t-transparent rounded-full" /></div>}>
                <ReevaChat />
              </Suspense>
            </ProtectedRoute>
          }
        />

        {/* AI Assistant */}
        <Route
          path="/ai-assistant"
          element={
            <ProtectedRoute>
              <Layout>
                <AIAssistant />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Chrome AI */}
        <Route
          path="/chrome-ai"
          element={
            <ProtectedRoute>
              <Layout>
                <ChromeAI />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Design Preview - Temporary for prototype review */}
        <Route
          path="/design-preview"
          element={
            <ProtectedRoute>
              <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
                <DesignPreview />
              </Suspense>
            </ProtectedRoute>
          }
        />

        {/* About */}
        <Route
          path="/about"
          element={
            <ProtectedRoute>
              <Layout>
                <About />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Vision */}
        <Route
          path="/vision"
          element={
            <ProtectedRoute>
              <Layout>
                <Vision />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Inspiration Museum */}
        <Route
          path="/inspiration"
          element={
            <ProtectedRoute>
              <Layout>
                <Inspiration />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* DevGuru - AI Research Mentor */}
        <Route
          path="/devguru"
          element={
            <ProtectedRoute>
              <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full" /></div>}>
                <DevGuru />
              </Suspense>
            </ProtectedRoute>
          }
        />

        {/* Help Center */}
        <Route
          path="/help"
          element={
            <ProtectedRoute>
              <Layout>
                <HelpCenter />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Quick Guide */}
        <Route
          path="/quick-guide"
          element={
            <ProtectedRoute>
              <Layout>
                <QuickGuide />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Glossary */}
        <Route
          path="/glossary"
          element={
            <ProtectedRoute>
              <Layout>
                <Glossary />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* FAQ */}
        <Route
          path="/faq"
          element={
            <ProtectedRoute>
              <Layout>
                <FAQ />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Keyboard Shortcuts */}
        <Route
          path="/keyboard-shortcuts"
          element={
            <ProtectedRoute>
              <Layout>
                <KeyboardShortcuts />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* What's New */}
        <Route
          path="/whats-new"
          element={
            <ProtectedRoute>
              <Layout>
                <WhatsNew />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Feedback */}
        <Route
          path="/feedback"
          element={
            <ProtectedRoute>
              <Layout>
                <Feedback />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Tips & Tricks */}
        <Route
          path="/tips"
          element={
            <ProtectedRoute>
              <Layout>
                <Tips />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Changelog */}
        <Route
          path="/changelog"
          element={
            <ProtectedRoute>
              <Layout>
                <Changelog />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Contact */}
        <Route
          path="/contact"
          element={
            <ProtectedRoute>
              <Layout>
                <Contact />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Privacy */}
        <Route
          path="/privacy"
          element={
            <ProtectedRoute>
              <Layout>
                <Privacy />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Terms */}
        <Route
          path="/terms"
          element={
            <ProtectedRoute>
              <Layout>
                <Terms />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Genetic Diversity */}
        <Route
          path="/genetic-diversity"
          element={
            <ProtectedRoute>
              <Layout>
                <GeneticDiversity />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Breeding Values */}
        <Route
          path="/breeding-values"
          element={
            <ProtectedRoute>
              <Layout>
                <BreedingValues />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* QTL Mapping */}
        <Route
          path="/qtl-mapping"
          element={
            <ProtectedRoute>
              <Layout>
                <QTLMapping />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Genomic Selection */}
        <Route
          path="/genomic-selection"
          element={
            <ProtectedRoute>
              <Layout>
                <GenomicSelection />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Marker-Assisted Selection */}
        <Route
          path="/marker-assisted-selection"
          element={
            <ProtectedRoute>
              <Layout>
                <MarkerAssistedSelection />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Haplotype Analysis */}
        <Route
          path="/haplotype-analysis"
          element={
            <ProtectedRoute>
              <Layout>
                <HaplotypeAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Linkage Disequilibrium */}
        <Route
          path="/linkage-disequilibrium"
          element={
            <ProtectedRoute>
              <Layout>
                <LinkageDisequilibrium />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Population Genetics */}
        <Route
          path="/population-genetics"
          element={
            <ProtectedRoute>
              <Layout>
                <PopulationGenetics />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Parentage Analysis */}
        <Route
          path="/parentage-analysis"
          element={
            <ProtectedRoute>
              <Layout>
                <ParentageAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Genetic Correlation */}
        <Route
          path="/genetic-correlation"
          element={
            <ProtectedRoute>
              <Layout>
                <GeneticCorrelation />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* G×E Interaction */}
        <Route
          path="/gxe-interaction"
          element={
            <ProtectedRoute>
              <Layout>
                <GxEInteraction />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Stability Analysis */}
        <Route
          path="/stability-analysis"
          element={
            <ProtectedRoute>
              <Layout>
                <StabilityAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Molecular Breeding */}
        <Route
          path="/molecular-breeding"
          element={
            <ProtectedRoute>
              <Layout>
                <MolecularBreeding />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Phenomic Selection */}
        <Route
          path="/phenomic-selection"
          element={
            <ProtectedRoute>
              <Layout>
                <PhenomicSelection />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Speed Breeding */}
        <Route
          path="/speed-breeding"
          element={
            <ProtectedRoute>
              <Layout>
                <SpeedBreeding />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Doubled Haploid */}
        <Route
          path="/doubled-haploid"
          element={
            <ProtectedRoute>
              <Layout>
                <DoubledHaploid />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Plant Vision AI */}
        <Route
          path="/plant-vision"
          element={
            <ProtectedRoute>
              <Layout>
                <PlantVision />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="/plant-vision/strategy" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><PlantVisionStrategy /></Suspense></Layout></ProtectedRoute>} />

        {/* AI Vision Training Ground */}
        <Route
          path="/ai-vision"
          element={
            <ProtectedRoute>
              <Layout>
                <VisionDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai-vision/datasets"
          element={
            <ProtectedRoute>
              <Layout>
                <VisionDatasets />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai-vision/training"
          element={
            <ProtectedRoute>
              <Layout>
                <VisionTraining />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai-vision/registry"
          element={
            <ProtectedRoute>
              <Layout>
                <VisionRegistry />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai-vision/annotate/:datasetId"
          element={
            <ProtectedRoute>
              <VisionAnnotate />
            </ProtectedRoute>
          }
        />

        {/* Disease Atlas */}
        <Route
          path="/disease-atlas"
          element={
            <ProtectedRoute>
              <Layout>
                <DiseaseAtlas />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Disease Resistance */}
        <Route
          path="/disease-resistance"
          element={
            <ProtectedRoute>
              <Layout>
                <DiseaseResistance />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Abiotic Stress */}
        <Route
          path="/abiotic-stress"
          element={
            <ProtectedRoute>
              <Layout>
                <AbioticStress />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Bioinformatics */}
        <Route
          path="/bioinformatics"
          element={
            <ProtectedRoute>
              <Layout>
                <Bioinformatics />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Crop Calendar */}
        <Route
          path="/crop-calendar"
          element={
            <ProtectedRoute>
              <Layout>
                <CropCalendar />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Spatial Analysis */}
        <Route
          path="/spatial-analysis"
          element={
            <ProtectedRoute>
              <Layout>
                <SpatialAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Pedigree Analysis */}
        <Route
          path="/pedigree-analysis"
          element={
            <ProtectedRoute>
              <Layout>
                <PedigreeAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Phenotype Analysis */}
        <Route
          path="/phenotype-analysis"
          element={
            <ProtectedRoute>
              <Layout>
                <PhenotypeAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Field Scanner */}
        <Route
          path="/field-scanner"
          element={
            <ProtectedRoute>
              <Layout>
                <FieldScanner />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Crop Health Dashboard */}
        <Route
          path="/crop-health"
          element={
            <ProtectedRoute>
              <Layout>
                <CropHealthDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Yield Predictor */}
        <Route
          path="/yield-predictor"
          element={
            <ProtectedRoute>
              <Layout>
                <YieldPredictor />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Collaboration Hub - TODO: Create page */}
        {/* <Route
          path="/collaboration"
          element={
            <ProtectedRoute>
              <Layout>
                <CollaborationHub />
              </Layout>
            </ProtectedRoute>
          }
        /> */}

        {/* Advanced Reports */}
        <Route
          path="/advanced-reports"
          element={
            <ProtectedRoute>
              <Layout>
                <AdvancedReports />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Data Sync */}
        <Route
          path="/data-sync"
          element={
            <ProtectedRoute>
              <Layout>
                <DataSync />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Team Management */}
        <Route
          path="/team-management"
          element={
            <ProtectedRoute>
              <Layout>
                <TeamManagement />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Protocol Library */}
        <Route
          path="/protocols"
          element={
            <ProtectedRoute>
              <Layout>
                <ProtocolLibrary />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Experiment Designer */}
        <Route
          path="/experiment-designer"
          element={
            <ProtectedRoute>
              <Layout>
                <ExperimentDesigner />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Resource Calendar */}
        <Route
          path="/resource-calendar"
          element={
            <ProtectedRoute>
              <Layout>
                <ResourceCalendar />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Environment Monitor */}
        <Route
          path="/environment-monitor"
          element={
            <ProtectedRoute>
              <Layout>
                <EnvironmentMonitor />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Cost Analysis */}
        <Route
          path="/cost-analysis"
          element={
            <ProtectedRoute>
              <Layout>
                <CostAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Publication Tracker */}
        <Route
          path="/publications"
          element={
            <ProtectedRoute>
              <Layout>
                <PublicationTracker />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Training Hub */}
        <Route
          path="/training"
          element={
            <ProtectedRoute>
              <Layout>
                <TrainingHub />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Variety Release */}
        <Route
          path="/variety-release"
          element={
            <ProtectedRoute>
              <Layout>
                <VarietyRelease />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Compliance Tracker */}
        <Route
          path="/compliance"
          element={
            <ProtectedRoute>
              <Layout>
                <ComplianceTracker />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Gene Bank */}
        <Route
          path="/genebank"
          element={
            <ProtectedRoute>
              <Layout>
                <GeneBank />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Breeding Goals */}
        <Route
          path="/breeding-goals"
          element={
            <ProtectedRoute>
              <Layout>
                <BreedingGoals />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Market Analysis */}
        <Route
          path="/market-analysis"
          element={
            <ProtectedRoute>
              <Layout>
                <MarketAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Stakeholder Portal */}
        <Route
          path="/stakeholders"
          element={
            <ProtectedRoute>
              <Layout>
                <StakeholderPortal />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Trial Comparison */}
        <Route
          path="/trial-comparison"
          element={
            <ProtectedRoute>
              <Layout>
                <TrialComparison />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Data Visualization */}
        <Route
          path="/visualization"
          element={
            <ProtectedRoute>
              <Layout>
                <DataVisualization />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* API Explorer */}
        <Route
          path="/api-explorer"
          element={
            <ProtectedRoute>
              <Layout>
                <APIExplorer />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Batch Operations */}
        <Route
          path="/batch-operations"
          element={
            <ProtectedRoute>
              <Layout>
                <BatchOperations />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Field Map */}
        <Route
          path="/field-map"
          element={
            <ProtectedRoute>
              <Layout>
                <FieldMap />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Plot History */}
        <Route
          path="/plot-history"
          element={
            <ProtectedRoute>
              <Layout>
                <PlotHistory />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Germplasm Passport */}
        <Route
          path="/germplasm-passport"
          element={
            <ProtectedRoute>
              <Layout>
                <GermplasmPassport />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Sample Tracking */}
        <Route
          path="/sample-tracking"
          element={
            <ProtectedRoute>
              <Layout>
                <SampleTracking />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Irrigation Planner */}
        <Route
          path="/irrigation"
          element={
            <ProtectedRoute>
              <Layout>
                <IrrigationPlanner />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Pest Monitor */}
        <Route
          path="/pest-monitor"
          element={
            <ProtectedRoute>
              <Layout>
                <PestMonitor />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Growth Tracker */}
        <Route
          path="/growth-tracker"
          element={
            <ProtectedRoute>
              <Layout>
                <GrowthTracker />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Harvest Log */}
        <Route
          path="/harvest-log"
          element={
            <ProtectedRoute>
              <Layout>
                <HarvestLog />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Drone Integration */}
        <Route
          path="/drones"
          element={
            <ProtectedRoute>
              <Layout>
                <DroneIntegration />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* IoT Sensors */}
        <Route
          path="/iot-sensors"
          element={
            <ProtectedRoute>
              <Layout>
                <IoTSensors />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Blockchain Traceability */}
        <Route
          path="/blockchain"
          element={
            <ProtectedRoute>
              <Layout>
                <BlockchainTraceability />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Analytics Dashboard */}
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Layout>
                <AnalyticsDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Weather Forecast */}
        <Route
          path="/weather-forecast"
          element={
            <ProtectedRoute>
              <Layout>
                <WeatherForecast />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Workflow Automation */}
        <Route
          path="/workflows"
          element={
            <ProtectedRoute>
              <Layout>
                <WorkflowAutomation />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Data Export Templates */}
        <Route
          path="/export-templates"
          element={
            <ProtectedRoute>
              <Layout>
                <DataExportTemplates />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Notification Center */}
        <Route
          path="/notification-center"
          element={
            <ProtectedRoute>
              <Layout>
                <NotificationCenter />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Language Settings */}
        <Route
          path="/languages"
          element={
            <ProtectedRoute>
              <Layout>
                <LanguageSettings />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Genetic Gain Calculator */}
        <Route
          path="/genetic-gain-calculator"
          element={
            <ProtectedRoute>
              <Layout>
                <GeneticGainCalculator />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Trial Network */}
        <Route
          path="/trial-network"
          element={
            <ProtectedRoute>
              <Layout>
                <TrialNetwork />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Parent Selection */}
        <Route
          path="/parent-selection"
          element={
            <ProtectedRoute>
              <Layout>
                <ParentSelection />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Offline Mode */}
        <Route
          path="/offline"
          element={
            <ProtectedRoute>
              <Layout>
                <OfflineMode />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Mobile App Settings */}
        <Route
          path="/mobile-app"
          element={
            <ProtectedRoute>
              <Layout>
                <MobileApp />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Breeding Simulator */}
        <Route
          path="/breeding-simulator"
          element={
            <ProtectedRoute>
              <Layout>
                <BreedingSimulator />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Data Dictionary */}
        <Route
          path="/data-dictionary"
          element={
            <ProtectedRoute>
              <Layout>
                <DataDictionary />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Activity Timeline */}
        <Route
          path="/activity"
          element={
            <ProtectedRoute>
              <Layout>
                <ActivityTimeline />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Germplasm Search */}
        <Route
          path="/germplasm-search"
          element={
            <ProtectedRoute>
              <Layout>
                <GermplasmSearch />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Field Planning */}
        <Route
          path="/field-planning"
          element={
            <ProtectedRoute>
              <Layout>
                <FieldPlanning />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Quick Entry */}
        <Route
          path="/quick-entry"
          element={
            <ProtectedRoute>
              <Layout>
                <QuickEntry />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* System Health */}
        <Route
          path="/system-health"
          element={
            <ProtectedRoute>
              <Layout>
                <SystemHealth />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Cross Prediction */}
        <Route
          path="/cross-prediction"
          element={
            <ProtectedRoute>
              <Layout>
                <CrossPrediction />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Trial Summary */}
        <Route
          path="/trial-summary"
          element={
            <ProtectedRoute>
              <Layout>
                <TrialSummary />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Selection Decision */}
        <Route
          path="/selection-decision"
          element={
            <ProtectedRoute>
              <Layout>
                <SelectionDecision />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Season Planning */}
        <Route
          path="/season-planning"
          element={
            <ProtectedRoute>
              <Layout>
                <SeasonPlanning />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Data Validation */}
        <Route
          path="/data-validation"
          element={
            <ProtectedRoute>
              <Layout>
                <DataValidation />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Breeding History */}
        <Route
          path="/breeding-history"
          element={
            <ProtectedRoute>
              <Layout>
                <BreedingHistory />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Resource Allocation */}
        <Route
          path="/resource-allocation"
          element={
            <ProtectedRoute>
              <Layout>
                <ResourceAllocation />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Genetic Map */}
        <Route
          path="/genetic-map"
          element={
            <ProtectedRoute>
              <Layout>
                <GeneticMap />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Performance Ranking */}
        <Route
          path="/performance-ranking"
          element={
            <ProtectedRoute>
              <Layout>
                <PerformanceRanking />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* WASM Genomics Engine */}
        <Route
          path="/wasm-genomics"
          element={
            <ProtectedRoute>
              <Layout>
                <WasmGenomics />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* WASM GBLUP Calculator */}
        <Route
          path="/wasm-gblup"
          element={
            <ProtectedRoute>
              <Layout>
                <WasmGBLUP />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* WASM Population Genetics */}
        <Route
          path="/wasm-popgen"
          element={
            <ProtectedRoute>
              <Layout>
                <WasmPopGen />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* WASM LD Analysis */}
        <Route
          path="/wasm-ld"
          element={
            <ProtectedRoute>
              <Layout>
                <WasmLDAnalysis />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* WASM Selection Index */}
        <Route
          path="/wasm-selection"
          element={
            <ProtectedRoute>
              <Layout>
                <WasmSelectionIndex />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* APEX FEATURES */}
        {/* AI Insights Dashboard */}
        <Route
          path="/insights"
          element={
            <ProtectedRoute>
              <Layout>
                <InsightsDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Apex Analytics */}
        <Route
          path="/apex-analytics"
          element={
            <ProtectedRoute>
              <Layout>
                <ApexAnalytics />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Selection Index Calculator */}
        <Route
          path="/selection-index-calculator"
          element={
            <ProtectedRoute>
              <Layout>
                <SelectionIndexCalculator />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Genetic Gain Tracker */}
        <Route
          path="/genetic-gain-tracker"
          element={
            <ProtectedRoute>
              <Layout>
                <GeneticGainTracker />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Harvest Management */}
        <Route
          path="/harvest-management"
          element={
            <ProtectedRoute>
              <Layout>
                <HarvestManagement />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Breeding Value Calculator */}
        <Route
          path="/breeding-value-calculator"
          element={
            <ProtectedRoute>
              <Layout>
                <BreedingValueCalculator />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* ============================================================ */}
        {/* FUTURE DIVISIONS - Roadmap Placeholders                      */}
        {/* These routes show "Coming Soon" pages for planned modules    */}
        {/* @see docs/gupt/1-future.md for full roadmap          */}
        {/* ============================================================ */}
        
        {/* Tier 1: Crop Intelligence */}
        <Route path="/crop-intelligence/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 1: Soil & Nutrients */}
        <Route path="/soil-nutrients/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 1: Crop Protection */}
        <Route path="/crop-protection/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 1: Water & Irrigation */}
        <Route path="/water-irrigation/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 1: Market & Economics */}
        <Route path="/market-economics/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 2: Sustainability */}
        <Route path="/sustainability/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 2: Farm Operations */}
        <Route path="/farm-operations/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 2: Robotics & Automation */}
        <Route path="/robotics/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 2: Post-Harvest & Supply Chain */}
        <Route path="/post-harvest/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 2: Livestock & Animal Husbandry */}
        <Route path="/livestock/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Tier 3: Aquaculture & Fisheries */}
        <Route path="/aquaculture/*" element={<ProtectedRoute><Layout><Suspense fallback={<div className="p-8 text-center">Loading...</div>}><FuturePlaceholder /></Suspense></Layout></ProtectedRoute>} />
        
        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* 404 Not Found */}
        <Route path="*" element={<NotFound />} />
      </Routes>
  )
}

function App() {
  return (
    <Router>
      <AppRoutes />
    </Router>
  )
}

export default App
