/**
 * About Page
 * Information about Bijmantra and R.E.E.V.A.i
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'

export function About() {
  const features = [
    { icon: '🤖', title: 'AI-Powered Analysis', desc: 'Bring your own AI (Claude, GPT, Gemini)' },
    { icon: '🌾', title: 'BrAPI v2.1 Compliant', desc: 'Full compliance with Breeding API standards' },
    { icon: '📱', title: 'PWA Ready', desc: 'Works offline, installable on any device' },
    { icon: '🔬', title: 'Complete Breeding Tools', desc: 'Trial design, selection index, genetic gain' },
    { icon: '🧬', title: 'Genotyping Support', desc: 'Variants, samples, allele matrices' },
    { icon: '📊', title: '107 Features', desc: 'Comprehensive breeding management' },
  ]

  const modules = [
    { name: 'Core', count: 9, color: 'bg-blue-500' },
    { name: 'Germplasm', count: 8, color: 'bg-green-500' },
    { name: 'Phenotyping', count: 6, color: 'bg-purple-500' },
    { name: 'Genotyping', count: 12, color: 'bg-orange-500' },
  ]

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      {/* Hero Section */}
      <div className="text-center py-8">
        <div className="w-24 h-24 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-xl mx-auto mb-6">
          <span className="text-5xl">🌱</span>
        </div>
        <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
          Bijmantra
        </h1>
        <p className="text-xl text-muted-foreground mt-3">
          Plant Breeding Information Management System
        </p>
        <div className="flex items-center justify-center gap-2 mt-4">
          <Badge variant="secondary" className="text-sm">BrAPI v2.1</Badge>
          <Badge variant="secondary" className="text-sm">PWA</Badge>
          <Badge variant="secondary" className="text-sm">Open Source</Badge>
        </div>
      </div>

      {/* Author Card */}
      <Card className="border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50">
        <CardHeader className="text-center pb-2">
          <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center shadow-lg mx-auto mb-4">
            <span className="text-3xl">👨‍💻</span>
          </div>
          <CardTitle className="text-2xl">Denish Dholaria</CardTitle>
          <CardDescription className="text-base">Creator & Lead Developer</CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <div className="inline-block">
            <h3 className="text-lg font-bold text-emerald-700">R.E.E.V.A.i</h3>
            <p className="text-sm text-muted-foreground italic">
              Rural Empowerment through Emerging Value-driven Agro-Intelligence
            </p>
          </div>
          
          <div className="bg-white/70 rounded-xl p-6 max-w-2xl mx-auto">
            <div className="flex items-start gap-3">
              <span className="text-2xl">💚</span>
              <div className="text-left">
                <p className="text-gray-700 leading-relaxed">
                  The name <span className="font-semibold text-emerald-600">"Reevai"</span> is inspired by 
                  <span className="font-semibold text-emerald-600"> REEVA</span>, my daughter's name. 
                  This project carries a deeply personal mission — to build climate-resilient technologies 
                  and provide better solutions against climate change.
                </p>
                <p className="text-gray-700 leading-relaxed mt-3">
                  My hope is to contribute to the betterment of our world and leave behind a better planet 
                  for future generations, including Reeva and all children who will inherit this Earth.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-4 pt-2">
            <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-200">
              🌍 Climate Action
            </Badge>
            <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-200">
              🌾 Agriculture Tech
            </Badge>
            <Badge className="bg-purple-100 text-purple-700 hover:bg-purple-200">
              🤖 AI for Good
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Mission */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🎯</span> Our Mission
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 leading-relaxed">
            Bijmantra aims to democratize plant breeding technology by providing a comprehensive, 
            open-source breeding information management system. We believe that modern breeding tools 
            should be accessible to researchers, farmers, and agricultural institutions worldwide — 
            regardless of their resources.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="p-4 bg-green-50 rounded-lg text-center">
              <span className="text-3xl">🌱</span>
              <h4 className="font-semibold mt-2">Empower Breeders</h4>
              <p className="text-sm text-muted-foreground">Modern tools for all</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg text-center">
              <span className="text-3xl">🌍</span>
              <h4 className="font-semibold mt-2">Climate Resilience</h4>
              <p className="text-sm text-muted-foreground">Adapt to change</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg text-center">
              <span className="text-3xl">🤝</span>
              <h4 className="font-semibold mt-2">Open Collaboration</h4>
              <p className="text-sm text-muted-foreground">Share knowledge</p>
            </div>
          </div>
        </CardContent>
      </Card>


      {/* Features Grid */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>✨</span> Key Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {features.map((feature, i) => (
              <div key={i} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <span className="text-2xl">{feature.icon}</span>
                <h4 className="font-semibold mt-2">{feature.title}</h4>
                <p className="text-sm text-muted-foreground">{feature.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* BrAPI Compliance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🔗</span> BrAPI v2.1 Compliance
          </CardTitle>
          <CardDescription>Full implementation of Breeding API standards</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {modules.map((module) => (
              <div key={module.name} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className={`w-12 h-12 ${module.color} rounded-full flex items-center justify-center text-white font-bold text-lg mx-auto`}>
                  {module.count}
                </div>
                <p className="font-medium mt-2">{module.name}</p>
                <p className="text-xs text-muted-foreground">{module.count} entities</p>
              </div>
            ))}
          </div>
          <div className="mt-6 p-4 bg-green-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="font-medium text-green-700">Total BrAPI Coverage</span>
              <span className="text-2xl font-bold text-green-700">100%</span>
            </div>
            <div className="w-full bg-green-200 rounded-full h-3 mt-2">
              <div className="bg-green-500 h-3 rounded-full" style={{ width: '100%' }}></div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Technology Stack */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🛠️</span> Technology Stack
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { name: 'React 18', icon: '⚛️' },
              { name: 'TypeScript', icon: '📘' },
              { name: 'Vite', icon: '⚡' },
              { name: 'Tailwind CSS', icon: '🎨' },
              { name: 'shadcn/ui', icon: '🧩' },
              { name: 'Zustand', icon: '🐻' },
              { name: 'React Query', icon: '🔄' },
              { name: 'PWA', icon: '📱' },
            ].map((tech) => (
              <div key={tech.name} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                <span>{tech.icon}</span>
                <span className="font-medium text-sm">{tech.name}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Footer CTA */}
      <div className="text-center py-8 space-y-4">
        <p className="text-muted-foreground">
          Built with 💚 for the global plant breeding community
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link to="/dashboard">
            <Button>
              <span className="mr-2">🏠</span> Go to Dashboard
            </Button>
          </Link>
          <Link to="/help">
            <Button variant="outline">
              <span className="mr-2">❓</span> Get Help
            </Button>
          </Link>
        </div>
        <p className="text-xs text-muted-foreground mt-6">
          © 2025 Bijmantra by R.E.E.V.A.i • Open Source • MIT License
        </p>
      </div>
    </div>
  )
}
