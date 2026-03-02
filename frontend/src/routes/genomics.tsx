import { lazy, Suspense } from 'react';
import { RouteObject } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
// Lazy Layout import to prevent circular dependency
const Layout = lazy(() => import('@/components/Layout').then(m => ({ default: m.Layout })));

// Samples & Genotyping
const Samples = lazy(() => import('@/pages/Samples').then(m => ({ default: m.Samples })));
const SampleForm = lazy(() => import('@/pages/SampleForm').then(m => ({ default: m.SampleForm })));
const SampleDetail = lazy(() => import('@/pages/SampleDetail').then(m => ({ default: m.SampleDetail })));
const SampleTracking = lazy(() => import('@/pages/SampleTracking').then(m => ({ default: m.SampleTracking })));

const Variants = lazy(() => import('@/pages/Variants').then(m => ({ default: m.Variants })));
const VariantDetail = lazy(() => import('@/pages/VariantDetail').then(m => ({ default: m.VariantDetail })));
const VariantSets = lazy(() => import('@/pages/VariantSets').then(m => ({ default: m.VariantSets })));

const Calls = lazy(() => import('@/pages/Calls').then(m => ({ default: m.Calls })));
const CallSets = lazy(() => import('@/pages/CallSets').then(m => ({ default: m.CallSets })));
const AlleleMatrix = lazy(() => import('@/pages/AlleleMatrix').then(m => ({ default: m.AlleleMatrix })));

const Plates = lazy(() => import('@/pages/Plates').then(m => ({ default: m.Plates })));
const References = lazy(() => import('@/pages/References').then(m => ({ default: m.References })));
const GenomeMaps = lazy(() => import('@/pages/GenomeMaps').then(m => ({ default: m.GenomeMaps })));
const GeneticMap = lazy(() => import('@/pages/GeneticMap').then(m => ({ default: m.GeneticMap })));
const MarkerPositions = lazy(() => import('@/pages/MarkerPositions').then(m => ({ default: m.MarkerPositions })));
const VendorOrders = lazy(() => import('@/pages/VendorOrders').then(m => ({ default: m.VendorOrders })));

// Molecular Breeding & Analysis
const MolecularBreeding = lazy(() => import('@/pages/MolecularBreeding').then(m => ({ default: m.MolecularBreeding })));
const GeneticDiversity = lazy(() => import('@/pages/GeneticDiversity').then(m => ({ default: m.GeneticDiversity })));
const QTLMapping = lazy(() => import('@/pages/QTLMapping').then(m => ({ default: m.QTLMapping })));
const GenomicSelection = lazy(() => import('@/pages/GenomicSelection').then(m => ({ default: m.GenomicSelection })));
const MarkerAssistedSelection = lazy(() => import('@/pages/MarkerAssistedSelection').then(m => ({ default: m.MarkerAssistedSelection })));
const HaplotypeAnalysis = lazy(() => import('@/pages/HaplotypeAnalysis').then(m => ({ default: m.HaplotypeAnalysis })));
const LinkageDisequilibrium = lazy(() => import('@/pages/LinkageDisequilibrium').then(m => ({ default: m.LinkageDisequilibrium })));
const PopulationGenetics = lazy(() => import('@/pages/PopulationGenetics').then(m => ({ default: m.PopulationGenetics })));
const ParentageAnalysis = lazy(() => import('@/pages/ParentageAnalysis').then(m => ({ default: m.ParentageAnalysis })));
const GeneticCorrelation = lazy(() => import('@/pages/GeneticCorrelation').then(m => ({ default: m.GeneticCorrelation })));
const GxEInteraction = lazy(() => import('@/pages/GxEInteraction').then(m => ({ default: m.GxEInteraction })));
const StabilityAnalysis = lazy(() => import('@/pages/StabilityAnalysis').then(m => ({ default: m.StabilityAnalysis })));
const PhenomicSelection = lazy(() => import('@/pages/PhenomicSelection').then(m => ({ default: m.PhenomicSelection })));
const SpeedBreeding = lazy(() => import('@/pages/SpeedBreeding').then(m => ({ default: m.SpeedBreeding })));
const DoubledHaploid = lazy(() => import('@/pages/DoubledHaploid').then(m => ({ default: m.DoubledHaploid })));

const WasmGenomics = lazy(() => import('@/pages/WasmGenomics').then(m => ({ default: m.WasmGenomics })));
const WasmGBLUP = lazy(() => import('@/pages/WasmGBLUP').then(m => ({ default: m.WasmGBLUP })));
const WasmPopGen = lazy(() => import('@/pages/WasmPopGen').then(m => ({ default: m.WasmPopGen })));
const WasmLDAnalysis = lazy(() => import('@/pages/WasmLDAnalysis').then(m => ({ default: m.WasmLDAnalysis })));
const WasmSelectionIndex = lazy(() => import('@/pages/WasmSelectionIndex').then(m => ({ default: m.WasmSelectionIndex })));

