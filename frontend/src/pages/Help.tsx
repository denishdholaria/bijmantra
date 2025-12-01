/**
 * Help & Documentation Page
 * User guide and BrAPI reference
 */

import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function Help() {
  const modules = [
    { name: 'Programs', icon: '🌾', path: '/programs', desc: 'Manage breeding programs and objectives' },
    { name: 'Germplasm', icon: '🌱', path: '/germplasm', desc: 'Track genetic material with MCPD compliance' },
    { name: 'Seed Lots', icon: '📦', path: '/seedlots', desc: 'Inventory management and stock tracking' },
    { name: 'Crosses', icon: '🧬', path: '/crosses', desc: 'Plan and record breeding crosses' },
    { name: 'Traits', icon: '🔬', path: '/traits', desc: 'Define observation variables (trait + method + scale)' },
    { name: 'Observations', icon: '📋', path: '/observations', desc: 'Collect and manage phenotypic data' },
    { name: 'Units', icon: '🌿', path: '/observationunits', desc: 'Manage plots, plants, and samples' },
    { name: 'Events', icon: '📆', path: '/events', desc: 'Log field activities and treatments' },
    { name: 'Trials', icon: '🧪', path: '/trials', desc: 'Organize field trials' },
    { name: 'Studies', icon: '📈', path: '/studies', desc: 'Research studies within trials' },
    { name: 'Locations', icon: '📍', path: '/locations', desc: 'Field sites with coordinates' },
    { name: 'Samples', icon: '🧫', path: '/samples', desc: 'Genotyping sample management' },
    { name: 'People', icon: '👥', path: '/people', desc: 'Team members and contacts' },
    { name: 'Lists', icon: '📋', path: '/lists', desc: 'Organize items into lists' },
    { name: 'Seasons', icon: '📅', path: '/seasons', desc: 'Growing seasons and time periods' },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">Help & Documentation</h1>
        <p className="text-muted-foreground mt-1">Learn how to use Bijmantra</p>
      </div>

      <Tabs defaultValue="quickstart" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="quickstart">Quick Start</TabsTrigger>
          <TabsTrigger value="modules">Modules</TabsTrigger>
          <TabsTrigger value="brapi">BrAPI</TabsTrigger>
          <TabsTrigger value="about">About</TabsTrigger>
        </TabsList>

        <TabsContent value="quickstart" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Getting Started</CardTitle>
              <CardDescription>Start using Bijmantra in 5 steps</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4 p-4 bg-muted rounded-lg">
                <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold">1</div>
                <div>
                  <h4 className="font-semibold">Create a Program</h4>
                  <p className="text-sm text-muted-foreground">Start by creating a breeding program to organize your work</p>
                  <Link to="/programs/new" className="text-primary text-sm hover:underline">Create Program →</Link>
                </div>
              </div>
              <div className="flex gap-4 p-4 bg-muted rounded-lg">
                <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold">2</div>
                <div>
                  <h4 className="font-semibold">Add Germplasm</h4>
                  <p className="text-sm text-muted-foreground">Register your genetic material with MCPD-compliant data</p>
                  <Link to="/germplasm/new" className="text-primary text-sm hover:underline">Add Germplasm →</Link>
                </div>
              </div>
              <div className="flex gap-4 p-4 bg-muted rounded-lg">
                <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold">3</div>
                <div>
                  <h4 className="font-semibold">Define Traits</h4>
                  <p className="text-sm text-muted-foreground">Create observation variables with trait, method, and scale</p>
                  <Link to="/traits/new" className="text-primary text-sm hover:underline">Define Trait →</Link>
                </div>
              </div>
              <div className="flex gap-4 p-4 bg-muted rounded-lg">
                <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold">4</div>
                <div>
                  <h4 className="font-semibold">Create a Trial & Study</h4>
                  <p className="text-sm text-muted-foreground">Set up field trials and studies for data collection</p>
                  <Link to="/trials/new" className="text-primary text-sm hover:underline">Create Trial →</Link>
                </div>
              </div>
              <div className="flex gap-4 p-4 bg-muted rounded-lg">
                <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold">5</div>
                <div>
                  <h4 className="font-semibold">Collect Data</h4>
                  <p className="text-sm text-muted-foreground">Record observations using the mobile-friendly data collection interface</p>
                  <Link to="/observations/collect" className="text-primary text-sm hover:underline">Collect Data →</Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="modules" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {modules.map((module) => (
              <Link key={module.path} to={module.path}>
                <Card className="h-full hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{module.icon}</span>
                      <h3 className="font-semibold">{module.name}</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">{module.desc}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="brapi" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>BrAPI v2.1 Compliance</CardTitle>
              <CardDescription>Breeding API standard implementation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>Bijmantra implements the BrAPI (Breeding API) v2.1 specification for interoperability with other breeding management systems.</p>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-semibold text-green-800">BrAPI-Core</h4>
                  <p className="text-sm text-green-700">Programs, Trials, Studies, Locations, People, Lists, Seasons</p>
                  <Badge className="mt-2 bg-green-600">7/9 Implemented</Badge>
                </div>
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-800">BrAPI-Germplasm</h4>
                  <p className="text-sm text-blue-700">Germplasm, Seed Lots, Crosses, Pedigree</p>
                  <Badge className="mt-2 bg-blue-600">3/7 Implemented</Badge>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <h4 className="font-semibold text-purple-800">BrAPI-Phenotyping</h4>
                  <p className="text-sm text-purple-700">Variables, Observations, Units, Events, Images</p>
                  <Badge className="mt-2 bg-purple-600">5/6 Implemented</Badge>
                </div>
                <div className="p-4 bg-orange-50 rounded-lg">
                  <h4 className="font-semibold text-orange-800">BrAPI-Genotyping</h4>
                  <p className="text-sm text-orange-700">Samples, Variants, Calls, Allele Matrix</p>
                  <Badge className="mt-2 bg-orange-600">1/11 Implemented</Badge>
                </div>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <h4 className="font-semibold mb-2">Resources</h4>
                <ul className="space-y-1 text-sm">
                  <li><a href="https://brapi.org" target="_blank" rel="noopener" className="text-primary hover:underline">BrAPI Official Website</a></li>
                  <li><a href="https://app.swaggerhub.com/apis/PlantBreedingAPI/" target="_blank" rel="noopener" className="text-primary hover:underline">BrAPI Specification (SwaggerHub)</a></li>
                  <li><a href="https://github.com/plantbreeding/BrAPI" target="_blank" rel="noopener" className="text-primary hover:underline">BrAPI GitHub Repository</a></li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="about" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>About Bijmantra</CardTitle>
              <CardDescription>Modern plant breeding management</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>Bijmantra is a modern, BrAPI v2.1 compliant Progressive Web Application for plant breeding management. It provides comprehensive tools for managing breeding programs, germplasm, trials, and phenotypic data collection.</p>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-semibold">Version</h4>
                  <p className="text-2xl font-mono">1.0.0</p>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-semibold">BrAPI Version</h4>
                  <p className="text-2xl font-mono">2.1</p>
                </div>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <h4 className="font-semibold mb-2">Technology Stack</h4>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">React 18</Badge>
                  <Badge variant="outline">TypeScript</Badge>
                  <Badge variant="outline">Vite</Badge>
                  <Badge variant="outline">TailwindCSS</Badge>
                  <Badge variant="outline">shadcn/ui</Badge>
                  <Badge variant="outline">React Query</Badge>
                  <Badge variant="outline">FastAPI</Badge>
                  <Badge variant="outline">PostgreSQL</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
