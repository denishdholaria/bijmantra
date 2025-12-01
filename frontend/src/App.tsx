import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Login } from '@/pages/Login'
import { Dashboard } from '@/pages/Dashboard'
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
import { BackupRestore } from '@/pages/BackupRestore'
import { DataQuality } from '@/pages/DataQuality'
import { ServerInfo } from '@/pages/ServerInfo'
import { GermplasmAttributes } from '@/pages/GermplasmAttributes'
import { GermplasmAttributeValues } from '@/pages/GermplasmAttributeValues'
import { Progeny } from '@/pages/Progeny'
import { TrialDesign } from '@/pages/TrialDesign'
import { SelectionIndex } from '@/pages/SelectionIndex'
import { GeneticGain } from '@/pages/GeneticGain'
import { PedigreeViewer } from '@/pages/PedigreeViewer'
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
import { DiseaseAtlas } from '@/pages/DiseaseAtlas'
import { FieldScanner } from '@/pages/FieldScanner'
import { CropHealthDashboard } from '@/pages/CropHealthDashboard'
import { YieldPredictor } from '@/pages/YieldPredictor'

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        
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
        
        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* 404 Not Found */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  )
}

export default App