const BreedingValues = lazy(() => import('@/pages/BreedingValues').then(m => ({ default: m.BreedingValues })));
const GeneticGain = lazy(() => import('@/pages/GeneticGain').then(m => ({ default: m.GeneticGain })));
const SelectionIndex = lazy(() => import('@/pages/SelectionIndex').then(m => ({ default: m.SelectionIndex })));
const SelectionIndexCalculator = lazy(() => import('@/pages/SelectionIndexCalculator').then(m => ({ default: m.SelectionIndexCalculator })));
const GeneticGainTracker = lazy(() => import('@/pages/GeneticGainTracker').then(m => ({ default: m.GeneticGainTracker })));
const BreedingValueCalculator = lazy(() => import('@/pages/BreedingValueCalculator').then(m => ({ default: m.BreedingValueCalculator })));
const GeneticGainCalculator = lazy(() => import('@/pages/GeneticGainCalculator').then(m => ({ default: m.GeneticGainCalculator })));

// Analysis Tools
const StructureDashboard = lazy(() => import('@/pages/Analysis/StructureDashboard').then(m => ({ default: m.default })));
const MixedModelTool = lazy(() => import('@/pages/Analysis/MixedModelTool').then(m => ({ default: m.default })));
const PedigreeViewer = lazy(() => import('@/pages/Analysis/PedigreeViewer').then(m => ({ default: m.default })));
const BreedingSimulator = lazy(() => import('@/pages/Analysis/BreedingSimulator').then(m => ({ default: m.default })));

const GenomicsViewerPage = lazy(() => import('@/divisions/plant-sciences/genomics/viewer/GenomicsViewerPage').then(m => ({ default: m.default })));

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

export const genomicsRoutes: RouteObject[] = [
  // Samples
  { path: '/samples', element: wrap(Samples) },
  { path: '/samples/new', element: wrap(SampleForm) },
  { path: '/samples/:id', element: wrap(SampleDetail) },
  { path: '/samples/:id/edit', element: wrap(SampleForm) },
  { path: '/sample-tracking', element: wrap(SampleTracking) },

  // Variants
  { path: '/variants', element: wrap(Variants) },
  { path: '/variants/:id', element: wrap(VariantDetail) },
  { path: '/variantsets', element: wrap(VariantSets) },

  // Calls
  { path: '/calls', element: wrap(Calls) },
  { path: '/callsets', element: wrap(CallSets) },
  { path: '/allelematrix', element: wrap(AlleleMatrix) },

  // Maps & Markers
  { path: '/plates', element: wrap(Plates) },
  { path: '/references', element: wrap(References) },
  { path: '/genomemaps', element: wrap(GenomeMaps) },
  { path: '/genetic-map', element: wrap(GeneticMap) },
  { path: '/markerpositions', element: wrap(MarkerPositions) },
  { path: '/vendororders', element: wrap(VendorOrders) },
  { path: '/viewer', element: wrap(GenomicsViewerPage) },

  // Molecular Analysis
  { path: '/molecular-breeding', element: wrap(MolecularBreeding) },
  { path: '/genetic-diversity', element: wrap(GeneticDiversity) },
  { path: '/qtl-mapping', element: wrap(QTLMapping) },
  { path: '/genomic-selection', element: wrap(GenomicSelection) },
  { path: '/marker-assisted-selection', element: wrap(MarkerAssistedSelection) },
  { path: '/haplotype-analysis', element: wrap(HaplotypeAnalysis) },
  { path: '/linkage-disequilibrium', element: wrap(LinkageDisequilibrium) },
  { path: '/population-genetics', element: wrap(PopulationGenetics) },
  { path: '/parentage-analysis', element: wrap(ParentageAnalysis) },
  { path: '/genetic-correlation', element: wrap(GeneticCorrelation) },
  { path: '/gxe-interaction', element: wrap(GxEInteraction) },
  { path: '/stability-analysis', element: wrap(StabilityAnalysis) },
  { path: '/phenomic-selection', element: wrap(PhenomicSelection) },
  { path: '/speed-breeding', element: wrap(SpeedBreeding) },
  { path: '/doubled-haploid', element: wrap(DoubledHaploid) },

  // WASM / Compute
  { path: '/wasm-genomics', element: wrap(WasmGenomics) },
  { path: '/wasm-gblup', element: wrap(WasmGBLUP) },
  { path: '/wasm-popgen', element: wrap(WasmPopGen) },
  { path: '/wasm-ld', element: wrap(WasmLDAnalysis) },
  { path: '/wasm-selection', element: wrap(WasmSelectionIndex) },

  // Breeding Values & Gain
  { path: '/breeding-values', element: wrap(BreedingValues) },
  { path: '/geneticgain', element: wrap(GeneticGain) },
  { path: '/selectionindex', element: wrap(SelectionIndex) },
  { path: '/selection-index-calculator', element: wrap(SelectionIndexCalculator) },
  { path: '/genetic-gain-calculator', element: wrap(GeneticGainCalculator) },
  { path: '/genetic-gain-tracker', element: wrap(GeneticGainTracker) },
  { path: '/breeding-value-calculator', element: wrap(BreedingValueCalculator) },

  // Analysis Dashboards
  { path: '/analysis/structure', element: wrap(StructureDashboard) },
  { path: '/analysis/mixed-model', element: wrap(MixedModelTool) },
  { path: '/analysis/pedigree-viewer', element: wrap(PedigreeViewer) },
  { path: '/analysis/breeding-simulator', element: wrap(BreedingSimulator) },
];
