/**
 * Knowledge Division - Routes
 *
 * Division 9: Documentation, training, and community resources.
 */

import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Documentation = lazy(() => import('./pages/Documentation'));
const Tutorials = lazy(() => import('./pages/Tutorials'));
const TrainingHub = lazy(() => import('./pages/TrainingHub'));
const Glossary = lazy(() => import('./pages/Glossary'));
const FAQ = lazy(() => import('./pages/FAQ'));
const Community = lazy(() => import('./pages/Community'));
const Forums = lazy(() => import('./pages/Forums'));
const ForumTopic = lazy(() => import('./pages/ForumTopic'));
const NewTopic = lazy(() => import('./pages/NewTopic'));

/**
 * Knowledge Division Routes
 */
export const knowledgeRoutes: RouteObject[] = [
  { path: '', element: <Dashboard /> },
  { path: 'dashboard', element: <Dashboard /> },
  { path: 'docs', element: <Documentation /> },
  { path: 'docs/:section', element: <Documentation /> },
  { path: 'tutorials', element: <Tutorials /> },
  { path: 'training', element: <TrainingHub /> },
  { path: 'glossary', element: <Glossary /> },
  { path: 'faq', element: <FAQ /> },
  { path: 'community', element: <Community /> },
  { path: 'forums', element: <Forums /> },
  { path: 'forums/new', element: <NewTopic /> },
  { path: 'forums/:topicId', element: <ForumTopic /> },
];

export default knowledgeRoutes;
