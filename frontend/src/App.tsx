import { BrowserRouter as Router, useRoutes } from 'react-router-dom';
import { 
  breedingRoutes, 
  seedOpsRoutes, 
  genomicsRoutes, 
  commercialRoutes, 
  futureRoutes, 
  adminRoutes, 
  aiRoutes, 
  coreRoutes 
} from '@/routes';

function AppRoutes() {
  const element = useRoutes([
    ...coreRoutes,
    ...breedingRoutes,
    ...seedOpsRoutes,
    ...genomicsRoutes,
    ...commercialRoutes,
    ...futureRoutes,
    ...adminRoutes,
    ...aiRoutes,
  ]);
  return element;
}

function App() {
  return (
    <Router>
      <AppRoutes />
    </Router>
  );
}

export default App;
