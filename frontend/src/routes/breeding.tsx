import { lazy, Suspense } from 'react';
import { RouteObject } from 'react-router-dom';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Layout } from '@/components/Layout';

// Lazy load Breeding pages
const Programs = lazy(() => import('@/pages/Programs').then(m => ({ default: m.Programs })));
const ProgramForm = lazy(() => import('@/pages/ProgramForm').then(m => ({ default: m.ProgramForm })));
const ProgramDetail = lazy(() => import('@/pages/ProgramDetail').then(m => ({ default: m.ProgramDetail })));
const ProgramEdit = lazy(() => import('@/pages/ProgramEdit').then(m => ({ default: m.ProgramEdit })));

const Trials = lazy(() => import('@/pages/Trials').then(m => ({ default: m.Trials })));
const TrialForm = lazy(() => import('@/pages/TrialForm').then(m => ({ default: m.TrialForm })));
const TrialDetail = lazy(() => import('@/pages/TrialDetail').then(m => ({ default: m.TrialDetail })));
const TrialEdit = lazy(() => import('@/pages/TrialEdit').then(m => ({ default: m.TrialEdit })));

const Studies = lazy(() => import('@/pages/Studies').then(m => ({ default: m.Studies })));
const StudyForm = lazy(() => import('@/pages/StudyForm').then(m => ({ default: m.StudyForm })));
const StudyDetail = lazy(() => import('@/pages/StudyDetail').then(m => ({ default: m.StudyDetail })));
const StudyEdit = lazy(() => import('@/pages/StudyEdit').then(m => ({ default: m.StudyEdit })));

const Locations = lazy(() => import('@/pages/Locations').then(m => ({ default: m.Locations })));
const LocationForm = lazy(() => import('@/pages/LocationForm').then(m => ({ default: m.LocationForm })));
const LocationDetail = lazy(() => import('@/pages/LocationDetail').then(m => ({ default: m.LocationDetail })));
const LocationEdit = lazy(() => import('@/pages/LocationEdit').then(m => ({ default: m.LocationEdit })));

const Germplasm = lazy(() => import('@/pages/Germplasm').then(m => ({ default: m.Germplasm })));
const GermplasmForm = lazy(() => import('@/pages/GermplasmForm').then(m => ({ default: m.GermplasmForm })));
const GermplasmDetail = lazy(() => import('@/pages/GermplasmDetail').then(m => ({ default: m.GermplasmDetail })));
const GermplasmEdit = lazy(() => import('@/pages/GermplasmEdit').then(m => ({ default: m.GermplasmEdit })));
const GermplasmComparison = lazy(() => import('@/pages/GermplasmComparison').then(m => ({ default: m.GermplasmComparison })));
const GermplasmAttributes = lazy(() => import('@/pages/GermplasmAttributes').then(m => ({ default: m.GermplasmAttributes })));
const GermplasmAttributeValues = lazy(() => import('@/pages/GermplasmAttributeValues').then(m => ({ default: m.GermplasmAttributeValues })));
const GermplasmPassport = lazy(() => import('@/pages/GermplasmPassport').then(m => ({ default: m.GermplasmPassport })));
const GermplasmSearch = lazy(() => import('@/pages/GermplasmSearch').then(m => ({ default: m.GermplasmSearch })));

const Crosses = lazy(() => import('@/pages/Crosses').then(m => ({ default: m.Crosses })));
const CrossForm = lazy(() => import('@/pages/CrossForm').then(m => ({ default: m.CrossForm })));
const CrossDetail = lazy(() => import('@/pages/CrossDetail').then(m => ({ default: m.CrossDetail })));
const CrossingProjects = lazy(() => import('@/pages/CrossingProjects').then(m => ({ default: m.CrossingProjects })));
const PlannedCrosses = lazy(() => import('@/pages/PlannedCrosses').then(m => ({ default: m.PlannedCrosses })));
const CrossingPlanner = lazy(() => import('@/pages/CrossingPlanner').then(m => ({ default: m.CrossingPlanner })));
const CrossPrediction = lazy(() => import('@/pages/CrossPrediction').then(m => ({ default: m.CrossPrediction })));

const Traits = lazy(() => import('@/pages/Traits').then(m => ({ default: m.Traits })));
const TraitForm = lazy(() => import('@/pages/TraitForm').then(m => ({ default: m.TraitForm })));
const TraitDetail = lazy(() => import('@/pages/TraitDetail').then(m => ({ default: m.TraitDetail })));
const TraitEdit = lazy(() => import('@/pages/TraitEdit').then(m => ({ default: m.TraitEdit })));
const Scales = lazy(() => import('@/pages/Scales').then(m => ({ default: m.Scales })));

const Observations = lazy(() => import('@/pages/Observations').then(m => ({ default: m.Observations })));
const DataCollect = lazy(() => import('@/pages/DataCollect').then(m => ({ default: m.DataCollect })));
const ObservationUnits = lazy(() => import('@/pages/ObservationUnits').then(m => ({ default: m.ObservationUnits })));
const ObservationUnitForm = lazy(() => import('@/pages/ObservationUnitForm').then(m => ({ default: m.ObservationUnitForm })));

