/**
 * Plant Sciences Division - Routes
 * 
 * Organizes all plant sciences related pages into subsections:
 * - Breeding Operations
 * - Genetics & Genomics
 * - Molecular Biology
 * - Crop Sciences
 * - Soil & Environment
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages for code splitting - using named exports
const PlantSciencesHub = lazy(() => import('./pages/PlantSciencesHub').then(m => ({ default: m.PlantSciencesHub })));

// Breeding Operations
const Programs = lazy(() => import('@/pages/Programs').then(m => ({ default: m.Programs })));
const ProgramDetail = lazy(() => import('@/pages/ProgramDetail').then(m => ({ default: m.ProgramDetail })));
const ProgramForm = lazy(() => import('@/pages/ProgramForm').then(m => ({ default: m.ProgramForm })));
const Trials = lazy(() => import('@/pages/Trials').then(m => ({ default: m.Trials })));
const TrialDetail = lazy(() => import('@/pages/TrialDetail').then(m => ({ default: m.TrialDetail })));
const TrialForm = lazy(() => import('@/pages/TrialForm').then(m => ({ default: m.TrialForm })));
const Studies = lazy(() => import('@/pages/Studies').then(m => ({ default: m.Studies })));
const StudyDetail = lazy(() => import('@/pages/StudyDetail').then(m => ({ default: m.StudyDetail })));
const StudyForm = lazy(() => import('@/pages/StudyForm').then(m => ({ default: m.StudyForm })));
const Locations = lazy(() => import('@/pages/Locations').then(m => ({ default: m.Locations })));
const LocationDetail = lazy(() => import('@/pages/LocationDetail').then(m => ({ default: m.LocationDetail })));
const LocationForm = lazy(() => import('@/pages/LocationForm').then(m => ({ default: m.LocationForm })));
const Seasons = lazy(() => import('@/pages/Seasons').then(m => ({ default: m.Seasons })));
const BreedingPipeline = lazy(() => import('@/pages/BreedingPipeline').then(m => ({ default: m.BreedingPipeline })));
const BreedingGoals = lazy(() => import('@/pages/BreedingGoals').then(m => ({ default: m.BreedingGoals })));
const BreedingHistory = lazy(() => import('@/pages/BreedingHistory').then(m => ({ default: m.BreedingHistory })));

// Germplasm & Crosses
const Germplasm = lazy(() => import('@/pages/Germplasm').then(m => ({ default: m.Germplasm })));
const GermplasmDetail = lazy(() => import('@/pages/GermplasmDetail').then(m => ({ default: m.GermplasmDetail })));
const GermplasmForm = lazy(() => import('@/pages/GermplasmForm').then(m => ({ default: m.GermplasmForm })));
const GermplasmSearch = lazy(() => import('@/pages/GermplasmSearch').then(m => ({ default: m.GermplasmSearch })));
const SeedLots = lazy(() => import('@/pages/SeedLots').then(m => ({ default: m.SeedLots })));
const SeedLotDetail = lazy(() => import('@/pages/SeedLotDetail').then(m => ({ default: m.SeedLotDetail })));
const Crosses = lazy(() => import('@/pages/Crosses').then(m => ({ default: m.Crosses })));
const CrossDetail = lazy(() => import('@/pages/CrossDetail').then(m => ({ default: m.CrossDetail })));
const CrossingPlanner = lazy(() => import('@/pages/CrossingPlanner').then(m => ({ default: m.CrossingPlanner })));
const PlannedCrosses = lazy(() => import('@/pages/PlannedCrosses').then(m => ({ default: m.PlannedCrosses })));
const Progeny = lazy(() => import('@/pages/Progeny').then(m => ({ default: m.Progeny })));
const PedigreeViewer = lazy(() => import('@/pages/PedigreeViewer').then(m => ({ default: m.PedigreeViewer })));

// Selection & Prediction
const SelectionIndex = lazy(() => import('@/pages/SelectionIndex').then(m => ({ default: m.SelectionIndex })));
const SelectionDecision = lazy(() => import('@/pages/SelectionDecision').then(m => ({ default: m.SelectionDecision })));
const ParentSelection = lazy(() => import('@/pages/ParentSelection').then(m => ({ default: m.ParentSelection })));
const CrossPrediction = lazy(() => import('@/pages/CrossPrediction').then(m => ({ default: m.CrossPrediction })));
const PerformanceRanking = lazy(() => import('@/pages/PerformanceRanking').then(m => ({ default: m.PerformanceRanking })));
const GeneticGain = lazy(() => import('@/pages/GeneticGain').then(m => ({ default: m.GeneticGain })));
const GeneticGainCalculator = lazy(() => import('@/pages/GeneticGainCalculator').then(m => ({ default: m.GeneticGainCalculator })));

// Genetics & Genomics
const GeneticDiversity = lazy(() => import('@/pages/GeneticDiversity').then(m => ({ default: m.GeneticDiversity })));
const PopulationGenetics = lazy(() => import('@/pages/PopulationGenetics').then(m => ({ default: m.PopulationGenetics })));
const LinkageDisequilibrium = lazy(() => import('@/pages/LinkageDisequilibrium').then(m => ({ default: m.LinkageDisequilibrium })));
const HaplotypeAnalysis = lazy(() => import('@/pages/HaplotypeAnalysis').then(m => ({ default: m.HaplotypeAnalysis })));
const BreedingValues = lazy(() => import('@/pages/BreedingValues').then(m => ({ default: m.BreedingValues })));
const GenomicSelection = lazy(() => import('@/pages/GenomicSelection').then(m => ({ default: m.GenomicSelection })));
const GeneticCorrelation = lazy(() => import('@/pages/GeneticCorrelation').then(m => ({ default: m.GeneticCorrelation })));
const QTLMapping = lazy(() => import('@/pages/QTLMapping').then(m => ({ default: m.QTLMapping })));
const MarkerAssistedSelection = lazy(() => import('@/pages/MarkerAssistedSelection').then(m => ({ default: m.MarkerAssistedSelection })));
const ParentageAnalysis = lazy(() => import('@/pages/ParentageAnalysis').then(m => ({ default: m.ParentageAnalysis })));
const GxEInteraction = lazy(() => import('@/pages/GxEInteraction').then(m => ({ default: m.GxEInteraction })));
const StabilityAnalysis = lazy(() => import('@/pages/StabilityAnalysis').then(m => ({ default: m.StabilityAnalysis })));
const GeneticMap = lazy(() => import('@/pages/GeneticMap').then(m => ({ default: m.GeneticMap })));

// Molecular Biology
const MolecularBreeding = lazy(() => import('@/pages/MolecularBreeding').then(m => ({ default: m.MolecularBreeding })));
const DoubledHaploid = lazy(() => import('@/pages/DoubledHaploid').then(m => ({ default: m.DoubledHaploid })));
const SpeedBreeding = lazy(() => import('@/pages/SpeedBreeding').then(m => ({ default: m.SpeedBreeding })));

// Phenotyping
const Traits = lazy(() => import('@/pages/Traits').then(m => ({ default: m.Traits })));
const TraitDetail = lazy(() => import('@/pages/TraitDetail').then(m => ({ default: m.TraitDetail })));
const Observations = lazy(() => import('@/pages/Observations').then(m => ({ default: m.Observations })));
const ObservationUnits = lazy(() => import('@/pages/ObservationUnits').then(m => ({ default: m.ObservationUnits })));
const DataCollect = lazy(() => import('@/pages/DataCollect').then(m => ({ default: m.DataCollect })));
const Images = lazy(() => import('@/pages/Images').then(m => ({ default: m.Images })));
const Events = lazy(() => import('@/pages/Events').then(m => ({ default: m.Events })));

// Genotyping
const Samples = lazy(() => import('@/pages/Samples').then(m => ({ default: m.Samples })));
const SampleDetail = lazy(() => import('@/pages/SampleDetail').then(m => ({ default: m.SampleDetail })));
const Variants = lazy(() => import('@/pages/Variants').then(m => ({ default: m.Variants })));
const VariantSets = lazy(() => import('@/pages/VariantSets').then(m => ({ default: m.VariantSets })));
const AlleleMatrix = lazy(() => import('@/pages/AlleleMatrix').then(m => ({ default: m.AlleleMatrix })));
const Plates = lazy(() => import('@/pages/Plates').then(m => ({ default: m.Plates })));
const GenomeMaps = lazy(() => import('@/pages/GenomeMaps').then(m => ({ default: m.GenomeMaps })));

// Field Operations
const FieldLayout = lazy(() => import('@/pages/FieldLayout').then(m => ({ default: m.FieldLayout })));
const FieldBook = lazy(() => import('@/pages/FieldBook').then(m => ({ default: m.FieldBook })));
const FieldMap = lazy(() => import('@/pages/FieldMap').then(m => ({ default: m.FieldMap })));
const FieldPlanning = lazy(() => import('@/pages/FieldPlanning').then(m => ({ default: m.FieldPlanning })));
const TrialDesign = lazy(() => import('@/pages/TrialDesign').then(m => ({ default: m.TrialDesign })));
const SeasonPlanning = lazy(() => import('@/pages/SeasonPlanning').then(m => ({ default: m.SeasonPlanning })));
const NurseryManagement = lazy(() => import('@/pages/NurseryManagement').then(m => ({ default: m.NurseryManagement })));
const HarvestPlanner = lazy(() => import('@/pages/HarvestPlanner').then(m => ({ default: m.HarvestPlanner })));
const HarvestLog = lazy(() => import('@/pages/HarvestLog').then(m => ({ default: m.HarvestLog })));
const SeedInventory = lazy(() => import('@/pages/SeedInventory').then(m => ({ default: m.SeedInventory })));

// Analysis & Simulation
const BreedingSimulator = lazy(() => import('@/pages/BreedingSimulator').then(m => ({ default: m.BreedingSimulator })));
const TrialComparison = lazy(() => import('@/pages/TrialComparison').then(m => ({ default: m.TrialComparison })));
const TrialNetwork = lazy(() => import('@/pages/TrialNetwork').then(m => ({ default: m.TrialNetwork })));
const Statistics = lazy(() => import('@/pages/Statistics').then(m => ({ default: m.Statistics })));
const DataVisualization = lazy(() => import('@/pages/DataVisualization').then(m => ({ default: m.DataVisualization })));

// WASM Tools
const WasmGenomics = lazy(() => import('@/pages/WasmGenomics').then(m => ({ default: m.WasmGenomics })));
const WasmGBLUP = lazy(() => import('@/pages/WasmGBLUP').then(m => ({ default: m.WasmGBLUP })));
const WasmPopGen = lazy(() => import('@/pages/WasmPopGen').then(m => ({ default: m.WasmPopGen })));
const WasmLDAnalysis = lazy(() => import('@/pages/WasmLDAnalysis').then(m => ({ default: m.WasmLDAnalysis })));
const WasmSelectionIndex = lazy(() => import('@/pages/WasmSelectionIndex').then(m => ({ default: m.WasmSelectionIndex })));

/**
 * Plant Sciences Division Routes
 */
