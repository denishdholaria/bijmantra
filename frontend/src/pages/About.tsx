/**
 * About Page
 * Information about Bijmantra and R.E.E.V.A.i
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'
import { ChangelogInline } from '@/components/Changelog'

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
    { year: '2010', event: 'BSc Biotechnology', desc: 'Monash University, Australia - Building the scientific foundation' },
    { year: '2012', event: 'MSc Plant Biotechnology', desc: 'University of Adelaide - Specializing in crop improvement' },
    { year: '2024', event: 'Agricultural Science', desc: 'University of Melbourne - Precision Agriculture, Agricultural Extension & Marketing' },
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
        <p className="text-2xl font-medium text-foreground mt-3">
          One Seed. Infinite Worlds.
        </p>
        <p className="text-base text-muted-foreground mt-2">
          योगः कर्मसु कौशलम् — Excellence in Action
        </p>
        <div className="flex items-center justify-center gap-2 mt-4">
          <Badge variant="secondary" className="text-sm">BrAPI v2.1</Badge>
          <Badge variant="secondary" className="text-sm">PWA</Badge>
          <Badge variant="secondary" className="text-sm">Open Source</Badge>
        </div>
      </div>

      {/* The Story Section */}
      <Card className="border-2 border-green-200 dark:border-green-800 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30">
        <CardHeader className="text-center pb-2">
          <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center shadow-lg mx-auto mb-4">
            <span className="text-3xl">🌾</span>
          </div>
          <CardTitle className="text-2xl">A Story Rooted in the Fields</CardTitle>
          <CardDescription className="text-base">From a cotton research farm to a global platform</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-white/70 dark:bg-slate-800/70 rounded-xl p-6 max-w-3xl mx-auto">
            <div className="prose prose-green dark:prose-invert max-w-none">
              <p className="text-foreground leading-relaxed text-lg">
                <span className="text-3xl float-left mr-3 mt-1">👦</span>
                At the age of twelve, while most children were playing cricket, a young boy in Gujarat, India 
                was walking through rows of cotton plants with his father, <span className="font-semibold text-emerald-700 dark:text-emerald-400">Dr. T. L. Dholaria</span>, 
                a PhD holder in Plant Breeding and Genetics. Those early mornings at the research farm weren't 
                just father-son time — they were the first lessons in a lifelong journey of understanding how 
                seeds carry the hopes of farmers and the future of food security.
              </p>
              
              <p className="text-foreground leading-relaxed mt-4">
                Watching his father develop new cotton hybrids, the boy learned that plant breeding isn't just 
                science — it's an art of patience, observation, and deep respect for nature. Each cross made, 
                each selection chosen, each trial planted was a step toward helping farmers grow better crops 
                and build better lives.
              </p>

              <p className="text-foreground leading-relaxed mt-4">
                That boy grew up to pursue his passion across three prestigious Australian universities — 
                <span className="font-semibold"> Monash University</span> (BSc Biotechnology), 
                <span className="font-semibold"> University of Adelaide</span> (MSc Plant Breeding & MSc Plant Biotechnology), 
                and the <span className="font-semibold">University of Melbourne</span> (Agricultural Science). 
                But the most valuable education always remained those early lessons from the cotton fields of Gujarat.
              </p>

              <div className="bg-emerald-50 dark:bg-emerald-900/30 rounded-lg p-4 mt-6 border-l-4 border-emerald-500">
                <p className="text-emerald-800 dark:text-emerald-300 italic">
                  "The seeds we plant today determine the harvest our children will reap tomorrow. 
                  Bijmantra is my contribution to ensuring that harvest is abundant, sustainable, 
                  and accessible to all who tend the earth."
                </p>
                <p className="text-emerald-600 dark:text-emerald-400 font-semibold mt-2">— Denish Dholaria, Creator of Bijmantra</p>
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
            <div className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
              <span className="text-2xl">🎓</span>
              <p className="font-semibold text-sm mt-1 text-foreground">BSc Biotechnology (2010)</p>
              <p className="text-xs text-muted-foreground">Monash University</p>
            </div>
            <div className="p-3 bg-green-50 dark:bg-green-900/30 rounded-lg">
              <span className="text-2xl">🧬</span>
              <p className="font-semibold text-sm mt-1 text-foreground">MSc Plant Breeding & Biotech (2012)</p>
              <p className="text-xs text-muted-foreground">University of Adelaide</p>
            </div>
            <div className="p-3 bg-purple-50 dark:bg-purple-900/30 rounded-lg">
              <span className="text-2xl">🌾</span>
              <p className="font-semibold text-sm mt-1 text-foreground">Agricultural Science (2024)</p>
              <p className="text-xs text-muted-foreground">University of Melbourne</p>
            </div>
          </div>

          <div className="bg-amber-50 dark:bg-amber-900/30 rounded-xl p-4 max-w-2xl mx-auto border border-amber-200 dark:border-amber-800">
            <div className="flex items-start gap-3">
              <span className="text-2xl">👨‍🔬</span>
              <div className="text-left">
                <p className="font-semibold text-amber-800 dark:text-amber-300">Mentored by Dr. T. L. Dholaria</p>
                <p className="text-sm text-amber-700 dark:text-amber-400">
                  PhD in Plant Breeding and Genetics • Pioneer in Cotton Hybrid Development • Gujarat, India
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-4 pt-2">
            <Badge className="bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-200 dark:hover:bg-emerald-900/60">
              🌍 Climate Action
            </Badge>
            <Badge className="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/60">
              🌾 Agriculture Tech
            </Badge>
            <Badge className="bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/60">
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
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-green-200 dark:bg-green-800"></div>
            <div className="space-y-6">
              {timeline.map((item, i) => (
                <div key={i} className="relative pl-12">
                  <div className="absolute left-2 w-5 h-5 bg-green-500 rounded-full border-4 border-white dark:border-slate-800 shadow"></div>
                  <div className="bg-muted rounded-lg p-4">
                    <Badge variant="outline" className="mb-2">{item.year}</Badge>
                    <h4 className="font-semibold text-foreground">{item.event}</h4>
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
          <p className="text-foreground leading-relaxed">
            Bijmantra aims to democratize plant breeding technology by providing a comprehensive, 
            open-source breeding information management system. We believe that modern breeding tools 
            should be accessible to researchers, farmers, and agricultural institutions worldwide — 
            regardless of their resources. Our hope is to contribute to the betterment of our world 
            and leave behind a better planet for future generations — for all children who will inherit this Earth.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="p-4 bg-green-50 dark:bg-green-900/30 rounded-lg text-center">
              <span className="text-3xl">🌱</span>
              <h4 className="font-semibold mt-2 text-foreground">Empower Breeders</h4>
              <p className="text-sm text-muted-foreground">Modern tools for all</p>
            </div>
            <div className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg text-center">
              <span className="text-3xl">🌍</span>
              <h4 className="font-semibold mt-2 text-foreground">Climate Resilience</h4>
              <p className="text-sm text-muted-foreground">Adapt to change</p>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-purple-900/30 rounded-lg text-center">
              <span className="text-3xl">🤝</span>
              <h4 className="font-semibold mt-2 text-foreground">Open Collaboration</h4>
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
              <div key={i} className="p-4 bg-muted rounded-lg hover:bg-muted/80 transition-colors">
                <span className="text-2xl">{feature.icon}</span>
                <h4 className="font-semibold mt-2 text-foreground">{feature.title}</h4>
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
              <div key={module.name} className="text-center p-4 bg-muted rounded-lg">
                <div className={`w-12 h-12 ${module.color} rounded-full flex items-center justify-center text-white font-bold text-lg mx-auto`}>
                  {module.count}
                </div>
                <p className="font-medium mt-2 text-foreground">{module.name}</p>
                <p className="text-xs text-muted-foreground">{module.count} entities</p>
              </div>
            ))}
          </div>
          <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/30 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="font-medium text-green-700 dark:text-green-300">Total BrAPI Coverage</span>
              <span className="text-2xl font-bold text-green-700 dark:text-green-300">100%</span>
            </div>
            <div className="w-full bg-green-200 dark:bg-green-800 rounded-full h-3 mt-2">
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
              <div key={tech.name} className="flex items-center gap-2 p-3 bg-muted rounded-lg">
                <span>{tech.icon}</span>
                <span className="font-medium text-sm text-foreground">{tech.name}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Changelog */}
      <Card>
        <CardContent className="pt-6">
          <ChangelogInline maxReleases={3} />
        </CardContent>
      </Card>

      {/* Gratitude to Teachers */}
      <Card className="border-2 border-blue-200 dark:border-blue-800 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30">
        <CardHeader className="text-center pb-2">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg mx-auto mb-4">
            <span className="text-2xl">🎓</span>
          </div>
          <CardTitle className="text-xl text-blue-800 dark:text-blue-300">Gratitude to My Teachers</CardTitle>
          <CardDescription className="text-base text-blue-600 dark:text-blue-400">
            आचार्य देवो भव — "The teacher is God"
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-center text-foreground max-w-2xl mx-auto">
            The knowledge I carry was shaped by exceptional educators. I am forever grateful 
            for their patience, wisdom, and dedication to teaching.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-white/70 dark:bg-slate-800/70 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">🏛️</span>
                <h4 className="font-semibold text-foreground">University of Adelaide</h4>
              </div>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>Professor Peter Langridge</li>
                <li>Professor Mark Tester</li>
                <li>Dr Carolyn Schultz</li>
                <li>Professor Amanda Able</li>
                <li>Professor Diana Mathers</li>
                <li className="italic">...and many more</li>
              </ul>
            </div>
            <div className="p-4 bg-white/70 dark:bg-slate-800/70 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">🏛️</span>
                <h4 className="font-semibold text-foreground">University of Melbourne</h4>
              </div>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>Professor Pablo J. Zarco-Tejada</li>
                <li>Dr Tomas Poblete</li>
                <li>Professor Ruth Nettle</li>
                <li className="italic">...and many more</li>
              </ul>
            </div>
          </div>
          
          <p className="text-center text-sm text-muted-foreground italic mt-4">
            Whatever I know, I owe to my teachers. Whatever errors exist, they are mine alone.
          </p>
        </CardContent>
      </Card>

      {/* Acknowledgments */}
      <Card className="border-2 border-amber-200 dark:border-amber-800 bg-gradient-to-br from-amber-50 to-yellow-50 dark:from-amber-950/30 dark:to-yellow-950/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🙏</span> Acknowledgments
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-white/70 dark:bg-slate-800/70 rounded-xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center shadow-md">
                <span className="text-2xl">☀️</span>
              </div>
              <div>
                <h3 className="text-xl font-bold text-amber-800 dark:text-amber-300">Solar Agrotech Private Limited</h3>
                <p className="text-amber-600 dark:text-amber-400">Proud Sponsor & Resource Provider</p>
              </div>
            </div>
            <p className="text-foreground leading-relaxed">
              This application was built thanks to the generous support and resources provided by 
              <span className="font-semibold text-amber-700 dark:text-amber-400"> Solar Agrotech Private Limited</span>. 
              Their commitment to agricultural innovation and technology has made it possible to develop 
              Bijmantra as an open-source platform for the global plant breeding community.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-white/70 dark:bg-slate-800/70 rounded-lg">
              <span className="text-2xl">👨‍🔬</span>
              <h4 className="font-semibold mt-2 text-foreground">Dr. T. L. Dholaria</h4>
              <p className="text-sm text-muted-foreground">
                For the foundational knowledge in plant breeding and genetics, and for showing that 
                science begins in the field, not just the laboratory.
              </p>
            </div>
            <div className="p-4 bg-white/70 dark:bg-slate-800/70 rounded-lg">
              <span className="text-2xl">🌏</span>
              <h4 className="font-semibold mt-2 text-foreground">Open Source Community</h4>
              <p className="text-sm text-muted-foreground">
                For the countless tools, libraries, and inspiration that make projects like this possible.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Ethical Use Notice */}
      <Card className="border-2 border-red-200 dark:border-red-800 bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950/30 dark:to-orange-950/30">
        <CardHeader className="text-center pb-2">
          <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-orange-600 rounded-full flex items-center justify-center shadow-lg mx-auto mb-4">
            <span className="text-2xl">🚫</span>
          </div>
          <CardTitle className="text-xl text-red-800 dark:text-red-300">Ethical Use Policy</CardTitle>
          <CardDescription className="text-base text-red-700 dark:text-red-400">Protecting Farmers' Rights & Seed Sovereignty</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-white/80 dark:bg-slate-800/80 rounded-xl p-6">
            <p className="text-foreground leading-relaxed font-medium text-center mb-4">
              Bijmantra is <span className="text-red-600 dark:text-red-400 font-bold">STRICTLY PROHIBITED</span> for use in developing:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 bg-red-100 dark:bg-red-900/40 rounded-lg">
                <span className="font-semibold text-red-800 dark:text-red-300">🚫 Terminator Technology</span>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">Seeds engineered to be sterile</p>
              </div>
              <div className="p-3 bg-red-100 dark:bg-red-900/40 rounded-lg">
                <span className="font-semibold text-red-800 dark:text-red-300">🚫 GURTs</span>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">Genetic Use Restriction Technologies</p>
              </div>
              <div className="p-3 bg-red-100 dark:bg-red-900/40 rounded-lg">
                <span className="font-semibold text-red-800 dark:text-red-300">🚫 Traitor Technology</span>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">Chemical-dependent trait activation</p>
              </div>
              <div className="p-3 bg-red-100 dark:bg-red-900/40 rounded-lg">
                <span className="font-semibold text-red-800 dark:text-red-300">🚫 Seed Termination</span>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">Any tech preventing seed saving</p>
              </div>
            </div>
            <p className="text-center mt-4 text-muted-foreground italic">
              "Seeds are the foundation of life. The ability of seeds to reproduce is a gift of nature 
              that belongs to all humanity, not a feature to be engineered away for corporate profit."
            </p>
            <p className="text-center text-sm text-muted-foreground mt-2">
              — Denish Dholaria, Creator of Bijmantra
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Inspiration Section - Prerna (प्रेरणा) */}
      <Card className="border-2 border-rose-200 dark:border-rose-800 bg-gradient-to-br from-rose-50 via-pink-50 to-orange-50 dark:from-rose-950/30 dark:via-pink-950/30 dark:to-orange-950/30">
        <CardHeader className="text-center pb-2">
          <div className="w-16 h-16 bg-gradient-to-br from-rose-500 to-orange-500 rounded-full flex items-center justify-center shadow-lg mx-auto mb-4">
            <span className="text-2xl">🕯️</span>
          </div>
          <CardTitle className="text-xl text-rose-800 dark:text-rose-300">Prerna (प्रेरणा)</CardTitle>
          <CardDescription className="text-base text-rose-600 dark:text-rose-400">For Those Who Work When the World Sleeps</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-white/80 dark:bg-slate-800/80 rounded-xl p-6 max-w-3xl mx-auto">
            <p className="text-foreground leading-relaxed italic text-center">
              "People are often unreasonable, illogical, and self-centered.<br/>
              <span className="font-semibold text-rose-700 dark:text-rose-400">Forgive them anyway.</span><br/><br/>
              If you are kind, people may accuse you of selfish ulterior motives.<br/>
              <span className="font-semibold text-rose-700 dark:text-rose-400">Be kind anyway.</span><br/><br/>
              If you are successful, you will win some false friends and some true enemies.<br/>
              <span className="font-semibold text-rose-700 dark:text-rose-400">Succeed anyway.</span><br/><br/>
              If you are honest and frank, people may cheat you.<br/>
              <span className="font-semibold text-rose-700 dark:text-rose-400">Be honest and frank anyway.</span><br/><br/>
              What you spend years building, someone could destroy overnight.<br/>
              <span className="font-semibold text-rose-700 dark:text-rose-400">Build anyway.</span><br/><br/>
              If you find serenity and happiness, they may be jealous.<br/>
              <span className="font-semibold text-rose-700 dark:text-rose-400">Be happy anyway.</span><br/><br/>
              The good you do today, people will often forget tomorrow.<br/>
              <span className="font-semibold text-rose-700 dark:text-rose-400">Do good anyway.</span><br/><br/>
              Give the world the best you have, and it may never be enough.<br/>
              <span className="font-semibold text-rose-700 dark:text-rose-400">Give the best you've got anyway.</span><br/><br/>
              You see, in the final analysis it is between you and God;<br/>
              it was never between you and them anyway."
            </p>
            <p className="text-center text-sm text-muted-foreground mt-4">
              — Often attributed to <span className="font-semibold">Mother Teresa</span> (found on her wall in Calcutta)<br/>
              Originally written by <span className="font-semibold">Kent M. Keith</span> as "The Paradoxical Commandments" (1968)
            </p>
          </div>
          <p className="text-center text-foreground max-w-2xl mx-auto mt-4">
            To every researcher working late nights alone in the lab, every scientist pursuing truth 
            against the odds, every student burning the midnight oil — you are not alone. 
            Your work matters. Keep going.
          </p>
          <div className="text-center">
            <Link to="/inspiration">
              <Button variant="outline" className="border-rose-300 text-rose-700 hover:bg-rose-50 dark:border-rose-700 dark:text-rose-300 dark:hover:bg-rose-950/50">
                <span className="mr-2">🏛️</span> Visit the Inspiration Museum
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Vision Section */}
      <Card className="border-2 border-indigo-200 dark:border-indigo-800 bg-gradient-to-br from-indigo-50 via-purple-50 to-slate-50 dark:from-indigo-950/30 dark:via-purple-950/30 dark:to-slate-950/30">
        <CardHeader className="text-center pb-2">
          <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg mx-auto mb-4">
            <span className="text-2xl">🌌</span>
          </div>
          <CardTitle className="text-xl text-indigo-800 dark:text-indigo-300">Our Vision</CardTitle>
          <CardDescription className="text-base text-indigo-600 dark:text-indigo-400">10, 100, and 1000 Year Plans</CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <p className="text-foreground max-w-2xl mx-auto">
            Bijmantra is built with a long-term perspective. We've documented our vision for the next decade, 
            century, and millennium — from AI-powered breeding to interplanetary agriculture.
          </p>
          <p className="text-indigo-700 dark:text-indigo-400 italic text-sm">
            "The seed contains the entire tree. The code contains the entire future."
          </p>
          <Link to="/vision">
            <Button className="bg-indigo-600 hover:bg-indigo-700">
              <span className="mr-2">🔭</span> Explore Our Vision
            </Button>
          </Link>
        </CardContent>
      </Card>

      {/* Footer CTA */}
      <div className="text-center py-8 space-y-4">
        <p className="text-lg text-muted-foreground italic">
          🌾 Thank you to all those who work in acres, not in hours.
        </p>
        <p className="text-muted-foreground">
          Built with 💚 for the global plant breeding community
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link to="/dashboard">
            <Button>
              <span className="mr-2">🏠</span> Go to Dashboard
            </Button>
          </Link>
          <Link to="/inspiration">
            <Button variant="outline" className="border-rose-300 text-rose-700 hover:bg-rose-50 dark:border-rose-700 dark:text-rose-300 dark:hover:bg-rose-950/50">
              <span className="mr-2">🏛️</span> Inspiration Museum
            </Button>
          </Link>
          <Link to="/vision">
            <Button variant="outline" className="border-indigo-300 text-indigo-700 hover:bg-indigo-50">
              <span className="mr-2">🌌</span> Our Vision
            </Button>
          </Link>
          <Link to="/dev-progress">
            <Button variant="outline" className="border-green-300 text-green-700 hover:bg-green-50">
              <span className="mr-2">📊</span> Dev Progress
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
            © 2025 Bijmantra by R.E.E.V.A.i • Open Source Agricultural Research Platform
          </p>
          <p className="text-xs text-muted-foreground">
            Supported by Solar Agrotech Private Limited
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            <Link to="/terms" className="text-green-600 hover:underline">BSAL License</Link> - Free to use, pay to sell
          </p>
          <p className="text-xs text-muted-foreground mt-4 italic">
            जय श्री गणेशाय नमो नमः! 🙏
          </p>
        </div>
      </div>
    </div>
  )
}