const Progeny = lazy(() => import('@/pages/Progeny').then(m => ({ default: m.Progeny })));
const PedigreeViewer = lazy(() => import('@/pages/PedigreeViewer').then(m => ({ default: m.PedigreeViewer })));
const Pedigree3D = lazy(() => import('@/pages/Pedigree3D').then(m => ({ default: m.Pedigree3D })).catch(() => ({ default: () => <div className="p-8 text-center text-gray-500">3D Pedigree unavailable</div> })));
const BreedingPipeline = lazy(() => import('@/pages/BreedingPipeline').then(m => ({ default: m.BreedingPipeline })));
const BreedingHistory = lazy(() => import('@/pages/BreedingHistory').then(m => ({ default: m.BreedingHistory })));
const BreedingSimulator = lazy(() => import('@/pages/BreedingSimulator').then(m => ({ default: m.BreedingSimulator })).catch(() => ({ default: () => <div className="p-8 text-center text-gray-500">3D Simulator unavailable</div> })));

// Helper to wrap components
const wrap = (Component: React.LazyExoticComponent<any> | React.ComponentType) => (
  <ProtectedRoute>
    <Layout>
      <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
        <Component />
      </Suspense>
    </Layout>
  </ProtectedRoute>
);

export const breedingRoutes: RouteObject[] = [
  // Programs
  { path: '/programs', element: wrap(Programs) },
  { path: '/programs/new', element: wrap(ProgramForm) },
  { path: '/programs/:programDbId', element: wrap(ProgramDetail) },
  { path: '/programs/:programDbId/edit', element: wrap(ProgramEdit) },

  // Trials
  { path: '/trials', element: wrap(Trials) },
  { path: '/trials/new', element: wrap(TrialForm) },
  { path: '/trials/:trialDbId', element: wrap(TrialDetail) },
  { path: '/trials/:trialDbId/edit', element: wrap(TrialEdit) },

  // Studies
  { path: '/studies', element: wrap(Studies) },
  { path: '/studies/new', element: wrap(StudyForm) },
  { path: '/studies/:studyDbId', element: wrap(StudyDetail) },
  { path: '/studies/:studyDbId/edit', element: wrap(StudyEdit) },

  // Locations
  { path: '/locations', element: wrap(Locations) },
  { path: '/locations/new', element: wrap(LocationForm) },
  { path: '/locations/:locationDbId', element: wrap(LocationDetail) },
  { path: '/locations/:locationDbId/edit', element: wrap(LocationEdit) },

  // Germplasm
  { path: '/germplasm', element: wrap(Germplasm) },
  { path: '/germplasm/new', element: wrap(GermplasmForm) },
  { path: '/germplasm/:germplasmDbId', element: wrap(GermplasmDetail) },
  { path: '/germplasm/:germplasmDbId/edit', element: wrap(GermplasmEdit) },
  { path: '/germplasm-comparison', element: wrap(GermplasmComparison) },
  { path: '/germplasmattributes', element: wrap(GermplasmAttributes) },
  { path: '/attributevalues', element: wrap(GermplasmAttributeValues) },
  { path: '/germplasm-passport', element: wrap(GermplasmPassport) },
  { path: '/germplasm-search', element: wrap(GermplasmSearch) },

  // Crosses
  { path: '/crosses', element: wrap(Crosses) },
  { path: '/crosses/new', element: wrap(CrossForm) },
  { path: '/crosses/:id', element: wrap(CrossDetail) },
  { path: '/crosses/:id/edit', element: wrap(CrossForm) }, // Reusing form for edit
  { path: '/crossingprojects', element: wrap(CrossingProjects) },
  { path: '/plannedcrosses', element: wrap(PlannedCrosses) },
  { path: '/crossingplanner', element: wrap(CrossingPlanner) },
  { path: '/cross-prediction', element: wrap(CrossPrediction) },

  // Traits
  { path: '/traits', element: wrap(Traits) },
  { path: '/traits/new', element: wrap(TraitForm) },
  { path: '/traits/:id', element: wrap(TraitDetail) },
  { path: '/traits/:id/edit', element: wrap(TraitEdit) },
  { path: '/scales', element: wrap(Scales) },

  // Observations
  { path: '/observations', element: wrap(Observations) },
  { path: '/observations/collect', element: wrap(DataCollect) },
  { path: '/observationunits', element: wrap(ObservationUnits) },
  { path: '/observationunits/new', element: wrap(ObservationUnitForm) },

  // Pedigree & History
  { path: '/progeny', element: wrap(Progeny) },
  { path: '/pedigree', element: wrap(PedigreeViewer) },
  { path: '/pedigree-3d', element: wrap(Pedigree3D) },
  { path: '/pipeline', element: wrap(BreedingPipeline) },
  { path: '/breeding-history', element: wrap(BreedingHistory) },
  { path: '/breeding-simulator', element: wrap(BreedingSimulator) },
];