export const plantSciencesRoutes: RouteObject[] = [
  // Hub (Mini-Gateway)
  { path: '', element: <PlantSciencesHub /> },

  // Breeding Operations
  { path: 'programs', element: <Programs /> },
  { path: 'programs/new', element: <ProgramForm /> },
  { path: 'programs/:id', element: <ProgramDetail /> },
  { path: 'programs/:id/edit', element: <ProgramForm /> },
  { path: 'trials', element: <Trials /> },
  { path: 'trials/new', element: <TrialForm /> },
  { path: 'trials/:id', element: <TrialDetail /> },
  { path: 'trials/:id/edit', element: <TrialForm /> },
  { path: 'studies', element: <Studies /> },
  { path: 'studies/new', element: <StudyForm /> },
  { path: 'studies/:id', element: <StudyDetail /> },
  { path: 'studies/:id/edit', element: <StudyForm /> },
  { path: 'locations', element: <Locations /> },
  { path: 'locations/new', element: <LocationForm /> },
  { path: 'locations/:id', element: <LocationDetail /> },
  { path: 'locations/:id/edit', element: <LocationForm /> },
  { path: 'seasons', element: <Seasons /> },
  { path: 'pipeline', element: <BreedingPipeline /> },
  { path: 'goals', element: <BreedingGoals /> },
  { path: 'history', element: <BreedingHistory /> },
  
  // Germplasm
  { path: 'germplasm', element: <Germplasm /> },
  { path: 'germplasm/new', element: <GermplasmForm /> },
  { path: 'germplasm/search', element: <GermplasmSearch /> },
  { path: 'germplasm/:id', element: <GermplasmDetail /> },
  { path: 'germplasm/:id/edit', element: <GermplasmForm /> },
  { path: 'seedlots', element: <SeedLots /> },
  { path: 'seedlots/:id', element: <SeedLotDetail /> },
  { path: 'crosses', element: <Crosses /> },
  { path: 'crosses/:id', element: <CrossDetail /> },
  { path: 'crossing-planner', element: <CrossingPlanner /> },
  { path: 'planned-crosses', element: <PlannedCrosses /> },
  { path: 'progeny', element: <Progeny /> },
  { path: 'pedigree', element: <PedigreeViewer /> },
  
  // Selection
  { path: 'selection-index', element: <SelectionIndex /> },
  { path: 'selection-decision', element: <SelectionDecision /> },
  { path: 'parent-selection', element: <ParentSelection /> },
  { path: 'cross-prediction', element: <CrossPrediction /> },
  { path: 'performance-ranking', element: <PerformanceRanking /> },
  { path: 'genetic-gain', element: <GeneticGain /> },
  { path: 'genetic-gain-calculator', element: <GeneticGainCalculator /> },
  
  // Genomics
  { path: 'genetic-diversity', element: <GeneticDiversity /> },
  { path: 'population-genetics', element: <PopulationGenetics /> },
  { path: 'linkage-disequilibrium', element: <LinkageDisequilibrium /> },
  { path: 'haplotype-analysis', element: <HaplotypeAnalysis /> },
  { path: 'breeding-values', element: <BreedingValues /> },
  { path: 'genomic-selection', element: <GenomicSelection /> },
  { path: 'genetic-correlation', element: <GeneticCorrelation /> },
  { path: 'qtl-mapping', element: <QTLMapping /> },
  { path: 'marker-assisted-selection', element: <MarkerAssistedSelection /> },
  { path: 'parentage-analysis', element: <ParentageAnalysis /> },
  { path: 'gxe-interaction', element: <GxEInteraction /> },
  { path: 'stability-analysis', element: <StabilityAnalysis /> },
  { path: 'genetic-map', element: <GeneticMap /> },
  
  // Molecular
  { path: 'molecular-breeding', element: <MolecularBreeding /> },
  { path: 'doubled-haploid', element: <DoubledHaploid /> },
  { path: 'speed-breeding', element: <SpeedBreeding /> },
  
  // Phenotyping
  { path: 'traits', element: <Traits /> },
  { path: 'traits/:id', element: <TraitDetail /> },
  { path: 'observations', element: <Observations /> },
  { path: 'observations/collect', element: <DataCollect /> },
  { path: 'observation-units', element: <ObservationUnits /> },
  { path: 'images', element: <Images /> },
  { path: 'events', element: <Events /> },
  
  // Genotyping
  { path: 'samples', element: <Samples /> },
  { path: 'samples/:id', element: <SampleDetail /> },
  { path: 'variants', element: <Variants /> },
  { path: 'variant-sets', element: <VariantSets /> },
  { path: 'allele-matrix', element: <AlleleMatrix /> },
  { path: 'plates', element: <Plates /> },
  { path: 'genome-maps', element: <GenomeMaps /> },
  
  // Field Operations
  { path: 'field-layout', element: <FieldLayout /> },
  { path: 'field-book', element: <FieldBook /> },
  { path: 'field-map', element: <FieldMap /> },
  { path: 'field-planning', element: <FieldPlanning /> },
  { path: 'trial-design', element: <TrialDesign /> },
  { path: 'season-planning', element: <SeasonPlanning /> },
  { path: 'nursery', element: <NurseryManagement /> },
  { path: 'harvest-planner', element: <HarvestPlanner /> },
  { path: 'harvest-log', element: <HarvestLog /> },
  { path: 'inventory', element: <SeedInventory /> },
  
  // Analysis
  { path: 'simulator', element: <BreedingSimulator /> },
  { path: 'trial-comparison', element: <TrialComparison /> },
  { path: 'trial-network', element: <TrialNetwork /> },
  { path: 'statistics', element: <Statistics /> },
  { path: 'visualization', element: <DataVisualization /> },
  
  // WASM Tools
  { path: 'wasm-genomics', element: <WasmGenomics /> },
  { path: 'wasm-gblup', element: <WasmGBLUP /> },
  { path: 'wasm-popgen', element: <WasmPopGen /> },
  { path: 'wasm-ld', element: <WasmLDAnalysis /> },
  { path: 'wasm-selection-index', element: <WasmSelectionIndex /> },
];

export default plantSciencesRoutes;
