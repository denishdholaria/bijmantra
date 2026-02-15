import { BrowserRouter as Router, useLocation, useRoutes } from 'react-router-dom';
import {
  breedingRoutes,
  seedOpsRoutes,
  genomicsRoutes,
  commercialRoutes,
  futureRoutes,
  adminRoutes,
  aiRoutes,
  coreRoutes,
  fieldRoutes,
} from '@/routes';
import { BijMantraDesktop } from '@/framework';

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
    ...fieldRoutes,
  ]);
  return element;
}

function AppLayout() {
  const location = useLocation();
  const isLogin = location.pathname === '/login';

  // Login page renders without shell
  if (isLogin) {
    return <AppRoutes />;
  }

  // Everything else renders inside the Web-OS Desktop Shell
  return (
    <BijMantraDesktop>
      <AppRoutes />
    </BijMantraDesktop>
  );
}

function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  );
}

export default App;
