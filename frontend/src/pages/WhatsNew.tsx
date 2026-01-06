/**
 * What's New - Release Notes & Updates
 * Changelog and new feature announcements
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Release {
  version: string
  date: string
  type: 'major' | 'minor' | 'patch'
  highlights: string[]
  features: { title: string; description: string; icon: string }[]
  fixes?: string[]
  breaking?: string[]
}

const releases: Release[] = [
  {
    version: '1.3.0',
    date: 'December 1, 2025',
    type: 'minor',
    highlights: [
      'Comprehensive Help & Documentation System',
      'Chrome Built-in AI Integration',
      'Hybrid AI Mode (Local + Cloud)',
    ],
    features: [
      { title: 'Help Center', description: 'Searchable documentation hub with categorized articles', icon: '📚' },
      { title: 'Quick Start Guide', description: 'Interactive 8-step onboarding with progress tracking', icon: '🚀' },
      { title: 'Glossary', description: '50+ breeding terms with definitions and related terms', icon: '📖' },
      { title: 'FAQ', description: 'Frequently asked questions organized by category', icon: '❓' },
      { title: 'Keyboard Shortcuts', description: 'Complete reference for power users', icon: '⌨️' },
      { title: 'Chrome AI', description: 'Local AI processing with Gemini Nano (Summarizer, Translator, Writer)', icon: '🌐' },
      { title: 'Hybrid AI Mode', description: 'Smart routing between local and cloud AI', icon: '🤖' },
    ],
    fixes: [
      'Fixed login authentication flow with demo mode fallback',
      'Fixed SelectItem empty value errors across multiple pages',
    ],
  },
  {
    version: '1.2.0',
    date: 'November 30, 2025',
    type: 'minor',
    highlights: [
      'AI Assistant with Multi-Provider Support',
      'Data Context Engine for AI',
      'About Page with R.E.E.V.A.i Story',
    ],
    features: [
      { title: 'AI Assistant', description: 'Chat interface for breeding data analysis', icon: '💬' },
      { title: 'AI Settings', description: 'Configure OpenAI, Anthropic, Google, or Mistral', icon: '⚙️' },
      { title: 'Data Context', description: 'AI automatically accesses your breeding data', icon: '📊' },
      { title: 'About Page', description: 'Author details and R.E.E.V.A.i mission', icon: 'ℹ️' },
    ],
  },
  {
    version: '1.1.0',
    date: 'November 29, 2025',
    type: 'minor',
    highlights: [
      '100+ Pages Milestone',
      'Complete BrAPI v2.1 Coverage',
      'Advanced Breeding Tools',
    ],
    features: [
      { title: 'Selection Index', description: 'Multi-trait selection with custom weights', icon: '📊' },
      { title: 'Genetic Gain Calculator', description: 'Estimate breeding progress', icon: '📈' },
      { title: 'Pedigree Viewer', description: 'Visual family tree navigation', icon: '🌳' },
      { title: 'Trial Design', description: 'RCBD, Alpha-lattice, and more', icon: '🎲' },
      { title: 'Field Book', description: 'Mobile-friendly data collection', icon: '📓' },
      { title: 'Crossing Planner', description: 'Plan and optimize crosses', icon: '💑' },
    ],
  },
  {
    version: '1.0.0',
    date: 'November 28, 2025',
    type: 'major',
    highlights: [
      'Initial Release',
      'Modern UI with Vertical Sidebar',
      'PWA with Offline Support',
    ],
    features: [
      { title: 'Programs', description: 'Breeding program management', icon: '🌾' },
      { title: 'Germplasm', description: 'Genetic material tracking', icon: '🌱' },
      { title: 'Trials & Studies', description: 'Field experiment management', icon: '🧪' },
      { title: 'Observations', description: 'Phenotypic data collection', icon: '📋' },
      { title: 'Locations', description: 'Site management with maps', icon: '📍' },
      { title: 'Dashboard', description: 'Overview and quick actions', icon: '📊' },
    ],
  },
]

export function WhatsNew() {
  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'major':
        return <Badge className="bg-purple-100 text-purple-700">Major Release</Badge>
      case 'minor':
        return <Badge className="bg-blue-100 text-blue-700">Feature Update</Badge>
      case 'patch':
        return <Badge className="bg-green-100 text-green-700">Bug Fix</Badge>
      default:
        return <Badge variant="secondary">{type}</Badge>
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">What's New</h1>
          <p className="text-muted-foreground mt-1">Release notes and updates</p>
        </div>
        <Link to="/help">
          <Button variant="outline">📚 Help Center</Button>
        </Link>
      </div>

      {/* Latest Release Banner */}
      <Card className="border-green-200 bg-gradient-to-r from-green-50 to-emerald-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-green-500 rounded-2xl flex items-center justify-center text-white text-2xl shadow-lg">
              🎉
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold">Version {releases[0].version}</h2>
                {getTypeBadge(releases[0].type)}
                <Badge variant="outline">Latest</Badge>
              </div>
              <p className="text-muted-foreground">{releases[0].date}</p>
              <div className="flex flex-wrap gap-2 mt-2">
                {releases[0].highlights.map((h, i) => (
                  <Badge key={i} variant="secondary">{h}</Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Release Timeline */}
      <div className="space-y-6">
        {releases.map((release, index) => (
          <Card key={release.version} className={index === 0 ? 'ring-2 ring-green-200' : ''}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    v{release.version}
                    {getTypeBadge(release.type)}
                    {index === 0 && <Badge className="bg-green-500">Current</Badge>}
                  </CardTitle>
                  <CardDescription>{release.date}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Features */}
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <span>✨</span> New Features
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {release.features.map((feature, i) => (
                    <div key={i} className="p-3 bg-muted rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <span>{feature.icon}</span>
                        <span className="font-medium text-sm">{feature.title}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{feature.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bug Fixes */}
              {release.fixes && release.fixes.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <span>🐛</span> Bug Fixes
                  </h4>
                  <ul className="text-sm space-y-1">
                    {release.fixes.map((fix, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-green-500">✓</span>
                        <span>{fix}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Breaking Changes */}
              {release.breaking && release.breaking.length > 0 && (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                  <h4 className="font-medium mb-2 flex items-center gap-2 text-red-800">
                    <span>⚠️</span> Breaking Changes
                  </h4>
                  <ul className="text-sm space-y-1 text-red-700">
                    {release.breaking.map((change, i) => (
                      <li key={i}>• {change}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Subscribe to Updates */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-4xl">📬</span>
              <div>
                <h3 className="font-semibold">Stay Updated</h3>
                <p className="text-sm text-muted-foreground">
                  Follow the project on GitHub for the latest updates
                </p>
              </div>
            </div>
            <a 
              href="https://github.com/denishdholaria/bijmantra" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              <Button>⭐ Star on GitHub</Button>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
