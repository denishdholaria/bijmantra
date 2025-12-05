/**
 * Knowledge Dashboard
 *
 * Central hub for documentation, learning, and resources.
 */

import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function Dashboard() {
  const sections = [
    { title: 'Documentation', path: '/knowledge/docs', icon: '📚', description: 'Technical guides and API reference' },
    { title: 'Tutorials', path: '/knowledge/tutorials', icon: '🎓', description: 'Step-by-step learning paths' },
    { title: 'Glossary', path: '/knowledge/glossary', icon: '📖', description: 'Plant breeding terminology' },
    { title: 'FAQ', path: '/knowledge/faq', icon: '❓', description: 'Frequently asked questions' },
    { title: 'Community', path: '/knowledge/community', icon: '👥', description: 'Forums and discussions' },
  ];

  const recentDocs = [
    { title: 'Getting Started with Bijmantra', category: 'Quickstart' },
    { title: 'Setting Up Your First Breeding Program', category: 'Tutorial' },
    { title: 'Understanding BrAPI Integration', category: 'Technical' },
    { title: 'Offline Data Sync Guide', category: 'Feature' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Knowledge Base</h1>
        <p className="text-gray-600 mt-1">Documentation, tutorials, and learning resources</p>
      </div>

      {/* Quick Links */}
      <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
        {sections.map((section) => (
          <Link key={section.path} to={section.path}>
            <Card className="h-full hover:border-green-500 hover:shadow-md transition-all">
              <CardContent className="p-4 text-center">
                <div className="text-4xl mb-2">{section.icon}</div>
                <div className="font-medium">{section.title}</div>
                <p className="text-xs text-gray-500 mt-1">{section.description}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <span className="text-3xl">🔍</span>
            <input
              type="text"
              placeholder="Search documentation, tutorials, and more..."
              className="flex-1 p-3 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
            />
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Recent Documentation */}
        <Card>
          <CardHeader><CardTitle>📄 Recent Documentation</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentDocs.map((doc, i) => (
                <Link key={i} to="/knowledge/docs" className="block p-3 rounded-lg hover:bg-gray-50">
                  <div className="font-medium text-green-600 hover:underline">{doc.title}</div>
                  <span className="text-xs text-gray-500">{doc.category}</span>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Learning Paths */}
        <Card>
          <CardHeader><CardTitle>🎯 Learning Paths</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              <LearningPath title="Beginner's Guide" progress={0} lessons={8} />
              <LearningPath title="Breeding Program Setup" progress={25} lessons={6} />
              <LearningPath title="Data Collection Mastery" progress={60} lessons={10} />
              <LearningPath title="Advanced Genomics" progress={0} lessons={12} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Tips */}
      <Card>
        <CardHeader><CardTitle>💡 Quick Tips</CardTitle></CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <TipCard icon="⌨️" title="Keyboard Shortcuts" tip="Press Ctrl+K to open command palette" />
            <TipCard icon="📱" title="Mobile App" tip="Install as PWA for offline field access" />
            <TipCard icon="🔄" title="Data Sync" tip="Changes sync automatically when online" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function LearningPath({ title, progress, lessons }: { title: string; progress: number; lessons: number }) {
  return (
    <div className="p-3 border rounded-lg">
      <div className="flex justify-between items-center mb-2">
        <span className="font-medium">{title}</span>
        <span className="text-sm text-gray-500">{lessons} lessons</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className="h-full bg-green-500 rounded-full" style={{ width: `${progress}%` }} />
      </div>
      <div className="text-xs text-gray-500 mt-1">{progress}% complete</div>
    </div>
  );
}

function TipCard({ icon, title, tip }: { icon: string; title: string; tip: string }) {
  return (
    <div className="p-4 bg-blue-50 rounded-lg">
      <div className="flex items-center gap-2 font-medium mb-1">
        <span>{icon}</span> {title}
      </div>
      <p className="text-sm text-gray-600">{tip}</p>
    </div>
  );
}

export default Dashboard;
