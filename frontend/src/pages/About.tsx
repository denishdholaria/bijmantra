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
    { icon: '📊', title: '200+ Features', desc: 'Comprehensive breeding management' },
  ]

  const modules = [
    { name: 'Core', count: 9, color: 'bg-blue-500' },
    { name: 'Germplasm', count: 8, color: 'bg-green-500' },
    { name: 'Phenotyping', count: 6, color: 'bg-purple-500' },
    { name: 'Genotyping', count: 12, color: 'bg-orange-500' },
  ]

  const timeline = [
    { year: 'Age 12', event: 'First steps into genetics', desc: 'Learning plant breeding alongside father at the cotton research farm in Gujarat, India' },
    { year: '2010s', event: 'BSc Biotechnology', desc: 'Monash University, Australia - Building the scientific foundation' },
    { year: '2010s', event: 'MSc Plant Breeding & Biotechnology', desc: 'University of Adelaide - Specializing in crop improvement' },
    { year: '2010s', event: 'Agricultural Science', desc: 'University of Melbourne - Broadening agricultural knowledge' },
    { year: '2025', event: 'Bijmantra Born', desc: 'Combining decades of experience into an open-source platform for the world' },
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

      {/* The Story Section */}
      <Card className="border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50">
        <CardHeader className="text-center pb-2">
          <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center shadow-lg mx-auto mb-4">
            <span className="text-3xl">🌾</span>
          </div>
          <CardTitle className="text-2xl">A Story Rooted in the Fields</CardTitle>
          <CardDescription className="text-base">From a cotton research farm to a global platform</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-white/70 rounded-xl p-6 max-w-3xl mx-auto">
            <div className="prose prose-green max-w-none">
              <p className="text-gray-700 leading-relaxed text-lg">
                <span className="text-3xl float-left mr-3 mt-1">👦</span>
                At the age of twelve, while most children were playing cricket, a young boy in Gujarat, India 
                was walking through rows of cotton plants with his father, <span className="font-semibold text-emerald-700">Dr. T. L. Dholaria</span>, 
                a PhD holder in Plant Breeding and Genetics. Those early mornings at the research farm weren't 
                just father-son time — they were the first lessons in a lifelong journey of understanding how 
                seeds carry the hopes of farmers and the future of food security.
              </p>
              
              <p className="text-gray-700 leading-relaxed mt-4">
                Watching his father develop new cotton hybrids, the boy learned that plant breeding isn't just 
                science — it's an art of patience, observation, and deep respect for nature. Each cross made, 
                each selection chosen, each trial planted was a step toward helping farmers grow better crops 
                and build better lives.
              </p>

              <p className="text-gray-700 leading-relaxed mt-4">
                That boy grew up to pursue his passion across three prestigious Australian universities — 
                <span className="font-semibold"> Monash University</span> (BSc Biotechnology), 
                <span className="font-semibold"> University of Adelaide</span> (MSc Plant Breeding & MSc Plant Biotechnology), 
                and the <span className="font-semibold">University of Melbourne</span> (Agricultural Science). 
                But the most valuable education always remained those early lessons from the cotton fields of Gujarat.
              </p>

              <div className="bg-emerald-50 rounded-lg p-4 mt-6 border-l-4 border-emerald-500">
                <p className="text-emerald-800 italic">
                  "The seeds we plant today determine the harvest our children will reap tomorrow. 
                  Bijmantra is my contribution to ensuring that harvest is abundant, sustainable, 
                  and accessible to all who tend the earth."
                </p>
                <p className="text-emerald-600 font-semibold mt-2">— Denish Dholaria, Creator of Bijmantra</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Author Card */}
      <Card>
        <CardHeader className="text-center pb-2">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg mx-auto mb-4">
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
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
            <div className="p-3 bg-blue-50 rounded-lg">
              <span className="text-2xl">🎓</span>
              <p className="font-semibold text-sm mt-1">BSc Biotechnology</p>
              <p className="text-xs text-muted-foreground">Monash University</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <span className="text-2xl">🧬</span>
              <p className="font-semibold text-sm mt-1">MSc Plant Breeding & Biotech</p>
              <p className="text-xs text-muted-foreground">University of Adelaide</p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <span className="text-2xl">🌾</span>
              <p className="font-semibold text-sm mt-1">Agricultural Science</p>
              <p className="text-xs text-muted-foreground">University of Melbourne</p>
            </div>
          </div>

          <div className="bg-amber-50 rounded-xl p-4 max-w-2xl mx-auto border border-amber-200">
            <div className="flex items-start gap-3">
              <span className="text-2xl">👨‍🔬</span>
              <div className="text-left">
                <p className="font-semibold text-amber-800">Mentored by Dr. T. L. Dholaria</p>
                <p className="text-sm text-amber-700">
                  PhD in Plant Breeding and Genetics • Pioneer in Cotton Hybrid Development • Gujarat, India
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

      {/* Journey Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🛤️</span> The Journey
          </CardTitle>
          <CardDescription>From cotton fields to code</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-green-200"></div>
            <div className="space-y-6">
              {timeline.map((item, i) => (
                <div key={i} className="relative pl-12">
                  <div className="absolute left-2 w-5 h-5 bg-green-500 rounded-full border-4 border-white shadow"></div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <Badge variant="outline" className="mb-2">{item.year}</Badge>
                    <h4 className="font-semibold">{item.event}</h4>
                    <p className="text-sm text-muted-foreground">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
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
            regardless of their resources. Our hope is to contribute to the betterment of our world 
            and leave behind a better planet for future generations — for all children who will inherit this Earth.
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

      {/* Acknowledgments */}
      <Card className="border-2 border-amber-200 bg-gradient-to-br from-amber-50 to-yellow-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🙏</span> Acknowledgments
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-white/70 rounded-xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center shadow-md">
                <span className="text-2xl">☀️</span>
              </div>
              <div>
                <h3 className="text-xl font-bold text-amber-800">Solar Agrotech Private Limited</h3>
                <p className="text-amber-600">Proud Sponsor & Resource Provider</p>
              </div>
            </div>
            <p className="text-gray-700 leading-relaxed">
              This application was built thanks to the generous support and resources provided by 
              <span className="font-semibold text-amber-700"> Solar Agrotech Private Limited</span>. 
              Their commitment to agricultural innovation and technology has made it possible to develop 
              Bijmantra as an open-source platform for the global plant breeding community.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-white/70 rounded-lg">
              <span className="text-2xl">👨‍🔬</span>
              <h4 className="font-semibold mt-2">Dr. T. L. Dholaria</h4>
              <p className="text-sm text-muted-foreground">
                For the foundational knowledge in plant breeding and genetics, and for showing that 
                science begins in the field, not just the laboratory.
              </p>
            </div>
            <div className="p-4 bg-white/70 rounded-lg">
              <span className="text-2xl">🌏</span>
              <h4 className="font-semibold mt-2">Open Source Community</h4>
              <p className="text-sm text-muted-foreground">
                For the countless tools, libraries, and inspiration that make projects like this possible.
              </p>
            </div>
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
        <div className="mt-6 space-y-1">
          <p className="text-xs text-muted-foreground">
            © 2025 Bijmantra by R.E.E.V.A.i • Open Source • MIT License
          </p>
          <p className="text-xs text-muted-foreground">
            Supported by Solar Agrotech Private Limited
          </p>
        </div>
      </div>
    </div>
  )
}
