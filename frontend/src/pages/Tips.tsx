/**
 * Tips & Tricks Page
 * Power user tips for getting the most out of Bijmantra
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Tip {
  id: string
  title: string
  description: string
  category: string
  icon: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  steps?: string[]
}

const tips: Tip[] = [
  // Data Entry
  {
    id: 'tip-1',
    title: 'Use Tab to Navigate Forms',
    description: 'Press Tab to quickly move between form fields. Shift+Tab goes backwards.',
    category: 'data-entry',
    icon: '⌨️',
    difficulty: 'beginner',
  },
  {
    id: 'tip-2',
    title: 'Bulk Import from Excel',
    description: 'Prepare your data in Excel using our templates, then import multiple records at once.',
    category: 'data-entry',
    icon: '📊',
    difficulty: 'intermediate',
    steps: [
      'Go to Import/Export',
      'Download the template for your data type',
      'Fill in your data in Excel',
      'Upload the completed file',
      'Review and confirm the import',
    ],
  },
  {
    id: 'tip-3',
    title: 'Quick Search with Cmd+K',
    description: 'Press Cmd+K (or Ctrl+K on Windows) to open the quick search from anywhere.',
    category: 'navigation',
    icon: '🔍',
    difficulty: 'beginner',
  },
  {
    id: 'tip-4',
    title: 'Collapse Sidebar for More Space',
    description: 'Click the collapse button or press Cmd+B to minimize the sidebar when you need more screen space.',
    category: 'navigation',
    icon: '📐',
    difficulty: 'beginner',
  },
  {
    id: 'tip-5',
    title: 'Use Selection Index for Multi-Trait Selection',
    description: 'Combine multiple traits with custom weights to rank germplasm objectively.',
    category: 'analysis',
    icon: '📊',
    difficulty: 'advanced',
    steps: [
      'Go to Selection Index tool',
      'Select the traits you want to include',
      'Assign weights based on importance',
      'Choose your selection method (economic, desired gains, etc.)',
      'View ranked germplasm list',
    ],
  },
  {
    id: 'tip-6',
    title: 'Ask AI for Data Analysis',
    description: 'The AI Assistant can analyze your breeding data and provide insights. Just ask!',
    category: 'ai',
    icon: '🤖',
    difficulty: 'intermediate',
    steps: [
      'Go to AI Assistant',
      'Enable "Include App Data" toggle',
      'Ask questions like "What are my top performers for yield?"',
      'Get AI-powered analysis and recommendations',
    ],
  },
  {
    id: 'tip-7',
    title: 'Use Chrome AI for Privacy',
    description: 'Chrome AI processes everything locally - your data never leaves your device.',
    category: 'ai',
    icon: '🔒',
    difficulty: 'intermediate',
  },
  {
    id: 'tip-8',
    title: 'Install as PWA for Offline Use',
    description: 'Install Bijmantra as an app on your device for offline data collection in the field.',
    category: 'mobile',
    icon: '📱',
    difficulty: 'beginner',
    steps: [
      'Open Bijmantra in Chrome',
      'Click the install icon in the address bar',
      'Or go to Menu → Install Bijmantra',
      'The app will work offline!',
    ],
  },
  {
    id: 'tip-9',
    title: 'Use Field Book for Mobile Data Collection',
    description: 'The Field Book is optimized for touch screens and works great on tablets.',
    category: 'mobile',
    icon: '📓',
    difficulty: 'beginner',
  },
  {
    id: 'tip-10',
    title: 'Track Pedigrees Visually',
    description: 'Use the Pedigree Viewer to see family trees and trace ancestry.',
    category: 'analysis',
    icon: '🌳',
    difficulty: 'intermediate',
  },
  {
    id: 'tip-11',
    title: 'Generate Trial Designs Automatically',
    description: 'Let the Trial Design tool create randomized layouts for your experiments.',
    category: 'analysis',
    icon: '🎲',
    difficulty: 'advanced',
    steps: [
      'Go to Trial Design',
      'Select your design type (RCBD, Alpha-lattice, etc.)',
      'Enter number of entries and replications',
      'Generate the randomized layout',
      'Export to Excel or print field maps',
    ],
  },
  {
    id: 'tip-12',
    title: 'Use Barcode Scanner for Fast Data Entry',
    description: 'Scan barcodes to quickly identify plots and germplasm during data collection.',
    category: 'data-entry',
    icon: '📷',
    difficulty: 'intermediate',
  },
  {
    id: 'tip-13',
    title: 'Export Reports in Multiple Formats',
    description: 'Generate professional reports and export as PDF, Excel, or CSV.',
    category: 'reporting',
    icon: '📋',
    difficulty: 'beginner',
  },
  {
    id: 'tip-14',
    title: 'Use Lists to Organize Germplasm',
    description: 'Create lists to group germplasm for specific purposes like trials or crosses.',
    category: 'organization',
    icon: '📝',
    difficulty: 'beginner',
  },
  {
    id: 'tip-15',
    title: 'Check Data Quality Regularly',
    description: 'Use the Data Quality tool to find missing values, outliers, and inconsistencies.',
    category: 'data-entry',
    icon: '✅',
    difficulty: 'intermediate',
  },
]

const categories = [
  { id: 'all', label: 'All Tips', icon: '💡' },
  { id: 'data-entry', label: 'Data Entry', icon: '📝' },
  { id: 'navigation', label: 'Navigation', icon: '🧭' },
  { id: 'analysis', label: 'Analysis', icon: '📊' },
  { id: 'ai', label: 'AI Features', icon: '🤖' },
  { id: 'mobile', label: 'Mobile', icon: '📱' },
  { id: 'reporting', label: 'Reporting', icon: '📋' },
  { id: 'organization', label: 'Organization', icon: '🗂️' },
]

export function Tips() {
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all')
  const [expandedTip, setExpandedTip] = useState<string | null>(null)

  const filteredTips = tips.filter(tip => {
    const matchesCategory = selectedCategory === 'all' || tip.category === selectedCategory
    const matchesDifficulty = selectedDifficulty === 'all' || tip.difficulty === selectedDifficulty
    return matchesCategory && matchesDifficulty
  })

  const getDifficultyBadge = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return <Badge className="bg-green-100 text-green-700">Beginner</Badge>
      case 'intermediate':
        return <Badge className="bg-blue-100 text-blue-700">Intermediate</Badge>
      case 'advanced':
        return <Badge className="bg-purple-100 text-purple-700">Advanced</Badge>
      default:
        return null
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Tips & Tricks</h1>
          <p className="text-muted-foreground mt-1">Get the most out of Bijmantra</p>
        </div>
        <Link to="/help">
          <Button variant="outline">📚 Help Center</Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Category</p>
            <div className="flex flex-wrap gap-2">
              {categories.map(cat => (
                <Button
                  key={cat.id}
                  variant={selectedCategory === cat.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory(cat.id)}
                >
                  {cat.icon} {cat.label}
                </Button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm font-medium mb-2">Difficulty</p>
            <div className="flex gap-2">
              <Button
                variant={selectedDifficulty === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedDifficulty('all')}
              >
                All Levels
              </Button>
              <Button
                variant={selectedDifficulty === 'beginner' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedDifficulty('beginner')}
                className={selectedDifficulty === 'beginner' ? '' : 'border-green-200 text-green-700'}
              >
                🌱 Beginner
              </Button>
              <Button
                variant={selectedDifficulty === 'intermediate' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedDifficulty('intermediate')}
                className={selectedDifficulty === 'intermediate' ? '' : 'border-blue-200 text-blue-700'}
              >
                🌿 Intermediate
              </Button>
              <Button
                variant={selectedDifficulty === 'advanced' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedDifficulty('advanced')}
                className={selectedDifficulty === 'advanced' ? '' : 'border-purple-200 text-purple-700'}
              >
                🌳 Advanced
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tips Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredTips.map(tip => (
          <Card 
            key={tip.id}
            className={`cursor-pointer transition-all ${expandedTip === tip.id ? 'ring-2 ring-primary' : ''}`}
            onClick={() => setExpandedTip(expandedTip === tip.id ? null : tip.id)}
          >
            <CardContent className="pt-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">{tip.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold">{tip.title}</h3>
                    {getDifficultyBadge(tip.difficulty)}
                  </div>
                  <p className="text-sm text-muted-foreground">{tip.description}</p>
                  
                  {expandedTip === tip.id && tip.steps && (
                    <div className="mt-4 pt-4 border-t">
                      <p className="text-sm font-medium mb-2">How to do it:</p>
                      <ol className="space-y-1">
                        {tip.steps.map((step, i) => (
                          <li key={i} className="text-sm flex items-start gap-2">
                            <span className="flex-shrink-0 w-5 h-5 bg-primary/10 text-primary rounded-full flex items-center justify-center text-xs">
                              {i + 1}
                            </span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredTips.length === 0 && (
        <div className="text-center py-12">
          <span className="text-4xl">🔍</span>
          <p className="mt-2 text-muted-foreground">No tips found for this filter</p>
        </div>
      )}

      {/* Pro Tips Banner */}
      <Card className="border-yellow-200 bg-yellow-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <span className="text-4xl">💡</span>
            <div>
              <h3 className="font-semibold text-yellow-800">Pro Tip</h3>
              <p className="text-sm text-yellow-700">
                Bookmark this page and check back regularly - we add new tips with each update!
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
