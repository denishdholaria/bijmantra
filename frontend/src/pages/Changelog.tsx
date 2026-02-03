/**
 * Changelog - Detailed Version History
 * Complete changelog with all changes
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface ChangelogEntry {
  version: string
  date: string
  changes: {
    type: 'added' | 'changed' | 'fixed' | 'removed' | 'security'
    description: string
  }[]
}

const changelog: ChangelogEntry[] = [
  {
    version: 'preview-1',
    date: '2026-01-09',
    changes: [
      { type: 'added', description: 'CALF (Computational Analysis and Functionality Level) assessment' },
      { type: 'added', description: 'MAHASARTHI navigation system (dock, browser, search)' },
      { type: 'added', description: 'Future workspaces roadmap (11 modules planned)' },
      { type: 'changed', description: 'Version updated to preview-1 reflecting actual state' },
      { type: 'changed', description: 'Documentation reorganized (gupt, standards, operations)' },
      { type: 'fixed', description: 'Zero Demo Data Policy violations identified' },
    ],
  },
  {
    version: '1.3.0',
    date: '2025-12-01',
    changes: [
      { type: 'added', description: 'Help Center with searchable documentation' },
      { type: 'added', description: 'Quick Start Guide with interactive onboarding' },
      { type: 'added', description: 'Glossary with 50+ breeding terms' },
      { type: 'added', description: 'FAQ page with categorized questions' },
      { type: 'added', description: 'Keyboard Shortcuts reference' },
      { type: 'added', description: "What's New page with release notes" },
      { type: 'added', description: 'Feedback page for bug reports and feature requests' },
      { type: 'added', description: 'Tips & Tricks page for power users' },
      { type: 'added', description: 'Chrome Built-in AI integration (Gemini Nano)' },
      { type: 'added', description: 'Summarizer API for trial results' },
      { type: 'added', description: 'Translator API for multi-language support' },
      { type: 'added', description: 'Cloud AI integration (Google Gemini, Groq, OpenAI, Anthropic)' },
      { type: 'fixed', description: 'Login authentication with demo mode fallback' },
      { type: 'fixed', description: 'SelectItem empty value errors' },
    ],
  },
  {
    version: '1.2.0',
    date: '2025-11-30',
    changes: [
      { type: 'added', description: 'AI Assistant with multi-provider support' },
      { type: 'added', description: 'AI Settings page for configuration' },
      { type: 'added', description: 'Data Context Engine for AI' },
      { type: 'added', description: 'About page with R.E.E.V.A.i story' },
      { type: 'added', description: 'Support for OpenAI, Anthropic, Google, Mistral' },
      { type: 'changed', description: 'Improved AI response formatting' },
    ],
  },
  {
    version: '1.1.0',
    date: '2025-11-29',
    changes: [
      { type: 'added', description: 'Selection Index tool' },
      { type: 'added', description: 'Genetic Gain Calculator' },
      { type: 'added', description: 'Pedigree Viewer' },
      { type: 'added', description: 'Trial Design tool (RCBD, Alpha-lattice)' },
      { type: 'added', description: 'Field Book for mobile data collection' },
      { type: 'added', description: 'Crossing Planner' },
      { type: 'added', description: 'Breeding Pipeline view' },
      { type: 'added', description: 'Harvest Planner' },
      { type: 'added', description: 'Seed Inventory management' },
      { type: 'added', description: 'Statistics and analysis tools' },
      { type: 'added', description: 'Nursery Management' },
      { type: 'added', description: 'Label Printing' },
      { type: 'added', description: 'Barcode Scanner' },
      { type: 'added', description: 'Weather integration' },
      { type: 'changed', description: 'Reached 100+ pages milestone' },
    ],
  },
  {
    version: '1.0.0',
    date: '2025-11-28',
    changes: [
      { type: 'added', description: 'Initial release' },
      { type: 'added', description: 'Programs management' },
      { type: 'added', description: 'Germplasm tracking' },
      { type: 'added', description: 'Trials and Studies' },
      { type: 'added', description: 'Observations and data collection' },
      { type: 'added', description: 'Locations with map support' },
      { type: 'added', description: 'Seed Lots management' },
      { type: 'added', description: 'Crosses tracking' },
      { type: 'added', description: 'Traits/Observation Variables' },
      { type: 'added', description: 'People/Contacts' },
      { type: 'added', description: 'Lists management' },
      { type: 'added', description: 'Seasons' },
      { type: 'added', description: 'Import/Export functionality' },
      { type: 'added', description: 'Reports generation' },
      { type: 'added', description: 'Modern UI with vertical sidebar' },
      { type: 'added', description: 'PWA with offline support' },
      { type: 'added', description: 'BrAPI v2.1 compliance' },
    ],
  },
]

export function Changelog() {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'added': return '✨'
      case 'changed': return '🔄'
      case 'fixed': return '🐛'
      case 'removed': return '🗑️'
      case 'security': return '🔒'
      default: return '•'
    }
  }

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'added':
        return <Badge className="bg-green-100 text-green-700 text-xs">Added</Badge>
      case 'changed':
        return <Badge className="bg-blue-100 text-blue-700 text-xs">Changed</Badge>
      case 'fixed':
        return <Badge className="bg-yellow-100 text-yellow-700 text-xs">Fixed</Badge>
      case 'removed':
        return <Badge className="bg-red-100 text-red-700 text-xs">Removed</Badge>
      case 'security':
        return <Badge className="bg-purple-100 text-purple-700 text-xs">Security</Badge>
      default:
        return null
    }
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Changelog</h1>
          <p className="text-muted-foreground mt-1">Complete version history</p>
        </div>
        <div className="flex gap-2">
          <Link to="/whats-new">
            <Button variant="outline">🎉 What's New</Button>
          </Link>
          <Link to="/help">
            <Button variant="outline">📚 Help</Button>
          </Link>
        </div>
      </div>

      {/* Legend */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-1">
              <span>✨</span>
              <Badge className="bg-green-100 text-green-700 text-xs">Added</Badge>
              <span className="text-xs text-muted-foreground">New features</span>
            </div>
            <div className="flex items-center gap-1">
              <span>🔄</span>
              <Badge className="bg-blue-100 text-blue-700 text-xs">Changed</Badge>
              <span className="text-xs text-muted-foreground">Updates</span>
            </div>
            <div className="flex items-center gap-1">
              <span>🐛</span>
              <Badge className="bg-yellow-100 text-yellow-700 text-xs">Fixed</Badge>
              <span className="text-xs text-muted-foreground">Bug fixes</span>
            </div>
            <div className="flex items-center gap-1">
              <span>🗑️</span>
              <Badge className="bg-red-100 text-red-700 text-xs">Removed</Badge>
              <span className="text-xs text-muted-foreground">Deprecated</span>
            </div>
            <div className="flex items-center gap-1">
              <span>🔒</span>
              <Badge className="bg-purple-100 text-purple-700 text-xs">Security</Badge>
              <span className="text-xs text-muted-foreground">Security updates</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Changelog Entries */}
      <div className="space-y-6">
        {changelog.map((entry, index) => (
          <Card key={entry.version} className={index === 0 ? 'ring-2 ring-green-200' : ''}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  v{entry.version}
                  {index === 0 && <Badge className="bg-green-500">Latest</Badge>}
                </CardTitle>
                <span className="text-sm text-muted-foreground">{entry.date}</span>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {entry.changes.map((change, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="flex-shrink-0">{getTypeIcon(change.type)}</span>
                    <span className="flex-shrink-0">{getTypeBadge(change.type)}</span>
                    <span className="text-sm">{change.description}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Footer */}
      <Card className="bg-muted/50">
        <CardContent className="pt-4">
          <div className="text-center text-sm text-muted-foreground">
            <p>This changelog follows <a href="https://keepachangelog.com" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Keep a Changelog</a> format</p>
            <p className="mt-1">Bijmantra uses <a href="https://semver.org" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Semantic Versioning</a></p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
