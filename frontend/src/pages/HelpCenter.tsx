/**
 * Help Center - Main Documentation Hub
 * Comprehensive help system for Bijmantra
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface HelpArticle {
  id: string
  title: string
  description: string
  category: string
  icon: string
  link?: string
  content?: string
}

const helpArticles: HelpArticle[] = [
  // Getting Started
  { id: 'gs-1', title: 'Welcome to Bijmantra', description: 'Introduction to the plant breeding platform', category: 'getting-started', icon: '👋', link: '/quick-guide' },
  { id: 'gs-2', title: 'Quick Start Guide', description: 'Get up and running in 5 minutes', category: 'getting-started', icon: '🚀', link: '/quick-guide' },
  { id: 'gs-3', title: 'Dashboard Overview', description: 'Understanding your breeding dashboard', category: 'getting-started', icon: '📊', link: '/dashboard' },
  { id: 'gs-4', title: 'Navigation & Layout', description: 'How to navigate the application', category: 'getting-started', icon: '🧭' },
  
  // Core Modules
  { id: 'cm-1', title: 'Managing Programs', description: 'Create and manage breeding programs', category: 'core', icon: '🌾', link: '/programs' },
  { id: 'cm-2', title: 'Working with Trials', description: 'Set up and manage field trials', category: 'core', icon: '🧪', link: '/trials' },
  { id: 'cm-3', title: 'Studies & Experiments', description: 'Organize your research studies', category: 'core', icon: '📈', link: '/studies' },
  { id: 'cm-4', title: 'Location Management', description: 'Add and manage field locations', category: 'core', icon: '📍', link: '/locations' },
  
  // Germplasm
  { id: 'gp-1', title: 'Germplasm Management', description: 'Register and track genetic material', category: 'germplasm', icon: '🌱', link: '/germplasm' },
  { id: 'gp-2', title: 'Seed Lot Tracking', description: 'Manage seed inventory and lots', category: 'germplasm', icon: '📦', link: '/seedlots' },
  { id: 'gp-3', title: 'Crosses & Hybridization', description: 'Plan and record crosses', category: 'germplasm', icon: '🧬', link: '/crosses' },
  { id: 'gp-4', title: 'Pedigree Tracking', description: 'View and manage pedigrees', category: 'germplasm', icon: '🌳', link: '/pedigree' },
  
  // Phenotyping
  { id: 'ph-1', title: 'Trait Definitions', description: 'Define and manage observation variables', category: 'phenotyping', icon: '🔬', link: '/traits' },
  { id: 'ph-2', title: 'Data Collection', description: 'Record phenotypic observations', category: 'phenotyping', icon: '📋', link: '/observations/collect' },
  { id: 'ph-3', title: 'Field Book Usage', description: 'Mobile-friendly data collection', category: 'phenotyping', icon: '📓', link: '/fieldbook' },
  { id: 'ph-4', title: 'Image Management', description: 'Capture and organize images', category: 'phenotyping', icon: '📷', link: '/images' },
  
  // Analysis Tools
  { id: 'at-1', title: 'Selection Index', description: 'Multi-trait selection tools', category: 'analysis', icon: '📊', link: '/selectionindex' },
  { id: 'at-2', title: 'Genetic Gain Calculator', description: 'Estimate breeding progress', category: 'analysis', icon: '📈', link: '/geneticgain' },
  { id: 'at-3', title: 'Trial Design', description: 'Statistical design tools', category: 'analysis', icon: '🎲', link: '/trialdesign' },
  { id: 'at-4', title: 'Statistics & Reports', description: 'Data analysis and reporting', category: 'analysis', icon: '📉', link: '/statistics' },
  
  // AI Features
  { id: 'ai-1', title: 'AI Assistant', description: 'Get AI-powered breeding insights', category: 'ai', icon: '🤖', link: '/ai-assistant' },
  { id: 'ai-2', title: 'Chrome AI (Local)', description: 'Use browser-based AI features', category: 'ai', icon: '🌐', link: '/chrome-ai' },
  { id: 'ai-3', title: 'AI Configuration', description: 'Set up AI providers', category: 'ai', icon: '⚙️', link: '/ai-settings' },
]

const categories = [
  { id: 'all', label: 'All Topics', icon: '📚' },
  { id: 'getting-started', label: 'Getting Started', icon: '🚀' },
  { id: 'core', label: 'Core Modules', icon: '🏠' },
  { id: 'germplasm', label: 'Germplasm', icon: '🌱' },
  { id: 'phenotyping', label: 'Phenotyping', icon: '🔬' },
  { id: 'analysis', label: 'Analysis', icon: '📊' },
  { id: 'ai', label: 'AI Features', icon: '🤖' },
]

const keyboardShortcuts = [
  { keys: ['⌘', 'K'], description: 'Open quick search' },
  { keys: ['⌘', '/'], description: 'Open help' },
  { keys: ['⌘', 'B'], description: 'Toggle sidebar' },
  { keys: ['⌘', 'N'], description: 'Create new item' },
  { keys: ['⌘', 'S'], description: 'Save current form' },
  { keys: ['Esc'], description: 'Close modal/dialog' },
  { keys: ['↑', '↓'], description: 'Navigate lists' },
  { keys: ['Enter'], description: 'Select/confirm' },
]

export function HelpCenter() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')

  const filteredArticles = helpArticles.filter(article => {
    const matchesSearch = article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         article.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || article.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Help Center</h1>
          <p className="text-muted-foreground mt-1">Documentation, guides, and support</p>
        </div>
        <div className="flex gap-2">
          <Link to="/quick-guide">
            <Button>🚀 Quick Start</Button>
          </Link>
          <Link to="/glossary">
            <Button variant="outline">📖 Glossary</Button>
          </Link>
        </div>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="max-w-2xl mx-auto text-center space-y-4">
            <h2 className="text-xl font-semibold">How can we help you?</h2>
            <div className="relative">
              <Input
                type="search"
                placeholder="Search documentation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-12 text-lg"
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xl">🔍</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Try searching for "germplasm", "trial design", or "AI assistant"
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link to="/quick-guide">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="pt-6 text-center">
              <span className="text-3xl">🚀</span>
              <h3 className="font-semibold mt-2">Quick Start</h3>
              <p className="text-xs text-muted-foreground">5-minute guide</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/keyboard-shortcuts">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="pt-6 text-center">
              <span className="text-3xl">⌨️</span>
              <h3 className="font-semibold mt-2">Shortcuts</h3>
              <p className="text-xs text-muted-foreground">Keyboard reference</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/faq">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="pt-6 text-center">
              <span className="text-3xl">❓</span>
              <h3 className="font-semibold mt-2">FAQ</h3>
              <p className="text-xs text-muted-foreground">Common questions</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/glossary">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardContent className="pt-6 text-center">
              <span className="text-3xl">📖</span>
              <h3 className="font-semibold mt-2">Glossary</h3>
              <p className="text-xs text-muted-foreground">Breeding terms</p>
            </CardContent>
          </Card>
        </Link>
      </div>

      <Tabs defaultValue="articles">
        <TabsList>
          <TabsTrigger value="articles">📚 Documentation</TabsTrigger>
          <TabsTrigger value="shortcuts">⌨️ Shortcuts</TabsTrigger>
          <TabsTrigger value="videos">🎬 Videos</TabsTrigger>
        </TabsList>

        <TabsContent value="articles" className="space-y-6 mt-4">
          {/* Category Filter */}
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

          {/* Articles Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredArticles.map(article => (
              <Card key={article.id} className="hover:shadow-md transition-shadow">
                {article.link ? (
                  <Link to={article.link}>
                    <CardHeader className="pb-2">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{article.icon}</span>
                        <div>
                          <CardTitle className="text-base">{article.title}</CardTitle>
                          <CardDescription className="text-sm">{article.description}</CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <Badge variant="secondary" className="text-xs">
                        {categories.find(c => c.id === article.category)?.label}
                      </Badge>
                    </CardContent>
                  </Link>
                ) : (
                  <>
                    <CardHeader className="pb-2">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{article.icon}</span>
                        <div>
                          <CardTitle className="text-base">{article.title}</CardTitle>
                          <CardDescription className="text-sm">{article.description}</CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <Badge variant="secondary" className="text-xs">
                        {categories.find(c => c.id === article.category)?.label}
                      </Badge>
                    </CardContent>
                  </>
                )}
              </Card>
            ))}
          </div>

          {filteredArticles.length === 0 && (
            <div className="text-center py-12">
              <span className="text-4xl">🔍</span>
              <p className="mt-2 text-muted-foreground">No articles found matching your search</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="shortcuts" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Keyboard Shortcuts</CardTitle>
              <CardDescription>Speed up your workflow with these shortcuts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {keyboardShortcuts.map((shortcut, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <span className="text-sm">{shortcut.description}</span>
                    <div className="flex gap-1">
                      {shortcut.keys.map((key, j) => (
                        <kbd key={j} className="px-2 py-1 bg-white border rounded text-xs font-mono shadow-sm">
                          {key}
                        </kbd>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="videos" className="mt-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <span className="text-6xl">🎬</span>
                <h3 className="text-xl font-semibold mt-4">Video Tutorials Coming Soon</h3>
                <p className="text-muted-foreground mt-2 max-w-md mx-auto">
                  We're working on video tutorials to help you get the most out of Bijmantra.
                  Check back soon!
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Contact Support */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-4xl">💬</span>
              <div>
                <h3 className="font-semibold">Need more help?</h3>
                <p className="text-sm text-muted-foreground">
                  Ask our AI assistant or check the community resources
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Link to="/ai-assistant">
                <Button>🤖 Ask AI Assistant</Button>
              </Link>
              <a href="https://github.com/plantbreeding/BrAPI" target="_blank" rel="noopener noreferrer">
                <Button variant="outline">🌐 BrAPI Community</Button>
              </a>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
