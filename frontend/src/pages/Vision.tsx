/**
 * Vision Page
 * 
 * A contemplative, immersive reading experience for Bijmantra's
 * 10-year, 100-year, and 1000-year vision documents.
 * 
 * "The seed contains the entire tree"
 */
import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Link } from 'react-router-dom'
import { 
  Rocket, 
  Globe, 
  Sparkles, 
  ChevronRight,
  ArrowLeft,
  Star,
  Leaf,
  Sun,
  Moon,
  BookOpen,
  Wheat,
  TreeDeciduous,
  RefreshCw,
  Scale,
  Heart,
  Target,
  Orbit
} from 'lucide-react'

export function Vision() {
  const [activeTab, setActiveTab] = useState('10')

  return (
    <div className="min-h-screen">
      {/* Hero Section with Starfield Effect */}
      <div className="relative overflow-hidden bg-gradient-to-b from-slate-900 via-indigo-950 to-slate-900 text-white py-16 px-4">
        {/* Animated Stars Background */}
        <div className="absolute inset-0 overflow-hidden">
          {[...Array(50)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-white rounded-full animate-pulse"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 3}s`,
                animationDuration: `${2 + Math.random() * 3}s`,
                opacity: 0.3 + Math.random() * 0.7,
              }}
            />
          ))}
        </div>
        
        <div className="relative z-10 max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-6">
            <Moon className="w-6 h-6 text-slate-400" />
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center shadow-2xl shadow-emerald-500/30">
              <Leaf className="w-8 h-8 text-white" />
            </div>
            <Sun className="w-6 h-6 text-amber-400" />
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-emerald-300 via-teal-200 to-cyan-300 bg-clip-text text-transparent">
            The Bijmantra Vision
          </h1>
          
          <p className="text-xl text-slate-300 mb-6 font-light italic">
            "बीजं मां सर्वभूतानां विद्धि पार्थ सनातनम्"
          </p>
          <p className="text-sm text-slate-400 mb-8">
            "Know Me to be the eternal seed of all beings" — Bhagavad Gita 7.10
          </p>
          
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30">
              <Sparkles className="w-3 h-3 mr-1" /> 10 Years
            </Badge>
            <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30">
              <Globe className="w-3 h-3 mr-1" /> 100 Years
            </Badge>
            <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30">
              <Rocket className="w-3 h-3 mr-1" /> 1000 Years
            </Badge>
          </div>
        </div>
      </div>

      {/* Navigation Back */}
      <div className="max-w-5xl mx-auto px-4 py-4">
        <Link to="/about">
          <Button variant="ghost" size="sm" className="text-muted-foreground">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to About
          </Button>
        </Link>
      </div>

      {/* Vision Tabs */}
      <div className="max-w-5xl mx-auto px-4 pb-16">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="10" className="data-[state=active]:bg-emerald-100 data-[state=active]:text-emerald-700">
              <Sparkles className="w-4 h-4 mr-2" /> 10 Years
            </TabsTrigger>
            <TabsTrigger value="100" className="data-[state=active]:bg-blue-100 data-[state=active]:text-blue-700">
              <Globe className="w-4 h-4 mr-2" /> 100 Years
            </TabsTrigger>
            <TabsTrigger value="1000" className="data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700">
              <Rocket className="w-4 h-4 mr-2" /> 1000 Years
            </TabsTrigger>
          </TabsList>

          {/* 10 Year Vision */}
          <TabsContent value="10" className="space-y-6 animate-fade-in">
            <Vision10Years />
          </TabsContent>

          {/* 100 Year Vision */}
          <TabsContent value="100" className="space-y-6 animate-fade-in">
            <Vision100Years />
          </TabsContent>

          {/* 1000 Year Vision */}
          <TabsContent value="1000" className="space-y-6 animate-fade-in">
            <Vision1000Years />
          </TabsContent>
        </Tabs>
      </div>

      {/* Footer */}
      <div className="bg-slate-50 border-t py-12 text-center">
        <p className="text-slate-600 italic mb-4">
          "The seed contains the entire tree. The code contains the entire future."
        </p>
        <p className="text-emerald-600 font-semibold">
          One Seed. Infinite Worlds. 🌱
        </p>
      </div>
    </div>
  )
}

