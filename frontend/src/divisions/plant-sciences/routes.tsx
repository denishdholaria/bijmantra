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

// Lazy load pages for code splitting
// Breeding Operations
const Programs = lazy(() => import('@/pages/Programs'));
const ProgramDetail = lazy(() => import('@/pages/ProgramDetail'));
const ProgramForm = lazy(() => import('@/pages/ProgramForm'));
const Trials = lazy(() => import('@/pages/Trials'));
const TrialDetail = lazy(() => import('@/pages/TrialDetail'));
const TrialForm = lazy(() => import('@/pages/TrialForm'));
const Studies = lazy(() => import('@/pages/Studies'));
const StudyDetail = lazy(() => import('@/pages/StudyDetail'));
const StudyForm = lazy(() => import('@/pages/StudyForm'));
const Locations = lazy(() => import('@/pages/Locations'));
const LocationDetail = lazy(() => import('@/pages/LocationDetail'));
const LocationForm = lazy(() => import('@/pages/LocationForm'));
const Seasons = lazy(() => import('@/pages/Seasons'));
const BreedingPipeline = lazy(() => import('@/pages/BreedingPipeline'));
const BreedingGoals = lazy(() => import('@/pages/BreedingGoals'));
const BreedingHistory = lazy(() => import('@/pages/BreedingHistory'));

// Germplasm & Crosses
const Germplasm = lazy(() => import('@/pages/Germplasm'));
const GermplasmDetail = lazy(() => import('@/pages/GermplasmDetail'));
const GermplasmForm = lazy(() => import('@/pages/GermplasmForm'));
const GermplasmSearch = lazy(() => import('@/pages/GermplasmSearch'));
const SeedLots = lazy(() => import('@/pages/SeedLots'));
const SeedLotDetail = lazy(() => import('@/pages/SeedLotDetail'));
const Crosses = lazy(() => import('@/pages/Crosses'));
const CrossDetail = lazy(() => import('@/pages/CrossDetail'));
const CrossingPlanner = lazy(() => import('@/pages/CrossingPlanner'));
const PlannedCrosses = lazy(() => import('@/pages/PlannedCrosses'));
const Progeny = lazy(() => import('@/pages/Progeny'));
const PedigreeViewer = lazy(() => import('@/pages/PedigreeViewer'));

// Selection & Prediction
const SelectionIndex = lazy(() => import('@/pages/SelectionIndex'));
const SelectionDecision = lazy(() => import('@/pages/SelectionDecision'));
const ParentSelection = lazy(() => import('@/pages/ParentSelection'));
const CrossPrediction = lazy(() => import('@/pages/CrossPrediction'));
const PerformanceRanking = lazy(() => import('@/pages/PerformanceRanking'));
const GeneticGain = lazy(() => import('@/pages/GeneticGain'));
const GeneticGainCalculator = lazy(() => import('@/pages/GeneticGainCalculator'));

// Genetics & Genomics
const GeneticDiversity = lazy(() => import('@/pages/GeneticDiversity'));
const PopulationGenetics = lazy(() => import('@/pages/PopulationGenetics'));
const LinkageDisequilibrium = lazy(() => import('@/pages/LinkageDisequilibrium'));
const HaplotypeAnalysis = lazy(() => import('@/pages/HaplotypeAnalysis'));
const BreedingValues = lazy(() => import('@/pages/BreedingValues'));
const GenomicSelection = lazy(() => import('@/pages/GenomicSelection'));
const GeneticCorrelation = lazy(() => import('@/pages/GeneticCorrelation'));
const QTLMapping = lazy(() => import('@/pages/QTLMapping'));
const MarkerAssistedSelection = lazy(() => import('@/pages/MarkerAssistedSelection'));
const ParentageAnalysis = lazy(() => import('@/pages/ParentageAnalysis'));
const GxEInteraction = lazy(() => import('@/pages/GxEInteraction'));
const StabilityAnalysis = lazy(() => import('@/pages/StabilityAnalysis'));
const GeneticMap = lazy(() => import('@/pages/GeneticMap'));

// Molecular Biology
const MolecularBreeding = lazy(() => import('@/pages/MolecularBreeding'));
const DoubledHaploid = lazy(() => import('@/pages/DoubledHaploid'));
const SpeedBreeding = lazy(() => import('@/pages/SpeedBreeding'));

// Phenotyping
const Traits = lazy(() => import('@/pages/Traits'));
const TraitDetail = lazy(() => import('@/pages/TraitDetail'));
const Observations = lazy(() => import('@/pages/Observations'));
const ObservationUnits = lazy(() => import('@/pages/ObservationUnits'));
const DataCollect = lazy(() => import('@/pages/DataCollect'));
const Images = lazy(() => import('@/pages/Images'));
const Events = lazy(() => import('@/pages/Events'));

// Genotyping
const Samples = lazy(() => import('@/pages/Samples'));
const SampleDetail = lazy(() => import('@/pages/SampleDetail'));
const Variants = lazy(() => import('@/pages/Variants'));
const VariantSets = lazy(() => import('@/pages/VariantSets'));
const AlleleMatrix = lazy(() => import('@/pages/AlleleMatrix'));
const Plates = lazy(() => import('@/pages/Plates'));
const GenomeMaps = lazy(() => import('@/pages/GenomeMaps'));

// Field Operations
const FieldLayout = lazy(() => import('@/pages/FieldLayout'));
const FieldBook = lazy(() => import('@/pages/FieldBook'));
const FieldMap = lazy(() => import('@/pages/FieldMap'));
const FieldPlanning = lazy(() => import('@/pages/FieldPlanning'));
const TrialDesign = lazy(() => import('@/pages/TrialDesign'));
const SeasonPlanning = lazy(() => import('@/pages/SeasonPlanning'));
const NurseryManagement = lazy(() => import('@/pages/NurseryManagement'));
const HarvestPlanner = lazy(() => import('@/pages/HarvestPlanner'));
const HarvestLog = lazy(() => import('@/pages/HarvestLog'));
const SeedInventory = lazy(() => import('@/pages/SeedInventory'));

// Analysis & Simulation
const BreedingSimulator = lazy(() => import('@/pages/BreedingSimulator'));
const TrialComparison = lazy(() => import('@/pages/TrialComparison'));
const TrialNetwork = lazy(() => import('@/pages/TrialNetwork'));
const Statistics = lazy(() => import('@/pages/Statistics'));
const DataVisualization = lazy(() => import('@/pages/DataVisualization'));

// WASM Tools
const WasmGenomics = lazy(() => import('@/pages/WasmGenomics'));
const WasmGBLUP = lazy(() => import('@/pages/WasmGBLUP'));
const WasmPopGen = lazy(() => import('@/pages/WasmPopGen'));
const WasmLDAnalysis = lazy(() => import('@/pages/WasmLDAnalysis'));
const WasmSelectionIndex = lazy(() => import('@/pages/WasmSelectionIndex'));

/**
 * Plant Sciences Division Routes
 */
export const plantSciencesRoutes: RouteObject[] = [
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
