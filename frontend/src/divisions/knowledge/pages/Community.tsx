/**
 * Community Page
 *
 * Community resources and discussions.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export function Community() {
  const resources = [
    { title: 'GitHub Repository', description: 'Source code, issues, and contributions', icon: '💻', url: 'https://github.com/denishdholaria/bijmantra' },
    { title: 'Discussion Forum', description: 'Ask questions and share knowledge', icon: '💬', url: '#' },
    { title: 'Feature Requests', description: 'Suggest new features and improvements', icon: '💡', url: '#' },
    { title: 'Bug Reports', description: 'Report issues and track fixes', icon: '🐛', url: '#' },
  ];

  const contributors = [
    { name: 'Denish Dholaria', role: 'Creator & Lead Developer', avatar: '👨‍💻' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Community</h1>
        <p className="text-gray-600 mt-1">Connect, contribute, and collaborate</p>
      </div>

      {/* Community Links */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {resources.map((resource) => (
          <Card key={resource.title} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6 text-center">
              <div className="text-4xl mb-3">{resource.icon}</div>
              <h3 className="font-medium">{resource.title}</h3>
              <p className="text-sm text-gray-500 mt-1">{resource.description}</p>
              <Button variant="outline" size="sm" className="mt-4" asChild>
                <a href={resource.url} target="_blank" rel="noopener noreferrer">Visit →</a>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Contributing */}
      <Card>
        <CardHeader><CardTitle>🤝 How to Contribute</CardTitle></CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 bg-green-50 rounded-lg">
              <h4 className="font-medium mb-2">🧪 Test & Report</h4>
              <p className="text-sm text-gray-600">Test features and report bugs via GitHub Issues</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium mb-2">📝 Documentation</h4>
              <p className="text-sm text-gray-600">Help improve docs and tutorials</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <h4 className="font-medium mb-2">💻 Code</h4>
              <p className="text-sm text-gray-600">Submit pull requests for features and fixes</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contributors */}
      <Card>
        <CardHeader><CardTitle>👥 Contributors</CardTitle></CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {contributors.map((c) => (
              <div key={c.name} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <span className="text-3xl">{c.avatar}</span>
                <div>
                  <div className="font-medium">{c.name}</div>
                  <div className="text-sm text-gray-500">{c.role}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Contact */}
      <Card>
        <CardHeader><CardTitle>📧 Contact</CardTitle></CardHeader>
        <CardContent>
          <p className="text-gray-600">
            For questions, feedback, or collaboration opportunities:
          </p>
          <a href="mailto:DenishDholaria@gmail.com" className="text-green-600 hover:underline font-medium">
            DenishDholaria@gmail.com
          </a>
        </CardContent>
      </Card>
    </div>
  );
}

export default Community;