// 10 Year Vision Component
function Vision10Years() {
  const phases = [
    {
      title: 'Phase 1: Foundation (2025-2027)',
      color: 'emerald',
      items: [
        { year: '2025', title: 'Core Platform', status: 'active', items: ['210+ pages built', 'BrAPI v2.1 compliant', 'Veena AI assistant', 'Offline-first PWA'] },
        { year: '2026', title: 'AI/ML Maturity', status: 'planned', items: ['Computer Vision', 'Yield Prediction', 'Cross Prediction', 'Federated Learning'] },
        { year: '2027', title: 'Enterprise Scale', status: 'planned', items: ['Multi-tenant SaaS', 'White-label', 'Enterprise SSO', 'Audit & Compliance'] },
      ]
    },
    {
      title: 'Phase 2: Expansion (2028-2030)',
      color: 'blue',
      items: [
        { year: '2028-29', title: 'Global Adoption', status: 'future', items: ['50+ languages', 'Mobile-native apps', 'IoT Integration', 'Blockchain Traceability'] },
        { year: '2030', title: 'Industry Standard', status: 'future', items: ['10,000+ programs', 'BrAPI 3.0 co-author', '100+ universities', 'Government adoption'] },
      ]
    },
    {
      title: 'Phase 3: Innovation (2031-2035)',
      color: 'purple',
      items: [
        { year: '2031-32', title: 'Next-Gen AI', status: 'visionary', items: ['Autonomous breeding agents', 'Digital twins', 'Quantum-ready algorithms'] },
        { year: '2033-35', title: 'Frontier Science', status: 'visionary', items: ['Climate adaptation models', 'Gene editing integration', 'Space agriculture prep'] },
      ]
    }
  ]

  const metrics = [
    { label: 'Active Programs', current: '10', target2030: '1,000', target2035: '10,000' },
    { label: 'Countries', current: '1', target2030: '50', target2035: '100+' },
    { label: 'Users', current: '100', target2030: '50,000', target2035: '500,000' },
    { label: 'Genetic Gain Improvement', current: '-', target2030: '15%', target2035: '30%' },
  ]

  return (
    <>
      <Card className="border-2 border-emerald-200 bg-gradient-to-br from-emerald-50 to-teal-50">
        <CardContent className="pt-6">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-emerald-800">2025 - 2035</h2>
            <p className="text-emerald-600">Practical Roadmap to Global Standard</p>
          </div>
          <p className="text-slate-700 leading-relaxed text-center max-w-3xl mx-auto">
            By 2035, Bijmantra will be the <strong>global standard for plant breeding data management</strong>, 
            serving 10,000+ breeding programs across 100+ countries, with AI-powered decision support 
            that accelerates genetic gain by 30%.
          </p>
        </CardContent>
      </Card>

      {/* Timeline */}
      {phases.map((phase, pi) => (
        <Card key={pi}>
          <CardContent className="pt-6">
            <h3 className={`text-lg font-bold text-${phase.color}-700 mb-4 flex items-center gap-2`}>
              <ChevronRight className="w-5 h-5" /> {phase.title}
            </h3>
            <div className="grid md:grid-cols-3 gap-4">
              {phase.items.map((item, i) => (
                <div key={i} className={`p-4 rounded-lg ${
                  item.status === 'active' ? 'bg-emerald-50 border-2 border-emerald-200' :
                  item.status === 'planned' ? 'bg-blue-50 border border-blue-200' :
                  item.status === 'future' ? 'bg-slate-50 border border-slate-200' :
                  'bg-purple-50 border border-purple-200'
                }`}>
                  <Badge variant="outline" className="mb-2">{item.year}</Badge>
                  <h4 className="font-semibold">{item.title}</h4>
                  <ul className="mt-2 space-y-1">
                    {item.items.map((li, j) => (
                      <li key={j} className="text-sm text-slate-600 flex items-start gap-1">
                        <Star className="w-3 h-3 mt-1 text-amber-500 flex-shrink-0" />
                        {li}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Metrics */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-bold mb-4">🎯 Key Metrics (2035 Targets)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Metric</th>
                  <th className="text-center py-2">2025</th>
                  <th className="text-center py-2">2030</th>
                  <th className="text-center py-2">2035</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((m, i) => (
                  <tr key={i} className="border-b">
                    <td className="py-2 font-medium">{m.label}</td>
                    <td className="text-center py-2 text-slate-500">{m.current}</td>
                    <td className="text-center py-2 text-blue-600">{m.target2030}</td>
                    <td className="text-center py-2 text-emerald-600 font-bold">{m.target2035}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </>
  )
}


// 100 Year Vision Component
function Vision100Years() {
  const eras = [
    {
      name: 'Era 1: Digital Transformation',
      period: '2025-2050',
      color: 'emerald',
      description: 'Mastering Earth agriculture with AI and genomics',
      milestones: [
        'Universal adoption of breeding software',
        'AI co-breeders designing experiments',
        '50% faster variety development',
        'Climate-adapted varieties for 2050',
        'Vertical farming integration'
      ]
    },
    {
      name: 'Era 2: Planetary Expansion',
      period: '2050-2100',
      color: 'blue',
      description: 'Expanding to Moon, Mars, and orbital stations',
      milestones: [
        'Lunar greenhouses operational',
        'Mars agriculture established',
        'Generation ship seed banks',
        'Radiation-hardened germplasm',
        'Multi-planet breeding programs'
      ]
    },
    {
      name: 'Era 3: Universal Food Security',
      period: '2100-2125',
      color: 'purple',
      description: 'No human goes hungry, anywhere',
      milestones: [
        'Terraforming pioneer crops',
        'Autonomous breeding stations',
        'Complete genetic libraries',
        'Post-scarcity food systems',
        'Foundation for interstellar expansion'
      ]
    }
  ]

  const legacyGoals = [
    { period: '2050', title: 'For Our Children', goals: ['No child goes hungry', 'Climate-resilient food systems', 'Preserved crop diversity'] },
    { period: '2075', title: 'For Our Grandchildren', goals: ['Sustainable agriculture everywhere', 'Space agriculture established', 'Recovered extinct species'] },
    { period: '2125', title: 'For Future Generations', goals: ['Multi-planet food security', 'Complete genetic knowledge', 'Foundation for interstellar expansion'] },
  ]

  return (
    <>
      <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">
        <CardContent className="pt-6">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-blue-800">2025 - 2125</h2>
            <p className="text-blue-600">Planetary Expansion & Universal Food Security</p>
          </div>
          <p className="text-slate-700 leading-relaxed text-center max-w-3xl mx-auto">
            By 2125, humanity will face challenges we can barely imagine. Climate change, population growth, 
            and interplanetary colonization will reshape agriculture. Bijmantra's role is to be the 
            <strong> knowledge infrastructure</strong> that enables humanity to feed itself across all these transformations.
          </p>
        </CardContent>
      </Card>

      {/* Eras */}
      <div className="grid md:grid-cols-3 gap-4">
        {eras.map((era, i) => (
          <Card key={i} className={`border-2 border-${era.color}-200`}>
            <CardContent className="pt-6">
              <Badge className={`bg-${era.color}-100 text-${era.color}-700 mb-2`}>{era.period}</Badge>
              <h3 className={`font-bold text-${era.color}-800`}>{era.name}</h3>
              <p className="text-sm text-slate-600 mt-1 mb-3">{era.description}</p>
              <ul className="space-y-2">
                {era.milestones.map((m, j) => (
                  <li key={j} className="text-sm flex items-start gap-2">
                    <Globe className={`w-4 h-4 mt-0.5 text-${era.color}-500 flex-shrink-0`} />
                    {m}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Legacy Goals */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-lg font-bold mb-4">📜 Legacy Goals</h3>
          <div className="grid md:grid-cols-3 gap-4">
            {legacyGoals.map((lg, i) => (
              <div key={i} className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg border border-amber-200">
                <Badge variant="outline" className="mb-2">{lg.period}</Badge>
                <h4 className="font-semibold text-amber-800">{lg.title}</h4>
                <ul className="mt-2 space-y-1">
                  {lg.goals.map((g, j) => (
                    <li key={j} className="text-sm text-amber-700">• {g}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Preserved Principles */}
      <Card className="bg-gradient-to-br from-slate-50 to-slate-100">
        <CardContent className="pt-6">
          <h3 className="text-lg font-bold mb-4">🌱 Preserved Principles</h3>
          <p className="text-slate-600 mb-4">Through all transformations, these principles remain:</p>
          <div className="grid md:grid-cols-3 gap-3">
            {[
              { icon: BookOpen, title: 'Open Knowledge', desc: 'Breeding data is a public good', color: 'bg-blue-100 text-blue-600' },
              { icon: Wheat, title: 'Farmer Sovereignty', desc: 'Farmers own their data and seeds', color: 'bg-amber-100 text-amber-600' },
              { icon: TreeDeciduous, title: 'Biodiversity', desc: 'Preserve all genetic diversity', color: 'bg-green-100 text-green-600' },
              { icon: RefreshCw, title: 'Sustainability', desc: 'Agriculture must regenerate', color: 'bg-emerald-100 text-emerald-600' },
              { icon: Scale, title: 'Equity', desc: 'Technology serves all', color: 'bg-purple-100 text-purple-600' },
              { icon: Heart, title: 'Humility', desc: 'We are stewards of nature', color: 'bg-pink-100 text-pink-600' },
            ].map((p, i) => (
              <div key={i} className="p-3 bg-white rounded-lg shadow-sm">
                <div className={`w-8 h-8 rounded-lg ${p.color} flex items-center justify-center`}>
                  <p.icon className="h-4 w-4" />
                </div>
                <h4 className="font-semibold mt-1">{p.title}</h4>
                <p className="text-xs text-slate-600">{p.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </>
  )
}

// 1000 Year Vision Component
function Vision1000Years() {
  const horizons = [
    {
      name: 'Horizon 1: Planetary',
      period: '2025-2200',
      icon: Globe,
      color: 'emerald',
      focus: 'Mastering Earth and near-space agriculture',
      items: ['Complete understanding of plant genetics', 'Climate-proof food systems', 'Lunar and Martian agriculture', 'Synthetic food production']
    },
    {
      name: 'Horizon 2: Stellar',
      period: '2200-2500',
      icon: Star,
      color: 'blue',
      focus: 'Expanding to other star systems',
      items: ['Generation ship seed banks', 'Exoplanet adaptation breeding', 'Light-year communication protocols', 'Autonomous breeding AI colonies']
    },
    {
      name: 'Horizon 3: Galactic',
      period: '2500-3025',
      icon: Orbit,
      color: 'purple',
      focus: 'Becoming a multi-stellar civilization',
      items: ['Galactic germplasm network', 'Universal genetic language', 'Post-biological agriculture', 'Cosmic-scale food security']
    }
  ]

  const eternalPrinciples = [
    { sanskrit: 'अहिंसा परमो धर्मः', translation: 'Non-violence is the highest duty', meaning: 'All life is sacred. Agriculture must nurture, not exploit.' },
    { sanskrit: 'वसुधैव कुटुम्बकम्', translation: 'The world is one family', meaning: 'We are caretakers for future generations, not owners.' },
    { sanskrit: 'विद्या ददाति विनयम्', translation: 'Knowledge gives humility', meaning: 'Knowledge exists to serve all beings, not to dominate.' },
    { sanskrit: 'चरैवेति चरैवेति', translation: 'Keep moving, keep moving', meaning: 'Never stop learning, adapting, improving.' },
  ]

  return (
    <>
      <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 via-indigo-50 to-slate-900 text-white overflow-hidden">
        <CardContent className="pt-6 relative">
          {/* Stars overlay */}
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-slate-900/90" />
          <div className="relative z-10">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-purple-800">2025 - 3025</h2>
              <p className="text-purple-600">The Millennial Perspective</p>
            </div>
            <div className="bg-white/80 rounded-xl p-6 max-w-3xl mx-auto">
              <p className="text-slate-700 leading-relaxed text-center">
                A thousand years ago, humanity had no concept of genetics, no understanding of DNA. 
                In a thousand years, our descendants will look back at our current understanding as we look at medieval alchemy.
                This is not a plan — it is a <strong>philosophical framework</strong> for thinking about agriculture across civilizational timescales.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Three Horizons */}
      <div className="space-y-4">
        {horizons.map((h, i) => (
          <Card key={i} className={`border-l-4 border-l-${h.color}-500`}>
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className={`w-16 h-16 bg-${h.color}-100 rounded-xl flex items-center justify-center flex-shrink-0`}>
                  <h.icon className={`h-8 w-8 text-${h.color}-600`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className={`font-bold text-${h.color}-800`}>{h.name}</h3>
                    <Badge variant="outline">{h.period}</Badge>
                  </div>
                  <p className="text-sm text-slate-600 mb-3">{h.focus}</p>
                  <div className="flex flex-wrap gap-2">
                    {h.items.map((item, j) => (
                      <Badge key={j} variant="secondary" className="text-xs">{item}</Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Eternal Principles */}
      <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200">
        <CardContent className="pt-6">
          <h3 className="text-lg font-bold text-amber-800 mb-4">🕉️ Eternal Principles</h3>
          <p className="text-amber-700 mb-4">No matter what technologies emerge, these principles endure:</p>
          <div className="grid md:grid-cols-2 gap-4">
            {eternalPrinciples.map((p, i) => (
              <div key={i} className="bg-white/70 rounded-lg p-4">
                <p className="text-lg font-semibold text-amber-800 mb-1">{p.sanskrit}</p>
                <p className="text-sm text-amber-600 italic mb-2">"{p.translation}"</p>
                <p className="text-sm text-slate-600">{p.meaning}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Message to the Future */}
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 text-white">
        <CardContent className="pt-6">
          <h3 className="text-lg font-bold mb-4">📜 Message to the Future</h3>
          <div className="bg-white/10 rounded-xl p-6">
            <p className="text-slate-300 leading-relaxed mb-4">
              To those who read this in 3025:
            </p>
            <p className="text-slate-200 leading-relaxed mb-4">
              We do not know what challenges you face, what technologies you wield, what wisdom you have gained. But we hope:
            </p>
            <ul className="space-y-2 text-slate-300">
              <li>• <strong className="text-emerald-400">You still grow food</strong> — That the sacred act of cultivation continues</li>
              <li>• <strong className="text-blue-400">You remember us</strong> — That our efforts contributed to your world</li>
              <li>• <strong className="text-purple-400">You preserved diversity</strong> — That no species was lost through our negligence</li>
              <li>• <strong className="text-amber-400">You feed all beings</strong> — That hunger is a memory, not a reality</li>
              <li>• <strong className="text-pink-400">You continue the journey</strong> — That you too plant seeds for the next millennium</li>
            </ul>
            <p className="text-slate-400 mt-6 text-sm italic">
              We built Bijmantra with love, hope, and humility. We knew we could not see the future, 
              but we tried to build something worthy of it.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Closing Meditation */}
      <Card className="text-center bg-gradient-to-br from-indigo-50 to-purple-50">
        <CardContent className="pt-6">
          <h3 className="text-lg font-bold text-indigo-800 mb-4">🕉️ Closing Meditation</h3>
          <div className="max-w-2xl mx-auto space-y-4">
            <p className="text-indigo-700 font-medium">
              ॐ सर्वे भवन्तु सुखिनः — May all beings be happy
            </p>
            <p className="text-indigo-700 font-medium">
              सर्वे सन्तु निरामयाः — May all beings be healthy
            </p>
            <p className="text-indigo-700 font-medium">
              सर्वे भद्राणि पश्यन्तु — May all beings see goodness
            </p>
            <p className="text-indigo-700 font-medium">
              मा कश्चिद्दुःखभाग्भवेत् — May no one suffer
            </p>
          </div>
        </CardContent>
      </Card>
    </>
  )
}
