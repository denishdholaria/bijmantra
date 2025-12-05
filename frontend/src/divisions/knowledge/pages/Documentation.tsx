/**
 * Documentation Page
 *
 * Technical documentation and guides.
 */

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function Documentation() {
  const { section } = useParams();
  const [activeSection, setActiveSection] = useState(section || 'getting-started');

  const sections = [
    { id: 'getting-started', title: 'Getting Started', icon: '🚀' },
    { id: 'divisions', title: 'Divisions', icon: '🏛️' },
    { id: 'api', title: 'API Reference', icon: '🔌' },
    { id: 'brapi', title: 'BrAPI Integration', icon: '🌐' },
    { id: 'offline', title: 'Offline Mode', icon: '📴' },
    { id: 'security', title: 'Security', icon: '🔒' },
  ];

  const content: Record<string, { title: string; content: string }> = {
    'getting-started': {
      title: 'Getting Started with Bijmantra',
      content: `
## Welcome to Bijmantra

Bijmantra is a comprehensive platform for agricultural science, plant breeding, and research, built on the Parashakti Framework.

### Quick Start

1. **Login** - Use your organization credentials
2. **Select Division** - Choose Plant Sciences, Seed Bank, or Earth Systems
3. **Create Program** - Set up your first breeding program
4. **Add Data** - Start recording trials, observations, and germplasm

### Key Features

- **Offline-First**: Works without internet, syncs when connected
- **Multi-Division**: Modular architecture for different research areas
- **BrAPI Compatible**: Interoperable with other breeding platforms
      `,
    },
    'divisions': {
      title: 'Division Structure',
      content: `
## Parashakti Framework Divisions

Bijmantra is organized into 9 specialized divisions:

| Division | Description |
|----------|-------------|
| Plant Sciences | Breeding, genomics, crop sciences |
| Seed Bank | Genetic resources, conservation |
| Earth Systems | Climate, weather, GIS |
| Integration Hub | Third-party API connections |
| Knowledge | Documentation, training |

Each division operates independently but shares core infrastructure.
      `,
    },
    'api': {
      title: 'API Reference',
      content: `
## REST API

Base URL: \`/api/v2\`

### Authentication
All endpoints require JWT authentication via Bearer token.

### Endpoints

- \`GET /programs\` - List breeding programs
- \`POST /programs\` - Create program
- \`GET /seed-bank/accessions\` - List accessions
- \`POST /seed-bank/accessions\` - Register accession
      `,
    },
  };

  const currentContent = content[activeSection] || content['getting-started'];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Documentation</h1>
        <p className="text-gray-600 mt-1">Technical guides and reference</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <Card className="lg:col-span-1">
          <CardContent className="p-0">
            <nav className="divide-y">
              {sections.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setActiveSection(s.id)}
                  className={`w-full p-3 text-left flex items-center gap-2 hover:bg-gray-50 ${activeSection === s.id ? 'bg-green-50 text-green-700' : ''}`}
                >
                  <span>{s.icon}</span>
                  <span className="font-medium">{s.title}</span>
                </button>
              ))}
            </nav>
          </CardContent>
        </Card>

        {/* Content */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>{currentContent.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-sm">{currentContent.content}</pre>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default Documentation;
