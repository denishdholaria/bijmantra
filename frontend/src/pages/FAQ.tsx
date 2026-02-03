/**
 * FAQ - Frequently Asked Questions
 * Common questions and answers about Bijmantra
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'

interface FAQItem {
  id: string
  question: string
  answer: string
  category: string
}

const faqItems: FAQItem[] = [
  // Getting Started
  {
    id: 'gs-1',
    question: 'What is Bijmantra?',
    answer: 'Bijmantra is a modern, BrAPI-compliant plant breeding management platform. It helps breeders manage their breeding programs, trials, germplasm, and phenotypic data. The name "Bijmantra" comes from Sanskrit, meaning "seed mantra" - reflecting our mission to empower plant breeders.',
    category: 'getting-started'
  },
  {
    id: 'gs-2',
    question: 'Do I need a backend server to use Bijmantra?',
    answer: 'Bijmantra works in "demo mode" without a backend server, allowing you to explore the interface. For full functionality with data persistence, you\'ll need to connect to a BrAPI-compliant backend server. The app automatically detects if a backend is available.',
    category: 'getting-started'
  },
  {
    id: 'gs-3',
    question: 'Is Bijmantra free to use?',
    answer: 'Yes! Bijmantra is open-source software released under a permissive license. You can use it freely for research, education, and commercial breeding programs. The source code is available on GitHub.',
    category: 'getting-started'
  },
  {
    id: 'gs-4',
    question: 'What browsers are supported?',
    answer: 'Bijmantra works best on modern browsers like Chrome, Firefox, Safari, and Edge. For Chrome AI features (local AI processing), Chrome 138 or later is required. The app is also a Progressive Web App (PWA) that can be installed on your device.',
    category: 'getting-started'
  },
  
  // Data Management
  {
    id: 'dm-1',
    question: 'How do I import existing data?',
    answer: 'Go to Import/Export in the Tools section. You can import data from CSV, Excel, or BrAPI-formatted JSON files. The system will validate your data and show any errors before importing. Templates are available for each data type.',
    category: 'data'
  },
  {
    id: 'dm-2',
    question: 'Can I export my data?',
    answer: 'Yes! All data can be exported in multiple formats including CSV, Excel, and BrAPI JSON. Go to Import/Export or use the export button on any list view. You can also generate formatted reports from the Reports section.',
    category: 'data'
  },
  {
    id: 'dm-3',
    question: 'Is my data secure?',
    answer: 'Your data security depends on your deployment. In demo mode, data is stored locally in your browser. When connected to a backend, data is stored on your server. We recommend using HTTPS and proper authentication for production deployments.',
    category: 'data'
  },
  {
    id: 'dm-4',
    question: 'Does Bijmantra work offline?',
    answer: 'Yes! Bijmantra is a Progressive Web App (PWA) with offline support. You can collect data in the field without internet connectivity. Data will sync automatically when you\'re back online.',
    category: 'data'
  },
  
  // Breeding Features
  {
    id: 'bf-1',
    question: 'How do I set up a new breeding program?',
    answer: 'Go to Programs → New Program. Enter your program name, abbreviation, and objectives. You can then create trials, register germplasm, and start collecting data. See the Quick Start Guide for step-by-step instructions.',
    category: 'breeding'
  },
  {
    id: 'bf-2',
    question: 'What trial designs are supported?',
    answer: 'Bijmantra supports common experimental designs including CRD (Completely Randomized Design), RCBD (Randomized Complete Block Design), Alpha-lattice, Augmented designs, and Split-plot designs. Use the Trial Design tool to generate layouts.',
    category: 'breeding'
  },
  {
    id: 'bf-3',
    question: 'How do I track pedigrees?',
    answer: 'Pedigree information is stored with each germplasm entry. You can specify parent1 (female) and parent2 (male) when registering germplasm. The Pedigree Viewer provides visual family trees and ancestry tracking.',
    category: 'breeding'
  },
  {
    id: 'bf-4',
    question: 'Can I calculate selection indices?',
    answer: 'Yes! The Selection Index tool allows you to combine multiple traits with custom weights. You can use economic weights, desired gains, or restriction indices. The tool ranks your germplasm based on the combined index.',
    category: 'breeding'
  },
  
  // AI Features
  {
    id: 'ai-1',
    question: 'What AI features are available?',
    answer: 'Bijmantra offers two AI systems: 1) Cloud AI (OpenAI, Anthropic, Google, Mistral) for complex analysis and recommendations, and 2) Chrome Built-in AI (Gemini Nano) for local, private processing. AI can help with data analysis, selection decisions, and answering breeding questions.',
    category: 'ai'
  },
  {
    id: 'ai-2',
    question: 'Do I need an API key for AI features?',
    answer: 'For Cloud AI features, yes - you need an API key from your chosen provider (OpenAI, Anthropic, etc.). Chrome Built-in AI is free and runs locally in your browser without any API key. Configure AI in Settings → AI Settings.',
    category: 'ai'
  },
  {
    id: 'ai-3',
    question: 'Is my data sent to AI providers?',
    answer: 'When using Cloud AI, your queries and relevant data context are sent to the AI provider. When using Chrome Built-in AI, all processing happens locally on your device - no data leaves your computer. Choose based on your privacy requirements.',
    category: 'ai'
  },
  {
    id: 'ai-4',
    question: 'How do I enable Chrome AI?',
    answer: 'Chrome AI requires Chrome 138+ with specific flags enabled. Go to chrome://flags and enable the Gemini Nano flags, then download the model from chrome://components. See the Chrome AI page for detailed setup instructions.',
    category: 'ai'
  },
  
  // Technical
  {
    id: 'tech-1',
    question: 'What is BrAPI?',
    answer: 'BrAPI (Breeding API) is a standardized RESTful web service specification for plant breeding data. It enables interoperability between breeding databases and tools. Bijmantra is fully BrAPI v2.1 compliant.',
    category: 'technical'
  },
  {
    id: 'tech-2',
    question: 'Can I connect to my existing BrAPI server?',
    answer: 'Yes! Bijmantra can connect to any BrAPI v2.1 compliant server. Configure the server URL in Settings. The app will automatically use your server for data storage and retrieval.',
    category: 'technical'
  },
  {
    id: 'tech-3',
    question: 'How do I deploy Bijmantra for my organization?',
    answer: 'Bijmantra can be deployed as a static web app or with a backend server. For static deployment, build the frontend and host on any web server. For full functionality, deploy the Python/FastAPI backend with PostgreSQL. See the documentation for deployment guides.',
    category: 'technical'
  },
  {
    id: 'tech-4',
    question: 'Can I customize Bijmantra?',
    answer: 'Yes! Bijmantra is open-source and built with React, TypeScript, and Tailwind CSS. You can fork the repository and customize it for your needs. Contributions are welcome!',
    category: 'technical'
  },
]

const categories = [
  { id: 'all', label: 'All Questions', icon: '❓' },
  { id: 'getting-started', label: 'Getting Started', icon: '🚀' },
  { id: 'data', label: 'Data Management', icon: '💾' },
  { id: 'breeding', label: 'Breeding Features', icon: '🌱' },
  { id: 'ai', label: 'AI Features', icon: '🤖' },
  { id: 'technical', label: 'Technical', icon: '⚙️' },
]

export function FAQ() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const filteredFAQs = faqItems.filter(item => {
    const matchesSearch = item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.answer.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Frequently Asked Questions</h1>
          <p className="text-muted-foreground mt-1">Find answers to common questions</p>
        </div>
        <Link to="/help">
          <Button variant="outline">← Back to Help</Button>
        </Link>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <Input
            type="search"
            placeholder="Search questions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-md"
          />
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
        </CardContent>
      </Card>

      {/* FAQ List */}
      <div className="space-y-3">
        {filteredFAQs.map(item => (
          <Card 
            key={item.id}
            className={`cursor-pointer transition-all ${expandedId === item.id ? 'ring-2 ring-primary' : ''}`}
            onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
          >
            <CardContent className="pt-4">
              <div className="flex items-start gap-3">
                <span className="text-xl flex-shrink-0">
                  {expandedId === item.id ? '➖' : '➕'}
                </span>
                <div className="flex-1">
                  <h3 className="font-semibold">{item.question}</h3>
                  {expandedId === item.id && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-muted-foreground whitespace-pre-line">{item.answer}</p>
                    </div>
                  )}
                </div>
                <Badge variant="outline" className="flex-shrink-0">
                  {categories.find(c => c.id === item.category)?.label}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredFAQs.length === 0 && (
        <div className="text-center py-12">
          <span className="text-4xl">🔍</span>
          <p className="mt-2 text-muted-foreground">No questions found matching your search</p>
        </div>
      )}

      {/* Still Need Help */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-4xl">💬</span>
              <div>
                <h3 className="font-semibold">Still have questions?</h3>
                <p className="text-sm text-muted-foreground">
                  Ask our AI assistant or check the documentation
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Link to="/ai-assistant">
                <Button>🤖 Ask AI</Button>
              </Link>
              <Link to="/glossary">
                <Button variant="outline">📖 Glossary</Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
