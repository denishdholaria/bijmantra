import { RouteObject } from 'react-router-dom';
import { AgronomyProvider } from './context/AgronomyContext';
import { Outlet } from 'react-router-dom';

// Pages
import CropList from './pages/CropList';
import CropForm from './pages/CropForm';
import CropDetail from './pages/CropDetail';
import FieldList from './pages/FieldList';
import FieldForm from './pages/FieldForm';
import FieldDetail from './pages/FieldDetail';
import SoilProfileList from './pages/SoilProfileList';
import SoilProfileForm from './pages/SoilProfileForm';
import SoilProfileDetail from './pages/SoilProfileDetail';
import SeasonList from './pages/SeasonList';
import SeasonForm from './pages/SeasonForm';
import SeasonDetail from './pages/SeasonDetail';
import FarmingPracticeList from './pages/FarmingPracticeList';
import FarmingPracticeForm from './pages/FarmingPracticeForm';
import FarmingPracticeDetail from './pages/FarmingPracticeDetail';

const AgronomyLayout = () => (
  <AgronomyProvider>
    <Outlet />
  </AgronomyProvider>
);

export const agronomyRoutes: RouteObject[] = [
  {
    path: 'agronomy',
    element: <AgronomyLayout />,
    children: [
      // Crops
      { path: 'crops', element: <CropList /> },
      { path: 'crops/new', element: <CropForm /> },
      { path: 'crops/:id', element: <CropDetail /> },
      { path: 'crops/:id/edit', element: <CropForm /> },

      // Fields
      { path: 'fields', element: <FieldList /> },
      { path: 'fields/new', element: <FieldForm /> },
      { path: 'fields/:id', element: <FieldDetail /> },
      { path: 'fields/:id/edit', element: <FieldForm /> },

      // Soil Profiles
      { path: 'soil-profiles', element: <SoilProfileList /> },
      { path: 'soil-profiles/new', element: <SoilProfileForm /> },
      { path: 'soil-profiles/:id', element: <SoilProfileDetail /> },
      { path: 'soil-profiles/:id/edit', element: <SoilProfileForm /> },

      // Seasons
      { path: 'seasons', element: <SeasonList /> },
      { path: 'seasons/new', element: <SeasonForm /> },
      { path: 'seasons/:id', element: <SeasonDetail /> },
      { path: 'seasons/:id/edit', element: <SeasonForm /> },

      // Farming Practices
      { path: 'practices', element: <FarmingPracticeList /> },
      { path: 'practices/new', element: <FarmingPracticeForm /> },
      { path: 'practices/:id', element: <FarmingPracticeDetail /> },
      { path: 'practices/:id/edit', element: <FarmingPracticeForm /> },
    ]
  }
];
